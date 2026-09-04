import hashlib
from typing import Dict, List, Optional
from backend.app.schemas.copilot_models import (
    EvidenceDocument,
    CaseRecord,
    EvidenceType,
    ClearanceLevel,
    QueryIntent,
)


def compute_sha256(content: str) -> str:
    """Computes SHA-256 hash for document integrity verification."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class CaseRepository:
    """Strictly partitioned in-memory repository for case evidence and records.

    Ensures zero cross-case contamination through case_id scoping.
    """

    def __init__(self) -> None:
        self._cases: Dict[str, CaseRecord] = {}
        self._documents_by_case: Dict[str, List[EvidenceDocument]] = {}

    def add_case(self, case: CaseRecord) -> None:
        """Registers a case and all associated documents with SHA-256 integrity hashes."""
        self._cases[case.case_id] = case
        self._documents_by_case[case.case_id] = []
        for doc in case.documents:
            if not doc.sha256_hash:
                doc.sha256_hash = compute_sha256(doc.content)
            self._documents_by_case[case.case_id].append(doc)

    def add_document(self, doc: EvidenceDocument) -> None:
        """Adds a single evidence document to a specific case partition."""
        if not doc.sha256_hash:
            doc.sha256_hash = compute_sha256(doc.content)
        if doc.case_id not in self._documents_by_case:
            self._documents_by_case[doc.case_id] = []
        self._documents_by_case[doc.case_id].append(doc)

    def get_case(self, case_id: str) -> Optional[CaseRecord]:
        """Returns the case record if exists, otherwise None."""
        return self._cases.get(case_id)

    def get_all_case_ids(self) -> List[str]:
        """Returns all registered case IDs."""
        return list(self._cases.keys())

    def retrieve_documents(
        self,
        case_id: str,
        query: str,
        intent: QueryIntent = QueryIntent.GENERAL_GROUNDED,
        limit: int = 10,
    ) -> List[EvidenceDocument]:
        """Retrieves documents strictly partitioned by case_id.

        It is structurally impossible to return documents from another case.
        """
        case_docs = self._documents_by_case.get(case_id, [])
        if not case_docs:
            return []

        # Intent-driven ranking / prioritization
        ranked_docs = self._rank_by_intent_and_relevance(case_docs, query, intent)
        return ranked_docs[:limit]

    def _rank_by_intent_and_relevance(
        self,
        documents: List[EvidenceDocument],
        query: str,
        intent: QueryIntent,
    ) -> List[EvidenceDocument]:
        """Weights document types based on investigative intent and keyword overlap."""
        type_priority = {
            QueryIntent.CASE_SUMMARY: [EvidenceType.FIR, EvidenceType.OFFICER_NOTE, EvidenceType.TIMELINE_LOG],
            QueryIntent.PERSONS_MENTIONED: [EvidenceType.FIR, EvidenceType.WITNESS_STATEMENT, EvidenceType.OFFICER_NOTE],
            QueryIntent.EVIDENCE_INVENTORY: [EvidenceType.SEIZURE_MEMO, EvidenceType.FORENSIC_REPORT, EvidenceType.CHAIN_OF_CUSTODY],
            QueryIntent.CHRONOLOGY: [EvidenceType.TIMELINE_LOG, EvidenceType.FIR, EvidenceType.OFFICER_NOTE],
            QueryIntent.RELATED_FIRS: [EvidenceType.FIR, EvidenceType.OFFICER_NOTE],
            QueryIntent.SUPPORTING_DOCS: [EvidenceType.FIR, EvidenceType.SEIZURE_MEMO, EvidenceType.WITNESS_STATEMENT, EvidenceType.FORENSIC_REPORT],
            QueryIntent.LOCATIONS_MENTIONED: [EvidenceType.SEIZURE_MEMO, EvidenceType.FIR, EvidenceType.WITNESS_STATEMENT, EvidenceType.OFFICER_NOTE],
            QueryIntent.GENERAL_GROUNDED: [],
        }

        preferred_types = type_priority.get(intent, [])
        query_words = set(query.lower().split())

        def score_doc(doc: EvidenceDocument) -> float:
            score = 0.0
            # Preferred type bonus
            if doc.doc_type in preferred_types:
                idx = preferred_types.index(doc.doc_type)
                score += (len(preferred_types) - idx) * 3.0

            # Content keyword match
            content_lower = (doc.title + " " + doc.content).lower()
            matches = sum(1 for w in query_words if w in content_lower and len(w) > 2)
            score += matches * 1.5

            return score

        return sorted(documents, key=score_doc, reverse=True)


def create_sample_investigation_repository() -> CaseRepository:
    """Builds a rich repository with two isolated cases for comprehensive testing:

    1. CASE-2024-001 (Cyber Heist & Physical Break-in at Meridian Vault)
    2. CASE-2024-002 (Unrelated Narcotic Smuggling Ring at Harbour Dock)
    """
    repo = CaseRepository()

    # --- CASE-2024-001: The Meridian Vault Incident ---
    doc1 = EvidenceDocument(
        doc_id="DOC-FIR-001",
        case_id="CASE-2024-001",
        title="First Information Report - Meridian Vault Heist",
        doc_type=EvidenceType.FIR,
        clearance=ClearanceLevel.RESTRICTED,
        content=(
            "FIR No: FIR-2024-088 registered at Central Cyber Crime Police Station on 12-Oct-2024 at 09:30 AM. "
            "Complainant: Rajesh Varma (Chief Security Officer, Meridian Bank). "
            "Incident Date: Night of 11-Oct-2024 between 11:45 PM and 02:15 AM. "
            "Location: Meridian Vault Facility, 44 Financial District, Sector 5. "
            "Sections of Law: Sections 380, 420, 468, 66C IT Act. "
            "Accused: Vikram Malhotra (former system administrator, prime suspect) and an unidentified accomplice. "
            "Brief Narrative: Physical intrusion combined with authorized credentials override allowed unauthorized "
            "access to digital cryptographic vaults and extraction of sensitive cold-storage ledgers."
        ),
        metadata={"fir_number": "FIR-2024-088", "police_station": "Central Cyber Crime"},
    )

    doc2 = EvidenceDocument(
        doc_id="DOC-WIT-002",
        case_id="CASE-2024-001",
        title="Witness Statement - Night Guard Sunil Sharma",
        doc_type=EvidenceType.WITNESS_STATEMENT,
        clearance=ClearanceLevel.RESTRICTED,
        content=(
            "Witness: Sunil Sharma (Security Guard, Badge #904). Recorded on 12-Oct-2024 at 14:00 PM by Inspector K. Sen. "
            "Statement: 'I was stationed at Gate B of 44 Financial District. At 11:40 PM on 11-Oct-2024, a dark sedan "
            "entered the alleyway. A man wearing a dark jacket matching the description of Vikram Malhotra presented a valid "
            "tier-2 security badge. He claimed emergency server maintenance. He left at 01:50 AM with a black Pelican hard case. "
            "Dr. Priya Desai from audit arrived later at 08:00 AM and discovered the discrepancy.'"
        ),
        metadata={"witness_name": "Sunil Sharma", "person_type": "WITNESS"},
    )

    doc3 = EvidenceDocument(
        doc_id="DOC-EVID-003",
        case_id="CASE-2024-001",
        title="Seizure Memo - Recovered Hardware & Tooling",
        doc_type=EvidenceType.SEIZURE_MEMO,
        clearance=ClearanceLevel.RESTRICTED,
        content=(
            "Seizure Memo Ref: SEIZ-2024-101. Date: 13-Oct-2024. Recovery Location: Abandoned vehicle near Old Warehouse 12, River Road. "
            "Seized Items: "
            "1. Item E-01: Kingston 128GB Encrypted USB Drive (Barcode: BC-88192, Hash: 3a9f4c8e...). "
            "2. Item E-02: Modified RFID Cloner Device with custom firmware. "
            "3. Item E-03: Dell Precision 7550 Laptop with external Wi-Fi Pineapple dongle. "
            "Chain of Custody: Handed over by Sub-Inspector Roy directly to Digital Forensics Lab Officer M. Joshi."
        ),
        metadata={"seizure_ref": "SEIZ-2024-101", "recovered_location": "Old Warehouse 12, River Road"},
    )

    doc4 = EvidenceDocument(
        doc_id="DOC-TIME-004",
        case_id="CASE-2024-001",
        title="Master Chronology and Timeline Log",
        doc_type=EvidenceType.TIMELINE_LOG,
        clearance=ClearanceLevel.RESTRICTED,
        content=(
            "Chronological Sequence of Events for Case CASE-2024-001: "
            "1. 11-Oct-2024 23:40: Vikram Malhotra enters Gate B at 44 Financial District facility. "
            "2. 11-Oct-2024 23:55: Digital access logs show admin login at Server Rack 4 using stolen token. "
            "3. 12-Oct-2024 01:15: Cryptographic keys exported to external flash drive E-01. "
            "4. 12-Oct-2024 01:50: Suspect exits facility carrying Pelican case. "
            "5. 12-Oct-2024 08:00: Dr. Priya Desai flags vault anomaly during morning audit. "
            "6. 12-Oct-2024 09:30: FIR-2024-088 lodged by Rajesh Varma. "
            "7. 13-Oct-2024 16:20: Abandoned dark sedan with Items E-01, E-02, E-03 recovered at Old Warehouse 12, River Road."
        ),
        metadata={"event_count": 7},
    )

    doc5 = EvidenceDocument(
        doc_id="DOC-FOR-005",
        case_id="CASE-2024-001",
        title="Cyber Forensic Examination Report - Vault Breach",
        doc_type=EvidenceType.FORENSIC_REPORT,
        clearance=ClearanceLevel.CONFIDENTIAL,
        content=(
            "Report No: FORENSIC-CYBER-882. Examiner: Senior Analyst Meera Joshi. "
            "Analysis of Item E-03 (Dell Laptop) and Item E-01 (USB Drive). "
            "Findings: Hardware logs confirm unauthorized payload injection at 00:32 AM on 12-Oct-2024. "
            "Digital fingerprint matches repository author 'v_malhotra_dev'. "
            "Cross-reference: Identifies related FIR-2024-012 (registered at North Cyber Station concerning previous credential phishing)."
        ),
        metadata={"examiner": "Meera Joshi", "classification": "CONFIDENTIAL"},
    )

    doc6 = EvidenceDocument(
        doc_id="DOC-TOP-006",
        case_id="CASE-2024-001",
        title="Classified Intelligence Dossier - Syndicate Links",
        doc_type=EvidenceType.OFFICER_NOTE,
        clearance=ClearanceLevel.SECRET,
        content=(
            "TOP-SECRET INVESTIGATIVE INTELLIGENCE. Case CASE-2024-001. "
            "Operative contact 'Ghost-7' reports Vikram Malhotra answered to handler known as 'Apex' in international waters. "
            "Emergency wiretap authorization active under warrant WT-9921."
        ),
        metadata={"restricted_to": "SECRET_CLEARANCE"},
    )

    case1 = CaseRecord(
        case_id="CASE-2024-001",
        title="Meridian Vault Cyber Heist",
        fir_number="FIR-2024-088",
        incident_date="2024-10-11",
        status="ACTIVE_INVESTIGATION",
        assigned_officers=["INV-101", "INV-102"],
        documents=[doc1, doc2, doc3, doc4, doc5, doc6],
    )
    repo.add_case(case1)

    # --- CASE-2024-002: Completely Unrelated Case (Narcotics Smuggling) ---
    doc2_1 = EvidenceDocument(
        doc_id="DOC-CASE2-FIR-01",
        case_id="CASE-2024-002",
        title="First Information Report - Harbour Narcotics Seizure",
        doc_type=EvidenceType.FIR,
        clearance=ClearanceLevel.RESTRICTED,
        content=(
            "FIR No: FIR-2024-331 registered at Coastal Marine Police Station. "
            "Complainant: Inspector Harish Rao. Accused: Tariq Mansoor. "
            "Location: Terminal 4, Harbour Docks. "
            "Seized: 45 kg contraband shipment hidden inside cargo container MSC-4491."
        ),
        metadata={"fir_number": "FIR-2024-331"},
    )
    case2 = CaseRecord(
        case_id="CASE-2024-002",
        title="Harbour Docks Narcotics Interception",
        fir_number="FIR-2024-331",
        incident_date="2024-09-20",
        status="PENDING_TRIAL",
        assigned_officers=["INV-201"],
        documents=[doc2_1],
    )
    repo.add_case(case2)

    return repo
