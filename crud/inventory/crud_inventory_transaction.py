from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlmodel import select, and_, or_, func
from sqlmodel.ext.asyncio.session import AsyncSession
from model.models import InventoryTransaction, Product
from core.exceptions import ValidationError
from ..base import CRUDBase

class CRUDInventoryTransaction(CRUDBase[InventoryTransaction]):
    async def create_transaction(
        self,
        db: AsyncSession,
        *,
        tenant_id: int,
        product_id: int,
        transaction_type: str,
        quantity: int,
        reference_id: Optional[str] = None,
        reference_type: Optional[str] = None,
        notes: Optional[str] = None
    ) -> InventoryTransaction:
        """Create a new inventory transaction"""
        if transaction_type not in ["in", "out", "adjustment"]:
            raise ValidationError(
                "Transaction type must be 'in', 'out', or 'adjustment'"
            )

        transaction = InventoryTransaction(
            tenant_id=tenant_id,
            product_id=product_id,
            transaction_type=transaction_type,
            quantity=quantity,
            reference_id=reference_id,
            reference_type=reference_type,
            notes=notes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        return transaction

    async def get_product_transactions(
        self,
        db: AsyncSession,
        *,
        product_id: int,
        tenant_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get transactions for a specific product"""
        query = (
            select(
                InventoryTransaction,
                Product.name.label("product_name"),
                Product.sku.label("product_sku")
            )
            .join(Product)
            .where(InventoryTransaction.product_id == product_id)
        )

        if tenant_id:
            query = query.where(InventoryTransaction.tenant_id == tenant_id)
        if start_date:
            query = query.where(InventoryTransaction.created_at >= start_date)
        if end_date:
            query = query.where(InventoryTransaction.created_at <= end_date)
        if transaction_type:
            query = query.where(
                InventoryTransaction.transaction_type == transaction_type
            )

        query = query.order_by(
            InventoryTransaction.created_at.desc()
        ).offset(skip).limit(limit)

        result = await db.execute(query)
        rows = result.all()

        return [
            {
                "id": row.InventoryTransaction.id,
                "product_id": row.InventoryTransaction.product_id,
                "product_name": row.product_name,
                "product_sku": row.product_sku,
                "transaction_type": row.InventoryTransaction.transaction_type,
                "quantity": row.InventoryTransaction.quantity,
                "reference_id": row.InventoryTransaction.reference_id,
                "reference_type": row.InventoryTransaction.reference_type,
                "notes": row.InventoryTransaction.notes,
                "created_at": row.InventoryTransaction.created_at
            }
            for row in rows
        ]

    async def get_transaction_summary(
        self,
        db: AsyncSession,
        *,
        tenant_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get summary of inventory transactions"""
        base_query = select(InventoryTransaction)
        
        if tenant_id:
            base_query = base_query.where(
                InventoryTransaction.tenant_id == tenant_id
            )
        if start_date:
            base_query = base_query.where(
                InventoryTransaction.created_at >= start_date
            )
        if end_date:
            base_query = base_query.where(
                InventoryTransaction.created_at <= end_date
            )

        # Get total transactions by type
        type_query = (
            select(
                InventoryTransaction.transaction_type,
                func.count().label("count"),
                func.sum(InventoryTransaction.quantity).label("total_quantity")
            )
            .select_from(base_query.subquery())
            .group_by(InventoryTransaction.transaction_type)
        )
        
        type_result = await db.execute(type_query)
        type_rows = type_result.all()
        
        summary = {
            "total_transactions": sum(row.count for row in type_rows),
            "transactions_by_type": {
                row.transaction_type: {
                    "count": row.count,
                    "total_quantity": row.total_quantity or 0
                }
                for row in type_rows
            }
        }

        return summary

    async def get_recent_transactions(
        self,
        db: AsyncSession,
        *,
        tenant_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get most recent inventory transactions"""
        query = (
            select(
                InventoryTransaction,
                Product.name.label("product_name"),
                Product.sku.label("product_sku")
            )
            .join(Product)
            .order_by(InventoryTransaction.created_at.desc())
            .limit(limit)
        )

        if tenant_id:
            query = query.where(InventoryTransaction.tenant_id == tenant_id)

        result = await db.execute(query)
        rows = result.all()

        return [
            {
                "id": row.InventoryTransaction.id,
                "product_name": row.product_name,
                "product_sku": row.product_sku,
                "transaction_type": row.InventoryTransaction.transaction_type,
                "quantity": row.InventoryTransaction.quantity,
                "created_at": row.InventoryTransaction.created_at
            }
            for row in rows
        ]

inventory_transaction = CRUDInventoryTransaction(InventoryTransaction)