from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, computed_field
from backend.app.models.case import CasePriority, CaseStatus


class CaseBase(BaseModel):
    case_number: str = Field(..., description="Unique Case/FIR identifier (e.g. FIR-2024-DEL-001)")
    title: str
    description: Optional[str] = None
    crime_type: str
    status: CaseStatus = CaseStatus.UNDER_INVESTIGATION
    priority: CasePriority = CasePriority.HIGH
    police_station: Optional[str] = "Central Cyber Crime Cell"
    district: Optional[str] = None
    state: Optional[str] = None
    location: Optional[str] = None
    incident_date: Optional[datetime] = None


class CaseCreate(BaseModel):
    case_number: str
    title: str
    description: Optional[str] = None
    crime_type: str
    status: Optional[CaseStatus] = CaseStatus.UNDER_INVESTIGATION
    priority: Optional[CasePriority] = CasePriority.HIGH
    police_station: Optional[str] = "Central Cyber Crime Cell"
    district: Optional[str] = None
    state: Optional[str] = None
    location: Optional[str] = None
    incident_date: Optional[datetime] = None
    assigned_officer_id: Optional[int] = None


class CaseUpdate(BaseModel):
    case_number: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    crime_type: Optional[str] = None
    status: Optional[CaseStatus] = None
    priority: Optional[CasePriority] = None
    police_station: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    location: Optional[str] = None
    incident_date: Optional[datetime] = None
    assigned_officer_id: Optional[int] = None


class CaseOut(CaseBase):
    id: int
    created_by_id: Optional[int] = None
    assigned_officer_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    @computed_field
    def case_id(self) -> str:
        """Alias returning case_number or string ID to satisfy case_id field contract."""
        return self.case_number

    @computed_field
    def created_by(self) -> Optional[str]:
        """Expose created_by representation."""
        return f"User #{self.created_by_id}" if self.created_by_id else "System"

    model_config = ConfigDict(from_attributes=True)
