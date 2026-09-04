import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from backend.app.schemas.evidence_models import AuditEvent, AuditEventType


class AuditLogger:
    """Append-only audit logger recording cryptographic and evidence verification events

    for forensic and chain-of-custody compliance.
    """

    def __init__(self) -> None:
        self._events: List[AuditEvent] = []

    def record_event(
        self,
        event_type: AuditEventType,
        evidence_id: str,
        case_id: str,
        actor: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """Appends an immutable audit event."""
        event = AuditEvent(
            event_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            event_type=event_type,
            evidence_id=evidence_id,
            case_id=case_id,
            actor=actor,
            timestamp=datetime.now(timezone.utc).isoformat(),
            details=details or {},
        )
        self._events.append(event)
        return event

    def get_events_for_evidence(self, evidence_id: str) -> List[AuditEvent]:
        """Retrieves all audit events associated with a specific evidence_id in chronological order."""
        return [e for e in self._events if e.evidence_id == evidence_id]

    def get_all_events(self) -> List[AuditEvent]:
        """Returns all recorded audit events."""
        return list(self._events)

    def clear(self) -> None:
        """Clears events in memory (used primarily for test isolation)."""
        self._events.clear()
