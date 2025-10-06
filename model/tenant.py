from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user import User
    from .product import Product
    from .warehouse import Warehouse
    from .stock_level import StockLevel
    from .inventory_transaction import InventoryTransaction
    from .role import Role
    from .order import Order
    from .sale import Sale

class Tenant(SQLModel, table=True):
    __tablename__ = "tenants"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    domain: str = Field(unique=True, index=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    users: List["User"] = Relationship(back_populates="tenant")
    products: List["Product"] = Relationship(back_populates="tenant")
    warehouses: List["Warehouse"] = Relationship(back_populates="tenant")
    stock_levels: List["StockLevel"] = Relationship(back_populates="tenant")
    inventory_transactions: List["InventoryTransaction"] = Relationship(back_populates="tenant")
    roles: List["Role"] = Relationship(back_populates="tenant")
    orders: List["Order"] = Relationship(back_populates="tenant")
    sales: List["Sale"] = Relationship(back_populates="tenant")
