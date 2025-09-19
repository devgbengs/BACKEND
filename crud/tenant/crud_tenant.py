from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from datetime import datetime

from model.models import Tenant
from schema.tenant import TenantCreate, TenantUpdate
from ..base import CRUDBase


class CRUDTenant(CRUDBase[Tenant, TenantCreate, TenantUpdate]):
    async def get_by_domain(self, db: Session, *, domain: str) -> Optional[Tenant]:
        """Get a tenant by domain name"""
        statement = select(self.model).where(self.model.domain == domain)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_active_tenants(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Tenant]:
        """Get all active tenants with pagination"""
        statement = (
            select(self.model)
            .where(self.model.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def create(self, db: Session, *, obj_in: TenantCreate) -> Tenant:
        """Create a new tenant"""
        db_obj = Tenant(
            name=obj_in.name,
            domain=obj_in.domain,
            contact_email=obj_in.contact_email,
            description=obj_in.description,
            is_active=obj_in.is_active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_name(self, db: Session, *, name: str) -> Optional[Tenant]:
        """Get a tenant by name"""
        statement = select(self.model).where(self.model.name == name)
        result = await db.execute(statement)
        return result.scalar_one_or_none()


# Create singleton instance
tenant = CRUDTenant(Tenant)