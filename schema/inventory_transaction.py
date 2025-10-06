from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field
from datetime import datetime
from pydantic import validator
from model.models import InventoryTransactionType

class InventoryTransactionBase(SQLModel):
    """Base schema for inventory transactions"""
    product_id: int = Field(..., description="ID of the product")
    warehouse_id: int = Field(..., description="ID of the warehouse")
    quantity: int = Field(..., gt=0, description="Quantity of items")
    transaction_type: InventoryTransactionType = Field(..., description="Type of transaction")
    reference_number: Optional[str] = Field(None, max_length=100, description="Reference number for the transaction")
    notes: Optional[str] = Field(None, max_length=255, description="Additional notes about the transaction")

class InventoryTransactionCreate(InventoryTransactionBase):
    """Schema for creating inventory transactions"""
    pass

class InventoryTransactionRead(InventoryTransactionBase):
    """Schema for reading inventory transactions"""
    id: int = Field(..., description="Transaction's unique identifier")
    tenant_id: int = Field(..., description="ID of the tenant this transaction belongs to")
    previous_quantity: int = Field(..., description="Quantity before the transaction")
    new_quantity: int = Field(..., description="Quantity after the transaction")
    created_at: datetime = Field(..., description="Timestamp of transaction creation")
    transaction_date: datetime = Field(..., description="Date when the transaction occurred")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "tenant_id": 1,
                "product_id": 1,
                "warehouse_id": 1,
                "quantity": 10,
                "transaction_type": "stock_in",
                "reference_number": "TRX-001",
                "notes": "Initial stock",
                "previous_quantity": 0,
                "new_quantity": 10,
                "created_at": "2025-09-19T10:00:00Z",
                "transaction_date": "2025-09-19T10:00:00Z"
            }
        }

class InventoryTransactionUpdate(SQLModel):
    """Schema for updating inventory transactions"""
    notes: Optional[str] = Field(None, max_length=255, description="Updated notes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "notes": "Updated notes for the transaction"
            }
        }