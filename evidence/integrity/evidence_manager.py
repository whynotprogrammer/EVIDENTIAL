import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, List
from backend.app.schemas.evidence_models import (
    EvidenceRecord,
    VerificationResult,
    AuditEventType,
)
from evidence.integrity.audit_logger import AuditLogger

STATUS_VALID = "VALID — INTEGRITY VERIFIED"
STATUS_INVALID = "INVALID — TAMPERING DETECTED"


class EvidenceManager:
    """Manages evidence intake, SHA-256 cryptographic hashing, persistence,

    tamper verification, and chain-of-custody audit logging.
    """

    def __init__(
        self,
        audit_logger: Optional[AuditLogger] = None,
        storage_dir: Optional[str] = None,
    ) -> None:
        self.audit_logger = audit_logger or AuditLogger()
        self.storage_dir = Path(storage_dir) if storage_dir else Path("storage/evidence")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._records: Dict[str, EvidenceRecord] = {}
        self._payloads: Dict[str, bytes] = {}

    @staticmethod
    def calculate_sha256(content: bytes) -> str:
        """Calculates standard SHA-256 cryptographic hexadecimal digest."""
        return hashlib.sha256(content).hexdigest()

    def upload_evidence(
        self,
        case_id: str,
        filename: str,
        content: bytes,
        uploaded_by: str,
        description: Optional[str] = None,
        evidence_id: Optional[str] = None,
    ) -> EvidenceRecord:
        """Uploads an evidence file, computes its SHA-256 hash, stores the required

        attributes (evidence_id, case_id, filename, hash, uploaded_by, timestamp),
        and records a HASH_GENERATED audit event.
        """
        assigned_id = evidence_id or f"EVID-{uuid.uuid4().hex[:8].upper()}"
        sha256_hash = self.calculate_sha256(content)
        current_time = datetime.now(timezone.utc).isoformat()

        # Save to storage
        case_store_dir = self.storage_dir / case_id
        case_store_dir.mkdir(parents=True, exist_ok=True)
        stored_file_path = case_store_dir / f"{assigned_id}_{filename}"
        
        try:
            with open(stored_file_path, "wb") as f:
                f.write(content)
            saved_path_str = str(stored_file_path)
        except Exception:
            saved_path_str = None

        self._payloads[assigned_id] = content

        record = EvidenceRecord(
            evidence_id=assigned_id,
            case_id=case_id,
            filename=filename,
            hash=sha256_hash,
            uploaded_by=uploaded_by,
            timestamp=current_time,
            file_size_bytes=len(content),
            storage_path=saved_path_str,
            description=description,
        )
        self._records[assigned_id] = record

        # Dispatch HASH_GENERATED audit event
        self.audit_logger.record_event(
            event_type=AuditEventType.HASH_GENERATED,
            evidence_id=assigned_id,
            case_id=case_id,
            actor=uploaded_by,
            details={
                "filename": filename,
                "hash": sha256_hash,
                "file_size_bytes": len(content),
            },
        )

        return record

    def get_evidence(self, evidence_id: str) -> Optional[EvidenceRecord]:
        """Retrieves stored evidence record by ID."""
        return self._records.get(evidence_id)

    def get_evidence_content(self, evidence_id: str) -> Optional[bytes]:
        """Retrieves stored evidence binary payload."""
        if evidence_id in self._payloads:
            return self._payloads[evidence_id]
        
        record = self.get_evidence(evidence_id)
        if record and record.storage_path and Path(record.storage_path).exists():
            with open(record.storage_path, "rb") as f:
                return f.read()
        return None

    def tamper_stored_payload(self, evidence_id: str, tampered_content: bytes) -> None:
        """Directly alters the stored file/payload without updating the recorded hash.

        Used in automated testing to simulate malicious alteration or corruption.
        """
        self._payloads[evidence_id] = tampered_content
        record = self.get_evidence(evidence_id)
        if record and record.storage_path and Path(record.storage_path).exists():
            with open(record.storage_path, "wb") as f:
                f.write(tampered_content)

    def verify_evidence(
        self,
        evidence_id: str,
        content_to_verify: Optional[bytes] = None,
        verified_by: str = "investigator",
    ) -> VerificationResult:
        """Verifies evidence integrity:

        1. Calculates current SHA-256 of the content (or stored payload).
        2. Compares with stored SHA-256.
        3. If equal: returns 'VALID — INTEGRITY VERIFIED' and logs EVIDENCE_VERIFIED.
        4. If different: returns 'INVALID — TAMPERING DETECTED' and logs INTEGRITY_FAILURE.
        """
        record = self.get_evidence(evidence_id)
        if not record:
            raise KeyError(f"Evidence ID '{evidence_id}' does not exist.")

        # Determine payload to test
        if content_to_verify is not None:
            active_content = content_to_verify
        else:
            active_content = self.get_evidence_content(evidence_id)
            if active_content is None:
                raise FileNotFoundError(f"Content for evidence ID '{evidence_id}' could not be located in storage.")

        current_hash = self.calculate_sha256(active_content)
        verified_at = datetime.now(timezone.utc).isoformat()

        if current_hash == record.hash:
            status = STATUS_VALID
            is_valid = True
            self.audit_logger.record_event(
                event_type=AuditEventType.EVIDENCE_VERIFIED,
                evidence_id=evidence_id,
                case_id=record.case_id,
                actor=verified_by,
                details={
                    "stored_hash": record.hash,
                    "calculated_hash": current_hash,
                    "status": status,
                },
            )
        else:
            status = STATUS_INVALID
            is_valid = False
            self.audit_logger.record_event(
                event_type=AuditEventType.INTEGRITY_FAILURE,
                evidence_id=evidence_id,
                case_id=record.case_id,
                actor=verified_by,
                details={
                    "stored_hash": record.hash,
                    "calculated_hash": current_hash,
                    "status": status,
                    "error": "Cryptographic digest divergence: file has been modified or corrupted.",
                },
            )

        return VerificationResult(
            status=status,
            is_valid=is_valid,
            evidence_id=evidence_id,
            stored_hash=record.hash,
            calculated_hash=current_hash,
            verified_at=verified_at,
            verified_by=verified_by,
            details=f"Verification finished with status: {status}",
        )
