from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.auth import router as auth_router
from backend.app.api.cases import router as cases_router
from backend.app.api.copilot import router as copilot_router
from backend.app.api.correlation import router as correlation_router
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.documents import router as documents_router
from backend.app.api.health import router as health_router
from backend.app.api.search import router as search_router
from backend.app.api.timeline import router as timeline_router
from backend.app.api.users import router as users_router
from backend.app.core.config import settings
from backend.app.core.logging_config import setup_logging
from backend.app.core.security import get_password_hash
from backend.app.db.base import Base
from backend.app.db.session import SessionLocal, engine
from backend.app.models.user import User, UserRole

logger = setup_logging()


def init_db():
    """Create tables and ensure default demo accounts exist."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check if default admin exists
        admin = db.query(User).filter(User.email == "admin@evidential.gov.in").first()
        if not admin:
            logger.info("Seeding initial default Administrator account...")
            admin = User(
                email="admin@evidential.gov.in",
                hashed_password=get_password_hash("Admin@123"),
                full_name="Chief Inspector Rajesh Verma",
                badge_number="DL-8842",
                department="State Digital Investigation Directorate",
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin)
        
        # Check if default investigator exists
        officer = db.query(User).filter(User.email == "officer@evidential.gov.in").first()
        if not officer:
            logger.info("Seeding initial default Investigator account...")
            officer = User(
                email="officer@evidential.gov.in",
                hashed_password=get_password_hash("Officer@123"),
                full_name="Investigating Officer Ananya Sen",
                badge_number="WB-4109",
                department="Cyber Crime & Special Investigation",
                role=UserRole.INVESTIGATOR,
                is_active=True,
            )
            db.add(officer)
        
        db.commit()
    except Exception as e:
        logger.error(f"Error initializing DB: {e}")
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize tables and seed root accounts
    logger.info("Starting up EVIDENTIAL Backend Service...")
    init_db()
    yield
    # Shutdown logic
    logger.info("Shutting down EVIDENTIAL Backend Service...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Secure Digital Investigation, Evidence Integrity and Multilingual Case Intelligence Platform",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Secure CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Include API v1 Routers (/api/v1/...)
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(cases_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(search_router, prefix=settings.API_V1_STR)
app.include_router(correlation_router, prefix=settings.API_V1_STR)
app.include_router(timeline_router, prefix=settings.API_V1_STR)
app.include_router(copilot_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)

# Top-level health check alias
app.include_router(health_router)
