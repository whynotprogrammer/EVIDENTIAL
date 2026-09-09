from datetime import datetime, timezone
from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.app.db.session import Base


class CourtEvidencePackage(Base):
    __tablename__ = "court_evidence_packages"

    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(String(64), unique=True, index=True, nullable=False)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    generated_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    generated_by_name = Column(String(255), nullable=False)
    status = Column(String(64), default="COURT_READY", nullable=False)
    package_hash = Column(String(64), nullable=False)
    package_data = Column(JSON, nullable=False)
    is_complete = Column(Boolean, default=True, nullable=False) # True = complete, False = incomplete/missing sections
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    case = relationship("Case")
    generated_by = relationship("User")
