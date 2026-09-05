from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from backend.app.models.audit import AuditAction, AuditStatus


class AuditEventBase(BaseModel):
    action: AuditAction
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = "127.0.0.1"
    status: AuditStatus = AuditStatus.SUCCESS


class AuditEventCreate(AuditEventBase):
    user_id: Optional[int] = None
    user_email: Optional[str] = None


class AuditEventOut(AuditEventBase):
    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
