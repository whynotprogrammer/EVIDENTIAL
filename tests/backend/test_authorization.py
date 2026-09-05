import pytest
from backend.app.models.case import Case, CasePriority, CaseStatus
from backend.app.models.user import User


def get_token_for(client, email, password):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}"
    return res.json()["access_token"]


def test_unauthenticated_cannot_access_cases_api(client):
    """Verify: unauthenticated users cannot access protected case APIs."""
    res = client.get("/api/v1/cases/")
    assert res.status_code in [401, 403]


def test_role_authorization_user_management(client):
    """
    Verify RBAC:
    - ADMIN can create new user accounts (authorized role).
    - INVESTIGATOR / VIEWER cannot create new user accounts (unauthorized role -> 403).
    """
    admin_token = get_token_for(client, "testadmin@evidential.gov.in", "AdminPass@123")
    investigator_token = get_token_for(client, "officer1@evidential.gov.in", "Officer1@123")
    viewer_token = get_token_for(client, "viewer@evidential.gov.in", "Viewer@123")

    new_user_payload = {
        "email": "new_analyst@evidential.gov.in",
        "password": "SecurePass@123",
        "full_name": "New Analyst",
        "role": "ANALYST",
    }

    # 1. Investigator attempts to create user -> 403
    inv_res = client.post(
        "/api/v1/users/",
        json=new_user_payload,
        headers={"Authorization": f"Bearer {investigator_token}"},
    )
    assert inv_res.status_code == 403
    assert "Administrative privileges required" in inv_res.json()["detail"]

    # 2. Viewer attempts to create user -> 403
    viw_res = client.post(
        "/api/v1/users/",
        json=new_user_payload,
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert viw_res.status_code == 403

    # 3. Admin creates user -> 201 Created (authorized role)
    adm_res = client.post(
        "/api/v1/users/",
        json=new_user_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert adm_res.status_code == 201
    assert adm_res.json()["email"] == "new_analyst@evidential.gov.in"


def test_role_authorization_case_creation(client):
    """
    Verify:
    - INVESTIGATOR and ADMIN can create cases.
    - VIEWER cannot create cases (unauthorized role -> 403).
    """
    investigator_token = get_token_for(client, "officer1@evidential.gov.in", "Officer1@123")
    viewer_token = get_token_for(client, "viewer@evidential.gov.in", "Viewer@123")

    case_payload = {
        "case_number": "FIR-2024-TEST-ROLE-01",
        "title": "Unauthorized DB Access Incident",
        "crime_type": "Cyber Trespass",
    }

    # Viewer attempts creation -> 403
    view_res = client.post(
        "/api/v1/cases/",
        json=case_payload,
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert view_res.status_code == 403
    assert "Access forbidden" in view_res.json()["detail"]

    # Investigator creates case -> 201 Created
    inv_res = client.post(
        "/api/v1/cases/",
        json=case_payload,
        headers={"Authorization": f"Bearer {investigator_token}"},
    )
    assert inv_res.status_code == 201
    assert inv_res.json()["case_number"] == "FIR-2024-TEST-ROLE-01"


def test_case_level_authorization(client, db_session):
    """
    Verify Case-Level Authorization:
    - Officer 1 creates and is assigned to Case A.
    - Officer 1 can view Case A.
    - Officer 2 cannot view Case A (403 Forbidden).
    - Officer 2 does not see Case A in case listing.
    - Admin can view Case A.
    """
    token_officer1 = get_token_for(client, "officer1@evidential.gov.in", "Officer1@123")
    token_officer2 = get_token_for(client, "officer2@evidential.gov.in", "Officer2@123")
    token_admin = get_token_for(client, "testadmin@evidential.gov.in", "AdminPass@123")

    # Officer 1 creates case
    case_payload = {
        "case_number": "FIR-2024-CONFIDENTIAL-99",
        "title": "Confidential Cyber Extortion Probe",
        "crime_type": "Cyber Extortion",
    }
    create_res = client.post(
        "/api/v1/cases/",
        json=case_payload,
        headers={"Authorization": f"Bearer {token_officer1}"},
    )
    assert create_res.status_code == 201
    case_id = create_res.json()["id"]

    # 1. Officer 1 views Case -> 200 OK
    res_off1 = client.get(
        f"/api/v1/cases/{case_id}",
        headers={"Authorization": f"Bearer {token_officer1}"},
    )
    assert res_off1.status_code == 200
    assert res_off1.json()["case_number"] == "FIR-2024-CONFIDENTIAL-99"

    # 2. Officer 2 views Case -> 403 FORBIDDEN (unauthorized case access)
    res_off2 = client.get(
        f"/api/v1/cases/{case_id}",
        headers={"Authorization": f"Bearer {token_officer2}"},
    )
    assert res_off2.status_code == 403
    assert "Unauthorized: You do not have permission to access this case." in res_off2.json()["detail"]

    # 3. Officer 2 lists cases -> Case 99 is filtered out
    list_off2 = client.get(
        "/api/v1/cases/",
        headers={"Authorization": f"Bearer {token_officer2}"},
    )
    assert list_off2.status_code == 200
    case_numbers = [c["case_number"] for c in list_off2.json()]
    assert "FIR-2024-CONFIDENTIAL-99" not in case_numbers

    # 4. Admin views Case -> 200 OK
    res_adm = client.get(
        f"/api/v1/cases/{case_id}",
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert res_adm.status_code == 200
    assert res_adm.json()["case_number"] == "FIR-2024-CONFIDENTIAL-99"
