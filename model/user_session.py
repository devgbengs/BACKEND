from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, String, DateTime, Boolean, Integer

class UserSession(SQLModel, table=True):
    """Model for tracking user sessions and refresh tokens."""
    
    __tablename__ = "user_sessions"
    
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(..., foreign_key="users.id", index=True)
    refresh_token: str = Field(..., sa_column=Column(String(length=512), unique=True))
    is_valid: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(...)
    invalidated_at: Optional[datetime] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)
    ip_address: Optional[str] = Field(default=None)
    
    class Config:
        orm_mode = True