from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Header
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime

from crud.sales.crud_sale import CRUDSale, sale
from core.exceptions import ValidationError
from core.database import get_async_session
from schema.sales import (
    SaleCreate, SaleRead, SaleUpdate, 
    SaleStatusUpdate, SalePaymentUpdate
)
from model.models import (
    Product, User, Sale, SaleItem,
    SaleStatus, PaymentStatus, PaymentMethod
)
from api.deps import get_current_active_user

# Initialize CRUD
#sale_crud = CRUDSale(Sale)

# Create router
sales_router = APIRouter()

@sales_router.post("/", response_model=Sale)
async def create_sale(
    *,
    sale_data: SaleCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Create a new sale"""
    # need to handle errors properly.
    try:
        return await sale.create_sale(
            db,
            tenant_id=current_user.tenant_id,
            obj_in=sale_data
        )
    except ValidationError as e:
        error_message = str(e)
        if len(error_message) > 200:  # Truncate long error messages for headers
            header_message = error_message[:197] + "..."
        else:
            header_message = error_message
        raise HTTPException(
            status_code=400,
            detail=error_message,
            headers={"X-Error": header_message}
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while creating the sale: {str(e)}"
        )

@sales_router.get("/{sale_id}", response_model=Sale)
async def get_sale(
    *,
    sale_id: int = Path(..., title="The ID of the sale to get"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get a specific sale"""
    db_sale = await sale.get(db, id=sale_id)
    if not db_sale or db_sale.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Sale not found")
    return db_sale

@sales_router.get("/customer/{customer_id}", response_model=List[Sale])
async def get_sales_by_customer(
    *,
    customer_id: int = Path(..., title="The ID of the customer"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, gt=0, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get sales for a specific customer"""
    return await sale.get_multi(
        db,
        skip=skip,
        limit=limit,
        customer_id=customer_id,
        tenant_id=current_user.tenant_id
    )

@sales_router.get("/user/{customer_id}", response_model=List[Sale])
async def get_user_sales(
    *,
    customer_id: int = Path(..., title="The ID of the user"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, gt=0, le=1000),
    status: Optional[SaleStatus] = Query(None),
    payment_status: Optional[PaymentStatus] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get sales created by a specific user"""
    # Only allow users to see their own sales unless they are admin
    if customer_id != current_user.id and "admin" not in current_user.role_names:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own sales"
        )
    
    query_filter = {
        "tenant_id": current_user.tenant_id,
        "customer_id": customer_id
    }
    
    if status:
        query_filter["status"] = status
    if payment_status:
        query_filter["payment_status"] = payment_status
    if start_date:
        query_filter["sale_date_gte"] = start_date
    if end_date:
        query_filter["sale_date_lte"] = end_date

    return await sale.get_multi(
        db,
        skip=skip,
        limit=limit,
        **query_filter
    )

@sales_router.get("/", response_model=List[Sale])
async def list_sales(
    *,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, gt=0, le=1000),
    status: Optional[SaleStatus] = Query(None),
    payment_status: Optional[PaymentStatus] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """List sales with optional filtering"""
    query_filter = {"tenant_id": current_user.tenant_id}
    if status:
        query_filter["status"] = status
    if payment_status:
        query_filter["payment_status"] = payment_status
    if start_date:
        query_filter["sale_date_gte"] = start_date
    if end_date:
        query_filter["sale_date_lte"] = end_date

    return await sale.get_multi(
        db,
        skip=skip,
        limit=limit,
        **query_filter
    )

@sales_router.patch("/{sale_id}/status", response_model=Sale)
async def update_sale_status(
    *,
    sale_id: int = Path(..., title="The ID of the sale to update"),
    status_update: SaleStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Update the status of a sale"""
    try:
        return await sale.update_status(
            db,
            sale_id=sale_id,
            tenant_id=current_user.tenant_id,
            new_status=status_update.status
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=400, 
            detail=str(e), 
            headers={"X-Error": f"An error occurred while updating the status for sale: {str(e)}"})

@sales_router.post("/{sale_id}/payments", response_model=Sale)
async def add_payment(
    *,
    sale_id: int = Path(..., title="The ID of the sale to update"),
    payment: SalePaymentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Add a payment to a sale"""
    try:
        return await sale.update_payment(
            db,
            sale_id=sale_id,
            tenant_id=current_user.tenant_id,
            amount=payment.amount,
            payment_method=payment.payment_method
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e), headers={"X-Error": f"An error occurred while creating the payment for sale: {str(e)}"})

@sales_router.patch("/{sale_id}", response_model=Sale)
async def update_sale(
    *,
    sale_id: int = Path(..., title="The ID of the sale to update"),
    sale_update: SaleUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Update a sale's basic information"""
    db_sale = await sale.get(db, id=sale_id)
    if not db_sale or db_sale.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    if db_sale.status not in [SaleStatus.DRAFT, SaleStatus.PENDING]:
        raise HTTPException(
            status_code=400,
            detail="Can only update draft or pending sales"
        )

    return await sale.update(
        db,
        db_obj=db_sale,
        obj_in=sale_update
    )

@sales_router.delete("/{sale_id}", response_model=Sale, deprecated=True)
async def delete_sale(
    *,
    sale_id: int = Path(..., title="The ID of the sale to delete"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Delete a sale"""
    db_sale = await sale.get(db, id=sale_id)
    if not db_sale or db_sale.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    # Only allow deletion of draft sales
    if db_sale.status != SaleStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail="Can only delete draft sales"
        )

    # delete associated sale items first due to foreign key constraints
    #items = await sale.get_sale_items(db, sale_id=sale_id)
    #for item in items:
    #    await sale.delete_sale_item(db, sale_id=sale_id, item_id=item.id)


    return await sale.delete(db, id=sale_id)