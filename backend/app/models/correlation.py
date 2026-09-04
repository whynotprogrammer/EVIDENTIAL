from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, Text
from sqlalchemy.orm import relationship

from backend.app.db.base import Base


class CaseCorrelation(Base):
    """
    Persisted Cross-FIR potential correlation records.
    Captures explainable evidence links between cases.
    """
    __tablename__ = "case_correlations"

    id = Column(Integer, primary_key=True, index=True)
    source_case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    related_case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    correlation_score = Column(Float, nullable=False, default=0.0)
    matching_factors = Column(JSON, nullable=False, default=list)
    matching_entities = Column(JSON, nullable=False, default=list)
    factor_scores = Column(JSON, nullable=True, default=dict)
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    source_case = relationship("Case", foreign_keys=[source_case_id], backref="correlations_outbound")
    related_case = relationship("Case", foreign_keys=[related_case_id], backref="correlations_inbound")
