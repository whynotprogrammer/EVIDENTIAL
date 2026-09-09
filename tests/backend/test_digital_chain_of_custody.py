import hashlib
import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.models.audit import AuditEvent
from backend.app.models.case import Case, CasePriority, CaseStatus
from backend.app.models.evidence import CustodyEvent, CustodyStatus, Evidence
from backend.app.models.timeline_event import InvestigationEvent
from backend.app.models.user import User, UserRole


def create_test_case(db_session, case_number="CASE-CUSTODY-001"):
    officer = db_session.query(User).filter(User.email == "officer1@evidential.gov.in").first()
    c = Case(
        case_number=case_number,
        title="Test Cyber Forensic Seizure Case",
        description="Seized hard drive and digital logs for testing chain of custody.",
        crime_type="CYBER_CRIME",
        status=CaseStatus.UNDER_INVESTIGATION,
        priority=CasePriority.HIGH,
        police_station="Cyber Police Station",
        created_by_id=officer.id,
        assigned_officer_id=officer.id,
    )
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c


def get_auth_headers(client, email="officer1@evidential.gov.in", password="Officer1@123"):
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_add_evidence_creates_collected_status_and_first_custody_event(client: TestClient, db_session):
    test_case = create_test_case(db_session, "CASE-CUSTODY-101")
    headers = get_auth_headers(client)

    file_content = b"CRITICAL FORENSIC EVIDENCE PAYLOAD 12345"
    expected_hash = hashlib.sha256(file_content).hexdigest()

    response = client.post(
        f"/api/v1/cases/{test_case.id}/evidence",
        headers=headers,
        data={
            "title": "Seized Laptop NVMe Storage",
            "description": "2TB NVMe SSD seized from suspect premises.",
            "evidence_type": "DIGITAL_FILE",
            "collection_location": "Building 4, Room 12",
            "notes": "Seized under Search Warrant #401",
        },
        files={"file": ("seized_ssd.img", file_content, "application/octet-stream")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["case_id"] == test_case.id
    assert data["title"] == "Seized Laptop NVMe Storage"
    assert data["status"] == "COLLECTED"
    assert data["sha256_hash"] == expected_hash
    assert data["is_tampered"] is False
    assert len(data["custody_events"]) == 1
    assert data["custody_events"][0]["action"] == "EVIDENCE_COLLECTED"
    assert data["custody_events"][0]["new_status"] == "COLLECTED"


def test_custody_workflow_state_machine_valid_transitions(client: TestClient, db_session):
    test_case = create_test_case(db_session, "CASE-CUSTODY-102")
    headers = get_auth_headers(client)

    # 1. Add Evidence (COLLECTED)
    file_content = b"SAMPLE EVIDENCE FILE FOR FULL WORKFLOW TEST"
    res = client.post(
        f"/api/v1/cases/{test_case.id}/evidence",
        headers=headers,
        data={"title": "Hard Drive #A"},
        files={"file": ("hd_a.raw", file_content, "application/octet-stream")},
    )
    assert res.status_code == 201
    ev_id = res.json()["id"]

    # 2. Seal Evidence (COLLECTED -> SEALED)
    res_seal = client.post(
        f"/api/v1/cases/{test_case.id}/evidence/{ev_id}/seal",
        headers=headers,
        json={"reason": "Sealed in evidence bag #9901"},
    )
    assert res_seal.status_code == 200
    assert res_seal.json()["status"] == "SEALED"

    # 3. Transfer Evidence (SEALED -> TRANSFERRED)
    res_trans = client.post(
        f"/api/v1/cases/{test_case.id}/evidence/{ev_id}/transfer",
        headers=headers,
        json={"to_custodian": "State Forensic Science Laboratory", "location": "FSL Intake Office"},
    )
    assert res_trans.status_code == 200
    assert res_trans.json()["status"] == "TRANSFERRED"

    # 4. Receive Evidence (TRANSFERRED -> RECEIVED)
    res_recv = client.post(
        f"/api/v1/cases/{test_case.id}/evidence/{ev_id}/receive",
        headers=headers,
        json={"received_by": "FSL Intake Officer", "location": "FSL Cyber Vault"},
    )
    assert res_recv.status_code == 200
    assert res_recv.json()["status"] == "RECEIVED"

    # 5. Start Examination (RECEIVED -> EXAMINED - in progress)
    res_start = client.post(
        f"/api/v1/cases/{test_case.id}/evidence/{ev_id}/start-examination",
        headers=headers,
        json={"examiner": "Dr. V. Rao", "purpose": "Bit-stream disk imaging"},
    )
    assert res_start.status_code == 200
    assert res_start.json()["status"] == "EXAMINED"

    # 6. Complete Examination (EXAMINED)
    res_comp = client.post(
        f"/api/v1/cases/{test_case.id}/evidence/{ev_id}/complete-examination",
        headers=headers,
        json={"examiner": "Dr. V. Rao", "result_notes": "Identified deleted transaction logs"},
    )
    assert res_comp.status_code == 200
    assert res_comp.json()["status"] == "EXAMINED"

    # 7. Attach Forensic Report (EXAMINED -> REPORT_GENERATED)
    report_content = b"OFFICIAL FORENSIC EXAMINATION REPORT PDF"
    res_rep = client.post(
        f"/api/v1/cases/{test_case.id}/evidence/{ev_id}/report",
        headers=headers,
        data={"report_title": "Forensic Analysis Report v1", "findings": "Deleted files recovered"},
        files={"file": ("fsl_report.pdf", report_content, "application/pdf")},
    )
    assert res_rep.status_code == 200
    assert res_rep.json()["status"] == "REPORT_GENERATED"
    assert res_rep.json()["forensic_report_hash"] == hashlib.sha256(report_content).hexdigest()

    # 8. Return Evidence (REPORT_GENERATED -> RETURNED)
    res_ret = client.post(
        f"/api/v1/cases/{test_case.id}/evidence/{ev_id}/return",
        headers=headers,
        json={"to_custodian": "Investigating Officer", "location": "Police Station Vault"},
    )
    assert res_ret.status_code == 200
    assert res_ret.json()["status"] == "RETURNED"

    # 9. Submit to Court (RETURNED -> COURT_SUBMITTED)
    res_crt = client.post(
        f"/api/v1/cases/{test_case.id}/evidence/{ev_id}/submit-court",
        headers=headers,
        json={"court_name": "District & Sessions Court", "submission_notes": "Submitted as Prosecution Exhibit #4"},
    )
    assert res_crt.status_code == 200
    assert res_crt.json()["status"] == "COURT_SUBMITTED"

    # Verify chain history
    res_chain = client.get(
        f"/api/v1/cases/{test_case.id}/evidence/{ev_id}/custody-chain",
        headers=headers,
    )
    assert res_chain.status_code == 200
    chain_data = res_chain.json()
    assert chain_data["current_status"] == "COURT_SUBMITTED"
    assert chain_data["total_events"] >= 8


def test_custody_workflow_invalid_transitions_rejected(client: TestClient, db_session):
    test_case = create_test_case(db_session, "CASE-CUSTODY-103")
    headers = get_auth_headers(client)

    # Add evidence (Status: COLLECTED)
    res = client.post(
        f"/api/v1/cases/{test_case.id}/evidence",
        headers=headers,
        data={"title": "Raw Flash Drive"},
    )
    ev_id = res.json()["id"]

    # Attempt illegal direct transition: COLLECTED -> submit-court (Must be RETURNED first)
    res_bad1 = client.post(
        f"/api/v1/cases/{test_case.id}/evidence/{ev_id}/submit-court",
        headers=headers,
        json={"court_name": "High Court"},
    )
    assert res_bad1.status_code == 400
    assert "Invalid state transition" in res_bad1.json()["detail"]

    # Attempt illegal direct transition: COLLECTED -> receive (Must be TRANSFERRED first)
    res_bad2 = client.post(
        f"/api/v1/cases/{test_case.id}/evidence/{ev_id}/receive",
        headers=headers,
    )
    assert res_bad2.status_code == 400


def test_custody_events_persisted_to_audit_ledger_and_timeline(client: TestClient, db_session):
    test_case = create_test_case(db_session, "CASE-CUSTODY-104")
    headers = get_auth_headers(client)

    initial_audit_count = db_session.query(AuditEvent).count()
    initial_timeline_count = db_session.query(InvestigationEvent).count()

    # Add evidence
    res = client.post(
        f"/api/v1/cases/{test_case.id}/evidence",
        headers=headers,
        data={"title": "Mobile Phone Samsung S22"},
    )
    ev_id = res.json()["id"]

    # Seal evidence
    client.post(
        f"/api/v1/cases/{test_case.id}/evidence/{ev_id}/seal",
        headers=headers,
    )

    new_audit_count = db_session.query(AuditEvent).count()
    new_timeline_count = db_session.query(InvestigationEvent).count()

    # Expect at least 2 audit events and 2 timeline events added
    assert new_audit_count >= initial_audit_count + 2
    assert new_timeline_count >= initial_timeline_count + 2


def test_real_sha256_integrity_verification_pass_and_tamper_detection(client: TestClient, db_session):
    test_case = create_test_case(db_session, "CASE-CUSTODY-105")
    headers = get_auth_headers(client)

    original_content = b"AUTHENTIC UNMODIFIED BINARY DATA FOR INTEGRITY CHECK"
    res = client.post(
        f"/api/v1/cases/{test_case.id}/evidence",
        headers=headers,
        data={"title": "Target File for Tamper Test"},
        files={"file": ("target.bin", original_content, "application/octet-stream")},
    )
    ev_id = res.json()["id"]
    file_path = res.json()["file_path"]

    # Verify intact file
    ver_res1 = client.post(
        f"/api/v1/cases/{test_case.id}/evidence/{ev_id}/verify",
        headers=headers,
    )
    assert ver_res1.status_code == 200
    vdata1 = ver_res1.json()
    assert vdata1["is_valid"] is True
    assert "✓ INTEGRITY VERIFIED" in vdata1["status"]

    # Manually tamper file content on disk
    if file_path and os.path.exists(file_path):
        with open(file_path, "wb") as f:
            f.write(b"TAMPERED MALICIOUS CONTENT INJECTED ON DISK")

    # Verify modified file
    ver_res2 = client.post(
        f"/api/v1/cases/{test_case.id}/evidence/{ev_id}/verify",
        headers=headers,
    )
    assert ver_res2.status_code == 200
    vdata2 = ver_res2.json()
    assert vdata2["is_valid"] is False
    assert "⚠ INTEGRITY VIOLATION DETECTED" in vdata2["status"]

    # Check evidence record updated with tamper flag
    detail_res = client.get(
        f"/api/v1/cases/{test_case.id}/evidence/{ev_id}",
        headers=headers,
    )
    assert detail_res.json()["is_tampered"] is True


def test_immutability_of_custody_events(client: TestClient, db_session):
    test_case = create_test_case(db_session, "CASE-CUSTODY-106")
    headers = get_auth_headers(client)

    res = client.post(
        f"/api/v1/cases/{test_case.id}/evidence",
        headers=headers,
        data={"title": "Immutable Ledger Subject"},
    )
    ev_id = res.json()["id"]

    client.post(
        f"/api/v1/cases/{test_case.id}/evidence/{ev_id}/seal",
        headers=headers,
    )

    events_in_db = db_session.query(CustodyEvent).filter(CustodyEvent.evidence_id == ev_id).all()
    assert len(events_in_db) == 2
    e1, e2 = events_in_db[0], events_in_db[1]
    assert e1.id != e2.id
    assert e1.action == "EVIDENCE_COLLECTED"
    assert e2.action == "EVIDENCE_SEALED"


def test_empty_state_when_no_evidence_or_events(client: TestClient, db_session):
    test_case = create_test_case(db_session, "CASE-CUSTODY-107")
    headers = get_auth_headers(client)

    res_list = client.get(
        f"/api/v1/cases/{test_case.id}/evidence",
        headers=headers,
    )
    assert res_list.status_code == 200
    assert res_list.json() == []

    res_404 = client.get(
        f"/api/v1/cases/{test_case.id}/evidence/99999",
        headers=headers,
    )
    assert res_404.status_code == 404
