from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime

from crud.inventory.crud_product import product
from crud.inventory.crud_stock_level import stock_level
from crud.inventory.crud_inventory_transaction import inventory_transaction
from core.database import get_async_session
from model.models import Product, StockLevel, InventoryTransaction, User
from schema.product import ProductCreate, ProductUpdate
from schema.inventory import InventoryTransactionCreate
from api.deps import get_current_active_user

# Temporary tenant ID for testing
TEST_TENANT_ID = 1

router = APIRouter()

# Product Routes
@router.post("/products/", response_model=Product)
async def create_product(
    *,
    product_data: ProductCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Create a new product"""
    product_dict = product_data.dict()
    product_dict["tenant_id"] = current_user.tenant_id
    return await product.create(db, obj_in=product_dict)

@router.get("/products/", response_model=List[Product])
async def list_products(
    *,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """List products with optional filtering"""
    products, _ = await product.search_products(
        db,
        search_term=search,
        category=category,
        min_price=min_price,
        max_price=max_price,
        tenant_id=current_user.tenant_id,
        skip=skip,
        limit=limit
    )
    return products

@router.get("/products/{product_id}", response_model=Product)
async def get_product(
    product_id: int = Path(..., title="The ID of the product to get"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get a specific product by ID"""
    db_product = await product.get(db, id=product_id)
    if not db_product or db_product.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@router.put("/products/{product_id}", response_model=Product)
async def update_product(
    *,
    product_id: int = Path(..., title="The ID of the product to update"),
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Update a product"""
    db_product = await product.get(db, id=product_id)
    if not db_product or db_product.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Product not found")
    return await product.update(db, db_obj=db_product, obj_in=product_data)

@router.get("/products/low-stock/", response_model=List[Product])
async def get_low_stock_products(
    *,
    threshold: Optional[int] = 10,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get products with low stock"""
    return await product.get_low_stock_products(
        db,
        threshold=threshold,
        tenant_id=current_user.tenant_id
    )

# Stock Level Routes
@router.get("/stock-levels/", response_model=List[Dict[str, Any]])
async def list_stock_levels(
    *,
    warehouse_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """List stock levels for a warehouse"""
    return await stock_level.get_warehouse_stock(
        db,
        warehouse_id=warehouse_id,
        tenant_id=current_user.tenant_id,
        skip=skip,
        limit=limit
    )

@router.put("/stock-levels/update/", response_model=StockLevel)
async def update_stock_level(
    *,
    product_id: int,
    warehouse_id: int,
    quantity_change: int,
    operation: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Update stock level for a product"""
    return await stock_level.update_stock_level(
        db,
        product_id=product_id,
        warehouse_id=warehouse_id,
        quantity_change=quantity_change,
        tenant_id=current_user.tenant_id,
        operation=operation
    )

@router.get("/stock-levels/alerts/", response_model=List[Dict[str, Any]])
async def get_stock_alerts(
    *,
    threshold: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get stock level alerts"""
    return await stock_level.get_low_stock_alerts(
        db,
        tenant_id=current_user.tenant_id,
        threshold=threshold
    )

@router.get("/stock-levels/summary/", response_model=Dict[str, Any])
async def get_stock_summary(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get summary of stock levels"""
    return await stock_level.get_stock_summary(
        db,
        tenant_id=current_user.tenant_id
    )

# Inventory Transaction Routes
@router.post("/transactions/", response_model=InventoryTransaction)
async def create_transaction(
    *,
    transaction_data: InventoryTransactionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Create a new inventory transaction"""
    transaction_dict = transaction_data.dict()
    transaction_dict["tenant_id"] = current_user.tenant_id
    return await inventory_transaction.create(
        db,
        obj_in=transaction_dict
    )

@router.get("/transactions/product/{product_id}", response_model=List[Dict[str, Any]])
async def get_product_transactions(
    *,
    product_id: int = Path(..., title="The ID of the product"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    transaction_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get transactions for a specific product"""
    return await inventory_transaction.get_product_transactions(
        db,
        product_id=product_id,
        tenant_id=current_user.tenant_id,
        start_date=start_date,
        end_date=end_date,
        transaction_type=transaction_type,
        skip=skip,
        limit=limit
    )

@router.get("/transactions/summary/", response_model=Dict[str, Any])
async def get_transaction_summary(
    *,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get summary of inventory transactions"""
    return await inventory_transaction.get_transaction_summary(
        db,
        tenant_id=current_user.tenant_id,
        start_date=start_date,
        end_date=end_date
    )

@router.get("/transactions/recent/", response_model=List[Dict[str, Any]])
async def get_recent_transactions(
    *,
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get recent inventory transactions"""
    return await inventory_transaction.get_recent_transactions(
        db,
        tenant_id=current_user.tenant_id,
        limit=limit
    )