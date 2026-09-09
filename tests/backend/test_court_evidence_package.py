import hashlib
import os
import pytest
from fastapi.testclient import TestClient

from backend.app.models.audit import AuditAction, AuditEvent
from backend.app.models.case import Case, CasePriority, CaseStatus
from backend.app.models.court_package import CourtEvidencePackage
from backend.app.models.evidence import CustodyEvent, CustodyStatus, Evidence
from backend.app.models.timeline_event import EventType, InvestigationEvent
from backend.app.models.user import User, UserRole


def create_test_case(db_session, case_number="CASE-CEP-001"):
    officer = db_session.query(User).filter(User.email == "officer1@evidential.gov.in").first()
    c = Case(
        case_number=case_number,
        title="State v. Suspect - Data Exfiltration Inquiry",
        description="Comprehensive investigation into unauthorized database exfiltration.",
        crime_type="CYBER_CRIME",
        status=CaseStatus.UNDER_INVESTIGATION,
        priority=CasePriority.CRITICAL,
        police_station="Central Cyber Police Station",
        district="Bengaluru Urban",
        state="Karnataka",
        location="Tech Zone 2, Outer Ring Road",
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


def test_readiness_checklist_for_empty_case(client: TestClient, db_session):
    """Verify dynamic readiness checklist correctly reports empty states on brand new case."""
    test_case = create_test_case(db_session, "CASE-CEP-READINESS-01")
    headers = get_auth_headers(client)

    response = client.get(f"/api/v1/cases/{test_case.id}/court-package/readiness", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["case_id"] == test_case.id
    assert data["case_number"] == test_case.case_number
    assert data["case_summary_status"] == "✓ Available"
    assert "⚠ Missing" in data["fir_status"]
    assert "⚠ Missing" in data["witness_statements_status"]
    assert "⚠ Missing" in data["evidence_register_status"]
    assert "⚠ Missing" in data["forensic_reports_status"]
    assert data["is_package_complete"] is False
    assert len(data["missing_sections"]) > 0

    # Verify Preview Data has proper empty messages and zero fake entries
    preview = data["preview"]
    assert preview["evidence_register"]["available"] is False
    assert preview["evidence_register"]["count"] == 0
    assert len(preview["evidence_register"]["items"]) == 0
    assert "NO EVIDENCE REGISTERED" in preview["evidence_register"]["empty_message"]
    assert "NO FIR AVAILABLE" in preview["fir"]["empty_message"]
    assert "NO FORENSIC REPORTS AVAILABLE" in preview["forensic_reports"]["empty_message"]


def test_generate_court_package_incomplete_case(client: TestClient, db_session):
    """Verify package generates successfully with status PACKAGE INCOMPLETE when sections are missing."""
    test_case = create_test_case(db_session, "CASE-CEP-GEN-01")
    headers = get_auth_headers(client)

    response = client.post(f"/api/v1/cases/{test_case.id}/court-package", headers=headers)
    assert response.status_code == 201
    pkg = response.json()

    assert pkg["case_id"] == test_case.id
    assert pkg["package_id"].startswith(f"CEP-{test_case.case_number}-")
    assert pkg["status"] == "PACKAGE INCOMPLETE"
    assert pkg["is_complete"] is False
    assert len(pkg["package_hash"]) == 64  # Valid SHA-256

    # Verify Audit Trail Entry
    audit = (
        db_session.query(AuditEvent)
        .filter(AuditEvent.action == AuditAction.COURT_PACKAGE_GENERATED, AuditEvent.resource_id == pkg["package_id"])
        .first()
    )
    assert audit is not None
    assert audit.status.value == "SUCCESS"

    # Verify Timeline Milestone
    timeline_event = (
        db_session.query(InvestigationEvent)
        .filter(InvestigationEvent.case_id == test_case.id, InvestigationEvent.event_type == EventType.COURT_FILING)
        .first()
    )
    assert timeline_event is not None
    assert pkg["package_id"] in timeline_event.title

    # Verify DB Persistence
    db_rec = db_session.query(CourtEvidencePackage).filter(CourtEvidencePackage.package_id == pkg["package_id"]).first()
    assert db_rec is not None
    assert db_rec.package_hash == pkg["package_hash"]


def test_package_generation_with_real_evidence_and_custody(client: TestClient, db_session):
    """Verify Court Package assembles real evidence, custody events, forensic reports, and signatures."""
    test_case = create_test_case(db_session, "CASE-CEP-REAL-02")
    headers = get_auth_headers(client)

    # 1. Add real digital evidence item
    file_bytes = b"CONFIDENTIAL FINANCIAL RECORD DATABASE EXPORT"
    expected_hash = hashlib.sha256(file_bytes).hexdigest()

    ev_res = client.post(
        f"/api/v1/cases/{test_case.id}/evidence",
        headers=headers,
        data={
            "title": "Suspect Encrypted USB Drive",
            "evidence_type": "USB_DRIVE",
            "collection_location": "Server Rack Room 3",
            "notes": "Recovered connected to target node",
        },
        files={"file": ("usb_backup.img", file_bytes, "application/octet-stream")},
    )
    assert ev_res.status_code == 201
    ev_data = ev_res.json()
    ev_id = ev_data["id"]

    # 2. Seal evidence
    seal_res = client.post(
        f"/api/v1/cases/{test_case.id}/evidence/{ev_id}/seal",
        headers=headers,
        json={"reason": "Tamper-evident anti-static container #USB-901"},
    )
    assert seal_res.status_code == 200

    # 3. Add custody transfer
    trans_res = client.post(
        f"/api/v1/cases/{test_case.id}/evidence/{ev_id}/transfer",
        headers=headers,
        json={
            "to_custodian": "Forensic Lab Officer Sharma",
            "location": "State Cyber Forensic Laboratory, Bengaluru",
            "reason": "Cryptographic file carving and volatile memory extraction",
        },
    )
    assert trans_res.status_code == 200

    # 4. Receive evidence
    recv_res = client.post(
        f"/api/v1/cases/{test_case.id}/evidence/{ev_id}/receive",
        headers=headers,
        json={"received_by": "Forensic Lab Officer Sharma", "location": "FSL Digital Vault"},
    )
    assert recv_res.status_code == 200

    # 5. Start examination
    exam_res = client.post(
        f"/api/v1/cases/{test_case.id}/evidence/{ev_id}/start-examination",
        headers=headers,
        json={"examiner": "Forensic Lab Officer Sharma", "purpose": "Bit-stream forensic acquisition"},
    )
    assert exam_res.status_code == 200

    # 6. Add forensic report
    report_bytes = b"FORENSIC LAB ANALYSIS REPORT: 154 files recovered. Hash confirmed unaltered."
    rep_res = client.post(
        f"/api/v1/cases/{test_case.id}/evidence/{ev_id}/report",
        headers=headers,
        data={
            "report_title": "Certified Digital Forensics Extraction Report",
            "findings": "Extraction verified without data corruption.",
        },
        files={"file": ("forensic_analysis_report.pdf", report_bytes, "application/pdf")},
    )
    assert rep_res.status_code == 200

    # 4. Check readiness checklist reflects real data
    readiness_res = client.get(f"/api/v1/cases/{test_case.id}/court-package/readiness", headers=headers)
    assert readiness_res.status_code == 200
    readiness = readiness_res.json()
    assert "✓ 1 Items" in readiness["evidence_register_status"]
    assert "✓ 1 Reports" in readiness["forensic_reports_status"]
    assert "✓ Complete" in readiness["chain_of_custody_status"] or "Events" in readiness["chain_of_custody_status"]
    assert "✓ Verified" in readiness["integrity_certificates_status"]

    # 5. Generate package
    gen_res = client.post(f"/api/v1/cases/{test_case.id}/court-package", headers=headers)
    assert gen_res.status_code == 201
    pkg = gen_res.json()

    package_data = pkg["package_data"]
    # Evidence Register verification
    assert package_data["evidence_register"]["available"] is True
    assert package_data["evidence_register"]["count"] == 1
    assert package_data["evidence_register"]["items"][0]["original_sha256"] == expected_hash

    # Forensic Reports verification
    assert package_data["forensic_reports"]["available"] is True
    assert package_data["forensic_reports"]["count"] == 1
    assert "forensic_analysis_report.pdf" in package_data["forensic_reports"]["reports"][0]["file_reference"]

    # Chain of Custody verification
    assert package_data["chain_of_custody"]["available"] is True
    assert package_data["chain_of_custody"]["total_events"] >= 2  # COLLECTED + TRANSFERRED

    # Integrity Certificate verification
    assert package_data["integrity_certificates"]["available"] is True
    assert package_data["integrity_certificates"]["all_valid"] is True
    assert package_data["integrity_certificates"]["certificates"][0]["original_sha256"] == expected_hash

    # Audit Certificate verification
    assert package_data["audit_certificate"]["total_audit_events"] >= 3
    assert "Section 65B" in package_data["audit_certificate"]["legal_statute_reference"]


def test_get_latest_and_by_id_court_package(client: TestClient, db_session):
    """Verify retrieval of latest package and fetching by unique package ID."""
    test_case = create_test_case(db_session, "CASE-CEP-FETCH-03")
    headers = get_auth_headers(client)

    # Initial query for non-existent package
    initial_latest = client.get(f"/api/v1/cases/{test_case.id}/court-package/latest", headers=headers)
    assert initial_latest.status_code == 200
    assert initial_latest.json() is None

    # Generate package
    gen_res = client.post(f"/api/v1/cases/{test_case.id}/court-package", headers=headers)
    assert gen_res.status_code == 201
    created_pkg = gen_res.json()
    pkg_id = created_pkg["package_id"]

    # Fetch latest
    latest_res = client.get(f"/api/v1/cases/{test_case.id}/court-package/latest", headers=headers)
    assert latest_res.status_code == 200
    latest_data = latest_res.json()
    assert latest_data["package_id"] == pkg_id
    assert latest_data["package_hash"] == created_pkg["package_hash"]

    # Fetch by package_id
    by_id_res = client.get(f"/api/v1/cases/{test_case.id}/court-package/{pkg_id}", headers=headers)
    assert by_id_res.status_code == 200
    assert by_id_res.json()["package_id"] == pkg_id


def test_unauthorized_officer_cannot_generate_court_package(client: TestClient, db_session):
    """Verify that an officer not assigned to the case receives 403 Forbidden."""
    test_case = create_test_case(db_session, "CASE-CEP-AUTH-04")

    # officer2 is not assigned to this case and is not ADMIN
    officer2_headers = get_auth_headers(client, email="officer2@evidential.gov.in", password="Officer2@123")

    readiness_res = client.get(f"/api/v1/cases/{test_case.id}/court-package/readiness", headers=officer2_headers)
    assert readiness_res.status_code == 403

    gen_res = client.post(f"/api/v1/cases/{test_case.id}/court-package", headers=officer2_headers)
    assert gen_res.status_code == 403
