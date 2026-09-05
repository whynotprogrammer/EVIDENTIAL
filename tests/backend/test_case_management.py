from datetime import datetime, timezone
import pytest


def get_token(client, email, password):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_create_case_with_required_fields(client):
    """Verify POST /api/v1/cases creates a case with all required fields."""
    token = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "case_number": "FIR-2024-WB-8810",
        "title": "State Grid SCADA Intrusion Attempt",
        "description": "Suspicious unauthorized shell commands on substation RTU controller",
        "crime_type": "Critical Infrastructure Cyber Attack",
        "location": "Bidhannagar Substation Complex, Kolkata",
        "incident_date": datetime.now(timezone.utc).isoformat(),
        "status": "UNDER_INVESTIGATION",
        "priority": "CRITICAL",
        "police_station": "Cyber Police Station, Salt Lake",
        "district": "North 24 Parganas",
        "state": "West Bengal",
    }

    response = client.post("/api/v1/cases", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()

    # Check all required fields
    assert data["case_id"] == "FIR-2024-WB-8810"
    assert data["case_number"] == "FIR-2024-WB-8810"
    assert "SCADA" in data["title"]
    assert "RTU" in data["description"]
    assert data["crime_type"] == "Critical Infrastructure Cyber Attack"
    assert data["location"] == "Bidhannagar Substation Complex, Kolkata"
    assert data["status"] == "UNDER_INVESTIGATION"
    assert data["created_by"] is not None
    assert "created_at" in data
    assert "updated_at" in data


def test_get_case_detail_by_id_and_case_number(client):
    """Verify GET /api/v1/cases/{case_id} resolves by both numeric ID and case_number string."""
    token = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "case_number": "FIR-2024-MAH-0045",
        "title": "ATM Network Skimming Ring",
        "crime_type": "Financial Cyber Fraud",
        "location": "Bandra Kurla Complex, Mumbai",
    }
    create_res = client.post("/api/v1/cases", json=payload, headers=headers)
    assert create_res.status_code == 201
    case_data = create_res.json()
    numeric_id = case_data["id"]
    case_num = case_data["case_number"]

    # 1. Fetch by numeric ID
    res_by_id = client.get(f"/api/v1/cases/{numeric_id}", headers=headers)
    assert res_by_id.status_code == 200
    assert res_by_id.json()["title"] == "ATM Network Skimming Ring"

    # 2. Fetch by case_number string
    res_by_num = client.get(f"/api/v1/cases/{case_num}", headers=headers)
    assert res_by_num.status_code == 200
    assert res_by_num.json()["id"] == numeric_id


def test_patch_case_update(client):
    """Verify PATCH /api/v1/cases/{case_id} updates metadata and investigation status."""
    token = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "case_number": "FIR-2024-UP-0912",
        "title": "Crypto Phishing Scheme",
        "crime_type": "Phishing & Wire Fraud",
        "location": "Noida Sector 62",
        "status": "OPEN",
    }
    create_res = client.post("/api/v1/cases", json=payload, headers=headers)
    assert create_res.status_code == 201
    case_id = create_res.json()["id"]

    # Update status to CLOSED and add resolution notes to description
    patch_payload = {
        "status": "CLOSED",
        "description": "Suspects apprehended in joint inter-state raid. Wallet keys recovered.",
        "priority": "LOW",
    }
    patch_res = client.patch(f"/api/v1/cases/{case_id}", json=patch_payload, headers=headers)
    assert patch_res.status_code == 200
    updated_data = patch_res.json()
    assert updated_data["status"] == "CLOSED"
    assert updated_data["priority"] == "LOW"
    assert "apprehended" in updated_data["description"]


def test_case_search(client):
    """Verify GET /api/v1/cases?search=... performs multi-field keyword search."""
    token = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    headers = {"Authorization": f"Bearer {token}"}

    # Create distinct cases
    client.post(
        "/api/v1/cases",
        json={
            "case_number": "FIR-2024-SEARCH-01",
            "title": "SIM Swap Extortion Campaign",
            "crime_type": "Telecom Hijacking",
            "location": "Cyberabad Hitec City",
        },
        headers=headers,
    )
    client.post(
        "/api/v1/cases",
        json={
            "case_number": "FIR-2024-SEARCH-02",
            "title": "Hospital Ransomware Lockdown",
            "crime_type": "Ransomware",
            "location": "AIIMS Campus Delhi",
        },
        headers=headers,
    )

    # Search by keyword "SIM"
    search_sim = client.get("/api/v1/cases?search=SIM", headers=headers)
    assert search_sim.status_code == 200
    sim_cases = search_sim.json()
    assert any("SIM" in c["title"] for c in sim_cases)

    # Search by crime type "Ransomware"
    search_ransom = client.get("/api/v1/cases?search=Ransomware", headers=headers)
    assert search_ransom.status_code == 200
    ransom_cases = search_ransom.json()
    assert any("Hospital" in c["title"] for c in ransom_cases)

    # Search by location "Cyberabad"
    search_loc = client.get("/api/v1/cases?search=Cyberabad", headers=headers)
    assert search_loc.status_code == 200
    loc_cases = search_loc.json()
    assert any("Cyberabad" in c["location"] for c in loc_cases)


def test_case_authorization_boundaries(client):
    """Verify non-assigned officers cannot patch or inspect other officers' cases."""
    token_off1 = get_token(client, "officer1@evidential.gov.in", "Officer1@123")
    token_off2 = get_token(client, "officer2@evidential.gov.in", "Officer2@123")

    create_res = client.post(
        "/api/v1/cases",
        json={
            "case_number": "FIR-2024-PRIV-007",
            "title": "Top Secret Ministry Data Exfiltration",
            "crime_type": "State Espionage",
        },
        headers={"Authorization": f"Bearer {token_off1}"},
    )
    assert create_res.status_code == 201
    case_id = create_res.json()["id"]

    # Officer 2 tries to PATCH Officer 1's case -> 403
    patch_res = client.patch(
        f"/api/v1/cases/{case_id}",
        json={"title": "Hacked Title by Unauthorized User"},
        headers={"Authorization": f"Bearer {token_off2}"},
    )
    assert patch_res.status_code == 403
    assert "Unauthorized" in patch_res.json()["detail"]
