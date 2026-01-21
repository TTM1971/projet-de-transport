from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SessionBase(BaseModel):
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class Session(SessionBase):
    id: str
    user_id: int
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    is_active: bool
    
    class Config:
        from_attributes = True
