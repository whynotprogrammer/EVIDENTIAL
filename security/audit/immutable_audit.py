import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from backend.app.schemas.audit_models import (
    AuditAction,
    AuditStatus,
    AuditRecord,
    AuditFilterParams,
)


class AuditImmutabilityViolationException(Exception):
    """Raised when an attempt is made to update, modify, or delete an immutable audit record."""
    pass


def compute_audit_hash(
    audit_id: str,
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    timestamp: str,
    status: str,
    metadata: Dict[str, Any],
    previous_hash: str,
) -> str:
    """Computes SHA-256 cryptographic digest binding all record fields and previous hash."""
    canonical_metadata = json.dumps(metadata, sort_keys=True)
    payload = f"{audit_id}|{user_id}|{action}|{resource_type}|{resource_id}|{timestamp}|{status}|{canonical_metadata}|{previous_hash}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ImmutableAuditLedger:
    """Cryptographically verifiable, append-only application audit ledger.

    Strictly forbids modifications and deletions, providing non-repudiation for
    legal defensibility.
    """

    GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

    def __init__(self) -> None:
        self._records: List[AuditRecord] = []
        self._index: Dict[str, AuditRecord] = {}
        self._latest_hash: str = self.GENESIS_HASH

    def log_event(
        self,
        user_id: str,
        action: AuditAction,
        resource_type: str,
        resource_id: str,
        status: AuditStatus = AuditStatus.SUCCESS,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None,
        audit_id: Optional[str] = None,
    ) -> AuditRecord:
        """Appends a new audit record to the cryptographic chain.

        Computes the record hash linked to the previous record hash.
        """
        assigned_id = audit_id or f"AUDIT-{uuid.uuid4().hex[:12].upper()}"
        event_time = timestamp or datetime.now(timezone.utc).isoformat()
        meta = metadata or {}
        prev_hash = self._latest_hash

        rec_hash = compute_audit_hash(
            audit_id=assigned_id,
            user_id=user_id,
            action=action.value,
            resource_type=resource_type,
            resource_id=resource_id,
            timestamp=event_time,
            status=status.value,
            metadata=meta,
            previous_hash=prev_hash,
        )

        record = AuditRecord(
            audit_id=assigned_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            timestamp=event_time,
            status=status,
            metadata=meta,
            previous_hash=prev_hash,
            record_hash=rec_hash,
        )

        self._records.append(record)
        self._index[assigned_id] = record
        self._latest_hash = rec_hash
        return record

    def get_record(self, audit_id: str) -> Optional[AuditRecord]:
        """Retrieves a single audit record by audit_id."""
        return self._index.get(audit_id)

    def query_records(self, filters: Optional[AuditFilterParams] = None) -> List[AuditRecord]:
        """Applies multi-criteria filtering across user, action, date, resource, and status."""
        results = self._records

        if not filters:
            return list(results)

        # Filter: User
        if filters.user_id:
            u_query = filters.user_id.lower()
            results = [r for r in results if u_query in r.user_id.lower()]

        # Filter: Action
        if filters.action:
            results = [r for r in results if r.action == filters.action]

        # Filter: Date (YYYY-MM-DD)
        if filters.date:
            results = [r for r in results if r.timestamp.startswith(filters.date)]

        # Filter: Date Range
        if filters.start_date:
            results = [r for r in results if r.timestamp >= filters.start_date]
        if filters.end_date:
            results = [r for r in results if r.timestamp <= filters.end_date]

        # Filter: Resource (matches resource_type or resource_id)
        if filters.resource:
            res_query = filters.resource.lower()
            results = [
                r for r in results
                if res_query in r.resource_type.lower() or res_query in r.resource_id.lower()
            ]
        if filters.resource_type:
            results = [r for r in results if filters.resource_type.lower() in r.resource_type.lower()]
        if filters.resource_id:
            results = [r for r in results if filters.resource_id.lower() in r.resource_id.lower()]

        # Filter: Status
        if filters.status:
            results = [r for r in results if r.status == filters.status]

        # Pagination
        offset = max(0, filters.offset)
        limit = max(1, filters.limit)
        return results[offset : offset + limit]

    def count_records(self, filters: Optional[AuditFilterParams] = None) -> int:
        """Returns total matching count for current filter set."""
        return len(self.query_records(
            filters.model_copy(update={"limit": 1000000, "offset": 0}) if filters else None
        ))

    def verify_ledger_integrity(self) -> Tuple[bool, Optional[str]]:
        """Verifies the cryptographic chain across all records.

        Returns (True, None) if intact, or (False, error_reason) if tampering is detected.
        """
        expected_prev = self.GENESIS_HASH

        for idx, record in enumerate(self._records):
            # Verify chain link
            if record.previous_hash != expected_prev:
                return (
                    False,
                    f"Cryptographic chain broken at record #{idx} (audit_id: {record.audit_id}): "
                    f"expected previous_hash '{expected_prev}', got '{record.previous_hash}'.",
                )

            # Recompute and verify record hash
            recomputed = compute_audit_hash(
                audit_id=record.audit_id,
                user_id=record.user_id,
                action=record.action.value,
                resource_type=record.resource_type,
                resource_id=record.resource_id,
                timestamp=record.timestamp,
                status=record.status.value,
                metadata=record.metadata,
                previous_hash=record.previous_hash,
            )
            if recomputed != record.record_hash:
                return (
                    False,
                    f"Tampering detected in record #{idx} (audit_id: {record.audit_id}): "
                    f"recalculated hash '{recomputed}' does not match recorded hash '{record.record_hash}'.",
                )

            expected_prev = record.record_hash

        return (True, None)

    def modify_record(self, audit_id: str, updates: Dict[str, Any]) -> None:
        """Attempting to update an audit record is strictly forbidden by design."""
        raise AuditImmutabilityViolationException(
            f"SECURITY ALERT: Audit record '{audit_id}' cannot be modified. "
            "Audit records are immutable and append-only for legal compliance."
        )

    def delete_record(self, audit_id: str) -> None:
        """Attempting to delete an audit record is strictly forbidden by design."""
        raise AuditImmutabilityViolationException(
            f"SECURITY ALERT: Audit record '{audit_id}' cannot be deleted. "
            "Audit records are immutable and append-only for legal compliance."
        )

    def tamper_record_for_testing(self, audit_id: str, field_name: str, new_value: Any) -> None:
        """Simulates internal database alteration / bit-flip for validation testing."""
        if audit_id in self._index:
            rec = self._index[audit_id]
            setattr(rec, field_name, new_value)
