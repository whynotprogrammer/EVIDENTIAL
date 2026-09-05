from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from backend.app.models.evidence import EvidenceType, VerificationStatus


class EvidenceBase(BaseModel):
    title: str
    description: Optional[str] = None
    evidence_type: EvidenceType = EvidenceType.DIGITAL_FILE


class EvidenceCreate(EvidenceBase):
    case_id: int


class EvidenceOut(EvidenceBase):
    id: int
    case_id: int
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    sha256_hash: str
    is_tampered: bool
    verification_status: VerificationStatus
    last_verified_at: Optional[datetime] = None
    uploaded_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvidenceVerifyResponse(BaseModel):
    evidence_id: int
    title: str
    stored_sha256: str
    current_sha256: str
    status: VerificationStatus
    is_valid: bool
    verified_at: datetime
    message: str
