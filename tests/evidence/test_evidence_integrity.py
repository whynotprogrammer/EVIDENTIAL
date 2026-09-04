import hashlib
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.schemas.evidence_models import (
    EvidenceRecord,
    VerificationResult,
    AuditEventType,
)
from evidence.integrity.evidence_manager import (
    EvidenceManager,
    STATUS_VALID,
    STATUS_INVALID,
)
from evidence.integrity.audit_logger import AuditLogger
from backend.app.api.evidence_routes import router as evidence_router, evidence_manager as api_manager


@pytest.fixture
def evidence_manager_instance(tmp_path) -> EvidenceManager:
    logger = AuditLogger()
    return EvidenceManager(audit_logger=logger, storage_dir=str(tmp_path / "evidence_store"))


@pytest.fixture
def test_client() -> TestClient:
    app = FastAPI()
    app.include_router(evidence_router)
    return TestClient(app)


class TestEvidenceIntegrityService:
    """Rigorous tests for evidence ingestion, SHA-256 calculation, tamper detection,

    and audit trail logging.
    """

    def test_upload_evidence_calculates_sha256_and_stores_required_fields(
        self, evidence_manager_instance: EvidenceManager
    ):
        """When evidence is uploaded: calculate SHA-256 and store:

        evidence_id, case_id, filename, hash, uploaded_by, timestamp.
        """
        raw_data = b"FORENSIC HARD DRIVE DISK IMAGE DUMP 0xFA1992"
        expected_hash = hashlib.sha256(raw_data).hexdigest()

        record = evidence_manager_instance.upload_evidence(
            case_id="CASE-2024-001",
            filename="hdd_dump.raw",
            content=raw_data,
            uploaded_by="OfficerSmith",
        )

        # Verify all required attributes exist
        assert record.evidence_id is not None
        assert record.evidence_id.startswith("EVID-")
        assert record.case_id == "CASE-2024-001"
        assert record.filename == "hdd_dump.raw"
        assert record.hash == expected_hash
        assert record.uploaded_by == "OfficerSmith"
        assert record.timestamp is not None

        # Verify audit event HASH_GENERATED was logged
        events = evidence_manager_instance.audit_logger.get_events_for_evidence(record.evidence_id)
        assert len(events) == 1
        assert events[0].event_type == AuditEventType.HASH_GENERATED
        assert events[0].details["hash"] == expected_hash

    def test_verify_evidence_valid_integrity(
        self, evidence_manager_instance: EvidenceManager
    ):
        """When current SHA-256 matches stored SHA-256:

        returns 'VALID — INTEGRITY VERIFIED' and logs EVIDENCE_VERIFIED audit event.
        """
        content = b"Surveillance footage snippet 2024-10-11 23:45:00"
        record = evidence_manager_instance.upload_evidence(
            case_id="CASE-2024-001",
            filename="cctv_ch04.mp4",
            content=content,
            uploaded_by="InvestigatorSen",
        )

        # Verification without altering file
        result = evidence_manager_instance.verify_evidence(
            evidence_id=record.evidence_id,
            verified_by="AuditorDoe",
        )

        assert result.status == "VALID — INTEGRITY VERIFIED"
        assert result.status == STATUS_VALID
        assert result.is_valid is True
        assert result.stored_hash == record.hash
        assert result.calculated_hash == record.hash

        # Verify audit event EVIDENCE_VERIFIED was logged
        events = evidence_manager_instance.audit_logger.get_events_for_evidence(record.evidence_id)
        event_types = [e.event_type for e in events]
        assert AuditEventType.HASH_GENERATED in event_types
        assert AuditEventType.EVIDENCE_VERIFIED in event_types

    def test_verify_evidence_invalid_tampering_detected(
        self, evidence_manager_instance: EvidenceManager
    ):
        """When stored content is modified (even a single byte alteration):

        returns 'INVALID — TAMPERING DETECTED' and logs INTEGRITY_FAILURE audit event.
        """
        original_content = b"ORIGINAL TAMPER-FREE CALL LOG AUDIO"
        record = evidence_manager_instance.upload_evidence(
            case_id="CASE-2024-001",
            filename="wiretap_call_01.wav",
            content=original_content,
            uploaded_by="CyberForensicUnit",
        )

        # Malicious tampering: flip 1 character
        tampered_content = b"ORIGINAL TAMPER-FREE CALL LOG AUDIO_MODIFIED"
        evidence_manager_instance.tamper_stored_payload(record.evidence_id, tampered_content)

        # Verify integrity
        result = evidence_manager_instance.verify_evidence(
            evidence_id=record.evidence_id,
            verified_by="InspectorSharma",
        )

        assert result.status == "INVALID — TAMPERING DETECTED"
        assert result.status == STATUS_INVALID
        assert result.is_valid is False
        assert result.calculated_hash != record.hash
        assert result.calculated_hash == hashlib.sha256(tampered_content).hexdigest()

        # Verify audit event INTEGRITY_FAILURE was logged
        events = evidence_manager_instance.audit_logger.get_events_for_evidence(record.evidence_id)
        event_types = [e.event_type for e in events]
        assert AuditEventType.HASH_GENERATED in event_types
        assert AuditEventType.INTEGRITY_FAILURE in event_types

    def test_audit_event_sequence_complete_lifecycle(
        self, evidence_manager_instance: EvidenceManager
    ):
        """Tests complete audit lifecycle: HASH_GENERATED -> EVIDENCE_VERIFIED -> INTEGRITY_FAILURE."""
        content = b"Digital Forensic Memo #881"
        record = evidence_manager_instance.upload_evidence(
            case_id="CASE-2024-001",
            filename="memo.pdf",
            content=content,
            uploaded_by="AgentK",
        )

        # Step 1: initial verification passes
        res1 = evidence_manager_instance.verify_evidence(record.evidence_id, verified_by="AgentK")
        assert res1.status == STATUS_VALID

        # Step 2: tampering occurs
        evidence_manager_instance.tamper_stored_payload(record.evidence_id, b"Corrupted content")
        res2 = evidence_manager_instance.verify_evidence(record.evidence_id, verified_by="AgentL")
        assert res2.status == STATUS_INVALID

        # Check all 3 audit events in order
        events = evidence_manager_instance.audit_logger.get_events_for_evidence(record.evidence_id)
        assert len(events) == 3
        assert events[0].event_type == AuditEventType.HASH_GENERATED
        assert events[1].event_type == AuditEventType.EVIDENCE_VERIFIED
        assert events[2].event_type == AuditEventType.INTEGRITY_FAILURE


