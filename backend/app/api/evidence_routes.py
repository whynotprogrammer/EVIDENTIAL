import base64
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, status
from backend.app.schemas.evidence_models import (
    EvidenceRecord,
    EvidenceUploadPayload,
    VerificationResult,
    VerificationPayload,
    AuditEvent,
)
from evidence.integrity.evidence_manager import (
    EvidenceManager,
    STATUS_VALID,
    STATUS_INVALID,
)

router = APIRouter(prefix="/evidence", tags=["Evidence Integrity"])

# Default singleton instance of EvidenceManager
evidence_manager = EvidenceManager()


@router.post(
    "",
    response_model=EvidenceRecord,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and register evidence with SHA-256 hash calculation",
)
async def upload_evidence(
    request: Request,
    case_id: Optional[str] = Form(None),
    uploaded_by: Optional[str] = Form("investigator"),
    description: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
) -> EvidenceRecord:
    """Uploads evidence either via multipart/form-data file upload or JSON payload.

    Calculates SHA-256, stores metadata, and generates a HASH_GENERATED audit event.
    """
    content_type = request.headers.get("content-type", "")

    # Handle multipart/form-data
    if "multipart/form-data" in content_type and file is not None:
        if not case_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Form field 'case_id' is required for file upload.",
            )
        file_bytes = await file.read()
        filename = file.filename or "evidence.bin"
        record = evidence_manager.upload_evidence(
            case_id=case_id,
            filename=filename,
            content=file_bytes,
            uploaded_by=uploaded_by or "investigator",
            description=description,
        )
        return record

    # Handle JSON payload
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request body. Send JSON or multipart/form-data.",
        )

    req_case_id = data.get("case_id")
    req_filename = data.get("filename")
    req_uploaded_by = data.get("uploaded_by", "investigator")
    req_description = data.get("description")

    if not req_case_id or not req_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fields 'case_id' and 'filename' are required.",
        )

    # Content can be base64 or plain text
    if "content_b64" in data and data["content_b64"]:
        try:
            content_bytes = base64.b64decode(data["content_b64"])
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid base64 payload in 'content_b64'.",
            )
    elif "content_text" in data and data["content_text"] is not None:
        content_bytes = data["content_text"].encode("utf-8")
    else:
        # Default to empty payload if none provided
        content_bytes = b""

    record = evidence_manager.upload_evidence(
        case_id=req_case_id,
        filename=req_filename,
        content=content_bytes,
        uploaded_by=req_uploaded_by,
        description=req_description,
    )
    return record


@router.get(
    "/{id}",
    response_model=EvidenceRecord,
    status_code=status.HTTP_200_OK,
    summary="Retrieve evidence record by ID",
)
def get_evidence(id: str) -> EvidenceRecord:
    """Retrieves an evidence record containing its calculated SHA-256 hash and metadata."""
    record = evidence_manager.get_evidence(id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence with ID '{id}' not found.",
        )
    return record


@router.post(
    "/{id}/verify",
    response_model=VerificationResult,
    status_code=status.HTTP_200_OK,
    summary="Verify evidence cryptographic integrity against stored SHA-256",
)
async def verify_evidence(
    id: str,
    request: Request,
) -> VerificationResult:
    """Calculates current SHA-256 of the stored file (or supplied payload) and compares with stored hash.

    Returns 'VALID — INTEGRITY VERIFIED' or 'INVALID — TAMPERING DETECTED'.
    Logs EVIDENCE_VERIFIED or INTEGRITY_FAILURE audit events.
    """
    record = evidence_manager.get_evidence(id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence with ID '{id}' not found.",
        )

    # Check for optional verification payload
    content_to_verify: Optional[bytes] = None
    verified_by = "investigator"

    try:
        data = await request.json()
        if isinstance(data, dict):
            verified_by = data.get("verified_by", "investigator")
            if "content_b64" in data and data["content_b64"]:
                content_to_verify = base64.b64decode(data["content_b64"])
            elif "content_text" in data and data["content_text"] is not None:
                content_to_verify = data["content_text"].encode("utf-8")
    except Exception:
        # If no JSON body, verify the stored file content directly
        pass

    try:
        result = evidence_manager.verify_evidence(
            evidence_id=id,
            content_to_verify=content_to_verify,
            verified_by=verified_by,
        )
        return result
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence with ID '{id}' not found.",
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/{id}/audit",
    response_model=List[AuditEvent],
    status_code=status.HTTP_200_OK,
    summary="Retrieve audit trail for evidence",
)
def get_evidence_audit_events(id: str) -> List[AuditEvent]:
    """Retrieves all chain-of-custody and verification audit events for the evidence."""
    record = evidence_manager.get_evidence(id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence with ID '{id}' not found.",
        )
    return evidence_manager.audit_logger.get_events_for_evidence(id)
