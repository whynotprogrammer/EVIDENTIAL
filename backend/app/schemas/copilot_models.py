from enum import Enum, IntEnum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ClearanceLevel(IntEnum):
    PUBLIC = 1
    RESTRICTED = 2
    CONFIDENTIAL = 3
    SECRET = 4
    TOP_SECRET = 5


class UserRole(str, Enum):
    VIEWER = "VIEWER"
    INVESTIGATOR = "INVESTIGATOR"
    CASE_OFFICER = "CASE_OFFICER"
    FORENSIC_EXAMINER = "FORENSIC_EXAMINER"
    ADMIN = "ADMIN"


class EvidenceType(str, Enum):
    FIR = "FIR"
    WITNESS_STATEMENT = "WITNESS_STATEMENT"
    FORENSIC_REPORT = "FORENSIC_REPORT"
    SEIZURE_MEMO = "SEIZURE_MEMO"
    CHAIN_OF_CUSTODY = "CHAIN_OF_CUSTODY"
    OFFICER_NOTE = "OFFICER_NOTE"
    TIMELINE_LOG = "TIMELINE_LOG"


class QueryIntent(str, Enum):
    CASE_SUMMARY = "CASE_SUMMARY"
    PERSONS_MENTIONED = "PERSONS_MENTIONED"
    EVIDENCE_INVENTORY = "EVIDENCE_INVENTORY"
    CHRONOLOGY = "CHRONOLOGY"
    RELATED_FIRS = "RELATED_FIRS"
    SUPPORTING_DOCS = "SUPPORTING_DOCS"
    LOCATIONS_MENTIONED = "LOCATIONS_MENTIONED"
    GENERAL_GROUNDED = "GENERAL_GROUNDED"


class UserProfile(BaseModel):
    user_id: str
    username: str
    role: UserRole
    clearance: ClearanceLevel
    assigned_case_ids: List[str] = Field(default_factory=list)
    is_admin: bool = False


class EvidenceDocument(BaseModel):
    doc_id: str
    case_id: str
    title: str
    doc_type: EvidenceType
    clearance: ClearanceLevel = ClearanceLevel.RESTRICTED
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    sha256_hash: Optional[str] = None


class CaseRecord(BaseModel):
    case_id: str
    title: str
    fir_number: str
    incident_date: Optional[str] = None
    status: str = "UNDER_INVESTIGATION"
    assigned_officers: List[str] = Field(default_factory=list)
    documents: List[EvidenceDocument] = Field(default_factory=list)


class SourceReference(BaseModel):
    doc_id: str
    title: str
    doc_type: EvidenceType
    clearance: ClearanceLevel
    snippet: str
    sha256_hash: Optional[str] = None
    relevance_score: float = 1.0


class CopilotQueryRequest(BaseModel):
    case_id: str
    question: str


class CopilotQueryResponse(BaseModel):
    case_id: str
    question: str
    answer: str
    source_references: List[SourceReference] = Field(default_factory=list)
    is_grounded: bool = True
    confidence: float = 1.0
    detected_intent: QueryIntent = QueryIntent.GENERAL_GROUNDED
    insufficient_evidence: bool = False
