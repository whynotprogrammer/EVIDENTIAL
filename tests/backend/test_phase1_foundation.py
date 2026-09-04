from sqlalchemy import text


def test_api_v1_health_endpoint(client):
    """Verify Acceptance Criteria: GET /api/v1/health returns healthy status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "EVIDENTIAL"
    assert data["version"] == "1.0.0"
    assert data["database"]["status"] == "connected"
    assert "timestamp" in data


def test_top_level_health_alias(client):
    """Verify top-level /health is also available."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_database_connection_live(db_session):
    """Verify direct DB connectivity through session."""
    result = db_session.execute(text("SELECT 1")).scalar()
    assert result == 1


def test_api_v1_versioning_routes(client):
    """Verify API versioning /api/v1/ is used across endpoints."""
    # Test auth route at /api/v1/auth/login
    auth_res = client.post(
        "/api/v1/auth/login",
        json={"email": "officer1@evidential.gov.in", "password": "Officer1@123"},
    )
    assert auth_res.status_code == 200
    token = auth_res.json()["access_token"]

    # Test cases route at /api/v1/cases/
    cases_res = client.get(
        "/api/v1/cases/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert cases_res.status_code == 200

    # Test dashboard route at /api/v1/dashboard/stats
    dash_res = client.get(
        "/api/v1/dashboard/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert dash_res.status_code == 200


def test_cors_headers(client):
    """Verify CORS middleware headers are properly returned."""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
