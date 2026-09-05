from typing import Optional
from pydantic import BaseModel
from backend.app.schemas.user import UserOut


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str
