from typing import List, Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from model.models import Warehouse
from schema.warehouse import WarehouseCreate, WarehouseUpdate
from core.exceptions import NotFoundException
from ..base import CRUDBase

class CRUDWarehouse(CRUDBase[Warehouse, WarehouseCreate, WarehouseUpdate]):
    async def get_by_code(
        self,
        db: AsyncSession,
        *,
        code: str,
        tenant_id: Optional[int] = None
    ) -> Optional[Warehouse]:
        """Get warehouse by its unique code"""
        query = select(self.model).where(self.model.code == code)
        if tenant_id:
            query = query.where(self.model.tenant_id == tenant_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_warehouses(
        self,
        db: AsyncSession,
        *,
        tenant_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Warehouse]:
        """Get all active warehouses"""
        query = select(self.model).where(self.model.is_active == True)
        if tenant_id:
            query = query.where(self.model.tenant_id == tenant_id)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

warehouse = CRUDWarehouse(Warehouse)