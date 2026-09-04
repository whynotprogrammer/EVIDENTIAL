import pytest
from sqlalchemy.orm import Session

from backend.app.models.case import Case, CasePriority, CaseStatus
from backend.app.models.document import Document, DocumentProcessingStatus, DocumentTranslation
from backend.app.models.entity import ExtractedEntity, EntityType
from backend.app.models.user import User, UserRole


def get_token(client, email="officer1@evidential.gov.in", password="Officer1@123"):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture
def populated_search_db(db_session: Session):
    """
    Sets up two isolated cases for Officer Sen (Investigator 1) and Officer Roy (Investigator 2).
    Ensures clear boundaries for testing cross-case authorization.
    """
    officer1 = db_session.query(User).filter(User.email == "officer1@evidential.gov.in").first()
    officer2 = db_session.query(User).filter(User.email == "officer2@evidential.gov.in").first()

    case_a = db_session.query(Case).filter(Case.case_number == "FIR-SEARCH-A-101").first()
    if not case_a:
        # Case A: Assigned exclusively to Officer 1
        case_a = Case(
            case_number="FIR-SEARCH-A-101",
            title="Connaught Place Crypto Phishing Syndicate",
            description="Investigation into illicit cryptocurrency laundering and OTP interception at Connaught Place.",
            crime_type="CYBER_CRIME",
            location="Connaught Place, New Delhi",
            police_station="Cyber Crime Police Station",
            status=CaseStatus.UNDER_INVESTIGATION,
            priority=CasePriority.HIGH,
            created_by_id=officer1.id,
            assigned_officer_id=officer1.id,
        )
        db_session.add(case_a)
        db_session.commit()
        db_session.refresh(case_a)

        # Document & Entities for Case A
        doc_a = Document(
            case_id=case_a.id,
            filename="crypto_ledger_evidence.pdf",
            original_filename="crypto_ledger_evidence.pdf",
            file_path="storage/uploads/crypto_ledger.pdf",
            sha256_hash="1111111111111111111111111111111111111111111111111111111111111111",
            original_text="Victim Suresh Sharma transferred 5.5 Bitcoins to wallet address after call from +91-9876543210 using vehicle DL-01-AB-1234.",
            detected_language="English",
            uploaded_by_id=officer1.id,
            processing_status=DocumentProcessingStatus.COMPLETED,
        )
        db_session.add(doc_a)
        db_session.commit()
        db_session.refresh(doc_a)

        # Entities for Case A
        ent_phone_a = ExtractedEntity(
            case_id=case_a.id,
            document_id=doc_a.id,
            entity_type=EntityType.PHONE,
            entity_value="+91-9876543210",
            normalized_value="+91-9876543210",
            confidence=0.98,
            context_snippet="...after call from +91-9876543210...",
        )
        ent_vehicle_a = ExtractedEntity(
            case_id=case_a.id,
            document_id=doc_a.id,
            entity_type=EntityType.VEHICLE,
            entity_value="DL-01-AB-1234",
            normalized_value="DL01AB1234",
            confidence=0.95,
            context_snippet="...using vehicle DL-01-AB-1234...",
        )
        db_session.add_all([ent_phone_a, ent_vehicle_a])
        db_session.commit()

    case_b = db_session.query(Case).filter(Case.case_number == "FIR-SEARCH-B-202").first()
    if not case_b:
        # Case B: Assigned exclusively to Officer 2 (Secret Narcotics Ring)
        case_b = Case(
            case_number="FIR-SEARCH-B-202",
            title="Classified Narcotics Smuggling Ring",
            description="Confidential probe into narcotic syndicate operating with code name Operation Cobra in Mumbai Port.",
            crime_type="NARCOTICS",
            location="Bandra, Mumbai",
            police_station="Narcotics Cell, Mumbai",
            status=CaseStatus.UNDER_INVESTIGATION,
            priority=CasePriority.CRITICAL,
            created_by_id=officer2.id,
            assigned_officer_id=officer2.id,
        )
        db_session.add(case_b)
        db_session.commit()
        db_session.refresh(case_b)

        # Document & Entities for Case B
        doc_b = Document(
            case_id=case_b.id,
            filename="narcotics_intercept.txt",
            original_filename="narcotics_intercept.txt",
            file_path="storage/uploads/narcotics_intercept.txt",
            sha256_hash="2222222222222222222222222222222222222222222222222222222222222222",
            original_text="Suspect Dawood Khan intercepted with 10 kg contraband near Bandra docks with phone +91-9123456789.",
            detected_language="English",
            uploaded_by_id=officer2.id,
            processing_status=DocumentProcessingStatus.COMPLETED,
        )
        db_session.add(doc_b)
        db_session.commit()
        db_session.refresh(doc_b)

        ent_phone_b = ExtractedEntity(
            case_id=case_b.id,
            document_id=doc_b.id,
            entity_type=EntityType.PHONE,
            entity_value="+91-9123456789",
            normalized_value="+91-9123456789",
            confidence=0.98,
            context_snippet="...with phone +91-9123456789...",
        )
        db_session.add(ent_phone_b)
        db_session.commit()

    return {"case_a": case_a, "case_b": case_b, "officer1": officer1, "officer2": officer2}


