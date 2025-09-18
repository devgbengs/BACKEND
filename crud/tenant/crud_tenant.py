from typing import List, Optional
from sqlmodel import Session, select
from model.models import Tenant
from schema import TenantCreate, TenantUpdate
from ..base import CRUDBase

class CRUDTenant(CRUDBase[Tenant, TenantCreate, TenantUpdate]):
    def get_by_domain(self, db: Session, *, domain: str) -> Optional[Tenant]:
        query = select(self.model).where(self.model.domain == domain)
        return db.exec(query).first()

    def get_active_tenants(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Tenant]:
        query = (
            select(self.model)
            .where(self.model.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return db.exec(query).all()

tenant = CRUDTenant(Tenant)