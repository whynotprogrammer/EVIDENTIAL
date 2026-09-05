from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy.orm import Session

from backend.app.models.case import Case, CasePriority, CaseStatus
from backend.app.models.document import Document, DocumentProcessingStatus
from backend.app.models.entity import EntityType, ExtractedEntity
from backend.app.models.evidence import Evidence, EvidenceType, VerificationStatus
from backend.app.models.timeline_event import EventType, InvestigationEvent
from backend.app.models.user import User


def get_token(client, email="officer1@evidential.gov.in", password="Officer1@123"):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture
def populated_timeline_db(db_session: Session):
    """
    Idempotent fixture setting up a rich investigation case with FIR, documents,
    AI extractions, evidence items, and milestones.
    """
    officer1 = db_session.query(User).filter(User.email == "officer1@evidential.gov.in").first()
    officer2 = db_session.query(User).filter(User.email == "officer2@evidential.gov.in").first()

    base_time = datetime(2024, 5, 1, 10, 0, 0, tzinfo=timezone.utc)

    # 1. Case Timeline Alpha (Officer 1's Case)
    case_alpha = db_session.query(Case).filter(Case.case_number == "FIR-TIMELINE-ALPHA").first()
    if not case_alpha:
        case_alpha = Case(
            case_number="FIR-TIMELINE-ALPHA",
            title="Connaught Place ATM Skimming & Identity Theft",
            description="Syndicate installing hardware skimmers across Connaught Place ATM kiosks.",
            crime_type="CYBER_CRIME",
            location="Connaught Place, New Delhi",
            police_station="Cyber Crime Police Station Central",
            incident_date=base_time,
            status=CaseStatus.UNDER_INVESTIGATION,
            priority=CasePriority.HIGH,
            created_by_id=officer1.id,
            assigned_officer_id=officer1.id,
            created_at=base_time + timedelta(hours=2),
        )
        db_session.add(case_alpha)
        db_session.commit()
        db_session.refresh(case_alpha)

    # Ensure document 1 exists
    doc1 = db_session.query(Document).filter(Document.case_id == case_alpha.id).first()
    if not doc1:
        # Document 1: Initial FIR Scan
        doc1 = Document(
            case_id=case_alpha.id,
            filename="fir_scan_001.pdf",
            original_filename="fir_scan_001.pdf",
            file_path="storage/uploads/fir_scan_001.pdf",
            sha256_hash="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            file_size_bytes=102400,
            mime_type="application/pdf",
            uploaded_by_id=officer1.id,
            created_at=base_time + timedelta(hours=3),
            updated_at=base_time + timedelta(hours=4),
            processing_status=DocumentProcessingStatus.COMPLETED,
            detected_language="English",
            original_text="Complainant Rakesh Gupta reported skimming device found at Connaught Place ATM.",
        )
        db_session.add(doc1)
        db_session.commit()
        db_session.refresh(doc1)

        # Entities extracted from Document 1
        ent_person = ExtractedEntity(
            case_id=case_alpha.id,
            document_id=doc1.id,
            entity_type=EntityType.PERSON,
            entity_value="Rakesh Gupta",
            confidence=0.98,
            context_snippet="Complainant Rakesh Gupta reported skimming device",
            created_at=base_time + timedelta(hours=4, minutes=5),
        )
        ent_loc = ExtractedEntity(
            case_id=case_alpha.id,
            document_id=doc1.id,
            entity_type=EntityType.LOCATION,
            entity_value="Connaught Place Outer Circle",
            confidence=0.95,
            created_at=base_time + timedelta(hours=4, minutes=6),
        )
        db_session.add_all([ent_person, ent_loc])

        # Physical Evidence Item
        ev_item = Evidence(
            case_id=case_alpha.id,
            title="Seized Magnetic Stripe Reader",
            description="Physical skimming overlay recovered from ATM fascia.",
            evidence_type=EvidenceType.PHYSICAL,
            file_path="evidence_vault/CP_SKIMMER_01.dat",
            sha256_hash="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            verification_status=VerificationStatus.VALID,
            created_at=base_time + timedelta(days=1),
        )
        db_session.add(ev_item)

        # Investigation Event Milestone
        inv_event = InvestigationEvent(
            case_id=case_alpha.id,
            title="Witness Statement Recorded",
            description="Bank security officer provided CCTV footage showing suspect vehicle.",
            event_type=EventType.WITNESS_STATEMENT,
            event_date=base_time + timedelta(days=2),
            location="Cyber Crime PS Central",
            source_document_id=doc1.id,
            created_at=base_time + timedelta(days=2),
        )
        db_session.add(inv_event)
        db_session.commit()

    # 2. Case Timeline Beta (Officer 2's Case - Strictly Unauthorized for Officer 1)
    case_beta = db_session.query(Case).filter(Case.case_number == "FIR-TIMELINE-BETA-SECRET").first()
    if not case_beta:
        case_beta = Case(
            case_number="FIR-TIMELINE-BETA-SECRET",
            title="Classified Surveillance Operation",
            description="Confidential intelligence wiretap records.",
            crime_type="TERRORISM",
            location="Red Fort Area, Delhi",
            status=CaseStatus.UNDER_INVESTIGATION,
            priority=CasePriority.CRITICAL,
            created_by_id=officer2.id,
            assigned_officer_id=officer2.id,
        )
        db_session.add(case_beta)
        db_session.commit()

    return {"alpha": case_alpha, "beta": case_beta, "officer1": officer1, "officer2": officer2}


