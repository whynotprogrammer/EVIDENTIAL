import enum
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.app.db.session import Base


class AuditAction(str, enum.Enum):
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    CASE_CREATED = "CASE_CREATED"
    CASE_VIEWED = "CASE_VIEWED"
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    OCR_STARTED = "OCR_STARTED"
    OCR_COMPLETED = "OCR_COMPLETED"
    TRANSLATION_CREATED = "TRANSLATION_CREATED"
    ENTITY_EXTRACTED = "ENTITY_EXTRACTED"
    AI_ANALYSIS_EXECUTED = "AI_ANALYSIS_EXECUTED"
    SEARCH_EXECUTED = "SEARCH_EXECUTED"
    EVIDENCE_ADDED = "EVIDENCE_ADDED"
    EVIDENCE_SEALED = "EVIDENCE_SEALED"
    EVIDENCE_TRANSFERRED = "EVIDENCE_TRANSFERRED"
    EVIDENCE_RECEIVED = "EVIDENCE_RECEIVED"
    EXAMINATION_STARTED = "EXAMINATION_STARTED"
    EXAMINATION_COMPLETED = "EXAMINATION_COMPLETED"
    REPORT_GENERATED = "REPORT_GENERATED"
    EVIDENCE_RETURNED = "EVIDENCE_RETURNED"
    COURT_SUBMITTED = "COURT_SUBMITTED"
    HASH_GENERATED = "HASH_GENERATED"
    EVIDENCE_VERIFIED = "EVIDENCE_VERIFIED"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"
    CORRELATION_ANALYZED = "CORRELATION_ANALYZED"
    COPILOT_QUERY = "COPILOT_QUERY"
    COURT_PACKAGE_GENERATED = "COURT_PACKAGE_GENERATED"


class AuditStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    WARNING = "WARNING"


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_email = Column(String(255), nullable=True)
    
    action = Column(Enum(AuditAction), nullable=False, index=True)
    resource_type = Column(String(64), nullable=True, index=True)
    resource_id = Column(String(64), nullable=True, index=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(64), nullable=True, default="127.0.0.1")
    status = Column(Enum(AuditStatus), default=AuditStatus.SUCCESS, nullable=False)
    
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    user = relationship("User")
