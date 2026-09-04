from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    HASH_GENERATED = "HASH_GENERATED"
    EVIDENCE_VERIFIED = "EVIDENCE_VERIFIED"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"


class EvidenceRecord(BaseModel):
    evidence_id: str
    case_id: str
    filename: str
    hash: str
    uploaded_by: str
    timestamp: str
    file_size_bytes: Optional[int] = None
    storage_path: Optional[str] = None
    description: Optional[str] = None


class EvidenceUploadPayload(BaseModel):
    case_id: str
    filename: str
    content_b64: Optional[str] = None
    content_text: Optional[str] = None
    uploaded_by: str = "investigator"
    description: Optional[str] = None


class VerificationResult(BaseModel):
    status: str
    is_valid: bool
    evidence_id: str
    stored_hash: str
    calculated_hash: str
    verified_at: str
    verified_by: str
    details: Optional[str] = None


class VerificationPayload(BaseModel):
    content_b64: Optional[str] = None
    content_text: Optional[str] = None
    verified_by: str = "investigator"


class AuditEvent(BaseModel):
    event_id: str
    event_type: AuditEventType
    evidence_id: str
    case_id: str
    actor: str
    timestamp: str
    details: Dict[str, Any] = Field(default_factory=dict)
