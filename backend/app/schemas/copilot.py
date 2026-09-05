from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SourceCitation(BaseModel):
    citation_id: str
    source_type: str = Field(..., description="CASE_RECORD, DOCUMENT, EXTRACTED_ENTITY, EVIDENCE, INVESTIGATION_LOG, CORRELATION_ENGINE")
    source_title: str
    document_filename: Optional[str] = None
    snippet: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CopilotQueryRequest(BaseModel):
    case_id: int = Field(..., description="Target authorized case ID to query")
    question: str = Field(..., min_length=2, max_length=1000, description="Investigation inquiry")


class CopilotQueryResponse(BaseModel):
    case_id: int
    case_number: str
    question: str
    answer: str
    citations: List[SourceCitation] = Field(default_factory=list)
    uncertainty_flag: bool = False
    confidence_level: str = "HIGH"

    model_config = ConfigDict(from_attributes=True)


class CopilotCaseSummaryResponse(BaseModel):
    case_id: int
    case_number: str
    case_title: str
    summary_answer: str
    citations: List[SourceCitation] = Field(default_factory=list)
    persons_identified: List[str] = Field(default_factory=list)
    evidence_count: int = 0
    timeline_events_count: int = 0

    model_config = ConfigDict(from_attributes=True)
