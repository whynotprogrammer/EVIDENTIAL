import enum
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.app.db.session import Base


class EntityType(str, enum.Enum):
    PERSON = "PERSON"
    PHONE = "PHONE"
    EMAIL = "EMAIL"
    LOCATION = "LOCATION"
    DATE = "DATE"
    VEHICLE = "VEHICLE"
    POLICE_STATION = "POLICE_STATION"
    CASE_NUMBER = "CASE_NUMBER"
    CRIME_TYPE = "CRIME_TYPE"
    LAW_SECTION = "LAW_SECTION"
    ORGANIZATION = "ORGANIZATION"


class ExtractedEntity(Base):
    __tablename__ = "extracted_entities"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=True, index=True)

    entity_type = Column(Enum(EntityType), nullable=False, index=True)
    entity_value = Column(String(255), nullable=False, index=True)
    normalized_value = Column(String(255), nullable=True, index=True)
    confidence = Column(Float, default=0.90, nullable=False)
    context_snippet = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    case = relationship("Case", back_populates="entities")
    document = relationship("Document", back_populates="entities")