# ============================================================================
# AUTOMATED TIMELINE TESTS
# ============================================================================

def test_timeline_chronological_sorting(client, populated_timeline_db):
    """
    CRITICAL REQUIREMENT:
    Investigation timeline events MUST be strictly sorted in chronological order.
    """
    token1 = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    headers = {"Authorization": f"Bearer {token1}"}

    case_id = populated_timeline_db["alpha"].id

    # Ascending order (default)
    res_asc = client.get(f"/api/v1/cases/{case_id}/timeline?order=asc", headers=headers)
    assert res_asc.status_code == 200
    data_asc = res_asc.json()

    assert data_asc["total_events"] >= 5
    events_asc = data_asc["events"]

    for i in range(len(events_asc) - 1):
        d1 = datetime.fromisoformat(events_asc[i]["event_date"].replace("Z", "+00:00"))
        d2 = datetime.fromisoformat(events_asc[i + 1]["event_date"].replace("Z", "+00:00"))
        assert d1 <= d2, f"Chronological ordering violation: {d1} > {d2} (events {i} and {i+1})"

    # Descending order
    res_desc = client.get(f"/api/v1/cases/{case_id}/timeline?order=desc", headers=headers)
    assert res_desc.status_code == 200
    events_desc = res_desc.json()["events"]

    for i in range(len(events_desc) - 1):
        d1 = datetime.fromisoformat(events_desc[i]["event_date"].replace("Z", "+00:00"))
        d2 = datetime.fromisoformat(events_desc[i + 1]["event_date"].replace("Z", "+00:00"))
        assert d1 >= d2, f"Descending ordering violation: {d1} < {d2}"


def test_timeline_source_grounding_no_invented_events(client, populated_timeline_db):
    """
    CRITICAL REQUIREMENT:
    Do not invent events. Every single event MUST have a verified source and source_type.
    """
    token1 = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    headers = {"Authorization": f"Bearer {token1}"}

    case_id = populated_timeline_db["alpha"].id

    res = client.get(f"/api/v1/cases/{case_id}/timeline", headers=headers)
    assert res.status_code == 200
    data = res.json()

    valid_source_types = {"CASE_RECORD", "DOCUMENT", "EXTRACTED_ENTITY", "EVIDENCE", "INVESTIGATION_LOG"}

    for event in data["events"]:
        # 1. Non-empty title and description
        assert event["title"] and len(event["title"].strip()) > 0
        assert event["description"] and len(event["description"].strip()) > 0

        # 2. Strict source verification
        assert event["source"] and len(event["source"].strip()) > 0, f"Event {event['title']} missing source"
        assert event["source_type"] in valid_source_types, f"Invalid source_type: {event['source_type']}"

        # 3. Source ID present
        assert event["source_id"] is not None


