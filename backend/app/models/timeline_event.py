import enum
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.app.db.session import Base


class EventType(str, enum.Enum):
    FIR_REGISTERED = "FIR_REGISTERED"
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    EVIDENCE_ADDED = "EVIDENCE_ADDED"
    EVIDENCE_TRANSFER = "EVIDENCE_TRANSFER"
    PERSON_IDENTIFIED = "PERSON_IDENTIFIED"
    LOCATION_IDENTIFIED = "LOCATION_IDENTIFIED"
    INVESTIGATION_EVENT = "INVESTIGATION_EVENT"
    AI_ANALYSIS_EVENT = "AI_ANALYSIS_EVENT"
    INCIDENT = "INCIDENT"
    FIR_LODGED = "FIR_LODGED"
    ARREST = "ARREST"
    SEIZURE = "SEIZURE"
    FORENSIC_EXAM = "FORENSIC_EXAM"
    WITNESS_STATEMENT = "WITNESS_STATEMENT"
    COURT_FILING = "COURT_FILING"


class InvestigationEvent(Base):
    __tablename__ = "investigation_events"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    
    event_date = Column(DateTime, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    event_type = Column(Enum(EventType), default=EventType.INCIDENT, nullable=False)
    location = Column(String(255), nullable=True)
    
    source_document_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    case = relationship("Case", back_populates="events")
    source_document = relationship("Document")
