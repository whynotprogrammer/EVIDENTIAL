import pytest
from backend.app.schemas.copilot_models import (
    UserProfile,
    UserRole,
    ClearanceLevel,
    CopilotQueryRequest,
    EvidenceDocument,
    EvidenceType,
)
from security.authorization.case_guard import (
    CaseGuard,
    UnauthorizedCaseAccessException,
    CaseIsolationViolationException,
)
from ai.rag.copilot import InvestigationCopilot
from ai.rag.llm_engine import INSUFFICIENT_EVIDENCE_PHRASE


@pytest.fixture
def case1_investigator() -> UserProfile:
    return UserProfile(
        user_id="INV-101",
        username="DetectiveMiller",
        role=UserRole.INVESTIGATOR,
        clearance=ClearanceLevel.RESTRICTED,  # Level 2
        assigned_case_ids=["CASE-2024-001"],
    )


@pytest.fixture
def case2_officer() -> UserProfile:
    return UserProfile(
        user_id="INV-201",
        username="OfficerRao",
        role=UserRole.INVESTIGATOR,
        clearance=ClearanceLevel.CONFIDENTIAL,  # Level 3
        assigned_case_ids=["CASE-2024-002"],
    )


@pytest.fixture
def senior_examiner() -> UserProfile:
    return UserProfile(
        user_id="EXAM-301",
        username="MeeraJoshi",
        role=UserRole.FORENSIC_EXAMINER,
        clearance=ClearanceLevel.SECRET,  # Level 4
        assigned_case_ids=["CASE-2024-001", "CASE-2024-002"],
    )


@pytest.fixture
def copilot() -> InvestigationCopilot:
    return InvestigationCopilot()


class TestAuthorizationAndCrossCaseSecurity:
    """Rigorous tests evaluating authorization barriers, clearance filtering, and cross-case isolation."""

    def test_unauthorized_case_access_rejected(
        self,
        case1_investigator: UserProfile,
        copilot: InvestigationCopilot,
    ):
        """User assigned only to CASE-2024-001 attempts to query CASE-2024-002.

        Must be rejected immediately with UnauthorizedCaseAccessException.
        """
        req = CopilotQueryRequest(
            case_id="CASE-2024-002",
            question="Summarize this case.",
        )
        with pytest.raises(UnauthorizedCaseAccessException) as exc_info:
            copilot.ask(user=case1_investigator, request=req)

        assert "is not assigned or authorized to access Case ID 'CASE-2024-002'" in str(exc_info.value)

    def test_unassigned_user_access_rejected(self, copilot: InvestigationCopilot):
        """User with no assigned cases must be denied access."""
        unassigned_user = UserProfile(
            user_id="USER-GUEST",
            username="GuestViewer",
            role=UserRole.VIEWER,
            clearance=ClearanceLevel.PUBLIC,
            assigned_case_ids=[],
        )
        req = CopilotQueryRequest(
            case_id="CASE-2024-001",
            question="What evidence exists?",
        )
        with pytest.raises(UnauthorizedCaseAccessException):
            copilot.ask(user=unassigned_user, request=req)

    def test_clearance_level_document_filtering(
        self,
        case1_investigator: UserProfile,
        senior_examiner: UserProfile,
        copilot: InvestigationCopilot,
    ):
        """Validates that documents exceeding the user's clearance are omitted.

        case1_investigator has RESTRICTED clearance, while DOC-FOR-005 is CONFIDENTIAL
        and DOC-TOP-006 is SECRET.
        """
        # 1. Investigator with RESTRICTED clearance retrieves documents
        docs_investigator = copilot.repository.retrieve_documents(
            case_id="CASE-2024-001",
            query="forensic analysis and syndicate links",
        )
        filtered_for_investigator = CaseGuard.filter_documents_by_clearance(
            case1_investigator, docs_investigator
        )
        # Verify no CONFIDENTIAL or SECRET docs are visible
        for doc in filtered_for_investigator:
            assert doc.clearance <= ClearanceLevel.RESTRICTED
            assert doc.doc_id not in ["DOC-FOR-005", "DOC-TOP-006"]

        # 2. Senior examiner with SECRET clearance can access up to SECRET
        filtered_for_examiner = CaseGuard.filter_documents_by_clearance(
            senior_examiner, docs_investigator
        )
        doc_ids_examiner = [d.doc_id for d in filtered_for_examiner]
        assert "DOC-FOR-005" in doc_ids_examiner  # CONFIDENTIAL is allowed

    def test_cross_case_data_leakage_prevention(
        self,
        case1_investigator: UserProfile,
        copilot: InvestigationCopilot,
    ):
        """User authorized for CASE-2024-001 asks about entities, suspects, or evidence

        that exclusively exist in CASE-2024-002 (e.g. Tariq Mansoor, Harbour Docks, Container MSC-4491).
        The copilot must NOT leak data from CASE-2024-002, and must return:
        "I cannot find sufficient evidence in the authorized case data."
        """
        cross_case_queries = [
            "Who is Tariq Mansoor?",
            "What contraband was seized at Terminal 4 Harbour Docks?",
            "Show me the seizure of container MSC-4491.",
            "Summarize the narcotics operation.",
        ]

        for query in cross_case_queries:
            req = CopilotQueryRequest(
                case_id="CASE-2024-001",
                question=query,
            )
            response = copilot.ask(user=case1_investigator, request=req)

            # Must return the strict fallback phrase
            assert response.answer == INSUFFICIENT_EVIDENCE_PHRASE
            assert response.insufficient_evidence is True
            # Zero source references to CASE-2024-002 documents
            assert len(response.source_references) == 0
            for ref in response.source_references:
                assert "CASE2" not in ref.doc_id

    def test_case_isolation_invariant_enforcement(self):
        """Tests that CaseGuard.verify_case_isolation raises CaseIsolationViolationException

        if an external case document is injected into a retrieval set.
        """
        foreign_doc = EvidenceDocument(
            doc_id="LEAKED-DOC-001",
            case_id="CASE-2024-002",  # Foreign case!
            title="Foreign Case Memo",
            doc_type=EvidenceType.OFFICER_NOTE,
            clearance=ClearanceLevel.RESTRICTED,
            content="Foreign leaked information.",
        )
        with pytest.raises(CaseIsolationViolationException) as exc_info:
            CaseGuard.verify_case_isolation(target_case_id="CASE-2024-001", documents=[foreign_doc])

        assert "Cross-case leakage detected" in str(exc_info.value)
