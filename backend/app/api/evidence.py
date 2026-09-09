import json
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.case import Case
from backend.app.models.evidence import EvidenceType
from backend.app.models.user import User
from backend.app.schemas.custody import (
    CourtSubmissionRequest,
    CustodyChainResponse,
    EvidenceCreatePayload,
    EvidenceDetailOut,
    ExaminationCompleteRequest,
    ExaminationStartRequest,
    ForensicReportRequest,
    IntegrityVerificationResult,
    ReceiveRequest,
    ReturnRequest,
    SealRequest,
    TransferRequest,
)
from backend.app.services.evidence_service import EvidenceService

router = APIRouter(prefix="/cases", tags=["Chain of Custody"])


def resolve_case_id(case_id_str: str, db: Session) -> int:
    """Helper to resolve numeric case ID from integer string or case_number."""
    if case_id_str.isdigit():
        c = db.query(Case).filter(Case.id == int(case_id_str)).first()
        if c:
            return c.id
    c = db.query(Case).filter(Case.case_number == case_id_str.strip()).first()
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case identifier '{case_id_str}' not found.",
        )
    return c.id


@router.get("/{case_id}/evidence", response_model=List[EvidenceDetailOut])
def list_case_evidence(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all digital evidence items registered for a case."""
    cid = resolve_case_id(case_id, db)
    return EvidenceService.list_case_evidence(db, current_user, cid)


@router.post("/{case_id}/evidence", response_model=EvidenceDetailOut, status_code=status.HTTP_201_CREATED)
async def add_evidence(
    case_id: str,
    request: Request,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    evidence_type: Optional[str] = Form("DIGITAL_FILE"),
    collection_location: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Register new evidence file into the Digital Chain of Custody.
    Supports multipart form-data (file upload) or JSON payload.
    """
    cid = resolve_case_id(case_id, db)
    content_type = request.headers.get("content-type", "")

    file_bytes: Optional[bytes] = None
    original_filename: Optional[str] = None
    mime_type: Optional[str] = None

    if title is not None or file is not None:
        if file is not None:
            file_bytes = await file.read()
            original_filename = file.filename
            mime_type = file.content_type
        
        req_title = title or original_filename or "Registered Evidence"
        req_type = EvidenceType.DIGITAL_FILE
        if evidence_type:
            try:
                req_type = EvidenceType(evidence_type.upper())
            except ValueError:
                req_type = EvidenceType.DIGITAL_FILE

        payload = EvidenceCreatePayload(
            title=req_title,
            description=description,
            evidence_type=req_type,
            collection_location=collection_location,
            notes=notes,
        )
    else:
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request body must be valid JSON or form payload.",
            )
        
        req_type = EvidenceType.DIGITAL_FILE
        if "evidence_type" in body and body["evidence_type"]:
            try:
                req_type = EvidenceType(body["evidence_type"].upper())
            except ValueError:
                req_type = EvidenceType.DIGITAL_FILE

        payload = EvidenceCreatePayload(
            title=body.get("title", "Registered Evidence"),
            description=body.get("description"),
            evidence_type=req_type,
            collection_location=body.get("collection_location"),
            notes=body.get("notes"),
        )
        if "file_content_text" in body and body["file_content_text"] is not None:
            file_bytes = body["file_content_text"].encode("utf-8")
            original_filename = body.get("filename", "evidence.txt")
            mime_type = "text/plain"

    return EvidenceService.add_evidence(
        db=db,
        current_user=current_user,
        case_id=cid,
        payload=payload,
        file_bytes=file_bytes,
        original_filename=original_filename,
        mime_type=mime_type,
    )


