from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel
from pydantic import EmailStr

# Base User Schema for shared attributes
class UserBase(SQLModel):
    email: EmailStr
    full_name: str
    user_name: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    role_names: List[str] = []
    permissions: List[str] = []

# Schema for user creation
class UserCreate(UserBase):
    password: str
    tenant_id: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user1@example.com",
                "full_name": "John Doe",
                "user_name": "johndoe",
                "phone_number": "+1234567890",
                "is_active": True,
                "is_superuser": False,
                "role_names": ["user"],
                "permissions": ["read:items"],
                "password": "userpass123"
            }
        }

# Schema for user updates
class UserUpdate(SQLModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    user_name: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = None
    role_names: Optional[List[str]] = None
    permissions: Optional[List[str]] = None

# Schema for user responses
class User(UserBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None
    mfa_enabled: Optional[bool] = None
    require_password_change: Optional[bool] = None

    class Config:
        from_attributes = True