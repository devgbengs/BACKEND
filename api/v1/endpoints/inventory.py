from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Response
from fastapi import Header
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime
from core.exceptions import ValidationError

from crud.inventory.crud_product import product
from crud.inventory.crud_stock_level import stock_level
from crud.inventory.crud_inventory_transaction import inventory_transaction
from crud.inventory.crud_warehouse import warehouse
from core.database import get_async_session
from model.models import (
    Product, StockLevel, InventoryTransaction, User, 
    Warehouse, InventoryTransactionType
)
from schema.product import ProductCreate, ProductUpdate
from schema.warehouse import WarehouseCreate, WarehouseUpdate
from schema.inventory_transaction import (
    InventoryTransactionCreate, 
    InventoryTransactionRead, 
    InventoryTransactionUpdate
)
from api.deps import get_current_active_user

# Create router
inventory_router = APIRouter()

# Product Routes
@inventory_router.post("/products/", response_model=Product)
async def create_product(
    *,
    product_data: ProductCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Create a new product"""
    product_dict = product_data.model_dump()
    product_dict["tenant_id"] = current_user.tenant_id
    return await product.create(db, obj_in=product_dict)

@inventory_router.get("/products/", response_model=List[Product])
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

@inventory_router.get("/products/{product_id}", response_model=Product)
async def get_product(
    product_id: int = Path(..., title="The ID of the product to get"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get a specific product by ID"""
    db_product = await product.get(db, id=product_id)
    if not db_product or db_product.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Product not found", headers={"X-Error": "Product not found"}   )
    return db_product

@inventory_router.put("/products/{product_id}", response_model=Product)
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

from pydantic import BaseModel

class BulkPriceUpdate(BaseModel):
    product_ids: List[int]
    price_change: float
    operation: str = "absolute"  # "absolute" or "percentage"

@inventory_router.put("/products/bulk-price-update/", response_model=List[Product])
async def bulk_update_prices(
    *,
    update_data: BulkPriceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Bulk update prices for multiple products"""
    updated_products = []
    errors = []
    
    for product_id in update_data.product_ids:
        try:
            # Get product
            db_product = await product.get(db, id=product_id)
            if not db_product or db_product.tenant_id != current_user.tenant_id:
                errors.append({"product_id": product_id, "error": "Product not found"})
                continue
            
            # Calculate new price
            if update_data.operation == "absolute":
                new_price = update_data.price_change
            else:  # percentage
                new_price = db_product.price * (1 + (update_data.price_change / 100))
            
            # Update product
            updated_product = await product.update(
                db,
                db_obj=db_product,
                obj_in={"price": new_price}
            )
            updated_products.append(updated_product)
            
        except Exception as e:
            errors.append({"product_id": product_id, "error": str(e)})
    
    if errors:
        raise HTTPException(
            status_code=207,
            detail={
                "message": "Some products could not be updated",
                "updated": len(updated_products),
                "errors": errors
            }
        )
    
    return updated_products

@inventory_router.get("/products/low-stock/", response_model=List[Product])
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

@inventory_router.delete("/products/{product_id}", response_model=Product)
async def delete_product(
    *,
    product_id: int = Path(..., title="The ID of the product to delete"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Delete a product"""
    db_product = await product.get(db, id=product_id)
    if not db_product or db_product.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if product has any existing transactions
    #transactions = await inventory_transaction.get_product_transactions(
    #    db, 
    #    product_id=product_id,
    #    tenant_id=current_user.tenant_id
    #)
    #if transactions:
    #    raise HTTPException(
    #        status_code=400,
    #        detail="Cannot delete product with existing transactions"
    #    )
    
    # Check if product has any stock levels
    stock_levels = await stock_level.get_product_stock(
        db, 
        product_id=product_id,
        tenant_id=current_user.tenant_id
    )
    if stock_levels:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete product with existing stock levels"
        )
    
    return await product.delete(db, id=product_id)

# Stock Level Routes
@inventory_router.get("/stock-levels/", response_model=List[Dict[str, Any]])
async def list_stock_levels(
    *,
    warehouse_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """List stock levels for a warehouse"""
    # works, but I would like to improve on this
    return await stock_level.get_warehouse_stock(
        db,
        warehouse_id=warehouse_id,
        tenant_id=current_user.tenant_id,
        skip=skip,
        limit=limit
    )

@inventory_router.put("/stock-levels/update/", response_model=StockLevel)
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
    # Validate input
    if operation not in ["add", "subtract"]:
        raise HTTPException(status_code=400, detail="Invalid operation. Must be 'add' or 'subtract'.")
    return await stock_level.update_stock_level(
        db,
        product_id=product_id,
        warehouse_id=warehouse_id,
        quantity_change=quantity_change,
        tenant_id=current_user.tenant_id,
        operation=operation
    )

@inventory_router.get("/stock-levels/alerts/", response_model=List[Dict[str, Any]])
async def get_stock_alerts(
    *,
    threshold: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get stock level alerts"""
    # validate threshold
    if threshold is not None and threshold < 0:
        raise HTTPException(status_code=400, detail="Invalid threshold value")

    return await stock_level.get_low_stock_alerts(
        db,
        tenant_id=current_user.tenant_id,
        threshold=threshold
    )

@inventory_router.get("/stock-levels/summary/", response_model=Dict[str, Any])
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
import logging

logger = logging.getLogger(__name__)


@inventory_router.post("/transactions/", response_model=InventoryTransaction)
async def create_transaction(
    *,
    transaction_data: InventoryTransactionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session),
    response: Response
):
    """Create a new inventory transaction"""
    try:
        logger.info(f"Creating transaction for tenant {current_user.tenant_id}")
        logger.debug(f"Transaction data: {transaction_data.dict()}")
        
        # Verify product exists and belongs to tenant
        db_product = await product.get(db, id=transaction_data.product_id)
        if not db_product:
            logger.warning(f"Product {transaction_data.product_id} not found")
            raise HTTPException(
                status_code=404, 
                detail="Product not found",
                headers={"X-Error": "Product not found"}
            )
        if db_product.tenant_id != current_user.tenant_id:
            logger.warning(f"Product {transaction_data.product_id} belongs to tenant {db_product.tenant_id}, not {current_user.tenant_id}")
            raise HTTPException(
                status_code=403, 
                detail="Access to product denied",
                headers={"X-Error": "Access to product denied"}
            )

        # Verify warehouse exists and belongs to tenant
        db_warehouse = await warehouse.get(db, id=transaction_data.warehouse_id)
        if not db_warehouse:
            logger.warning(f"Warehouse {transaction_data.warehouse_id} not found")
            raise HTTPException(
                status_code=404, 
                detail="Warehouse not found",
                headers={"X-Error": "Warehouse not found"}
            )
        if db_warehouse.tenant_id != current_user.tenant_id:
            logger.warning(f"Warehouse {transaction_data.warehouse_id} belongs to tenant {db_warehouse.tenant_id}, not {current_user.tenant_id}")
            raise HTTPException(
                status_code=403, 
                detail="Access to warehouse denied",
                headers={"X-Error": "Access to warehouse denied"}
            )

        # Generate reference number if not provided
        if not transaction_data.reference_number:
            transaction_data.reference_number = f"TRX-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # Log transaction details before creation
        logger.info(f"Creating transaction with product_id={transaction_data.product_id}, "
                   f"warehouse_id={transaction_data.warehouse_id}, "
                   f"type={transaction_data.transaction_type}, "
                   f"quantity={transaction_data.quantity}")

        try:
            # Create the transaction using the CRUD utility
            db_transaction = await inventory_transaction.create_transaction(
                db,
                tenant_id=current_user.tenant_id,
                product_id=transaction_data.product_id,
                warehouse_id=transaction_data.warehouse_id,
                transaction_type=transaction_data.transaction_type,
                quantity=transaction_data.quantity,
                reference_number=transaction_data.reference_number,
                notes=transaction_data.notes
            )
            
            logger.info(f"Successfully created transaction with id {db_transaction.id}")
            response.headers["X-Transaction-ID"] = str(db_transaction.id)
            response.headers["X-Reference-Number"] = str(db_transaction.reference_number)
            response.headers["X-Transaction-Status"] = "success"
            return db_transaction
            
        except Exception as crud_error:
            logger.error(f"Error in CRUD operation: {str(crud_error)}")
            # Roll back the transaction
            await db.rollback()
            raise crud_error
    
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e),
            headers={"X-Error": str(e)}
        )
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while creating the transaction: {str(e)}",
            headers={"X-Error": f"An error occurred while creating the transaction: {str(e)}"}
        )



@inventory_router.get("/transactions/product/{product_id}", response_model=List[InventoryTransaction])
async def get_product_transactions(
    *,
    product_id: int = Path(..., title="The ID of the product"),
    start_date: Optional[datetime] = Query(None, description="Filter transactions from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter transactions up to this date"),
    transaction_type: Optional[str] = Query(None, description="Filter by transaction type"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, gt=0, le=1000, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get transactions for a specific product"""
    try:
        # Verify product exists and belongs to tenant
        db_product = await product.get(db, id=product_id)
        if not db_product:
            raise HTTPException(status_code=404, detail="Product not found")
        if db_product.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Access to product denied")

        # Validate transaction type if provided
        if transaction_type and transaction_type not in ['stock_in', 'stock_out', 'adjustment', 'transfer']:
            raise HTTPException(status_code=400, detail="Invalid transaction type")

        # Validate date range
        if start_date and end_date and end_date < start_date:
            raise HTTPException(status_code=400, detail="End date cannot be before start date")

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
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve product transactions: {str(e)}",
            headers= {"ReferenceError":"jsj"}
        )

class TransactionSummaryResponse(SQLModel):
    total_transactions: int
    total_stock_in: int
    total_stock_out: int
    total_adjustments: int
    total_transfers: int
    net_quantity_change: int
    transaction_counts: Dict[str, int]
    quantity_by_type: Dict[str, int]

@inventory_router.get("/transactions/summary/", response_model=TransactionSummaryResponse)
async def get_transaction_summary(
    *,
    start_date: Optional[datetime] = Query(None, description="Filter transactions from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter transactions up to this date"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get summary of inventory transactions for the current tenant"""
    try:
        return await inventory_transaction.get_transaction_summary(
            db,
            tenant_id=current_user.tenant_id,
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve transaction summary: {str(e)}"
        )

@inventory_router.get("/transactions/recent/", response_model=List[InventoryTransactionRead])
async def get_recent_transactions(
    *,
    limit: int = Query(default=10, gt=0, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get most recent inventory transactions for the current tenant"""
    try:
        return await inventory_transaction.get_recent_transactions(
            db,
            tenant_id=current_user.tenant_id,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve recent transactions: {str(e)}"
        )

@inventory_router.get("/transactions/{transaction_id}", response_model=InventoryTransaction)
async def get_transaction(
    *,
    transaction_id: int = Path(..., title="The ID of the transaction to get"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get a specific inventory transaction"""
    db_transaction = await inventory_transaction.get(db, id=transaction_id)
    if not db_transaction or db_transaction.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return db_transaction

@inventory_router.delete("/transactions/{transaction_id}", response_model=InventoryTransaction)
async def delete_transaction(
    *,
    transaction_id: int = Path(..., title="The ID of the transaction to delete"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Delete an inventory transaction"""
    db_transaction = await inventory_transaction.get(db, id=transaction_id)
    if not db_transaction or db_transaction.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Only allow deletion of the most recent transaction for a product-warehouse combination
    latest_transaction = await inventory_transaction.get_recent_transactions(
        db,
        #product_id=db_transaction.product_id,
        #warehouse_id=db_transaction.warehouse_id,
        tenant_id=current_user.tenant_id
    )
    
    #if latest_transaction.id != transaction_id:
    #    raise HTTPException(
    #        status_code=400,
    #        detail="Can only delete the most recent transaction for a product-warehouse combination"
   #     )
    
    return await inventory_transaction.delete(db, id=transaction_id)

# Warehouse Routes
@inventory_router.post("/warehouses/", response_model=Warehouse)
async def create_warehouse(
    *,
    warehouse_in: WarehouseCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Create a new warehouse"""
    warehouse_dict = warehouse_in.dict()
    warehouse_dict["tenant_id"] = current_user.tenant_id
    return await warehouse.create(db, obj_in=warehouse_dict)

@inventory_router.get("/warehouses/", response_model=List[Warehouse])
async def list_warehouses(
    *,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """List all warehouses for the current tenant"""
    return await warehouse.get_active_warehouses(
        db,
        tenant_id=current_user.tenant_id,
        skip=skip,
        limit=limit
    )

@inventory_router.get("/warehouses/{warehouse_id}", response_model=Warehouse)
async def get_warehouse(
    *,
    warehouse_id: int = Path(..., title="The ID of the warehouse to get"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get a specific warehouse"""
    result = await warehouse.get(db, id=warehouse_id)
    if not result or result.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return result

@inventory_router.put("/warehouses/{warehouse_id}", response_model=Warehouse)
async def update_warehouse(
    *,
    warehouse_id: int = Path(..., title="The ID of the warehouse to update"),
    warehouse_in: WarehouseUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Update a warehouse"""
    db_warehouse = await warehouse.get(db, id=warehouse_id)
    if not db_warehouse or db_warehouse.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    return await warehouse.update(
        db,
        db_obj=db_warehouse,
        obj_in=warehouse_in
    )

@inventory_router.delete("/warehouses/{warehouse_id}", response_model=Warehouse)
async def delete_warehouse(
    *,
    warehouse_id: int = Path(..., title="The ID of the warehouse to delete"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Delete a warehouse"""
    
    db_warehouse = await warehouse.get(db, id=warehouse_id)
    if not db_warehouse or db_warehouse.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    # Check if warehouse has any stock levels
    stock_levels = await stock_level.get_warehouse_stock(
        db, 
        warehouse_id=warehouse_id,
        tenant_id=current_user.tenant_id
    )
    if stock_levels:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete warehouse with existing stock levels"
        )
    
     #Check if warehouse has any transactions
    transactions = await inventory_transaction.get_recent_transactions(
        db,
        #warehouse_id=warehouse_id,
        tenant_id=current_user.tenant_id
    )
    if transactions:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete warehouse with existing transactions"
        )
    
    return await warehouse.delete(db, id=warehouse_id)

