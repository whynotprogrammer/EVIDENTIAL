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


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    evidence_type = Column(Enum(EvidenceType), default=EvidenceType.DIGITAL_FILE, nullable=False)
    
    file_path = Column(String(512), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(64), nullable=True)
    
    # SHA-256 Cryptographic Fingerprint
    sha256_hash = Column(String(64), nullable=False, index=True)
    
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
