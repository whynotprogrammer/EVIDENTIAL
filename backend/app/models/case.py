import enum
from datetime import datetime, timezone
from sqlalchemy import JSON, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.app.db.session import Base


class CaseStatus(str, enum.Enum):
    IMPORTED = "IMPORTED"
    OPEN = "OPEN"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    PENDING_REVIEW = "PENDING_REVIEW"
    CLOSED = "CLOSED"


class CasePriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(64), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    crime_type = Column(String(128), nullable=False, index=True)
    status = Column(Enum(CaseStatus), default=CaseStatus.UNDER_INVESTIGATION, nullable=False, index=True)
    priority = Column(Enum(CasePriority), default=CasePriority.HIGH, nullable=False)
    
    # Jurisdiction & Location Details
    police_station = Column(String(128), nullable=True, default="Central Cyber Crime Cell")
    district = Column(String(128), nullable=True)
    state = Column(String(128), nullable=True)
    location = Column(String(255), nullable=True)
    incident_date = Column(DateTime, nullable=True)

    # Karnataka Police FIR source fields. These retain the CSV values separately
    # from EVIDENTIAL's operational case metadata (status, priority, ownership).
    source_record_key = Column(String(64), unique=True, index=True, nullable=True)
    fir_year = Column(Integer, nullable=True, index=True)
    fir_month = Column(Integer, nullable=True, index=True)
    fir_day = Column(Integer, nullable=True)
    fir_type = Column(String(64), nullable=True)
    fir_stage = Column(String(255), nullable=True, index=True)
    complaint_mode = Column(String(128), nullable=True)
    crime_head = Column(String(255), nullable=True, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    offence_duration = Column(String(128), nullable=True)
    act_section = Column(Text, nullable=True)
    io_name = Column(String(255), nullable=True)
    kgid = Column(String(64), nullable=True)
    internal_io = Column(String(64), nullable=True)
    distance_from_ps = Column(String(255), nullable=True)
    beat_name = Column(String(255), nullable=True)
    village_area_name = Column(String(255), nullable=True)
    male = Column(Integer, nullable=True)
    female = Column(Integer, nullable=True)
    boy = Column(Integer, nullable=True)
    girl = Column(Integer, nullable=True)
    age_0 = Column(Integer, nullable=True)
    victim_count = Column(Integer, nullable=True)
    accused_count = Column(Integer, nullable=True)
    arrested_male = Column(Integer, nullable=True)
    arrested_female = Column(Integer, nullable=True)
    arrested_count = Column(Integer, nullable=True)
    accused_chargesheeted_count = Column(Integer, nullable=True)
    conviction_count = Column(Integer, nullable=True)
    unit_id = Column(String(64), nullable=True)
    source_payload = Column(JSON, nullable=True)

    # Ownership & Creator
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by_user = relationship("User", foreign_keys=[created_by_id])

    assigned_officer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_officer = relationship("User", foreign_keys=[assigned_officer_id], back_populates="assigned_cases")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    documents = relationship("Document", back_populates="case", cascade="all, delete-orphan")
    evidence_items = relationship("Evidence", back_populates="case", cascade="all, delete-orphan")
    entities = relationship("ExtractedEntity", back_populates="case", cascade="all, delete-orphan")
    events = relationship("InvestigationEvent", back_populates="case", cascade="all, delete-orphan")
