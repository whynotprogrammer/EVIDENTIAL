from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint validating API service status and database connectivity.
    """
    db_status = "disconnected"
    db_dialect = "unknown"
    try:
        # Perform live ping on DB
        result = db.execute(text("SELECT 1")).scalar()
        if result == 1:
            db_status = "connected"
            db_dialect = db.bind.dialect.name
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unhealthy", "database": f"connection failed: {str(e)}"},
        )

    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "database": {
            "status": db_status,
            "dialect": db_dialect,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
