from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime
from pydantic import EmailStr

class TenantBase(SQLModel):
    name: str = Field(index=True)
    domain: Optional[str] = Field(default=None, index=True)
    contact_email: EmailStr
    is_active: bool = Field(default=True)
    description: Optional[str] = None

class TenantCreate(TenantBase):
    pass

class TenantUpdate(SQLModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None

# Add this at the end of the file to avoid circular imports
from schema.user import User  # noqa