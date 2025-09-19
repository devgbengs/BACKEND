from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime
from pydantic import validator
from model.models import InventoryTransactionType

class InventoryTransactionBase(SQLModel):
    product_id: int = Field(foreign_key="products.id", index=True)
    warehouse_id: int = Field(foreign_key="warehouses.id", index=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    reference_number: str = Field(unique=True, index=True)
    transaction_type: InventoryTransactionType
    quantity: int
    previous_quantity: int
    new_quantity: int
    unit_price: Optional[float] = None
    transaction_date: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

    @validator('quantity')
    def validate_quantity(cls, v):
        if v == 0:
            raise ValueError('Quantity cannot be zero')
        return v

    @validator('new_quantity')
    def validate_new_quantity(cls, v):
        if v < 0:
            raise ValueError('New quantity cannot be negative')
        return v

    @validator('unit_price')
    def validate_unit_price(cls, v):
        if v and v < 0:
            raise ValueError('Unit price cannot be negative')
        return v

class InventoryTransactionCreate(InventoryTransactionBase):
    pass

class InventoryTransactionUpdate(SQLModel):
    reference_number: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    notes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "reference_number": "TRX-001",
                "quantity": 100,
                "unit_price": 10.99,
                "notes": "Stock adjustment"
            }
        }