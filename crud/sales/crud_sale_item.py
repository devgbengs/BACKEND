from typing import List, Optional
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import text

from model.models import SaleItem
from schema.sales import SaleItemCreate, SaleItemUpdate
from ..base import CRUDBase

class CRUDSaleItem(CRUDBase[SaleItem, SaleItemCreate, SaleItemUpdate]):
    async def get_by_sale(
        self,
        db: Session,
        *,
        sale_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[SaleItem]:
        """Get all sale items for a specific sale."""
        statement = (
            select(SaleItem)
            .where(SaleItem.sale_id == sale_id)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def remove_by_sale(
        self,
        db: Session,
        *,
        sale_id: int
    ) -> int:
        """Remove all sale items for a specific sale.
        Returns the number of items deleted."""
        statement = select(SaleItem).where(SaleItem.sale_id == sale_id)
        result = await db.execute(statement)
        items = result.scalars().all()
        
        for item in items:
            await db.delete(item)
        
        await db.commit()
        return len(items)

    async def create_multi(
        self,
        db: Session,
        *,
        sale_id: int,
        items: List[SaleItemCreate]
    ) -> List[SaleItem]:
        """Create multiple sale items for a sale."""
        db_items = []
        for item in items:
            item_data = item.dict()
            item_data['sale_id'] = sale_id
            db_item = SaleItem(**item_data)
            db.add(db_item)
            db_items.append(db_item)
        
        await db.commit()
        for item in db_items:
            await db.refresh(item)
        
        return db_items

# Create singleton instance
sale_item = CRUDSaleItem(SaleItem)