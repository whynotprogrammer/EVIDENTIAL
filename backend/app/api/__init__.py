from backend.app.api.copilot_routes import router as copilot_router
from backend.app.api.evidence_routes import router as evidence_router
from backend.app.api.audit_routes import router as audit_router
from backend.app.api.dashboard_routes import router as dashboard_router

__all__ = ["copilot_router", "evidence_router", "audit_router", "dashboard_router"]

