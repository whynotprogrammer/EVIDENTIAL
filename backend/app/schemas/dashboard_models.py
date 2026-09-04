from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class DashboardMetrics(BaseModel):
    total_cases: int = 0
    active_cases: int = 0
    documents_processed: int = 0
    evidence_items: int = 0
    potential_correlations: int = 0
    audit_events: int = 0


class EvidenceActivityPoint(BaseModel):
    date: str
    ingested_count: int
    verified_count: int


class ChartData(BaseModel):
    cases_by_status: Dict[str, int] = Field(default_factory=dict)
    cases_by_crime_type: Dict[str, int] = Field(default_factory=dict)
    cases_by_language: Dict[str, int] = Field(default_factory=dict)
    evidence_activity: List[EvidenceActivityPoint] = Field(default_factory=list)


class RecentCaseItem(BaseModel):
    case_id: str
    title: str
    fir_number: str
    status: str
    crime_type: str
    updated_at: str


class RecentDocumentItem(BaseModel):
    doc_id: str
    case_id: str
    title: str
    doc_type: str
    language: str
    uploaded_at: str


class RecentCorrelationItem(BaseModel):
    correlation_id: str
    entity_a: str
    entity_b: str
    confidence_score: float
    correlation_type: str
    detected_at: str


class RecentAuditItem(BaseModel):
    audit_id: str
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    status: str
    timestamp: str


class RecentActivity(BaseModel):
    latest_cases: List[RecentCaseItem] = Field(default_factory=list)
    latest_documents: List[RecentDocumentItem] = Field(default_factory=list)
    latest_correlations: List[RecentCorrelationItem] = Field(default_factory=list)
    latest_audit_events: List[RecentAuditItem] = Field(default_factory=list)


class NavigationItem(BaseModel):
    name: str
    path: str
    icon: Optional[str] = None
    badge_count: Optional[int] = None
    is_active: bool = False


class CommandCenterResponse(BaseModel):
    metrics: DashboardMetrics
    charts: ChartData
    recent_activity: RecentActivity
    navigation_items: List[NavigationItem]
    system_status: str = "OPERATIONAL"
    timestamp: str
