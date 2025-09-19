from typing import Optional
from pydantic import validator
from sqlmodel import SQLModel, Field
from datetime import datetime

class ProductBase(SQLModel):
    name: str = Field(index=True)
    sku: str = Field(unique=True, index=True)
    description: Optional[str] = None
    price: float = Field(default=0.0)
    category: str = Field(index=True)
    quantity: int = Field(default=0)
    is_active: bool = Field(default=True)
    tenant_id: Optional[int] = None

    @validator('sku')
    def validate_sku(cls, v):
        if not v or len(v) < 3:
            raise ValueError('SKU must be at least 3 characters')
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('SKU must be alphanumeric with only - and _ allowed')
        return v.upper()

    @validator('price')
    def validate_price(cls, v):
        if v < 0:
            raise ValueError('Price cannot be negative')
        return round(v, 2)

    @validator('quantity')
    def validate_quantity(cls, v):
        if v < 0:
            raise ValueError('Quantity cannot be negative')
        return v

class ProductCreate(ProductBase):
    pass

class ProductUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    quantity: Optional[int] = None
    is_active: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Sample Product",
                "description": "A great product",
                "price": 19.99,
                "category": "Electronics",
                "quantity": 100,
                "is_active": True
            }
        }