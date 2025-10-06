from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

from .tenant import Tenant
from .product import Product
from .warehouse import Warehouse
from .enums import InventoryTransactionType

class InventoryTransaction(SQLModel, table=True):
    __tablename__ = "inventory_transactions"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    warehouse_id: int = Field(foreign_key="warehouses.id", index=True)
    transaction_type: InventoryTransactionType = Field(index=True)
    quantity: int = Field(...)
    previous_quantity: int
    new_quantity: int
    reference_number: Optional[str] = Field(None, max_length=100)
    reference_type: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = Field(None, max_length=255)
    transaction_date: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    tenant: Optional[Tenant] = Relationship(back_populates="inventory_transactions")
    product: Product = Relationship(back_populates="inventory_transactions")
    warehouse: Warehouse = Relationship(back_populates="inventory_transactions")