def test_all_required_event_types_represented(client, populated_timeline_db):
    """
    Verifies representation of all mandatory event types:
      - FIR registered
      - Document uploaded
      - AI analysis event
      - Person identified
      - Location identified
      - Evidence added
      - Investigation event
    """
    token1 = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    headers = {"Authorization": f"Bearer {token1}"}

    case_id = populated_timeline_db["alpha"].id

    res = client.get(f"/api/v1/cases/{case_id}/timeline", headers=headers)
    assert res.status_code == 200
    events = res.json()["events"]

    event_types = {e["event_type"] for e in events}

    assert "FIR_REGISTERED" in event_types
    assert "DOCUMENT_UPLOADED" in event_types
    assert "AI_ANALYSIS_EVENT" in event_types
    assert "PERSON_IDENTIFIED" in event_types
    assert "LOCATION_IDENTIFIED" in event_types
    assert "EVIDENCE_ADDED" in event_types
    assert any(et in event_types for et in ("WITNESS_STATEMENT", "INVESTIGATION_EVENT", "SEIZURE", "ARREST"))


def test_timeline_pre_retrieval_authorization(client, populated_timeline_db):
    """
    CRITICAL SECURITY CHECK:
    Officer 1 must NOT be able to access the timeline of Officer 2's unauthorized Case Beta.
    Must return 403 Forbidden.
    """
    token1 = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    headers_user_a = {"Authorization": f"Bearer {token1}"}

    unauthorized_case_id = populated_timeline_db["beta"].id

    res = client.get(f"/api/v1/cases/{unauthorized_case_id}/timeline", headers=headers_user_a)
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]

    # Now verify Officer 2 CAN access their own Case Beta timeline
    token2 = get_token(client, "officer2@evidential.gov.in", "Officer2@123")
    headers_user_b = {"Authorization": f"Bearer {token2}"}

    res_b = client.get(f"/api/v1/cases/{unauthorized_case_id}/timeline", headers=headers_user_b)
    assert res_b.status_code == 200
    assert res_b.json()["case_id"] == unauthorized_case_id


def test_create_custom_investigation_milestone(client, populated_timeline_db):
    """
    Verifies that an authorized officer can log an official investigation milestone
    with source attribution, which then appears in the synthesized timeline.
    """
    token1 = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    headers = {"Authorization": f"Bearer {token1}"}

    case_id = populated_timeline_db["alpha"].id

    payload = {
        "title": "Primary Suspect Intercepted at IGI Airport",
        "description": "Suspect apprehended while boarding international flight with forged passport.",
        "event_date": "2024-05-10T18:00:00Z",
        "event_type": "ARREST",
        "location": "IGI Airport Terminal 3, New Delhi",
    }

    create_res = client.post(f"/api/v1/cases/{case_id}/timeline/events", json=payload, headers=headers)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["title"] == payload["title"]
    assert created_data["event_type"] == "ARREST"

    # Now verify it appears in the synthesized timeline
    timeline_res = client.get(f"/api/v1/cases/{case_id}/timeline", headers=headers)
    assert timeline_res.status_code == 200
    events = timeline_res.json()["events"]

    assert any(e["title"] == "Primary Suspect Intercepted at IGI Airport" for e in events)
    arrest_event = next(e for e in events if e["title"] == "Primary Suspect Intercepted at IGI Airport")
    assert arrest_event["source_type"] == "INVESTIGATION_LOG"
    assert arrest_event["source"] is not None
