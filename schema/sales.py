from typing import Optional, List
from datetime import datetime
from pydantic import validator
from sqlmodel import SQLModel, Field
from model.models import SaleStatus, PaymentStatus, PaymentMethod

class SaleItemBase(SQLModel):
    """Base schema for sale items"""
    product_id: int = Field(..., description="ID of the product being sold")
    quantity: int = Field(..., gt=0, description="Quantity of the product")
    unit_price: float = Field(..., gt=0, description="Price per unit")
    discount_percent: Optional[float] = Field(0, ge=0, le=100, description="Discount percentage")
    tax_percent: Optional[float] = Field(0, ge=0, description="Tax percentage")

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        return v

class SaleItemCreate(SaleItemBase):
    """Schema for creating sale items"""
    pass

class SaleItemRead(SaleItemBase):
    """Schema for reading sale items"""
    id: int
    sale_id: int
    discount_amount: float
    tax_amount: float
    subtotal: float
    total: float

class SaleBase(SQLModel):
    """Base schema for sales"""
    customer_id: Optional[int] = Field(None, description="ID of the customer")
    warehouse_id: int = Field(..., description="ID of the warehouse to fulfill the order from")
    payment_method: Optional[PaymentMethod] = Field(None, description="Method of payment")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")

class SaleCreate(SaleBase):
    """Schema for creating sales"""
    items: List[SaleItemCreate] = Field(..., min_items=1, description="List of items in the sale")

    class Config:
        schema_extra = {
            "example": {
                "customer_id": 1,
                "warehouse_id": 1,
                "payment_method": "CASH",
                "notes": "Regular customer purchase",
                "items": [
                    {
                        "product_id": 1,
                        "quantity": 2,
                        "unit_price": 29.99,
                        "discount_percent": 10,
                        "tax_percent": 5
                    }
                ]
            }
        }

class SaleRead(SaleBase):
    """Schema for reading sales"""
    id: int
    reference_number: str
    sale_date: datetime
    status: SaleStatus
    payment_status: PaymentStatus
    subtotal: float
    discount_amount: float
    tax_amount: float
    total_amount: float
    paid_amount: float
    balance_amount: float
    created_at: datetime
    updated_at: datetime
    items: List[SaleItemRead]

class SaleUpdate(SQLModel):
    """Schema for updating sales"""
    payment_method: Optional[PaymentMethod] = None
    notes: Optional[str] = Field(None, max_length=500)

    class Config:
        schema_extra = {
            "example": {
                "payment_method": "card",
                "notes": "Updated payment method"
            }
        }

class SaleStatusUpdate(SQLModel):
    """Schema for updating sale status"""
    status: SaleStatus = Field(..., description="New status for the sale")

class SalePaymentUpdate(SQLModel):
    """Schema for updating sale payment"""
    amount: float = Field(..., gt=0, description="Payment amount")
    payment_method: PaymentMethod = Field(..., description="Method of payment")