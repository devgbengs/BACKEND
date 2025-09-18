from typing import List, Optional, Tuple, Dict, Any
import asyncio
from datetime import datetime, timedelta
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, and_, or_, func
from sqlalchemy.exc import IntegrityError, DBAPIError
from model.models import Order, OrderItem, OrderStatus, Product
from schema import OrderCreate, OrderUpdate
from core.exceptions import (
    NotFoundException,
    ValidationError,
    InsufficientStockError,
    BusinessRuleError
)
from ..base import CRUDBase
from ..inventory.crud_product import product as product_crud

class CRUDOrder(CRUDBase[Order, OrderCreate, OrderUpdate]):
    async def get_by_order_number(
        self,
        db: AsyncSession,
        *,
        order_number: str,
        tenant_id: Optional[int] = None
    ) -> Optional[Order]:
        """Get order by order number with optional tenant filter"""
        query = select(self.model).where(self.model.order_number == order_number)
        if tenant_id:
            query = query.where(self.model.tenant_id == tenant_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Order]:
        """Get orders for a specific user with pagination"""
        query = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_status(
        self,
        db: AsyncSession,
        *,
        status: OrderStatus,
        tenant_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Order]:
        """Get orders by status with pagination and optional tenant filter"""
        query = select(self.model).where(self.model.status == status)
        if tenant_id:
            query = query.where(self.model.tenant_id == tenant_id)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_date_range(
        self,
        db: AsyncSession,
        *,
        start_date: datetime,
        end_date: datetime,
        tenant_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Order]:
        """Get orders within a date range with pagination"""
        query = (
            select(self.model)
            .where(self.model.created_at >= start_date)
            .where(self.model.created_at <= end_date)
        )
        if tenant_id:
            query = query.where(self.model.tenant_id == tenant_id)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_orders_with_stats(
        self,
        db: AsyncSession,
        *,
        tenant_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get comprehensive order statistics"""
        query = select(
            func.count(self.model.id).label("total_orders"),
            func.sum(self.model.total_amount).label("total_revenue"),
            func.avg(self.model.total_amount).label("average_order_value")
        )

        if tenant_id:
            query = query.where(self.model.tenant_id == tenant_id)
        if start_date:
            query = query.where(self.model.created_at >= start_date)
        if end_date:
            query = query.where(self.model.created_at <= end_date)

        result = await db.execute(query)
        row = result.first()

        return {
            "total_orders": row[0] or 0,
            "total_revenue": row[1] or 0.0,
            "average_order_value": row[2] or 0.0
        }

    async def process_order(
        self,
        db: AsyncSession,
        *,
        order_id: int,
        new_status: OrderStatus
    ) -> Order:
        """Process order status change with inventory updates"""
        try:
            async with db.begin_nested():
                order = await self.get(db, id=order_id)
                if not order:
                    raise NotFoundException("Order not found")

                # Validate status transition
                valid_transitions = {
                    OrderStatus.PENDING: [OrderStatus.PROCESSING, OrderStatus.CANCELLED],
                    OrderStatus.PROCESSING: [OrderStatus.COMPLETED, OrderStatus.CANCELLED],
                    OrderStatus.COMPLETED: [],
                    OrderStatus.CANCELLED: []
                }

                if new_status not in valid_transitions.get(order.status, []):
                    raise ValidationError(
                        f"Invalid status transition from {order.status} to {new_status}"
                    )

                # Handle inventory for status changes
                if new_status == OrderStatus.PROCESSING:
                    # Reserve inventory
                    items_query = select(OrderItem).where(OrderItem.order_id == order_id)
                    result = await db.execute(items_query)
                    items = result.scalars().all()

                    for item in items:
                        await product_crud.update_stock(
                            db,
                            product_id=item.product_id,
                            quantity_change=item.quantity,
                            operation="remove"
                        )

                elif new_status == OrderStatus.CANCELLED and order.status == OrderStatus.PROCESSING:
                    # Return items to inventory if cancelling a processing order
                    items_query = select(OrderItem).where(OrderItem.order_id == order_id)
                    result = await db.execute(items_query)
                    items = result.scalars().all()

                    for item in items:
                        await product_crud.update_stock(
                            db,
                            product_id=item.product_id,
                            quantity_change=item.quantity,
                            operation="add"
                        )

                # Update order status
                order.status = new_status
                db.add(order)
                await db.commit()
                await db.refresh(order)
                return order

        except Exception as e:
            await db.rollback()
            raise BusinessRuleError(f"Error processing order: {str(e)}")

    async def get_popular_products(
        self,
        db: AsyncSession,
        *,
        tenant_id: Optional[int] = None,
        days: int = 30,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get most popular products based on order frequency"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = (
            select(
                Product.id,
                Product.name,
                Product.sku,
                func.sum(OrderItem.quantity).label("total_quantity"),
                func.count(OrderItem.id).label("order_count"),
                func.sum(OrderItem.total_price).label("total_revenue")
            )
            .join(OrderItem, Product.id == OrderItem.product_id)
            .join(Order, OrderItem.order_id == Order.id)
            .where(Order.created_at >= start_date)
            .group_by(Product.id, Product.name, Product.sku)
            .order_by(func.count(OrderItem.id).desc())
            .limit(limit)
        )

        if tenant_id:
            query = query.where(Product.tenant_id == tenant_id)

        result = await db.execute(query)
        rows = result.all()
        
        return [
            {
                "product_id": row[0],
                "name": row[1],
                "sku": row[2],
                "total_quantity": row[3],
                "order_count": row[4],
                "total_revenue": row[5]
            }
            for row in rows
        ]

order = CRUDOrder(Order)