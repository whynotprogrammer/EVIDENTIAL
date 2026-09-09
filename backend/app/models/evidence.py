import enum
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.app.db.session import Base


class EvidenceType(str, enum.Enum):
    DOCUMENT = "DOCUMENT"
    DIGITAL_FILE = "DIGITAL_FILE"
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    FORENSIC_IMAGE = "FORENSIC_IMAGE"
    PHYSICAL = "PHYSICAL"


class VerificationStatus(str, enum.Enum):
    VALID = "VALID"
    TAMPERING_DETECTED = "TAMPERING_DETECTED"
    UNVERIFIED = "UNVERIFIED"


class CustodyStatus(str, enum.Enum):
    COLLECTED = "COLLECTED"
    SEALED = "SEALED"
    TRANSFERRED = "TRANSFERRED"
    RECEIVED = "RECEIVED"
    EXAMINED = "EXAMINED"
    REPORT_GENERATED = "REPORT_GENERATED"
    RETURNED = "RETURNED"
    COURT_SUBMITTED = "COURT_SUBMITTED"


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    
    evidence_number = Column(String(64), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    evidence_type = Column(Enum(EvidenceType), default=EvidenceType.DIGITAL_FILE, nullable=False)
    
    file_path = Column(String(512), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(64), nullable=True)
    
    # SHA-256 Cryptographic Fingerprint
    sha256_hash = Column(String(64), nullable=False, index=True)
    
    # Chain of Custody & Status
    status = Column(Enum(CustodyStatus), default=CustodyStatus.COLLECTED, nullable=False, index=True)
    current_custodian = Column(String(255), nullable=True)
    collected_by = Column(String(255), nullable=True)
    collection_location = Column(String(255), nullable=True)
    collection_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    # Forensic Report Attachment
    forensic_report_path = Column(String(512), nullable=True)
    forensic_report_hash = Column(String(64), nullable=True)

    # Integrity Tracking
    is_tampered = Column(Boolean, default=False, nullable=False)
    verification_status = Column(
        Enum(VerificationStatus),
        default=VerificationStatus.VALID,
        nullable=False,
    )
    last_verified_at = Column(DateTime, nullable=True)

    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_by = relationship("User")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    case = relationship("Case", back_populates="evidence_items")
    custody_events = relationship(
        "CustodyEvent",
        back_populates="evidence",
        cascade="all, delete-orphan",
        order_by="CustodyEvent.timestamp.asc()",
    )


class CustodyEvent(Base):
    """Immutable audit record representing a single digital chain of custody transaction."""
    __tablename__ = "custody_events"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id", ondelete="CASCADE"), nullable=False, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)

    action = Column(String(64), nullable=False, index=True)
    previous_status = Column(String(64), nullable=True)
    new_status = Column(String(64), nullable=False)

    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_name = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    location = Column(String(255), nullable=True)
    from_custodian = Column(String(255), nullable=True)
    to_custodian = Column(String(255), nullable=True)
    reason = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    evidence_hash = Column(String(64), nullable=False)
    digital_signature = Column(String(255), nullable=True)
    device_info = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    evidence = relationship("Evidence", back_populates="custody_events")
    case = relationship("Case")
    actor = relationship("User")
