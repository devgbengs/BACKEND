from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlmodel import select, and_, or_, func
from model.models import StockLevel
from sqlmodel.ext.asyncio.session import AsyncSession
from model.models import (
    InventoryTransaction, Product, InventoryTransactionType, StockLevel
)
from schema.inventory_transaction import InventoryTransactionCreate, InventoryTransactionUpdate
from core.exceptions import ValidationError
from ..base import CRUDBase

class CRUDInventoryTransaction(CRUDBase[InventoryTransaction, InventoryTransactionCreate, InventoryTransactionUpdate]):
    async def create_transaction(
        self,
        db: AsyncSession,
        *,
        tenant_id: int,
        product_id: int,
        warehouse_id: int,
        transaction_type: str,
        quantity: int,
        reference_number: Optional[str] = None,
        notes: Optional[str] = None
    ) -> InventoryTransaction:
        """Create a new inventory transaction"""
        try:
            # Get current stock level
            stock_query = select(StockLevel).where(
                and_(
                    StockLevel.product_id == product_id,
                    StockLevel.warehouse_id == warehouse_id,
                    StockLevel.tenant_id == tenant_id
                )
            )
            result = await db.execute(stock_query)
            stock = result.scalar_one_or_none()
            
            # Initialize stock level if it doesn't exist
            if not stock:
                stock = StockLevel(
                    product_id=product_id,
                    warehouse_id=warehouse_id,
                    tenant_id=tenant_id,
                    quantity=0
                )
                db.add(stock)
                await db.flush()  # This will assign an ID to the stock level
            
            previous_quantity = stock.quantity
        
            # Calculate new quantity based on transaction type
            if transaction_type == "STOCK_IN":
                new_quantity = previous_quantity + quantity
            elif transaction_type == "STOCK_OUT":
                if previous_quantity < quantity:
                    raise ValidationError(f"Insufficient stock. Available: {previous_quantity}")
                new_quantity = previous_quantity - quantity
            elif transaction_type == "ADJUSTMENT":
                if quantity < 0:
                    raise ValidationError("Adjustment quantity cannot be negative")
                new_quantity = quantity
            elif transaction_type == "TRANSFER":
                if previous_quantity < quantity:
                    raise ValidationError(f"Insufficient stock for transfer. Available: {previous_quantity}")
                new_quantity = previous_quantity - quantity
            else:
                raise ValidationError(f"Invalid transaction type: {transaction_type}")

            # Validate final quantity
            if new_quantity < 0:
                raise ValidationError("Operation would result in negative stock")

            # Create or update stock level
            if not stock:
                stock = StockLevel(
                    product_id=product_id,
                    warehouse_id=warehouse_id,
                    tenant_id=tenant_id,
                    quantity=new_quantity
                )
                db.add(stock)
            else:
                stock.quantity = new_quantity
                db.add(stock)

            # Create transaction record
            transaction = InventoryTransaction(
                tenant_id=tenant_id,
                product_id=product_id,
                warehouse_id=warehouse_id,
                transaction_type=transaction_type,
                quantity=quantity,
                previous_quantity=previous_quantity,
                new_quantity=new_quantity,
                reference_number=reference_number,
                notes=notes,
                created_at=datetime.utcnow(),
                transaction_date=datetime.utcnow()
            )

            db.add(transaction)
            await db.commit()
            await db.refresh(transaction)
            return transaction

        except ValidationError as e:
            await db.rollback()
            raise e
        except Exception as e:
            await db.rollback()
            raise ValidationError(f"Error creating transaction: {str(e)}")

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
                #"reference_id": row.InventoryTransaction.reference_id,
                #"reference_type": row.InventoryTransaction.reference_type,
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
                InventoryTransaction.transaction_date >= start_date
            )
        if end_date:
            base_query = base_query.where(
                InventoryTransaction.transaction_date <= end_date
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

        result = await db.execute(type_query)
        type_rows = result.all()

        # Initialize counters
        total_stock_in = 0
        total_stock_out = 0
        total_adjustments = 0
        total_transfers = 0
        transaction_counts = {
            "stock_in": 0,
            "stock_out": 0,
            "adjustment": 0,
            "transfer": 0
        }
        quantity_by_type = {
            "stock_in": 0,
            "stock_out": 0,
            "adjustment": 0,
            "transfer": 0
        }

        # Process results
        for row in type_rows:
            t_type = row.transaction_type
            count = row.count
            quantity = row.total_quantity or 0

            transaction_counts[t_type] = count
            quantity_by_type[t_type] = quantity

            if t_type == "stock_in":
                total_stock_in = quantity
            elif t_type == "stock_out":
                total_stock_out = quantity
            elif t_type == "adjustment":
                total_adjustments = quantity
            elif t_type == "transfer":
                total_transfers = quantity

        return {
            "total_transactions": sum(transaction_counts.values()),
            "total_stock_in": total_stock_in,
            "total_stock_out": total_stock_out,
            "total_adjustments": total_adjustments,
            "total_transfers": total_transfers,
            "net_quantity_change": total_stock_in - total_stock_out + total_adjustments,
            "transaction_counts": transaction_counts,
            "quantity_by_type": quantity_by_type
        }
            
        
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
    ) -> List[InventoryTransaction]:
        """Get most recent inventory transactions"""
        query = (
            select(InventoryTransaction)
            .order_by(InventoryTransaction.created_at.desc())
            .limit(limit)
        )

        if tenant_id:
            query = query.where(InventoryTransaction.tenant_id == tenant_id)

        result = await db.execute(query)
        return [row for row in result.scalars().all()]

inventory_transaction = CRUDInventoryTransaction(InventoryTransaction)