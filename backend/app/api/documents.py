import os
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.api.cases import find_case_by_identifier
from backend.app.api.deps import get_current_user, get_db, require_roles, verify_case_access
from backend.app.models.audit import AuditAction, AuditStatus
from backend.app.models.document import Document, DocumentProcessingStatus, DocumentVersion
from backend.app.models.user import User, UserRole
from backend.app.schemas.document import DocumentOut
from backend.app.services.audit_service import log_audit_event
from backend.app.services.document_service import save_fir_document, validate_file

router = APIRouter(tags=["FIR Documents"])


@router.post("/cases/{case_id}/documents/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_fir_document(
    request: Request,
    case_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.INVESTIGATOR])),
):
    """
    Upload and register an FIR document (PDF, JPG, PNG).
    Validates file type, size limit, filename, content-type, and magic bytes.
    Computes SHA-256 cryptographic hash and creates immutable version record.
    """
    case = find_case_by_identifier(case_id, db)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    # Enforce case-level authorization
    verify_case_access(case, current_user)

    # Read binary contents
    file_bytes = await file.read()

    # Validate file security and headers
    sanitized_name, ext = validate_file(file, file_bytes)

    # Store file immutably on disk
    stored_name, full_path, sha256_hash = save_fir_document(
        case_id=case.id,
        original_name=sanitized_name,
        ext=ext,
        file_bytes=file_bytes,
    )

    # Create Document record
    db_doc = Document(
        case_id=case.id,
        filename=stored_name,
        original_filename=sanitized_name,
        file_path=full_path,
        file_size_bytes=len(file_bytes),
        mime_type=file.content_type or f"application/{ext.lstrip('.')}",
        sha256_hash=sha256_hash,
        uploaded_by_id=current_user.id,
        processing_status=DocumentProcessingStatus.PENDING,
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    # Create initial DocumentVersion record (v1)
    db_version = DocumentVersion(
        document_id=db_doc.id,
        version_number=1,
        file_path=full_path,
        file_size_bytes=len(file_bytes),
        sha256_hash=sha256_hash,
        uploaded_by_id=current_user.id,
    )
    db.add(db_version)
    db.commit()
    db.refresh(db_doc)

    # Log audit event
    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit_event(
        db=db,
        action=AuditAction.DOCUMENT_UPLOADED,
        user=current_user,
        resource_type="DOCUMENT",
        resource_id=str(db_doc.id),
        details=f"Uploaded FIR document '{sanitized_name}' ({len(file_bytes)} bytes, SHA-256: {sha256_hash}) for case {case.case_number}",
        ip_address=client_ip,
        status=AuditStatus.SUCCESS,
    )

    return db_doc


@router.get("/cases/{case_id}/documents", response_model=List[DocumentOut])
def list_case_documents(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all FIR documents registered under a case with authorization verification."""
    case = find_case_by_identifier(case_id, db)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    
    verify_case_access(case, current_user)

    documents = (
        db.query(Document)
        .filter(Document.case_id == case.id)
        .order_by(Document.created_at.desc())
        .all()
    )
    return documents


@router.get("/documents/{document_id}", response_model=DocumentOut)
def get_document_detail(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve document metadata and version history."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    verify_case_access(doc.case, current_user)
    return doc


@router.get("/documents/{document_id}/download")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download the original immutable document file."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    verify_case_access(doc.case, current_user)

    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored file not found on disk")

    return FileResponse(
        path=doc.file_path,
        filename=doc.original_filename,
        media_type=doc.mime_type or "application/octet-stream",
    )


@router.post("/documents/{document_id}/process", response_model=DocumentOut)
def process_document_pipeline(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.INVESTIGATOR, UserRole.ANALYST])),
):
    """
    Triggers the Document AI Processing Pipeline:
    Validation -> Preprocessing -> OCR -> Language Detection -> Text Storage -> Translation -> Entity Extraction -> Crime Classification.
    """
    from ai.pipeline import DocumentAIPipeline

    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    verify_case_access(doc.case, current_user)

    try:
        processed_doc = DocumentAIPipeline.process_document(
            document_id=doc.id,
            db=db,
            actor_user=current_user,
        )
        return processed_doc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document AI processing failed: {str(exc)}",
        )