class TestEvidenceAPIEndpoints:
    """Integration tests for POST /evidence, GET /evidence/{id}, and POST /evidence/{id}/verify."""

    def test_api_post_evidence_json(self, test_client: TestClient):
        """POST /evidence via JSON."""
        content_text = "Seized cryptographic token recovery data"
        expected_hash = hashlib.sha256(content_text.encode("utf-8")).hexdigest()

        response = test_client.post(
            "/evidence",
            json={
                "case_id": "CASE-2024-001",
                "filename": "token_data.txt",
                "content_text": content_text,
                "uploaded_by": "DetectiveMiller",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["case_id"] == "CASE-2024-001"
        assert data["filename"] == "token_data.txt"
        assert data["hash"] == expected_hash
        assert data["uploaded_by"] == "DetectiveMiller"
        assert "timestamp" in data
        assert "evidence_id" in data

    def test_api_post_evidence_multipart(self, test_client: TestClient):
        """POST /evidence via multipart/form-data."""
        file_payload = b"Binary memory dump bytes 0x00 0xFF 0x12"
        expected_hash = hashlib.sha256(file_payload).hexdigest()

        response = test_client.post(
            "/evidence",
            data={
                "case_id": "CASE-2024-001",
                "uploaded_by": "OfficerRay",
                "description": "Memory dump",
            },
            files={"file": ("mem.bin", file_payload, "application/octet-stream")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "mem.bin"
        assert data["hash"] == expected_hash

    def test_api_get_evidence_by_id(self, test_client: TestClient):
        """GET /evidence/{id}."""
        # Upload first
        upload_resp = test_client.post(
            "/evidence",
            json={
                "case_id": "CASE-2024-001",
                "filename": "test_get.log",
                "content_text": "Sample server log",
                "uploaded_by": "Admin",
            },
        )
        ev_id = upload_resp.json()["evidence_id"]

        # Retrieve
        get_resp = test_client.get(f"/evidence/{ev_id}")
        assert get_resp.status_code == 200
        get_data = get_resp.json()
        assert get_data["evidence_id"] == ev_id
        assert get_data["filename"] == "test_get.log"

    def test_api_get_evidence_not_found(self, test_client: TestClient):
        """GET /evidence/{non_existent_id} returns 404."""
        resp = test_client.get("/evidence/EVID-NONEXISTENT")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"]

    def test_api_post_evidence_verify_valid(self, test_client: TestClient):
        """POST /evidence/{id}/verify returns 'VALID — INTEGRITY VERIFIED'."""
        content = "Unaltered evidence document text"
        upload_resp = test_client.post(
            "/evidence",
            json={
                "case_id": "CASE-2024-001",
                "filename": "unaltered.txt",
                "content_text": content,
                "uploaded_by": "Examiner",
            },
        )
        ev_id = upload_resp.json()["evidence_id"]

        verify_resp = test_client.post(f"/evidence/{ev_id}/verify", json={})
        assert verify_resp.status_code == 200
        verify_data = verify_resp.json()
        assert verify_data["status"] == "VALID — INTEGRITY VERIFIED"
        assert verify_data["is_valid"] is True

    def test_api_post_evidence_verify_tampered(self, test_client: TestClient):
        """POST /evidence/{id}/verify returns 'INVALID — TAMPERING DETECTED' on tampering."""
        content = "Legitimate evidence content"
        upload_resp = test_client.post(
            "/evidence",
            json={
                "case_id": "CASE-2024-001",
                "filename": "to_be_tampered.txt",
                "content_text": content,
                "uploaded_by": "Examiner",
            },
        )
        ev_id = upload_resp.json()["evidence_id"]

        # Directly tamper the stored payload in the API manager
        api_manager.tamper_stored_payload(ev_id, b"Corrupted malicious content injected")

        verify_resp = test_client.post(f"/evidence/{ev_id}/verify", json={})
        assert verify_resp.status_code == 200
        verify_data = verify_resp.json()
        assert verify_data["status"] == "INVALID — TAMPERING DETECTED"
        assert verify_data["is_valid"] is False

    def test_api_get_evidence_audit_trail(self, test_client: TestClient):
        """GET /evidence/{id}/audit returns full audit trail."""
        upload_resp = test_client.post(
            "/evidence",
            json={
                "case_id": "CASE-2024-001",
                "filename": "audit_test.txt",
                "content_text": "Audit test",
                "uploaded_by": "OfficerA",
            },
        )
        ev_id = upload_resp.json()["evidence_id"]

        # Verify it once
        test_client.post(f"/evidence/{ev_id}/verify", json={})

        audit_resp = test_client.get(f"/evidence/{ev_id}/audit")
        assert audit_resp.status_code == 200
        events = audit_resp.json()
        assert len(events) == 2
        assert events[0]["event_type"] == "HASH_GENERATED"
        assert events[1]["event_type"] == "EVIDENCE_VERIFIED"
