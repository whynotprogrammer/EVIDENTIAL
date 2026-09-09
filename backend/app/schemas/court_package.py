from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CaseSummarySection(BaseModel):
    case_id: int
    case_number: str
    title: str
    crime_type: str
    status: str
    priority: str
    police_station: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    location: Optional[str] = None
    incident_date: Optional[str] = None
    registration_date: str
    investigating_officer: str
    description: Optional[str] = None


class FIRDocumentRef(BaseModel):
    id: int
    original_filename: str
    file_size_bytes: Optional[int] = None
    sha256_hash: str
    uploaded_at: str


class FIRSection(BaseModel):
    available: bool
    case_number: Optional[str] = None
    fir_year: Optional[int] = None
    fir_stage: Optional[str] = None
    fir_type: Optional[str] = None
    crime_head: Optional[str] = None
    act_section: Optional[str] = None
    complaint_mode: Optional[str] = None
    police_station: Optional[str] = None
    district: Optional[str] = None
    victim_count: Optional[int] = None
    accused_count: Optional[int] = None
    arrested_count: Optional[int] = None
    documents: List[FIRDocumentRef] = Field(default_factory=list)
    empty_message: Optional[str] = None


class WitnessStatementItem(BaseModel):
    witness_id: str
    witness_name: str
    statement_date: str
    statement_status: str
    statement_content: Optional[str] = None
    location: Optional[str] = None
    verification_status: str = "OFFICIALLY_LOGGED"


class WitnessStatementsSection(BaseModel):
    available: bool
    count: int
    statements: List[WitnessStatementItem] = Field(default_factory=list)
    empty_message: Optional[str] = None


class EvidenceRegisterItem(BaseModel):
    evidence_id: int
    evidence_number: str
    evidence_name: str
    evidence_type: str
    description: Optional[str] = None
    collected_by: Optional[str] = None
    collection_date: Optional[str] = None
    collection_location: Optional[str] = None
    current_status: str
    current_custodian: Optional[str] = None
    original_sha256: str
    current_sha256: str
    integrity_status: str


class EvidenceRegisterSection(BaseModel):
    available: bool
    count: int
    items: List[EvidenceRegisterItem] = Field(default_factory=list)
    empty_message: Optional[str] = None


class ForensicReportItem(BaseModel):
    report_id: str
    evidence_id: int
    evidence_number: str
    title: str
    generated_by: str
    date_time: str
    report_status: str
    report_hash: Optional[str] = None
    file_reference: Optional[str] = None
    findings: Optional[str] = None


class ForensicReportsSection(BaseModel):
    available: bool
    count: int
    reports: List[ForensicReportItem] = Field(default_factory=list)
    empty_message: Optional[str] = None


class TimelineEventItem(BaseModel):
    date: str
    time: str
    action: str
    event_type: str
    actor: str
    location: Optional[str] = None
    description: Optional[str] = None
    source_document: Optional[str] = None


class TimelineSection(BaseModel):
    available: bool
    count: int
    events: List[TimelineEventItem] = Field(default_factory=list)
    empty_message: Optional[str] = None


class CustodyHistoryEvent(BaseModel):
    action: str
    who: str
    when: str
    where: Optional[str] = None
    from_custodian: Optional[str] = None
    to_custodian: Optional[str] = None
    why: Optional[str] = None
    evidence_hash: str
    digital_signature: Optional[str] = None
    device_info: Optional[str] = None


class CustodyItemChain(BaseModel):
    evidence_id: int
    evidence_number: str
    title: str
    current_status: str
    current_custodian: Optional[str] = None
    total_events: int
    events: List[CustodyHistoryEvent] = Field(default_factory=list)


class ChainOfCustodySection(BaseModel):
    available: bool
    total_events: int
    items: List[CustodyItemChain] = Field(default_factory=list)
    empty_message: Optional[str] = None


class IntegrityCertificateItem(BaseModel):
    evidence_id: int
    evidence_number: str
    title: str
    original_sha256: str
    current_sha256: str
    status: str
    is_valid: bool
    verified_at: str
    verified_by: str


class IntegrityCertificatesSection(BaseModel):
    available: bool
    all_valid: bool
    total_items: int
    verified_items: int
    items: List[IntegrityCertificateItem] = Field(default_factory=list)
    certificates: List[IntegrityCertificateItem] = Field(default_factory=list)
    empty_message: Optional[str] = None


class DigitalSignatureItem(BaseModel):
    signer: str
    action: str
    timestamp: str
    verification_status: str
    signature_reference: str
    device_info: Optional[str] = None


class DigitalSignaturesSection(BaseModel):
    available: bool
    count: int
    signatures: List[DigitalSignatureItem] = Field(default_factory=list)
    implementation_note: str = "Cryptographic SHA-256 HMAC & node-attested digital signature protocol (EVIDENTIAL Security Architecture)"
    empty_message: Optional[str] = None


class AuditCertificateSection(BaseModel):
    certificate_id: Optional[str] = None
    case_number: Optional[str] = None
    total_evidence_items: int
    total_custody_events: int
    total_audit_events: int
    integrity_violations: int
    unauthorized_actions: int
    verified_signatures: int
    chain_of_custody_status: str # "COMPLETE" or "INCOMPLETE"
    evidence_integrity_status: str # "VERIFIED" or "ATTENTION REQUIRED"
    integrity_declaration: str = "I hereby certify that the electronic records and custody ledger entries documented in this dossier have been maintained in the ordinary course of official duty with cryptographic verification intact."
    certified_at: str
    certified_by: str
    audit_chain_valid: bool
    legal_statute_reference: str = "Section 65B Indian Evidence Act, 1872 / Section 63 Bharatiya Sakshya Adhiniyam, 2023"


class PackageMetadata(BaseModel):
    package_id: str
    case_id: int
    case_number: str
    generated_by: str
    generated_at: str
    status: str
    package_hash: str
    is_complete: bool
    missing_sections: List[str] = Field(default_factory=list)


class CourtEvidencePackageData(BaseModel):
    metadata: PackageMetadata
    case_summary: CaseSummarySection
    fir: FIRSection
    witness_statements: WitnessStatementsSection
    evidence_register: EvidenceRegisterSection
    forensic_reports: ForensicReportsSection
    investigation_timeline: TimelineSection
    chain_of_custody: ChainOfCustodySection
    integrity_certificates: IntegrityCertificatesSection
    digital_signatures: DigitalSignaturesSection
    audit_certificate: AuditCertificateSection


class CourtEvidencePackageOut(BaseModel):
    id: int
    package_id: str
    case_id: int
    generated_by_name: str
    status: str
    package_hash: str
    is_complete: bool
    created_at: datetime
    package_data: CourtEvidencePackageData

    model_config = ConfigDict(from_attributes=True)


class CourtPackageReadiness(BaseModel):
    case_id: int
    case_number: str
    case_summary_status: str
    fir_status: str
    witness_statements_status: str
    evidence_register_status: str
    forensic_reports_status: str
    investigation_timeline_status: str
    chain_of_custody_status: str
    integrity_certificates_status: str
    digital_signatures_status: str
    audit_certificate_status: str
    is_package_complete: bool
    missing_sections: List[str] = Field(default_factory=list)
    preview: CourtEvidencePackageData
