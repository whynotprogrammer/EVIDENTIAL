from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class AuditAction(str, Enum):
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    CASE_CREATED = "CASE_CREATED"
    CASE_VIEWED = "CASE_VIEWED"
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    OCR_COMPLETED = "OCR_COMPLETED"
    TRANSLATION_CREATED = "TRANSLATION_CREATED"
    SEARCH_EXECUTED = "SEARCH_EXECUTED"
    CORRELATION_EXECUTED = "CORRELATION_EXECUTED"
    AI_QUERY = "AI_QUERY"
    EVIDENCE_ADDED = "EVIDENCE_ADDED"
    HASH_GENERATED = "HASH_GENERATED"
    EVIDENCE_VERIFIED = "EVIDENCE_VERIFIED"


class AuditStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    DENIED = "DENIED"
    WARNING = "WARNING"


class AuditRecord(BaseModel):
    audit_id: str
    user_id: str
    action: AuditAction
    resource_type: str
    resource_id: str
    timestamp: str
    status: AuditStatus
    metadata: Dict[str, Any] = Field(default_factory=dict)
    previous_hash: str = "GENESIS"
    record_hash: str = ""


class AuditLogRequest(BaseModel):
    user_id: str
    action: AuditAction
    resource_type: str
    resource_id: str
    status: AuditStatus = AuditStatus.SUCCESS
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AuditFilterParams(BaseModel):
    user_id: Optional[str] = None
    action: Optional[AuditAction] = None
    date: Optional[str] = None  # YYYY-MM-DD format
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    resource: Optional[str] = None  # Matches resource_type or resource_id
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    status: Optional[AuditStatus] = None
    limit: int = 100
    offset: int = 0


class AuditQueryResponse(BaseModel):
    records: List[AuditRecord]
    total_count: int
    chain_valid: bool = True
