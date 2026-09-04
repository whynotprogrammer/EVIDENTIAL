import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.schemas.copilot_models import UserProfile, UserRole, ClearanceLevel
from backend.app.schemas.audit_models import (
    AuditAction,
    AuditStatus,
    AuditRecord,
    AuditFilterParams,
)
from security.audit.immutable_audit import (
    ImmutableAuditLedger,
    AuditImmutabilityViolationException,
)
from security.authorization.audit_guard import (
    AuditGuard,
    UnauthorizedAuditAccessException,
)
from backend.app.api.audit_routes import router as audit_router, audit_ledger as api_ledger


@pytest.fixture
def fresh_ledger() -> ImmutableAuditLedger:
    return ImmutableAuditLedger()


@pytest.fixture
def admin_auditor() -> UserProfile:
    return UserProfile(
        user_id="ADMIN-01",
        username="LeadAuditor",
        role=UserRole.ADMIN,
        clearance=ClearanceLevel.TOP_SECRET,
        is_admin=True,
    )


@pytest.fixture
def unauthorized_user() -> UserProfile:
    return UserProfile(
        user_id="VIEWER-99",
        username="RestrictedGuest",
        role=UserRole.VIEWER,
        clearance=ClearanceLevel.PUBLIC,
        is_admin=False,
    )


@pytest.fixture
def test_client() -> TestClient:
    app = FastAPI()
    app.include_router(audit_router)
    return TestClient(app)


