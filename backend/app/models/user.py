import enum
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String
from sqlalchemy.orm import relationship

from backend.app.db.session import Base


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    INVESTIGATOR = "INVESTIGATOR"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"
    AUDITOR = "AUDITOR"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    badge_number = Column(String(64), nullable=True)
    department = Column(String(128), nullable=True, default="Cyber Crime & Special Investigation")
    role = Column(Enum(UserRole), default=UserRole.INVESTIGATOR, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    assigned_cases = relationship("Case", foreign_keys="[Case.assigned_officer_id]", back_populates="assigned_officer")
