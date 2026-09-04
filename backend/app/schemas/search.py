import enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SearchResultType(str, enum.Enum):
    CASE = "CASE"
    DOCUMENT = "DOCUMENT"
    ENTITY = "ENTITY"


class SearchQuery(BaseModel):
    q: Optional[str] = Field(None, description="General keyword search term")
    case_number: Optional[str] = Field(None, description="Specific case number search")
    entity_type: Optional[str] = Field(None, description="Filter by entity type (e.g. PHONE, VEHICLE, PERSON)")
    entity_value: Optional[str] = Field(None, description="Filter by exact or partial entity value")
    crime_type: Optional[str] = Field(None, description="Filter by crime classification")
    location: Optional[str] = Field(None, description="Filter by location, city, or police station")
    skip: int = Field(0, ge=0, description="Offset for pagination")
    limit: int = Field(50, ge=1, le=200, description="Max number of results to return")


class SearchResultItem(BaseModel):
    result_type: SearchResultType
    case_id: int
    case_number: str
    case_title: str
    crime_type: Optional[str] = None
    document_id: Optional[int] = None
    document_filename: Optional[str] = None
    entity_id: Optional[int] = None
    entity_type: Optional[str] = None
    entity_value: Optional[str] = None
    match_field: str
    match_snippet: str
    score: float = 1.0


class SearchResponse(BaseModel):
    total: int
    query: Optional[str] = None
    filters_applied: Dict[str, Any] = {}
    search_mode: str = "KEYWORD_ENTITY_AUTHORIZED"
    results: List[SearchResultItem] = []
