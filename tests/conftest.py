from datetime import datetime, timezone
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.security import get_password_hash
from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.models.user import User, UserRole
from backend.app.models.case import Case, CaseStatus, CasePriority

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def keep_unit_tests_offline(request, monkeypatch):
    """Only the explicitly marked neural test may load/download a model."""
    if request.node.get_closest_marker("neural_translation") is None:
        monkeypatch.setenv("EVIDENTIAL_TRANSLATION_LOCAL_ONLY", "true")
    else:
        monkeypatch.delenv("EVIDENTIAL_TRANSLATION_LOCAL_ONLY", raising=False)


@pytest.fixture(scope="session", autouse=True)
def initialize_database():
    """Create all tables once for the test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Yield a clean database session with standard role fixtures."""
    session = TestingSessionLocal()
    
    # 1. Admin User
    admin = session.query(User).filter(User.email == "testadmin@evidential.gov.in").first()
    if not admin:
        admin = User(
            email="testadmin@evidential.gov.in",
            hashed_password=get_password_hash("AdminPass@123"),
            full_name="Admin Chief",
            badge_number="ADM-001",
            role=UserRole.ADMIN,
            is_active=True,
        )
        session.add(admin)

    # 2. Investigator 1 (Officer Sen)
    officer1 = session.query(User).filter(User.email == "officer1@evidential.gov.in").first()
    if not officer1:
        officer1 = User(
            email="officer1@evidential.gov.in",
            hashed_password=get_password_hash("Officer1@123"),
            full_name="Officer Sen",
            badge_number="INV-101",
            role=UserRole.INVESTIGATOR,
            is_active=True,
        )
        session.add(officer1)

    # 3. Investigator 2 (Officer Roy)
    officer2 = session.query(User).filter(User.email == "officer2@evidential.gov.in").first()
    if not officer2:
        officer2 = User(
            email="officer2@evidential.gov.in",
            hashed_password=get_password_hash("Officer2@123"),
            full_name="Officer Roy",
            badge_number="INV-102",
            role=UserRole.INVESTIGATOR,
            is_active=True,
        )
        session.add(officer2)

    # 4. Analyst
    analyst = session.query(User).filter(User.email == "analyst@evidential.gov.in").first()
    if not analyst:
        analyst = User(
            email="analyst@evidential.gov.in",
            hashed_password=get_password_hash("Analyst@123"),
            full_name="Analyst Priya",
            badge_number="ANA-201",
            role=UserRole.ANALYST,
            is_active=True,
        )
        session.add(analyst)

    # 5. Viewer
    viewer = session.query(User).filter(User.email == "viewer@evidential.gov.in").first()
    if not viewer:
        viewer = User(
            email="viewer@evidential.gov.in",
            hashed_password=get_password_hash("Viewer@123"),
            full_name="Viewer Kumar",
            badge_number="VIW-301",
            role=UserRole.VIEWER,
            is_active=True,
        )
        session.add(viewer)

    # 6. Deactivated User
    deact = session.query(User).filter(User.email == "deactivated@evidential.gov.in").first()
    if not deact:
        deact = User(
            email="deactivated@evidential.gov.in",
            hashed_password=get_password_hash("DeactPass@123"),
            full_name="Inactive User",
            role=UserRole.INVESTIGATOR,
            is_active=False,
        )
        session.add(deact)

    session.commit()
    
    yield session
    session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Yield a TestClient with cleanly scoped dependency override."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
