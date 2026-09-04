from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from backend.app.models.entity import EntityType


class EntityBase(BaseModel):
    entity_type: EntityType
    entity_value: str
    normalized_value: Optional[str] = None
    confidence: float = 0.90
    context_snippet: Optional[str] = None


class EntityCreate(EntityBase):
    case_id: int
    document_id: Optional[int] = None


class EntityOut(EntityBase):
    id: int
    case_id: int
    document_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
