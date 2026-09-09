import json
import os
import tempfile
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db, require_roles, verify_case_access
from backend.app.models.audit import AuditAction, AuditStatus
from backend.app.models.case import Case, CasePriority, CaseStatus
from backend.app.models.document import Document, DocumentProcessingStatus, DocumentVersion
from backend.app.models.user import User, UserRole
from backend.app.schemas.case import CaseCreate, CaseOut, CaseUpdate
from backend.app.services.audit_service import log_audit_event
from backend.app.services.document_service import save_fir_document, validate_file

router = APIRouter(prefix="/cases", tags=["Cases"])


def _case_from_payload(case_in: CaseCreate, db: Session, current_user: User) -> Case:
    """Create the single, shared Case record used by every registration path."""
    existing = db.query(Case).filter(Case.case_number == case_in.case_number.strip()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Case with number '{case_in.case_number}' already exists.")
    assigned_id = case_in.assigned_officer_id if (current_user.role == UserRole.ADMIN and case_in.assigned_officer_id) else current_user.id
    return Case(
        case_number=case_in.case_number.strip(), title=case_in.title, description=case_in.description,
        crime_type=case_in.crime_type, status=case_in.status or CaseStatus.UNDER_INVESTIGATION,
        priority=case_in.priority or CasePriority.HIGH, police_station=case_in.police_station,
        district=case_in.district, state=case_in.state, location=case_in.location,
        incident_date=case_in.incident_date, created_by_id=current_user.id, assigned_officer_id=assigned_id,
        act_section=case_in.act_section,
        registration_method=case_in.registration_method,
        source_document_reference=case_in.source_document_reference,
        extraction_metadata=case_in.extraction_metadata,
    )


def _audit_case_created(db: Session, request: Request, current_user: User, case: Case, method: str, source_reference: Optional[str] = None) -> None:
    details = f"Registered case {case.case_number}: {case.title}. Registration method: {method}."
    if source_reference:
        details += f" Source document: {source_reference}."
    log_audit_event(db=db, action=AuditAction.CASE_CREATED, user=current_user, resource_type="CASE", resource_id=str(case.id), details=details, ip_address=request.client.host if request.client else "127.0.0.1", status=AuditStatus.SUCCESS)


def find_case_by_identifier(case_id: str, db: Session) -> Optional[Case]:
    """Retrieve case by numeric database ID or unique case_number string."""
    if case_id.isdigit():
        case = db.query(Case).filter(Case.id == int(case_id)).first()
        if case:
            return case
    return db.query(Case).filter(Case.case_number == case_id.strip()).first()


@router.get("", response_model=List[CaseOut])
@router.get("/", response_model=List[CaseOut])
def list_cases(
    status: Optional[CaseStatus] = None,
    crime_type: Optional[str] = None,
    priority: Optional[CasePriority] = None,
    district: Optional[str] = None,
    police_station: Optional[str] = None,
    crime_head: Optional[str] = None,
    fir_year: Optional[int] = Query(None, ge=1900, le=2100),
    fir_stage: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List cases with case-level authorization and search:
    - ADMIN sees all cases across the system.
    - Non-ADMIN users see only cases assigned to them or unassigned cases.
    - Search matches case_number, title, description, and location.
    """
    query = db.query(Case)

    # Case-level authorization filter
    if current_user.role != UserRole.ADMIN:
        query = query.filter(
            or_(
                Case.assigned_officer_id == current_user.id,
                Case.created_by_id == current_user.id,
                Case.assigned_officer_id == None,
            )
        )
    
    if status:
        query = query.filter(Case.status == status)
    if crime_type:
        query = query.filter(Case.crime_type.ilike(f"%{crime_type}%"))
    if priority:
        query = query.filter(Case.priority == priority)
    if district:
        query = query.filter(Case.district.ilike(f"%{district}%"))
    if police_station:
        query = query.filter(Case.police_station.ilike(f"%{police_station}%"))
    if crime_head:
        query = query.filter(Case.crime_head.ilike(f"%{crime_head}%"))
    if fir_year:
        query = query.filter(Case.fir_year == fir_year)
    if fir_stage:
        query = query.filter(Case.fir_stage.ilike(f"%{fir_stage}%"))
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Case.case_number.ilike(search_term),
                Case.title.ilike(search_term),
                Case.description.ilike(search_term),
                Case.location.ilike(search_term),
                Case.crime_type.ilike(search_term),
                Case.police_station.ilike(search_term),
                Case.district.ilike(search_term),
                Case.crime_head.ilike(search_term),
                Case.fir_stage.ilike(search_term),
            )
        )
    
    cases = query.order_by(Case.created_at.desc()).offset(skip).limit(limit).all()
    return cases


@router.post("", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
def create_case(
    request: Request,
    case_in: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.INVESTIGATOR])),
):
    """
    Register a new investigation case.
    Role requirement: ADMIN or INVESTIGATOR.
    """
    db_case = _case_from_payload(case_in, db, current_user)
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    _audit_case_created(db, request, current_user, db_case, case_in.registration_method)

    return db_case


@router.post("/ai-assisted/extract")
async def extract_case_intake(
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.INVESTIGATOR])),
):
    """Run the installed OCR and AI extractors before a case is registered.

    No Case or Document row is created here; review and explicit confirmation are
    required before anything is placed in the official registry.
    """
    file_bytes = await file.read()
    sanitized_name, ext = validate_file(file, file_bytes)
    temp_path = ""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name
        from ai.ocr.ocr_engine import OCREngine
        from ai.nlp.entity_extractor import EntityExtractor
        from ai.classification.classifier import DocumentClassifier

        ocr = OCREngine.extract_text(temp_path, mime_type=file.content_type)
        text = (ocr.text or "").strip()
        if not text:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No readable text was found in this document. Please upload a clearer document or register the case manually.")
        entities = [item.to_dict() for item in EntityExtractor.extract_entities(text)]
        law_sections = [item["normalized_value"] for item in entities if item["entity_type"] == "LAW_SECTION"]
        classification = DocumentClassifier.classify_document(text=text, law_sections=law_sections)

        def first(entity_type: str) -> Optional[str]:
            return next((item["normalized_value"] for item in entities if item["entity_type"] == entity_type), None)

        fields: Dict[str, Any] = {
            "case_number": first("CASE_NUMBER"),
            "police_station": first("POLICE_STATION"),
            "location": first("LOCATION"),
            "crime_type": classification.primary_category if classification else None,
            "act_section": "; ".join(law_sections) if law_sections else None,
            "description": text,
            "vehicles": [item["normalized_value"] for item in entities if item["entity_type"] == "VEHICLE"],
            "witnesses": [], "complainant": None, "victim": None, "accused": [],
        }
        return {
            "filename": sanitized_name,
            "fields": fields,
            "entities": entities,
            "metadata": {
                "ocr_engine": ocr.engine,
                "ocr_confidence": ocr.confidence,
                "detected_scripts": getattr(ocr, "detected_scripts", []),
                "extracted_at": datetime.now(timezone.utc).isoformat(),
            },
        }
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


@router.post("/ai-assisted/register", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
async def register_ai_assisted_case(
    request: Request,
    file: UploadFile = File(...),
    case_data: str = Form(...),
    extraction_metadata: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.INVESTIGATOR])),
):
    """Confirm an officer-reviewed AI intake and register it in the normal case system."""
    try:
        payload = json.loads(case_data)
        payload["registration_method"] = "AI_ASSISTED"
        payload["extraction_metadata"] = json.loads(extraction_metadata) if extraction_metadata else None
        case_in = CaseCreate.model_validate(payload)
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid case review data: {exc}")

    file_bytes = await file.read()
    sanitized_name, ext = validate_file(file, file_bytes)
    db_case = _case_from_payload(case_in, db, current_user)
    db.add(db_case)
    db.flush()
    try:
        stored_name, full_path, sha256_hash = save_fir_document(db_case.id, sanitized_name, ext, file_bytes)
        db_doc = Document(case_id=db_case.id, filename=stored_name, original_filename=sanitized_name, file_path=full_path,
                          file_size_bytes=len(file_bytes), mime_type=file.content_type or "application/octet-stream",
                          sha256_hash=sha256_hash, uploaded_by_id=current_user.id, processing_status=DocumentProcessingStatus.PENDING)
        db.add(db_doc)
        db.flush()
        db.add(DocumentVersion(document_id=db_doc.id, version_number=1, file_path=full_path, file_size_bytes=len(file_bytes), sha256_hash=sha256_hash, uploaded_by_id=current_user.id))
        db_case.source_document_reference = f"document:{db_doc.id}"
        db.commit()
        db.refresh(db_case)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="The case could not be registered with its source document. Please retry.")

    # Persist the source document through the existing processing pipeline after
    # registration; review data remains stored with the case regardless.
    try:
        from ai.pipeline import DocumentAIPipeline
        DocumentAIPipeline.process_document(db_doc.id, db, current_user)
    except Exception:
        # The document record retains the real pipeline failure state. Do not
        # invent extracted values or reverse an already confirmed registration.
        pass
    _audit_case_created(db, request, current_user, db_case, "AI_ASSISTED", db_case.source_document_reference)
    return db_case


@router.get("/{case_id}", response_model=CaseOut)
def get_case(
    request: Request,
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve details for a single case by ID or case_number.
    Enforces case-level authorization check.
    """
    case = find_case_by_identifier(case_id, db)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    
    # Enforce case authorization
    verify_case_access(case, current_user)

    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit_event(
        db=db,
        action=AuditAction.CASE_VIEWED,
        user=current_user,
        resource_type="CASE",
        resource_id=str(case.id),
        details=f"Viewed case {case.case_number}",
        ip_address=client_ip,
        status=AuditStatus.SUCCESS,
    )

    return case


@router.patch("/{case_id}", response_model=CaseOut)
@router.put("/{case_id}", response_model=CaseOut)
def update_case(
    case_id: str,
    case_update: CaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.INVESTIGATOR])),
):
    """
    Update case metadata or investigation status.
    Role requirement: ADMIN or assigned INVESTIGATOR.
    """
    case = find_case_by_identifier(case_id, db)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    
    # Enforce case authorization
    verify_case_access(case, current_user)
    
    update_data = case_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case, field, value)
    
    db.commit()
    db.refresh(case)
    return case
