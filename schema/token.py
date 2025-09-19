from pydantic import BaseModel
from typing import Optional, List

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None

class TokenData(BaseModel):
    sub: str  # user_id
    exp: Optional[int] = None  # expiration timestamp
    type: Optional[str] = None  # token type: "access" or "refresh"