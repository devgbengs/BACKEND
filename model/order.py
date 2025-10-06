from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

from .tenant import Tenant
from .user import User
from .product import Product
from .enums import OrderStatus, PaymentStatus, PaymentMethod

class Order(SQLModel, table=True):
    __tablename__ = "orders"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    order_number: str = Field(unique=True, index=True)
    status: OrderStatus = Field(default=OrderStatus.PENDING, index=True)
    payment_status: PaymentStatus = Field(default=PaymentStatus.UNPAID, index=True)
    payment_method: Optional[PaymentMethod] = None
    subtotal: float = Field(default=0.0)
    tax_amount: float = Field(default=0.0)
    total: float = Field(default=0.0)
    notes: Optional[str] = None
    order_date: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    tenant: Optional[Tenant] = Relationship(back_populates="orders")
    user: User = Relationship(back_populates="orders")
    items: List["OrderItem"] = Relationship(back_populates="order")

class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", index=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    quantity: int = Field(...)
    unit_price: float
    discount_percent: float = Field(default=0.0)
    discount_amount: float = Field(default=0.0)
    tax_percent: float = Field(default=0.0)
    tax_amount: float = Field(default=0.0)
    subtotal: float
    total: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    order: Order = Relationship(back_populates="items")
    product: Product = Relationship(back_populates="order_items")