@router.get("/{case_id}/evidence/{evidence_id}", response_model=EvidenceDetailOut)
def get_evidence_detail(
    case_id: str,
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve details and complete event log for an evidence item."""
    cid = resolve_case_id(case_id, db)
    return EvidenceService.get_evidence_or_404(db, current_user, cid, evidence_id)


@router.get("/{case_id}/evidence/{evidence_id}/custody-chain", response_model=CustodyChainResponse)
def get_custody_chain(
    case_id: str,
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the full chronological chain of custody log for an evidence item."""
    cid = resolve_case_id(case_id, db)
    return EvidenceService.get_custody_chain(db, current_user, cid, evidence_id)


@router.post("/{case_id}/evidence/{evidence_id}/seal", response_model=EvidenceDetailOut)
def seal_evidence(
    case_id: str,
    evidence_id: int,
    payload: SealRequest = SealRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Transition evidence status from COLLECTED to SEALED."""
    cid = resolve_case_id(case_id, db)
    return EvidenceService.seal_evidence(db, current_user, cid, evidence_id, payload)


@router.post("/{case_id}/evidence/{evidence_id}/transfer", response_model=EvidenceDetailOut)
def transfer_evidence(
    case_id: str,
    evidence_id: int,
    payload: TransferRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Transition evidence status from SEALED or RETURNED to TRANSFERRED."""
    cid = resolve_case_id(case_id, db)
    return EvidenceService.transfer_evidence(db, current_user, cid, evidence_id, payload)


@router.post("/{case_id}/evidence/{evidence_id}/receive", response_model=EvidenceDetailOut)
def receive_evidence(
    case_id: str,
    evidence_id: int,
    payload: ReceiveRequest = ReceiveRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Transition evidence status from TRANSFERRED to RECEIVED."""
    cid = resolve_case_id(case_id, db)
    return EvidenceService.receive_evidence(db, current_user, cid, evidence_id, payload)


@router.post("/{case_id}/evidence/{evidence_id}/start-examination", response_model=EvidenceDetailOut)
def start_examination(
    case_id: str,
    evidence_id: int,
    payload: ExaminationStartRequest = ExaminationStartRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Transition evidence status from RECEIVED to EXAMINED (examination in progress)."""
    cid = resolve_case_id(case_id, db)
    return EvidenceService.start_examination(db, current_user, cid, evidence_id, payload)


@router.post("/{case_id}/evidence/{evidence_id}/complete-examination", response_model=EvidenceDetailOut)
def complete_examination(
    case_id: str,
    evidence_id: int,
    payload: ExaminationCompleteRequest = ExaminationCompleteRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Confirm completion of forensic analysis."""
    cid = resolve_case_id(case_id, db)
    return EvidenceService.complete_examination(db, current_user, cid, evidence_id, payload)


@router.post("/{case_id}/evidence/{evidence_id}/report", response_model=EvidenceDetailOut)
async def attach_forensic_report(
    case_id: str,
    evidence_id: int,
    request: Request,
    report_title: Optional[str] = Form(None),
    findings: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Attach official forensic report and transition status to REPORT_GENERATED."""
    cid = resolve_case_id(case_id, db)
    content_type = request.headers.get("content-type", "")

    report_bytes: Optional[bytes] = None
    report_filename: Optional[str] = None

    if "multipart/form-data" in content_type and file is not None:
        report_bytes = await file.read()
        report_filename = file.filename
        payload = ForensicReportRequest(
            report_title=report_title or "Official Forensic Report",
            findings=findings or "Detailed findings attached.",
            notes=notes,
        )
    else:
        try:
            body = await request.json()
        except Exception:
            body = {}
        payload = ForensicReportRequest(
            report_title=body.get("report_title", "Official Forensic Report"),
            findings=body.get("findings", "Detailed findings attached."),
            notes=body.get("notes"),
        )
        if "file_content_text" in body and body["file_content_text"] is not None:
            report_bytes = body["file_content_text"].encode("utf-8")
            report_filename = body.get("filename", "forensic_report.pdf")

    return EvidenceService.attach_forensic_report(
        db=db,
        current_user=current_user,
        case_id=cid,
        evidence_id=evidence_id,
        payload=payload,
        report_bytes=report_bytes,
        report_filename=report_filename,
    )


@router.post("/{case_id}/evidence/{evidence_id}/return", response_model=EvidenceDetailOut)
def return_evidence(
    case_id: str,
    evidence_id: int,
    payload: ReturnRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Transition evidence status from REPORT_GENERATED to RETURNED."""
    cid = resolve_case_id(case_id, db)
    return EvidenceService.return_evidence(db, current_user, cid, evidence_id, payload)


@router.post("/{case_id}/evidence/{evidence_id}/submit-court", response_model=EvidenceDetailOut)
def submit_to_court(
    case_id: str,
    evidence_id: int,
    payload: CourtSubmissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Transition evidence status from RETURNED to COURT_SUBMITTED (Final State)."""
    cid = resolve_case_id(case_id, db)
    return EvidenceService.submit_to_court(db, current_user, cid, evidence_id, payload)


@router.post("/{case_id}/evidence/{evidence_id}/verify", response_model=IntegrityVerificationResult)
def verify_evidence_integrity(
    case_id: str,
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Perform real-time SHA-256 cryptographic check of stored file against original recorded digest.
    Logs verification result into Audit Ledger and updates evidence verification status.
    """
    cid = resolve_case_id(case_id, db)
    return EvidenceService.verify_integrity(db, current_user, cid, evidence_id)