def test_keyword_search(client, populated_search_db):
    """Test general keyword search across case records and document text."""
    token1 = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    headers = {"Authorization": f"Bearer {token1}"}

    # Search for term present in Case A title
    res = client.get("/api/v1/search?q=Crypto", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert any(r["case_number"] == "FIR-SEARCH-A-101" for r in data["results"])

    # Search for term present in Document A text ("Bitcoin")
    res_doc = client.get("/api/v1/search?q=Bitcoin", headers=headers)
    assert res_doc.status_code == 200
    data_doc = res_doc.json()
    assert data_doc["total"] >= 1
    assert any(r["result_type"] == "DOCUMENT" and "Bitcoin" in r["match_snippet"] for r in data_doc["results"])


def test_entity_search(client, populated_search_db):
    """Test targeted entity search by entity_type and entity_value."""
    token1 = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    headers = {"Authorization": f"Bearer {token1}"}

    # Search by entity type PHONE
    res = client.get("/api/v1/search?entity_type=PHONE", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert all(r["entity_type"] == "PHONE" for r in data["results"] if r["result_type"] == "ENTITY")

    # Search by vehicle entity value
    res_veh = client.get("/api/v1/search?entity_type=VEHICLE&entity_value=DL-01-AB-1234", headers=headers)
    assert res_veh.status_code == 200
    data_veh = res_veh.json()
    assert data_veh["total"] >= 1
    assert any(r["entity_value"] == "DL-01-AB-1234" for r in data_veh["results"])


def test_unauthorized_case_cross_access_strictly_prevented(client, populated_search_db):
    """
    CRITICAL SECURITY TEST:
    Authorization MUST happen before retrieval.
    User A (Officer 1) must NEVER retrieve Case B data under any circumstances.
    """
    token1 = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    headers_user_a = {"Authorization": f"Bearer {token1}"}

    # 1. Search for Case B's exclusive keyword ("Narcotics")
    res1 = client.get("/api/v1/search?q=Narcotics", headers=headers_user_a)
    assert res1.status_code == 200
    data1 = res1.json()
    # Officer 1 must NOT see Case B
    assert not any(r["case_number"] == "FIR-SEARCH-B-202" for r in data1["results"])
    assert not any("Bandra" in r["match_snippet"] for r in data1["results"])

    # 2. Search for Case B's secret code name ("Cobra")
    res2 = client.get("/api/v1/search?q=Cobra", headers=headers_user_a)
    assert res2.status_code == 200
    assert res2.json()["total"] == 0

    # 3. Search for Case B's phone number ("9123456789")
    res3 = client.get("/api/v1/search?q=9123456789", headers=headers_user_a)
    assert res3.status_code == 200
    assert res3.json()["total"] == 0

    # 4. Now search AS User B (Officer 2) - Officer 2 SHOULD see Case B
    token2 = get_token(client, "officer2@evidential.gov.in", "Officer2@123")
    headers_user_b = {"Authorization": f"Bearer {token2}"}

    res_b = client.get("/api/v1/search?q=Narcotics", headers=headers_user_b)
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert any(r["case_number"] == "FIR-SEARCH-B-202" for r in data_b["results"])

    # And Officer 2 must NOT see Case A
    res_b_cross = client.get("/api/v1/search?q=Crypto", headers=headers_user_b)
    assert res_b_cross.status_code == 200
    assert not any(r["case_number"] == "FIR-SEARCH-A-101" for r in res_b_cross.json()["results"])


def test_empty_search(client, populated_search_db):
    """Test empty, whitespace, and parameterless searches return 0 results cleanly without errors."""
    token = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    headers = {"Authorization": f"Bearer {token}"}

    # Empty string
    res1 = client.get("/api/v1/search?q=", headers=headers)
    assert res1.status_code == 200
    assert res1.json()["total"] == 0

    # Pure whitespace
    res2 = client.get("/api/v1/search?q=   ", headers=headers)
    assert res2.status_code == 200
    assert res2.json()["total"] == 0

    # No query parameters
    res3 = client.get("/api/v1/search", headers=headers)
    assert res3.status_code == 200
    assert res3.json()["total"] == 0


def test_special_characters_search(client, populated_search_db):
    """Test SQL wildcards, quotes, backslashes, and XSS payloads are safely handled without errors."""
    token = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    headers = {"Authorization": f"Bearer {token}"}

    dangerous_inputs = [
        "%",
        "_",
        "%%%",
        "' OR '1'='1",
        "'; DROP TABLE cases; --",
        "<script>alert('xss')</script>",
        "\\",
        "\\\\",
        "*.*",
        "$#@!^&*",
    ]

    for term in dangerous_inputs:
        res = client.get("/api/v1/search", params={"q": term}, headers=headers)
        assert res.status_code == 200, f"Failed for special character payload: {term}"
        data = res.json()
        assert "results" in data
        assert isinstance(data["results"], list)


def test_large_result_set_pagination(client, db_session):
    """Test pagination with limits and skip offsets on a set of generated records."""
    token = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    headers = {"Authorization": f"Bearer {token}"}
    officer1 = db_session.query(User).filter(User.email == "officer1@evidential.gov.in").first()

    # Generate 15 distinct cases for Officer 1
    for i in range(15):
        case = Case(
            case_number=f"FIR-PAGINATION-{i:03d}",
            title=f"Automated Telecommunication Fraud Case #{i}",
            description="Recurring SIM box fraud pattern across telecom towers.",
            crime_type="CYBER_CRIME",
            created_by_id=officer1.id,
            assigned_officer_id=officer1.id,
        )
        db_session.add(case)
    db_session.commit()

    # Query with limit 5, skip 0
    res_page1 = client.get("/api/v1/search?q=Telecommunication&limit=5&skip=0", headers=headers)
    assert res_page1.status_code == 200
    data1 = res_page1.json()
    assert len(data1["results"]) == 5
    assert data1["total"] >= 15

    # Query with limit 5, skip 5 (page 2)
    res_page2 = client.get("/api/v1/search?q=Telecommunication&limit=5&skip=5", headers=headers)
    assert res_page2.status_code == 200
    data2 = res_page2.json()
    assert len(data2["results"]) == 5

    # Ensure page 1 and page 2 results are mutually exclusive
    page1_ids = [r["case_id"] for r in data1["results"]]
    page2_ids = [r["case_id"] for r in data2["results"]]
    assert not set(page1_ids).intersection(set(page2_ids))
