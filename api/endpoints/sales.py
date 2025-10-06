from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user, get_db
from crud import crud
from model import User
from model.sale import Sale, SaleStatus, PaymentStatus

router = APIRouter()

@router.get("/sales/", response_model=List[Sale])
async def list_sales(
    *,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    tenant_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    user_id: Optional[int] = None,
    status: Optional[SaleStatus] = None,
    payment_status: Optional[PaymentStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get list of sales with optional filters"""
    # Ensure tenant_id matches current user's tenant
    if tenant_id and tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=400,
            detail="Requested tenant ID does not match user's tenant"
        )
    
    sales = await crud.sale.get_multi(
        db,
        skip=skip,
        limit=limit,
        tenant_id=tenant_id or current_user.tenant_id,
        customer_id=customer_id,
        user_id=user_id,
        status=status,
        payment_status=payment_status,
        sale_date_gte=start_date,
        sale_date_lte=end_date
    )
    return sales

@router.get("/sales/user/{user_id}", response_model=List[Sale])
async def list_user_sales(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    status: Optional[SaleStatus] = None,
    payment_status: Optional[PaymentStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get list of sales for a specific user"""
    # Verify user belongs to the same tenant
    user = await crud.user.get(db, id=user_id)
    if not user or user.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=404,
            detail="User not found or not in your tenant"
        )
    
    sales = await crud.sale.get_user_sales(
        db,
        user_id=user_id,
        tenant_id=current_user.tenant_id,
        skip=skip,
        limit=limit,
        status=status,
        payment_status=payment_status,
        start_date=start_date,
        end_date=end_date
    )
    return sales