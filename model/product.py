from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

from .tenant import Tenant

if TYPE_CHECKING:
    from .stock_level import StockLevel
    from .inventory_transaction import InventoryTransaction
    from .order import OrderItem

class Product(SQLModel, table=True):
    __tablename__ = "products"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    name: str = Field(index=True)
    sku: str = Field(unique=True, index=True)
    description: Optional[str] = None
    price: float = Field(default=0.0)
    min_stock: int = Field(default=0)
    max_stock: int = Field(default=0)
    category: str = Field(index=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    tenant: Optional[Tenant] = Relationship(back_populates="products")
    stock_levels: List["StockLevel"] = Relationship(back_populates="product")
    inventory_transactions: List["InventoryTransaction"] = Relationship(back_populates="product")
    order_items: List["OrderItem"] = Relationship(back_populates="product")
