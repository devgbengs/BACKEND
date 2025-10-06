from typing import Optional
from pydantic import EmailStr
from sqlmodel import SQLModel, Field

class WarehouseBase(SQLModel):
    name: str = Field(index=True)
    code: str = Field(unique=True, index=True)
    location: Optional[str] = None
    address: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    is_active: bool = Field(default=True)

class WarehouseCreate(WarehouseBase):
    pass

class WarehouseUpdate(SQLModel):
    name: Optional[str] = None
    location: Optional[str] = None
    address: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    is_active: Optional[bool] = None