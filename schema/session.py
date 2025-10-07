from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class SessionBase(BaseModel):
    user_id: int
    refresh_token: str
    expires_at: datetime
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

class SessionCreate(SessionBase):
    pass

class SessionUpdate(BaseModel):
    is_valid: Optional[bool] = None
    invalidated_at: Optional[datetime] = None

class SessionRead(SessionBase):
    id: int
    is_valid: bool
    created_at: datetime
    invalidated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
