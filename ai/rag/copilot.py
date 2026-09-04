from typing import Optional
from backend.app.schemas.copilot_models import (
    UserProfile,
    CopilotQueryRequest,
    CopilotQueryResponse,
    QueryIntent,
)
from security.authorization.case_guard import (
    CaseGuard,
    UnauthorizedCaseAccessException,
    CaseIsolationViolationException,
)
from ai.rag.security import (
    QuerySecurityProcessor,
    PromptInjectionDetectedException,
)
from ai.rag.retriever import CaseRepository, create_sample_investigation_repository
from ai.rag.context_builder import ContextBuilder
from ai.rag.llm_engine import (
    BaseLLMClient,
    GroundedInvestigationLLM,
    CitationValidator,
    INSUFFICIENT_EVIDENCE_PHRASE,
)


class InvestigationCopilot:
    """End-to-end grounded investigation assistant orchestrator.

    Implements the full authorized pipeline:
    User Question -> Authorization -> Query Processing -> Case Retrieval ->
    Clearance Filter -> Context Assembly -> Grounded LLM -> Citation Validation -> Source References.
    """

    def __init__(
        self,
        repository: Optional[CaseRepository] = None,
        llm_engine: Optional[BaseLLMClient] = None,
    ) -> None:
        self.repository = repository or create_sample_investigation_repository()
        self.llm_engine = llm_engine or GroundedInvestigationLLM()

    def ask(
        self,
        user: UserProfile,
        request: CopilotQueryRequest,
    ) -> CopilotQueryResponse:
        """Executes an investigative query through the authorized, grounded pipeline."""

        # 1. Authorization & Case Isolation Check
        CaseGuard.verify_case_access(user, request.case_id)

        # 2. Query Security & Sanitization
        sanitized_query = QuerySecurityProcessor.sanitize_query(request.question)
        detected_intent = QuerySecurityProcessor.classify_intent(sanitized_query)

        # 3. Case Retrieval (strictly bounded by request.case_id)
        raw_documents = self.repository.retrieve_documents(
            case_id=request.case_id,
            query=sanitized_query,
            intent=detected_intent,
        )

        # 4. Enforce Inviolable Cross-Case Isolation
        CaseGuard.verify_case_isolation(request.case_id, raw_documents)

        # 5. Clearance Filtering (ABAC)
        authorized_documents = CaseGuard.filter_documents_by_clearance(user, raw_documents)

        # If no authorized documents exist after clearance filtering
        if not authorized_documents:
            return CopilotQueryResponse(
                case_id=request.case_id,
                question=request.question,
                answer=INSUFFICIENT_EVIDENCE_PHRASE,
                source_references=[],
                is_grounded=True,
                confidence=1.0,
                detected_intent=detected_intent,
                insufficient_evidence=True,
            )

        # 6. Context Assembly & Hardened Prompt Construction
        prompt = ContextBuilder.build_prompt(
            case_id=request.case_id,
            question=sanitized_query,
            documents=authorized_documents,
        )

        # 7. Grounded LLM Response Generation
        raw_answer = self.llm_engine.generate_response(
            prompt=prompt,
            question=sanitized_query,
            context_docs=authorized_documents,
            intent=detected_intent,
        )

        # 8. Citation Extraction and Grounding Validation
        sources, is_grounded = CitationValidator.validate_and_extract_sources(
            answer=raw_answer,
            authorized_docs=authorized_documents,
        )

        is_insufficient = INSUFFICIENT_EVIDENCE_PHRASE in raw_answer

        return CopilotQueryResponse(
            case_id=request.case_id,
            question=request.question,
            answer=raw_answer,
            source_references=sources,
            is_grounded=is_grounded,
            confidence=1.0 if (is_grounded and not is_insufficient) else (0.0 if is_insufficient else 0.5),
            detected_intent=detected_intent,
            insufficient_evidence=is_insufficient,
        )
