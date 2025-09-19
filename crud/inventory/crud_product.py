from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, and_, or_, func
from model.models import Product, OrderItem, Order
from schema.product import ProductCreate, ProductUpdate
from core.exceptions import ValidationError, InsufficientStockError, NotFoundException
from ..base import CRUDBase

class CRUDProduct(CRUDBase[Product, ProductCreate, ProductUpdate]):
    async def get_by_sku(
        self,
        db: AsyncSession,
        *,
        sku: str,
        tenant_id: Optional[int] = None
    ) -> Optional[Product]:
        query = select(self.model).where(self.model.sku == sku)
        if tenant_id:
            query = query.where(self.model.tenant_id == tenant_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_category(
        self,
        db: AsyncSession,
        *,
        category: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        query = (
            select(self.model)
            .where(self.model.category == category)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_active_products(
        self,
        db: AsyncSession,
        *,
        tenant_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        query = select(self.model).where(self.model.is_active == True)
        if tenant_id:
            query = query.where(self.model.tenant_id == tenant_id)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def search_products(
        self,
        db: AsyncSession,
        *,
        search_term: Optional[str] = None,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        tenant_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Product], int]:
        query = select(self.model)

        if search_term:
            query = query.where(
                or_(
                    self.model.name.contains(search_term),
                    self.model.sku.contains(search_term),
                    self.model.description.contains(search_term)
                )
            )

        if tenant_id:
            query = query.where(self.model.tenant_id == tenant_id)
        
        if category:
            query = query.where(self.model.category == category)
        
        if min_price is not None:
            query = query.where(self.model.price >= min_price)
        
        if max_price is not None:
            query = query.where(self.model.price <= max_price)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query) or 0

        # Get paginated results
        result = await db.execute(query.offset(skip).limit(limit))
        items = result.scalars().all()

        return items, total

    async def update_stock(
        self,
        db: AsyncSession,
        *,
        product_id: int,
        quantity_change: int,
        operation: str
    ) -> Product:
        """Update product stock with validation and tracking"""
        if operation not in ["add", "remove"]:
            raise ValidationError("Operation must be 'add' or 'remove'")

        query = select(self.model).where(self.model.id == product_id)
        result = await db.execute(query)
        product = result.scalar_one_or_none()

        if not product:
            raise NotFoundException("Product not found")

        if operation == "remove" and product.quantity - quantity_change < 0:
            raise InsufficientStockError(
                f"Insufficient stock. Available: {product.quantity}"
            )

        new_quantity = (
            product.quantity + quantity_change if operation == "add"
            else product.quantity - quantity_change
        )

        # Update product
        update_data = {"quantity": new_quantity}
        return await super().update(db, db_obj=product, obj_in=update_data)

    async def get_low_stock_products(
        self,
        db: AsyncSession,
        *,
        threshold: int = 10,
        tenant_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        """Get products with stock below threshold"""
        query = (
            select(self.model)
            .where(self.model.quantity <= threshold)
            .where(self.model.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        
        if tenant_id:
            query = query.where(self.model.tenant_id == tenant_id)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def get_product_sales_stats(
        self,
        db: AsyncSession,
        *,
        product_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get sales statistics for a product"""
        query = (
            select(
                func.count(OrderItem.id).label("total_orders"),
                func.sum(OrderItem.quantity).label("total_quantity"),
                func.sum(OrderItem.total_price).label("total_revenue")
            )
            .join(Order)
            .where(OrderItem.product_id == product_id)
        )

        if start_date:
            query = query.where(Order.created_at >= start_date)
        if end_date:
            query = query.where(Order.created_at <= end_date)

        result = await db.execute(query)
        row = result.first()

        return {
            "total_orders": row[0] or 0,
            "total_quantity": row[1] or 0,
            "total_revenue": row[2] or 0.0
        }

    async def get_category_products_count(
        self,
        db: AsyncSession,
        *,
        tenant_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get product count by category"""
        query = (
            select(
                self.model.category,
                func.count(self.model.id).label("product_count")
            )
            .group_by(self.model.category)
        )

        if tenant_id:
            query = query.where(self.model.tenant_id == tenant_id)

        result = await db.execute(query)
        rows = result.all()
        return [
            {"category": row[0], "count": row[1]}
            for row in rows
        ]

product = CRUDProduct(Product)