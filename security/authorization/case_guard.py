from typing import List
from backend.app.schemas.copilot_models import UserProfile, EvidenceDocument, UserRole, ClearanceLevel


class UnauthorizedCaseAccessException(Exception):
    """Raised when a user attempts to access a case they are not authorized for."""
    pass


class InsufficientClearanceException(Exception):
    """Raised when an operation requires higher security clearance than the user possesses."""
    pass


class CaseIsolationViolationException(Exception):
    """Raised when cross-case data retrieval or leakage is detected."""
    pass


class CaseGuard:
    """Enforces Role-Based and Attribute-Based Access Control (RBAC/ABAC)

    guaranteeing strict case boundary isolation and security clearance enforcement.
    """

    @staticmethod
    def verify_case_access(user: UserProfile, requested_case_id: str) -> None:
        """Verifies if the given user is authorized to access the requested case.

        Admin users have platform-level access, while investigators and case officers
        must be explicitly assigned to the case.
        """
        if user.is_admin or user.role == UserRole.ADMIN:
            return

        if requested_case_id not in user.assigned_case_ids:
            raise UnauthorizedCaseAccessException(
                f"Access Denied: User '{user.username}' (ID: {user.user_id}, Role: {user.role.value}) "
                f"is not assigned or authorized to access Case ID '{requested_case_id}'."
            )

    @staticmethod
    def filter_documents_by_clearance(
        user: UserProfile, documents: List[EvidenceDocument]
    ) -> List[EvidenceDocument]:
        """Filters out any documents whose clearance requirement exceeds the user's clearance level."""
        authorized_docs: List[EvidenceDocument] = []
        for doc in documents:
            if doc.clearance <= user.clearance:
                authorized_docs.append(doc)
        return authorized_docs

    @staticmethod
    def verify_case_isolation(
        target_case_id: str, documents: List[EvidenceDocument]
    ) -> None:
        """Strictly verifies that no document from an external or foreign case is present.

        Raises CaseIsolationViolationException immediately if cross-case contamination occurs.
        """
        for doc in documents:
            if doc.case_id != target_case_id:
                raise CaseIsolationViolationException(
                    f"CRITICAL SECURITY ALERT: Cross-case leakage detected! Document '{doc.doc_id}' "
                    f"belongs to foreign Case '{doc.case_id}' but was retrieved for Case '{target_case_id}'."
                )
