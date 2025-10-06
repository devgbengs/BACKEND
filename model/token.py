from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

# Forward references
if False:
    from .user import User

class Token(SQLModel, table=True):
    __tablename__ = "tokens"
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    token_type: Optional[str] = Field(default=None)
    expires_at: Optional[datetime] = Field(default=None)
    revoked: Optional[bool] = Field(default=False)
    revoked_at: Optional[datetime] = Field(default=None)
    revocation_reason: Optional[str] = Field(default=None)

    # Relationships
    user: Optional["User"] = Relationship("model.user.User", back_populates="tokens")