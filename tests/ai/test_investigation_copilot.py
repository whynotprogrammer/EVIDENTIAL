import pytest
from backend.app.schemas.copilot_models import (
    UserProfile,
    UserRole,
    ClearanceLevel,
    CopilotQueryRequest,
    QueryIntent,
)
from ai.rag.copilot import InvestigationCopilot
from ai.rag.llm_engine import INSUFFICIENT_EVIDENCE_PHRASE


@pytest.fixture
def investigator() -> UserProfile:
    return UserProfile(
        user_id="INV-101",
        username="DetectiveMiller",
        role=UserRole.INVESTIGATOR,
        clearance=ClearanceLevel.CONFIDENTIAL,
        assigned_case_ids=["CASE-2024-001"],
    )


@pytest.fixture
def copilot() -> InvestigationCopilot:
    return InvestigationCopilot()


class TestInvestigationCopilotCore:
    """Rigorous tests verifying the 7 canonical investigative questions,

    grounding, citation integrity, and explicit uncertainty handling.
    """

    def test_question_1_summarize_case(self, investigator: UserProfile, copilot: InvestigationCopilot):
        """1. Summarize this case."""
        req = CopilotQueryRequest(case_id="CASE-2024-001", question="Summarize this case.")
        resp = copilot.ask(user=investigator, request=req)

        assert resp.detected_intent == QueryIntent.CASE_SUMMARY
        assert resp.is_grounded is True
        assert "[DOC:DOC-FIR-001]" in resp.answer
        assert "Meridian Vault" in resp.answer or "Vikram Malhotra" in resp.answer
        assert len(resp.source_references) > 0

    def test_question_2_persons_mentioned(self, investigator: UserProfile, copilot: InvestigationCopilot):
        """2. Who are the persons mentioned?"""
        req = CopilotQueryRequest(case_id="CASE-2024-001", question="Who are the persons mentioned?")
        resp = copilot.ask(user=investigator, request=req)

        assert resp.detected_intent == QueryIntent.PERSONS_MENTIONED
        assert resp.is_grounded is True
        assert "Rajesh Varma" in resp.answer
        assert "Vikram Malhotra" in resp.answer
        assert "Sunil Sharma" in resp.answer
        assert "Priya Desai" in resp.answer
        assert "[DOC:DOC-FIR-001]" in resp.answer
        assert len(resp.source_references) >= 2

    def test_question_3_what_evidence_exists(self, investigator: UserProfile, copilot: InvestigationCopilot):
        """3. What evidence exists?"""
        req = CopilotQueryRequest(case_id="CASE-2024-001", question="What evidence exists?")
        resp = copilot.ask(user=investigator, request=req)

        assert resp.detected_intent == QueryIntent.EVIDENCE_INVENTORY
        assert resp.is_grounded is True
        assert "Kingston 128GB" in resp.answer
        assert "RFID Cloner" in resp.answer
        assert "Dell Precision 7550" in resp.answer
        assert "Chain of Custody" in resp.answer
        assert "[DOC:DOC-EVID-003]" in resp.answer

    def test_question_4_chronology(self, investigator: UserProfile, copilot: InvestigationCopilot):
        """4. What happened chronologically?"""
        req = CopilotQueryRequest(case_id="CASE-2024-001", question="What happened chronologically?")
        resp = copilot.ask(user=investigator, request=req)

        assert resp.detected_intent == QueryIntent.CHRONOLOGY
        assert resp.is_grounded is True
        assert "11-Oct-2024 23:40" in resp.answer
        assert "12-Oct-2024 01:15" in resp.answer
        assert "13-Oct-2024 16:20" in resp.answer
        assert "[DOC:DOC-TIME-004]" in resp.answer

    def test_question_5_related_firs(self, investigator: UserProfile, copilot: InvestigationCopilot):
        """5. Which FIRs may be related?"""
        req = CopilotQueryRequest(case_id="CASE-2024-001", question="Which FIRs may be related?")
        resp = copilot.ask(user=investigator, request=req)

        assert resp.detected_intent == QueryIntent.RELATED_FIRS
        assert resp.is_grounded is True
        assert "FIR-2024-088" in resp.answer
        assert "FIR-2024-012" in resp.answer
        assert "[DOC:DOC-FIR-001]" in resp.answer
        assert "[DOC:DOC-FOR-005]" in resp.answer

    def test_question_6_supporting_documents(self, investigator: UserProfile, copilot: InvestigationCopilot):
        """6. Which documents support this answer?"""
        req = CopilotQueryRequest(case_id="CASE-2024-001", question="Which documents support this answer?")
        resp = copilot.ask(user=investigator, request=req)

        assert resp.detected_intent == QueryIntent.SUPPORTING_DOCS
        assert resp.is_grounded is True
        assert "First Information Report" in resp.answer
        assert len(resp.source_references) >= 3

    def test_question_7_locations_mentioned(self, investigator: UserProfile, copilot: InvestigationCopilot):
        """7. What locations are mentioned?"""
        req = CopilotQueryRequest(case_id="CASE-2024-001", question="What locations are mentioned?")
        resp = copilot.ask(user=investigator, request=req)

        assert resp.detected_intent == QueryIntent.LOCATIONS_MENTIONED
        assert resp.is_grounded is True
        assert "44 Financial District" in resp.answer
        assert "Gate B" in resp.answer
        assert "Central Cyber Crime" in resp.answer
        assert "Old Warehouse 12" in resp.answer
        assert "[DOC:DOC-FIR-001]" in resp.answer
        assert "[DOC:DOC-EVID-003]" in resp.answer

    @pytest.mark.parametrize(
        "unsupported_question",
        [
            "Where were the stolen diamonds hidden?",
            "What weapon or firearm was used in the murder?",
            "Who is John Doe?",
            "What is the alibi for Alice?",
            "Was poison found in the victim's blood?",
        ],
    )
    def test_explicit_uncertainty_fallback_on_absent_data(
        self,
        unsupported_question: str,
        investigator: UserProfile,
        copilot: InvestigationCopilot,
    ):
        """Validates that any question asking for information not present in the authorized case records

        strictly returns:
        'I cannot find sufficient evidence in the authorized case data.'
        without hallucination or extrapolation.
        """
        req = CopilotQueryRequest(case_id="CASE-2024-001", question=unsupported_question)
        resp = copilot.ask(user=investigator, request=req)

        assert resp.answer == INSUFFICIENT_EVIDENCE_PHRASE
        assert resp.insufficient_evidence is True
        assert len(resp.source_references) == 0

    def test_tamper_evident_source_reference_integrity(
        self,
        investigator: UserProfile,
        copilot: InvestigationCopilot,
    ):
        """Verifies that all source references returned in responses contain valid SHA-256 hashes

        that match the document contents in the repository.
        """
        req = CopilotQueryRequest(case_id="CASE-2024-001", question="What evidence exists?")
        resp = copilot.ask(user=investigator, request=req)

        assert len(resp.source_references) > 0
        for src in resp.source_references:
            assert src.sha256_hash is not None
            assert len(src.sha256_hash) == 64
            # Verify match in repo
            doc = next((d for d in copilot.repository.get_case("CASE-2024-001").documents if d.doc_id == src.doc_id), None)
            assert doc is not None
            assert src.sha256_hash == doc.sha256_hash
