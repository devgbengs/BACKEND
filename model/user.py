from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import JSON, Column
from pydantic import EmailStr

from .tenant import Tenant
from .user_role import UserRole

if TYPE_CHECKING:
    from .order import Order
    from .sale import Sale
    from .role import Role

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: Optional[int] = Field(default=None, foreign_key="tenants.id", index=True)
    email: EmailStr = Field(unique=True, index=True)
    user_name: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: str = Field(index=True)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Role names stored as JSON array
    role_names: List[str] = Field(
        default=["user"],
        sa_column=Column(JSON)
    )

    # Relationships
    tenant: Optional[Tenant] = Relationship(back_populates="users")
    orders: List["Order"] = Relationship(back_populates="user")
    sales: List["Sale"] = Relationship(back_populates="customer")
    roles: List["Role"] = Relationship(
        back_populates="users",
        link_model=UserRole
    )
