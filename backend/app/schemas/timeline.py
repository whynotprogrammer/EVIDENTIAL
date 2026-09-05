from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.timeline_event import EventType


class TimelineEventItem(BaseModel):
    id: str
    event_date: datetime
    event_type: str
    title: str
    description: Optional[str] = None
    source: str = Field(..., description="Exact verified originating entity, document, or case record")
    source_type: str = Field(..., description="CASE_RECORD, DOCUMENT, EXTRACTED_ENTITY, EVIDENCE, INVESTIGATION_LOG")
    source_id: Optional[int] = None
    source_document: Optional[str] = None
    location: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class CaseTimelineResponse(BaseModel):
    case_id: int
    case_number: str
    case_title: str
    total_events: int
    events: List[TimelineEventItem]


class TimelineEventBase(BaseModel):
    title: str
    description: Optional[str] = None
    event_date: datetime
    event_type: EventType = EventType.INVESTIGATION_EVENT
    location: Optional[str] = None


class TimelineEventCreate(TimelineEventBase):
    source_document_id: Optional[int] = None


class TimelineEventOut(BaseModel):
    id: int
    case_id: int
    title: str
    description: Optional[str] = None
    event_date: datetime
    event_type: EventType
    location: Optional[str] = None
    source_document_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
