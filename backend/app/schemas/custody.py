from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.evidence import CustodyStatus, EvidenceType, VerificationStatus


class EvidenceCreatePayload(BaseModel):
    title: str = Field(..., min_length=2, max_length=255, description="Evidence title or name")
    description: Optional[str] = None
    evidence_type: EvidenceType = EvidenceType.DIGITAL_FILE
    collection_location: Optional[str] = None
    collection_date: Optional[datetime] = None
    notes: Optional[str] = None


class SealRequest(BaseModel):
    reason: Optional[str] = Field(default="Evidence secured and sealed for chain of custody")
    notes: Optional[str] = None


class TransferRequest(BaseModel):
    to_custodian: str = Field(..., min_length=2, max_length=255, description="Name or department of recipient")
    location: Optional[str] = Field(default="Evidence Vault / Transfer Office")
    reason: Optional[str] = Field(default="Transfer of physical/digital custody")
    notes: Optional[str] = None


class ReceiveRequest(BaseModel):
    received_by: Optional[str] = None
    location: Optional[str] = Field(default="Evidence Repository")
    condition_notes: Optional[str] = Field(default="Received in intact condition")


class ExaminationStartRequest(BaseModel):
    examiner: Optional[str] = None
    purpose: Optional[str] = Field(default="Forensic digital analysis and extraction")
    notes: Optional[str] = None


class ExaminationCompleteRequest(BaseModel):
    examiner: Optional[str] = None
    result_notes: Optional[str] = Field(default="Examination completed cleanly")


class ForensicReportRequest(BaseModel):
    report_title: Optional[str] = Field(default="Official Forensic Investigation Report")
    findings: Optional[str] = Field(default="Detailed digital forensic findings attached")
    notes: Optional[str] = None


class ReturnRequest(BaseModel):
    from_custodian: Optional[str] = None
    to_custodian: str = Field(..., min_length=2, max_length=255, description="Recipient returning to")
    location: Optional[str] = Field(default="Investigating Agency Repository")
    reason: Optional[str] = Field(default="Return of evidence post forensic examination")
    notes: Optional[str] = None


class CourtSubmissionRequest(BaseModel):
    submitted_by: Optional[str] = None
    court_name: str = Field(..., min_length=2, max_length=255, description="Court of jurisdiction / Judiciary Authority")
    submission_notes: Optional[str] = Field(default="Submitted into judicial custody / evidence record")
    notes: Optional[str] = None


class CustodyEventOut(BaseModel):
    id: int
    evidence_id: int
    case_id: int
    action: str
    previous_status: Optional[str] = None
    new_status: str
    actor_id: Optional[int] = None
    actor_name: str
    timestamp: datetime
    location: Optional[str] = None
    from_custodian: Optional[str] = None
    to_custodian: Optional[str] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    evidence_hash: str
    digital_signature: Optional[str] = None
    device_info: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvidenceDetailOut(BaseModel):
    id: int
    case_id: int
    evidence_number: str
    title: str
    description: Optional[str] = None
    evidence_type: EvidenceType
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    sha256_hash: str
    status: CustodyStatus
    current_custodian: Optional[str] = None
    collected_by: Optional[str] = None
    collection_location: Optional[str] = None
    collection_date: Optional[datetime] = None
    notes: Optional[str] = None
    forensic_report_path: Optional[str] = None
    forensic_report_hash: Optional[str] = None
    is_tampered: bool
    verification_status: VerificationStatus
    last_verified_at: Optional[datetime] = None
    uploaded_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    custody_events: List[CustodyEventOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class CustodyChainResponse(BaseModel):
    evidence_id: int
    evidence_number: str
    case_id: int
    current_status: CustodyStatus
    current_custodian: Optional[str] = None
    total_events: int
    events: List[CustodyEventOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class IntegrityVerificationResult(BaseModel):
    evidence_id: int
    evidence_number: str
    stored_sha256: str
    current_sha256: str
    status: str
    is_valid: bool
    verified_at: datetime
    verified_by: str
    message: str

    model_config = ConfigDict(from_attributes=True)