class TestAuditLedgerCore:
    """Rigorous tests verifying logging for all 13 canonical actions, all 8 required fields,

    cryptographic hash-chaining, and multi-criteria filtering.
    """

    @pytest.mark.parametrize(
        "action,resource_type,resource_id",
        [
            (AuditAction.LOGIN, "AUTH", "SESSION-101"),
            (AuditAction.LOGOUT, "AUTH", "SESSION-101"),
            (AuditAction.CASE_CREATED, "CASE", "CASE-2024-001"),
            (AuditAction.CASE_VIEWED, "CASE", "CASE-2024-001"),
            (AuditAction.DOCUMENT_UPLOADED, "DOCUMENT", "DOC-001"),
            (AuditAction.OCR_COMPLETED, "DOCUMENT", "DOC-001"),
            (AuditAction.TRANSLATION_CREATED, "DOCUMENT", "DOC-001"),
            (AuditAction.SEARCH_EXECUTED, "SEARCH", "QUERY-88"),
            (AuditAction.CORRELATION_EXECUTED, "GRAPH", "CORR-01"),
            (AuditAction.AI_QUERY, "COPILOT", "ASK-101"),
            (AuditAction.EVIDENCE_ADDED, "EVIDENCE", "EVID-001"),
            (AuditAction.HASH_GENERATED, "EVIDENCE", "EVID-001"),
            (AuditAction.EVIDENCE_VERIFIED, "EVIDENCE", "EVID-001"),
        ],
    )
    def test_record_all_13_audit_actions(
        self,
        fresh_ledger: ImmutableAuditLedger,
        action: AuditAction,
        resource_type: str,
        resource_id: str,
    ):
        """Validates that all 13 required audit actions can be logged with all 8 required fields:

        audit_id, user_id, action, resource_type, resource_id, timestamp, status, metadata.
        """
        record = fresh_ledger.log_event(
            user_id="INV-101",
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=AuditStatus.SUCCESS,
            metadata={"test_key": "test_val"},
        )

        assert record.audit_id is not None
        assert record.audit_id.startswith("AUDIT-")
        assert record.user_id == "INV-101"
        assert record.action == action
        assert record.resource_type == resource_type
        assert record.resource_id == resource_id
        assert record.timestamp is not None
        assert record.status == AuditStatus.SUCCESS
        assert record.metadata == {"test_key": "test_val"}
        assert len(record.record_hash) == 64
        assert record.previous_hash is not None

    def test_cryptographic_hash_chain_verification(self, fresh_ledger: ImmutableAuditLedger):
        """Verifies that each logged record is cryptographically linked to the preceding record,

        and that any tampering breaks the hash chain.
        """
        r1 = fresh_ledger.log_event("USER-A", AuditAction.LOGIN, "AUTH", "S-1")
        r2 = fresh_ledger.log_event("USER-A", AuditAction.CASE_VIEWED, "CASE", "C-1")
        r3 = fresh_ledger.log_event("USER-A", AuditAction.LOGOUT, "AUTH", "S-1")

        assert r2.previous_hash == r1.record_hash
        assert r3.previous_hash == r2.record_hash

        # Untampered chain verification passes
        is_valid, err = fresh_ledger.verify_ledger_integrity()
        assert is_valid is True
        assert err is None

        # Simulate malicious tampering in middle record
        fresh_ledger.tamper_record_for_testing(r2.audit_id, "status", AuditStatus.DENIED)

        # Tampering detected
        is_valid_tampered, err_tampered = fresh_ledger.verify_ledger_integrity()
        assert is_valid_tampered is False
        assert "Tampering detected" in err_tampered

    def test_multi_criteria_filtering(self, fresh_ledger: ImmutableAuditLedger):
        """Validates filtering by: user, action, date, resource, status."""
        fresh_ledger.log_event("INV-101", AuditAction.CASE_CREATED, "CASE", "C-01", AuditStatus.SUCCESS, timestamp="2024-10-12T08:00:00Z")
        fresh_ledger.log_event("INV-102", AuditAction.CASE_VIEWED, "CASE", "C-01", AuditStatus.SUCCESS, timestamp="2024-10-12T08:30:00Z")
        fresh_ledger.log_event("INV-101", AuditAction.EVIDENCE_ADDED, "EVIDENCE", "E-99", AuditStatus.SUCCESS, timestamp="2024-10-13T09:00:00Z")
        fresh_ledger.log_event("HACKER-01", AuditAction.LOGIN, "AUTH", "S-99", AuditStatus.DENIED, timestamp="2024-10-13T10:00:00Z")

        # 1. Filter by User
        res_user = fresh_ledger.query_records(AuditFilterParams(user_id="INV-101"))
        assert len(res_user) == 2
        assert all(r.user_id == "INV-101" for r in res_user)

        # 2. Filter by Action
        res_action = fresh_ledger.query_records(AuditFilterParams(action=AuditAction.CASE_CREATED))
        assert len(res_action) == 1
        assert res_action[0].action == AuditAction.CASE_CREATED

        # 3. Filter by Date (YYYY-MM-DD)
        res_date = fresh_ledger.query_records(AuditFilterParams(date="2024-10-12"))
        assert len(res_date) == 2

        # 4. Filter by Resource
        res_resource = fresh_ledger.query_records(AuditFilterParams(resource="EVIDENCE"))
        assert len(res_resource) == 1
        assert res_resource[0].resource_type == "EVIDENCE"

        # 5. Filter by Status
        res_status = fresh_ledger.query_records(AuditFilterParams(status=AuditStatus.DENIED))
        assert len(res_status) == 1
        assert res_status[0].user_id == "HACKER-01"


class TestAuditSecurityAndImmutability:
    """Rigorous tests enforcing the security requirement:

    'Unauthorized users must not modify audit records' and absolute append-only immutability.
    """

    def test_unauthorized_user_cannot_read_audit_records(self, unauthorized_user: UserProfile):
        """Unauthorized viewers without sufficient role/clearance cannot inspect audit logs."""
        with pytest.raises(UnauthorizedAuditAccessException) as exc_info:
            AuditGuard.verify_read_access(unauthorized_user)

        assert "is not authorized to access audit logs" in str(exc_info.value)

    def test_unauthorized_user_cannot_modify_audit_records(self, unauthorized_user: UserProfile):
        """Unauthorized users attempting to modify audit records are blocked."""
        with pytest.raises(AuditImmutabilityViolationException) as exc_info:
            AuditGuard.prevent_modification(unauthorized_user, "AUDIT-12345")

        assert "Modification attempt on audit record 'AUDIT-12345'" in str(exc_info.value)

    def test_unauthorized_user_cannot_delete_audit_records(self, unauthorized_user: UserProfile):
        """Unauthorized users attempting to delete audit records are blocked."""
        with pytest.raises(AuditImmutabilityViolationException) as exc_info:
            AuditGuard.prevent_deletion(unauthorized_user, "AUDIT-12345")

        assert "Deletion attempt on audit record 'AUDIT-12345'" in str(exc_info.value)

    def test_authorized_admin_cannot_modify_or_delete_audit_records(
        self, admin_auditor: UserProfile, fresh_ledger: ImmutableAuditLedger
    ):
        """Even administrators and authorized auditors cannot modify or delete audit records

        (Strict Immutability Guarantee).
        """
        rec = fresh_ledger.log_event("ADMIN-01", AuditAction.LOGIN, "AUTH", "S-1")

        with pytest.raises(AuditImmutabilityViolationException):
            fresh_ledger.modify_record(rec.audit_id, {"status": AuditStatus.FAILURE})

        with pytest.raises(AuditImmutabilityViolationException):
            fresh_ledger.delete_record(rec.audit_id)


