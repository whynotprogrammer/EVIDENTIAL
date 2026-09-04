from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr
from backend.app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    badge_number: Optional[str] = None
    department: Optional[str] = "Cyber Crime & Special Investigation"
    role: UserRole = UserRole.INVESTIGATOR
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    badge_number: Optional[str] = None
    department: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserOut(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
