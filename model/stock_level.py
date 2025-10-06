from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

from .tenant import Tenant
from .product import Product
from .warehouse import Warehouse

class StockLevel(SQLModel, table=True):
    __tablename__ = "stock_levels"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    warehouse_id: int = Field(foreign_key="warehouses.id", index=True)
    quantity: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    tenant: Optional[Tenant] = Relationship(back_populates="stock_levels")
    product: Optional[Product] = Relationship(back_populates="stock_levels")
    warehouse: Optional[Warehouse] = Relationship(back_populates="stock_levels")