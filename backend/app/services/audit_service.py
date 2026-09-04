from typing import Optional
from sqlalchemy.orm import Session
from backend.app.models.audit import AuditAction, AuditEvent, AuditStatus
from backend.app.models.user import User


def log_audit_event(
    db: Session,
    action: AuditAction,
    user: Optional[User] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[str] = None,
    ip_address: str = "127.0.0.1",
    status: AuditStatus = AuditStatus.SUCCESS,
) -> AuditEvent:
    """Create an immutable audit event in the system log."""
    event = AuditEvent(
        user_id=user.id if user else None,
        user_email=user.email if user else "anonymous",
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        status=status,
    )
    db.add(event)
    try:
        db.commit()
        db.refresh(event)
    except Exception:
        db.rollback()
    return event
