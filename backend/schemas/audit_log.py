from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
from typing import Literal

class AuditLogBase(BaseModel):
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    severity: Literal["info", "warning", "error", "critical"] = "info"

class AuditLogCreate(AuditLogBase):
    user_id: Optional[int] = None

class AuditLog(AuditLogBase):
    id: int
    user_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True
