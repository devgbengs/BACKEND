from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlmodel import select, and_, func
from sqlmodel.ext.asyncio.session import AsyncSession
from model.models import StockLevel, Product, Warehouse
from schema.stock_level import StockLevelCreate, StockLevelUpdate
from core.exceptions import NotFoundException, ValidationError
from ..base import CRUDBase

class CRUDStockLevel(CRUDBase[StockLevel, StockLevelCreate, StockLevelUpdate]):
    async def get_product_stock(
        self,
        db: AsyncSession,
        *,
        product_id: int,
        warehouse_id: Optional[int] = None,
        tenant_id: Optional[int] = None
    ) -> List[StockLevel]:
        """Get stock levels for a specific product"""
        query = select(StockLevel).where(StockLevel.product_id == product_id)
        
        if warehouse_id:
            query = query.where(StockLevel.warehouse_id == warehouse_id)
        if tenant_id:
            query = query.where(StockLevel.tenant_id == tenant_id)
            
        result = await db.execute(query)
        return result.scalars().all()

    async def update_stock_level(
        self,
        db: AsyncSession,
        *,
        product_id: int,
        warehouse_id: int,
        quantity_change: int,
        tenant_id: int,
        operation: str
    ) -> StockLevel:
        """Update stock level for a product in a specific warehouse"""
        if operation not in ["add", "remove"]:
            raise ValidationError("Operation must be 'add' or 'remove'")

        # Get current stock level
        query = select(StockLevel).where(
            and_(
                StockLevel.product_id == product_id,
                StockLevel.warehouse_id == warehouse_id,
                StockLevel.tenant_id == tenant_id
            )
        )
        result = await db.execute(query)
        stock_level = result.scalar_one_or_none()

        if not stock_level:
            # Create new stock level if it doesn't exist
            stock_level = StockLevel(
                product_id=product_id,
                warehouse_id=warehouse_id,
                tenant_id=tenant_id,
                quantity=0
            )
            db.add(stock_level)

        # Update quantity
        if operation == "add":
            stock_level.quantity += quantity_change
        else:  # remove
            if stock_level.quantity - quantity_change < 0:
                raise ValidationError(
                    f"Insufficient stock. Available: {stock_level.quantity}"
                )
            stock_level.quantity -= quantity_change

        await db.commit()
        await db.refresh(stock_level)
        return stock_level

    async def get_warehouse_stock(
        self,
        db: AsyncSession,
        *,
        warehouse_id: int,
        tenant_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all stock levels in a warehouse with product details"""
        query = (
            select(
                StockLevel,
                Product.name.label("product_name"),
                Product.sku.label("product_sku")
            )
            .join(Product)
            .where(StockLevel.warehouse_id == warehouse_id)
            .offset(skip)
            .limit(limit)
        )

        if tenant_id:
            query = query.where(StockLevel.tenant_id == tenant_id)

        result = await db.execute(query)
        rows = result.all()
        
        return [
            {
                "id": row.StockLevel.id,
                "product_id": row.StockLevel.product_id,
                "product_name": row.product_name,
                "product_sku": row.product_sku,
                "quantity": row.StockLevel.quantity,
                "warehouse_id": row.StockLevel.warehouse_id
            }
            for row in rows
        ]

    async def get_low_stock_alerts(
        self,
        db: AsyncSession,
        *,
        tenant_id: Optional[int] = None,
        threshold: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get products with low stock levels across warehouses"""
        query = (
            select(
                StockLevel,
                Product,
                Warehouse.name.label("warehouse_name")
            )
            .join(Product)
            .join(Warehouse)
            .where(
                and_(
                    StockLevel.quantity <= Product.min_stock if threshold is None
                    else StockLevel.quantity <= threshold
                )
            )
        )

        if tenant_id:
            query = query.where(StockLevel.tenant_id == tenant_id)

        result = await db.execute(query)
        rows = result.all()

        return [
            {
                "product_id": row.Product.id,
                "product_name": row.Product.name,
                "product_sku": row.Product.sku,
                "warehouse_id": row.StockLevel.warehouse_id,
                "warehouse_name": row.warehouse_name,
                "current_stock": row.StockLevel.quantity,
                "min_stock": row.Product.min_stock,
                "max_stock": row.Product.max_stock
            }
            for row in rows
        ]

    async def get_stock_summary(
        self,
        db: AsyncSession,
        *,
        tenant_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get summary of stock levels across all warehouses"""
        query = (
            select(
                func.count(StockLevel.id).label("total_stock_records"),
                func.sum(StockLevel.quantity).label("total_items"),
                func.count(
                    func.distinct(StockLevel.product_id)
                ).label("unique_products"),
                func.count(
                    func.distinct(StockLevel.warehouse_id)
                ).label("warehouses_with_stock")
            )
        )

        if tenant_id:
            query = query.where(StockLevel.tenant_id == tenant_id)

        result = await db.execute(query)
        row = result.one()

        return {
            "total_stock_records": row.total_stock_records or 0,
            "total_items": row.total_items or 0,
            "unique_products": row.unique_products or 0,
            "warehouses_with_stock": row.warehouses_with_stock or 0
        }

stock_level = CRUDStockLevel(StockLevel)