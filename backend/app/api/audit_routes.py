from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Header, Query, status

from backend.app.schemas.copilot_models import UserProfile, UserRole, ClearanceLevel
from backend.app.schemas.audit_models import (
    AuditAction,
    AuditStatus,
    AuditRecord,
    AuditLogRequest,
    AuditFilterParams,
    AuditQueryResponse,
)
from security.audit.immutable_audit import (
    ImmutableAuditLedger,
    AuditImmutabilityViolationException,
)
from security.authorization.audit_guard import (
    AuditGuard,
    UnauthorizedAuditAccessException,
)

router = APIRouter(prefix="/api/v1/audit", tags=["Audit Trail"])

# Singleton instance of the ImmutableAuditLedger
audit_ledger = ImmutableAuditLedger()


def get_current_auditor(
    x_user_id: Optional[str] = Header(default="ADMIN-01"),
    x_username: Optional[str] = Header(default="LeadAuditor"),
    x_user_role: Optional[str] = Header(default="ADMIN"),
    x_clearance: Optional[int] = Header(default=4),
) -> UserProfile:
    """Extracts caller profile from headers for audit access authorization."""
    try:
        role = UserRole(x_user_role)
    except ValueError:
        role = UserRole.VIEWER

    try:
        clearance = ClearanceLevel(x_clearance)
    except ValueError:
        clearance = ClearanceLevel.PUBLIC

    return UserProfile(
        user_id=x_user_id or "ANON",
        username=x_username or "anonymous",
        role=role,
        clearance=clearance,
        is_admin=(role == UserRole.ADMIN),
    )


@router.post(
    "/events",
    response_model=AuditRecord,
    status_code=status.HTTP_201_CREATED,
    summary="Record an immutable application audit event",
)
def record_audit_event(
    payload: AuditLogRequest,
    current_user: UserProfile = Depends(get_current_auditor),
) -> AuditRecord:
    """Records an event in the cryptographically chained, immutable audit ledger."""
    record = audit_ledger.log_event(
        user_id=payload.user_id,
        action=payload.action,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        status=payload.status,
        metadata=payload.metadata,
    )
    return record


@router.get(
    "/events",
    response_model=AuditQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Query audit trail with multi-criteria filters",
)
def query_audit_events(
    user: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[AuditAction] = Query(None, description="Filter by audit action"),
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    start_date: Optional[str] = Query(None, description="Filter start date"),
    end_date: Optional[str] = Query(None, description="Filter end date"),
    resource: Optional[str] = Query(None, description="Filter by resource type or ID"),
    status_filter: Optional[AuditStatus] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: UserProfile = Depends(get_current_auditor),
) -> AuditQueryResponse:
    """Queries audit events with optional filters: user, action, date, resource, status."""
    try:
        AuditGuard.verify_read_access(current_user)
    except UnauthorizedAuditAccessException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    filters = AuditFilterParams(
        user_id=user,
        action=action,
        date=date,
        start_date=start_date,
        end_date=end_date,
        resource=resource,
        status=status_filter,
        limit=limit,
        offset=offset,
    )

    records = audit_ledger.query_records(filters)
    total_count = audit_ledger.count_records(filters)
    is_valid, _ = audit_ledger.verify_ledger_integrity()

    return AuditQueryResponse(
        records=records,
        total_count=total_count,
        chain_valid=is_valid,
    )


@router.get(
    "/events/{audit_id}",
    response_model=AuditRecord,
    status_code=status.HTTP_200_OK,
    summary="Retrieve single audit record",
)
def get_audit_record(
    audit_id: str,
    current_user: UserProfile = Depends(get_current_auditor),
) -> AuditRecord:
    """Retrieves a single audit record by ID."""
    try:
        AuditGuard.verify_read_access(current_user)
    except UnauthorizedAuditAccessException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    record = audit_ledger.get_record(audit_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit record '{audit_id}' not found.",
        )
    return record


@router.get(
    "/verify",
    status_code=status.HTTP_200_OK,
    summary="Verify cryptographic chain integrity of audit ledger",
)
def verify_audit_chain(
    current_user: UserProfile = Depends(get_current_auditor),
):
    """Verifies that the entire audit trail hash-chain is unbroken and tamper-free."""
    try:
        AuditGuard.verify_read_access(current_user)
    except UnauthorizedAuditAccessException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    is_valid, error = audit_ledger.verify_ledger_integrity()
    return {
        "chain_valid": is_valid,
        "records_count": len(audit_ledger._records),
        "detail": "Cryptographic chain verified unbroken" if is_valid else error,
    }


@router.put(
    "/events/{audit_id}",
    status_code=status.HTTP_403_FORBIDDEN,
    summary="Rejects any modification attempt (Immutability)",
)
def modify_audit_event(
    audit_id: str,
    current_user: UserProfile = Depends(get_current_auditor),
):
    """Explicitly blocks and forbids any update to audit records."""
    try:
        AuditGuard.prevent_modification(current_user, audit_id)
    except AuditImmutabilityViolationException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete(
    "/events/{audit_id}",
    status_code=status.HTTP_403_FORBIDDEN,
    summary="Rejects any deletion attempt (Immutability)",
)
def delete_audit_event(
    audit_id: str,
    current_user: UserProfile = Depends(get_current_auditor),
):
    """Explicitly blocks and forbids any deletion of audit records."""
    try:
        AuditGuard.prevent_deletion(current_user, audit_id)
    except AuditImmutabilityViolationException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