class TestAuditAPIEndpoints:
    """Integration tests for REST API endpoints and query filter query parameters."""

    def test_api_record_audit_event(self, test_client: TestClient):
        """POST /api/v1/audit/events creates immutable record."""
        response = test_client.post(
            "/api/v1/audit/events",
            headers={"x-user-role": "ADMIN", "x-clearance": "4"},
            json={
                "user_id": "INV-SEN",
                "action": "OCR_COMPLETED",
                "resource_type": "DOCUMENT",
                "resource_id": "DOC-991",
                "status": "SUCCESS",
                "metadata": {"pages": 5, "accuracy": 0.98},
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == "INV-SEN"
        assert data["action"] == "OCR_COMPLETED"
        assert "record_hash" in data
        assert len(data["record_hash"]) == 64

    def test_api_query_audit_events_with_filters(self, test_client: TestClient):
        """GET /api/v1/audit/events with user, action, date, resource, status filters."""
        # Seed test event
        test_client.post(
            "/api/v1/audit/events",
            headers={"x-user-role": "ADMIN", "x-clearance": "4"},
            json={
                "user_id": "FILTER-USER-01",
                "action": "TRANSLATION_CREATED",
                "resource_type": "DOCUMENT",
                "resource_id": "DOC-TRANS-01",
                "status": "SUCCESS",
            },
        )

        # Query with matching filters
        response = test_client.get(
            "/api/v1/audit/events",
            headers={"x-user-role": "ADMIN", "x-clearance": "4"},
            params={
                "user": "FILTER-USER-01",
                "action": "TRANSLATION_CREATED",
                "resource": "DOC-TRANS-01",
                "status": "SUCCESS",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["chain_valid"] is True
        assert len(data["records"]) >= 1
        assert data["records"][0]["user_id"] == "FILTER-USER-01"

    def test_api_query_unauthorized_user_denied(self, test_client: TestClient):
        """GET /api/v1/audit/events without authorization returns 403 Forbidden."""
        response = test_client.get(
            "/api/v1/audit/events",
            headers={"x-user-role": "VIEWER", "x-clearance": "1"},  # Unauthorized!
        )
        assert response.status_code == 403
        assert "is not authorized to access audit logs" in response.json()["detail"]

    def test_api_verify_chain_integrity(self, test_client: TestClient):
        """GET /api/v1/audit/verify returns cryptographic chain verification."""
        response = test_client.get(
            "/api/v1/audit/verify",
            headers={"x-user-role": "ADMIN", "x-clearance": "4"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["chain_valid"] is True
        assert "Cryptographic chain verified unbroken" in data["detail"]

    def test_api_put_delete_modification_strictly_blocked(self, test_client: TestClient):
        """PUT and DELETE on /api/v1/audit/events/{id} are strictly rejected with 403 Forbidden."""
        # Attempt modification
        put_resp = test_client.put(
            "/api/v1/audit/events/AUDIT-12345",
            headers={"x-user-role": "ADMIN", "x-clearance": "4"},
            json={"status": "FAILURE"},
        )
        assert put_resp.status_code == 403

        # Attempt deletion
        del_resp = test_client.delete(
            "/api/v1/audit/events/AUDIT-12345",
            headers={"x-user-role": "ADMIN", "x-clearance": "4"},
        )
        assert del_resp.status_code == 403
