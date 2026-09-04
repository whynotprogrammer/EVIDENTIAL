from backend.app.schemas.copilot_models import UserProfile, UserRole, ClearanceLevel
from security.audit.immutable_audit import AuditImmutabilityViolationException


class UnauthorizedAuditAccessException(Exception):
    """Raised when an unauthorized user attempts to access or query audit trail logs."""
    pass


class AuditGuard:
    """Enforces strict security access controls for the EVIDENTIAL audit trail.

    Guarantees that unauthorized users cannot inspect audit logs, and NO users
    (including administrators) can modify or delete audit records.
    """

    AUTHORIZED_ROLES = {
        UserRole.ADMIN,
        UserRole.CASE_OFFICER,
    }

    @classmethod
    def verify_read_access(cls, user: UserProfile) -> None:
        """Verifies if user has necessary authorization and clearance to view audit trail."""
        if user.is_admin or user.role in cls.AUTHORIZED_ROLES:
            return

        # Users below CONFIDENTIAL clearance or unauthorized roles are denied
        if user.clearance < ClearanceLevel.CONFIDENTIAL:
            raise UnauthorizedAuditAccessException(
                f"Access Denied: User '{user.username}' with role '{user.role.value}' and clearance "
                f"'{user.clearance.name}' is not authorized to access audit logs."
            )

    @classmethod
    def prevent_modification(cls, user: UserProfile, audit_id: str) -> None:
        """Enforces absolute immutability: unauthorized users and even administrators

        cannot modify audit records.
        """
        raise AuditImmutabilityViolationException(
            f"SECURITY ENFORCEMENT: Modification attempt on audit record '{audit_id}' by user "
            f"'{user.username}' was blocked. Audit records are cryptographically immutable."
        )

    @classmethod
    def prevent_deletion(cls, user: UserProfile, audit_id: str) -> None:
        """Enforces absolute immutability: unauthorized users and even administrators

        cannot delete audit records.
        """
        raise AuditImmutabilityViolationException(
            f"SECURITY ENFORCEMENT: Deletion attempt on audit record '{audit_id}' by user "
            f"'{user.username}' was blocked. Audit records are cryptographically immutable."
        )
