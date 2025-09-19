from typing import Optional
from pydantic import validator
from sqlmodel import SQLModel
from datetime import datetime

class InventoryTransactionCreate(SQLModel):
    product_id: int
    warehouse_id: int
    quantity: int
    transaction_type: str
    reference_number: Optional[str] = None
    notes: Optional[str] = None

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        return v

    @validator('transaction_type')
    def validate_transaction_type(cls, v):
        valid_types = ['stock_in', 'stock_out', 'adjustment', 'transfer']
        if v not in valid_types:
            raise ValueError(f'Transaction type must be one of: {", ".join(valid_types)}')
        return v