from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel
from pydantic import BaseModel

class SessionBase(SQLModel):
    user_id: int
    token: str
    is_active: bool = True
    expires_at: Optional[datetime] = None

class SessionCreate(SessionBase):
    pass

class SessionUpdate(BaseModel):
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None

class Session(SessionBase):
    id: int
    created_at: datetime
    last_activity: datetime

    class Config:
        orm_mode = True