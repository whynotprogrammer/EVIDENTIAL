import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.schemas.dashboard_models import (
    DashboardMetrics,
    ChartData,
    RecentActivity,
    NavigationItem,
    CommandCenterResponse,
)
from backend.app.services.dashboard_service import DashboardService
from backend.app.api.dashboard_routes import router as dashboard_router


@pytest.fixture
def dashboard_service_instance() -> DashboardService:
    return DashboardService()


@pytest.fixture
def test_client() -> TestClient:
    app = FastAPI()
    app.include_router(dashboard_router)
    return TestClient(app)


class TestDashboardService:
    """Unit tests verifying data aggregation for the 6 metrics, 4 charts, 4 activity streams, and 8 navigation modules."""

    def test_metrics_aggregation_contains_all_6_required_kpis(
        self, dashboard_service_instance: DashboardService
    ):
        """Validates calculation of: TOTAL CASES, ACTIVE CASES, DOCUMENTS PROCESSED,

        EVIDENCE ITEMS, POTENTIAL CORRELATIONS, AUDIT EVENTS.
        """
        metrics = dashboard_service_instance.get_metrics()
        assert metrics.total_cases > 0
        assert metrics.active_cases > 0
        assert metrics.documents_processed > 0
        assert metrics.evidence_items > 0
        assert metrics.potential_correlations > 0
        assert metrics.audit_events > 0

    def test_charts_aggregation_contains_all_4_required_visualizations(
        self, dashboard_service_instance: DashboardService
    ):
        """Validates: Cases by status, Cases by crime type, Cases by language, Evidence activity."""
        charts = dashboard_service_instance.get_charts()
        assert len(charts.cases_by_status) >= 3
        assert "ACTIVE" in charts.cases_by_status
        assert len(charts.cases_by_crime_type) >= 3
        assert "Cyber Crime" in charts.cases_by_crime_type
        assert len(charts.cases_by_language) >= 3
        assert "English" in charts.cases_by_language
        assert len(charts.evidence_activity) >= 5
        assert charts.evidence_activity[0].ingested_count >= 0

    def test_recent_activity_contains_all_4_required_feeds(
        self, dashboard_service_instance: DashboardService
    ):
        """Validates: Latest cases, Latest documents, Latest correlations, Latest audit events."""
        activity = dashboard_service_instance.get_recent_activity()
        assert len(activity.latest_cases) > 0
        assert activity.latest_cases[0].case_id.startswith("CASE-")
        assert len(activity.latest_documents) > 0
        assert activity.latest_documents[0].doc_id.startswith("DOC-")
        assert len(activity.latest_correlations) > 0
        assert activity.latest_correlations[0].correlation_id.startswith("CORR-")
        assert len(activity.latest_audit_events) > 0
        assert activity.latest_audit_events[0].audit_id.startswith("AUDIT-")

    def test_navigation_modules_contain_all_8_required_items(
        self, dashboard_service_instance: DashboardService
    ):
        """Validates all 8 required navigation modules:

        Dashboard, Cases, Documents, Evidence, Investigation, Correlation, AI Copilot, Audit.
        """
        nav_items = dashboard_service_instance.get_navigation_items()
        nav_names = [item.name for item in nav_items]
        expected_modules = [
            "Dashboard",
            "Cases",
            "Documents",
            "Evidence",
            "Investigation",
            "Correlation",
            "AI Copilot",
            "Audit",
        ]
        for mod in expected_modules:
            assert mod in nav_names


class TestDashboardAPIEndpoints:
    """Integration tests for FastAPI /api/v1/dashboard/* routes."""

    def test_get_dashboard_overview_success(self, test_client: TestClient):
        """GET /api/v1/dashboard/overview returns full consolidated payload."""
        resp = test_client.get("/api/v1/dashboard/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["system_status"] == "OPERATIONAL"

        # Check metrics
        m = data["metrics"]
        assert "total_cases" in m
        assert "active_cases" in m
        assert "documents_processed" in m
        assert "evidence_items" in m
        assert "potential_correlations" in m
        assert "audit_events" in m

        # Check charts
        c = data["charts"]
        assert "cases_by_status" in c
        assert "cases_by_crime_type" in c
        assert "cases_by_language" in c
        assert "evidence_activity" in c

        # Check recent activity
        ra = data["recent_activity"]
        assert "latest_cases" in ra
        assert "latest_documents" in ra
        assert "latest_correlations" in ra
        assert "latest_audit_events" in ra

        # Check navigation
        nav = data["navigation_items"]
        assert len(nav) == 8

    def test_get_dashboard_metrics(self, test_client: TestClient):
        """GET /api/v1/dashboard/metrics."""
        resp = test_client.get("/api/v1/dashboard/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_cases"] >= data["active_cases"]

    def test_get_dashboard_charts(self, test_client: TestClient):
        """GET /api/v1/dashboard/charts."""
        resp = test_client.get("/api/v1/dashboard/charts")
        assert resp.status_code == 200
        data = resp.json()
        assert "cases_by_status" in data

    def test_get_dashboard_recent_activity(self, test_client: TestClient):
        """GET /api/v1/dashboard/recent-activity."""
        resp = test_client.get("/api/v1/dashboard/recent-activity")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["latest_cases"]) > 0

    def test_get_dashboard_navigation(self, test_client: TestClient):
        """GET /api/v1/dashboard/navigation."""
        resp = test_client.get("/api/v1/dashboard/navigation")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == 8
