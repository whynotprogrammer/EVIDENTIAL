from datetime import timedelta
import jwt
import pytest
from backend.app.core.config import settings
from backend.app.core.security import (
    compute_sha256,
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from backend.app.models.user import User


def test_password_hashing_and_never_store_plaintext(db_session):
    """Ensure plaintext passwords are never stored and bcrypt salt/hash works."""
    raw_password = "OfficerSecret@2026!"
    hashed = get_password_hash(raw_password)

    assert hashed != raw_password
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False

    # Verify user in database has hashed password only
    user = db_session.query(User).filter(User.email == "officer1@evidential.gov.in").first()
    assert user is not None
    assert user.hashed_password != "Officer1@123"
    assert user.hashed_password.startswith("$2b$") or user.hashed_password.startswith("$2a$")


def test_jwt_token_flow():
    """Verify standard JWT encoding and decoding."""
    token = create_access_token(subject=101, role="INVESTIGATOR")
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "101"
    assert payload["role"] == "INVESTIGATOR"


def test_valid_login(client):
    """Verify: valid login returns 200 and signed JWT access token."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "officer1@evidential.gov.in", "password": "Officer1@123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "officer1@evidential.gov.in"
    assert data["user"]["role"] == "INVESTIGATOR"


def test_invalid_password(client):
    """Verify: invalid password returns 401 Unauthorized."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "officer1@evidential.gov.in", "password": "WrongPassword999!"},
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_missing_token(client):
    """Verify: missing token returns 401 or 403."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code in [401, 403]


def test_expired_token(client):
    """Verify: expired token returns 401 Unauthorized."""
    expired_token = create_access_token(
        subject=101,
        role="INVESTIGATOR",
        expires_delta=timedelta(seconds=-60),
    )
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert "expired or invalid" in response.json()["detail"]


def test_invalid_token(client):
    """Verify: corrupted/tampered token returns 401 Unauthorized."""
    invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.corrupted_payload.fake_signature"
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )
    assert response.status_code == 401
    assert "expired or invalid" in response.json()["detail"]


def test_deactivated_user_cannot_login(client):
    """Verify: deactivated user account is rejected."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "deactivated@evidential.gov.in", "password": "DeactPass@123"},
    )
    assert response.status_code == 403
    assert "deactivated" in response.json()["detail"]


def test_authenticated_me_profile(client):
    """Verify: protected /api/v1/auth/me returns identity with valid Bearer token."""
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "officer1@evidential.gov.in", "password": "Officer1@123"},
    )
    token = login_res.json()["access_token"]

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["email"] == "officer1@evidential.gov.in"
    assert user_data["role"] == "INVESTIGATOR"
