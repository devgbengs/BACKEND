from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

from .tenant import Tenant

class Warehouse(SQLModel, table=True):
    __tablename__ = "warehouses"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    name: str = Field(index=True)
    code: str = Field(unique=True, index=True)
    address: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    tenant: Optional[Tenant] = Relationship(back_populates="warehouses")
    stock_levels: List["StockLevel"] = Relationship(back_populates="warehouse")
    inventory_transactions: List["InventoryTransaction"] = Relationship(back_populates="warehouse")
