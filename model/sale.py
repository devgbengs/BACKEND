from typing import List, Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

from .enums import SaleStatus, PaymentStatus, PaymentMethod
from .tenant import Tenant
from .user import User

class Sale(SQLModel, table=True):
    """Model for sales transactions"""
    __tablename__ = "sales"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    customer_id: Optional[int] = Field(foreign_key="users.id", index=True)
    reference_number: str = Field(unique=True, index=True)
    sale_date: datetime = Field(default_factory=datetime.utcnow)
    status: SaleStatus = Field(default=SaleStatus.DRAFT)
    payment_status: PaymentStatus = Field(default=PaymentStatus.UNPAID)
    payment_method: Optional[PaymentMethod] = None
    subtotal: float = Field(default=0, ge=0)
    discount_amount: float = Field(default=0, ge=0)
    tax_amount: float = Field(default=0, ge=0)
    total_amount: float = Field(default=0, ge=0)
    paid_amount: float = Field(default=0, ge=0)
    balance_amount: float = Field(default=0)
    notes: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    items: List["SaleItem"] = Relationship(back_populates="sale")
    customer: Optional[User] = Relationship(back_populates="sales")
    tenant: Optional[Tenant] = Relationship()

class SaleItem(SQLModel, table=True):
    """Model for individual items in a sale"""
    __tablename__ = "sale_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    sale_id: int = Field(foreign_key="sales.id", index=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)
    discount_percent: float = Field(default=0, ge=0, le=100)
    discount_amount: float = Field(default=0, ge=0)
    tax_percent: float = Field(default=0, ge=0)
    tax_amount: float = Field(default=0, ge=0)
    subtotal: float = Field(gt=0)
    total: float = Field(gt=0)

    # Relationships
    sale: Sale = Relationship(back_populates="items")
    product: Optional["Product"] = Relationship()

from .product import Product  # Import at bottom to avoid circular imports