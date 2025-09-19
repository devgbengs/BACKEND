from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime
from pydantic import validator

class StockLevelBase(SQLModel):
    quantity: int = Field(default=0)
    minimum_level: Optional[int] = Field(default=0)
    maximum_level: Optional[int] = Field(default=None)
    reorder_point: Optional[int] = Field(default=None)
    product_id: int = Field(foreign_key="products.id", index=True)
    warehouse_id: int = Field(foreign_key="warehouses.id", index=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)

    @validator('quantity')
    def validate_quantity(cls, v):
        if v < 0:
            raise ValueError('Quantity cannot be negative')
        return v

    @validator('minimum_level')
    def validate_minimum_level(cls, v):
        if v and v < 0:
            raise ValueError('Minimum level cannot be negative')
        return v

    @validator('maximum_level')
    def validate_maximum_level(cls, v):
        if v and v < 0:
            raise ValueError('Maximum level cannot be negative')
        return v

    @validator('reorder_point')
    def validate_reorder_point(cls, v):
        if v and v < 0:
            raise ValueError('Reorder point cannot be negative')
        return v

class StockLevelCreate(StockLevelBase):
    pass

class StockLevelUpdate(SQLModel):
    quantity: Optional[int] = None
    minimum_level: Optional[int] = None
    maximum_level: Optional[int] = None
    reorder_point: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "quantity": 100,
                "minimum_level": 10,
                "maximum_level": 1000,
                "reorder_point": 20
            }
        }