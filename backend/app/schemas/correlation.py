from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CaseSummary(BaseModel):
    id: int
    case_number: str
    title: str
    crime_type: str
    status: Optional[str] = None
    district: Optional[str] = None
    fir_year: Optional[int] = None
    crime_head: Optional[str] = None


class MatchedEntityItem(BaseModel):
    entity_type: str
    source_value: str
    related_value: str
    similarity: float
    match_type: str = "EXACT"


class CorrelationResult(BaseModel):
    source_case: CaseSummary
    related_case: CaseSummary
    correlation_score: float = Field(..., ge=0.0, le=1.0)
    matching_entities: List[MatchedEntityItem] = Field(default_factory=list)
    matching_factors: List[str] = Field(default_factory=list)
    factor_scores: Optional[Dict[str, float]] = None
    explanation: str


class CorrelationListResponse(BaseModel):
    source_case_id: int
    total: int
    correlations: List[CorrelationResult]


class CorrelationAnalyzeRequest(BaseModel):
    source_case_id: int
    target_case_id: Optional[int] = None
    min_threshold: Optional[float] = 0.25
