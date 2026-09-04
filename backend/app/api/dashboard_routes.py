from typing import List
from fastapi import APIRouter, status

from backend.app.schemas.dashboard_models import (
    DashboardMetrics,
    ChartData,
    RecentActivity,
    NavigationItem,
    CommandCenterResponse,
)
from backend.app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/v1/dashboard", tags=["Command Center Dashboard"])

dashboard_service = DashboardService()


@router.get(
    "/overview",
    response_model=CommandCenterResponse,
    status_code=status.HTTP_200_OK,
    summary="Get full enterprise command center overview",
)
def get_dashboard_overview() -> CommandCenterResponse:
    """Consolidated endpoint delivering all 6 metrics, 4 charts, 4 activity streams, and 8 navigation modules."""
    return dashboard_service.get_overview()


@router.get(
    "/metrics",
    response_model=DashboardMetrics,
    status_code=status.HTTP_200_OK,
    summary="Get core KPI metrics",
)
def get_dashboard_metrics() -> DashboardMetrics:
    """Returns TOTAL CASES, ACTIVE CASES, DOCUMENTS PROCESSED, EVIDENCE ITEMS, POTENTIAL CORRELATIONS, AUDIT EVENTS."""
    return dashboard_service.get_metrics()


@router.get(
    "/charts",
    response_model=ChartData,
    status_code=status.HTTP_200_OK,
    summary="Get distribution charts data",
)
def get_dashboard_charts() -> ChartData:
    """Returns Cases by status, Cases by crime type, Cases by language, and Evidence activity."""
    return dashboard_service.get_charts()


@router.get(
    "/recent-activity",
    response_model=RecentActivity,
    status_code=status.HTTP_200_OK,
    summary="Get recent activity feeds",
)
def get_recent_activity() -> RecentActivity:
    """Returns Latest cases, Latest documents, Latest correlations, and Latest audit events."""
    return dashboard_service.get_recent_activity()


@router.get(
    "/navigation",
    response_model=List[NavigationItem],
    status_code=status.HTTP_200_OK,
    summary="Get navigation modules list",
)
def get_navigation_modules() -> List[NavigationItem]:
    """Returns Dashboard, Cases, Documents, Evidence, Investigation, Correlation, AI Copilot, Audit."""
    return dashboard_service.get_navigation_items()
