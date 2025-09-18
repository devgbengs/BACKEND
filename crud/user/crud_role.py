from typing import List, Optional
from sqlmodel import Session, select
from model.models import Role
from schema import RoleCreate, RoleUpdate
from ..base import CRUDBase

class CRUDRole(CRUDBase[Role, RoleCreate, RoleUpdate]):
    def get_by_name(self, db: Session, *, name: str, tenant_id: Optional[int] = None) -> Optional[Role]:
        query = select(self.model).where(self.model.name == name)
        if tenant_id:
            query = query.where(self.model.tenant_id == tenant_id)
        return db.exec(query).first()

    def get_by_tenant(self, db: Session, *, tenant_id: int, skip: int = 0, limit: int = 100) -> List[Role]:
        query = (
            select(self.model)
            .where(self.model.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
        )
        return db.exec(query).all()

    def get_default_roles(self, db: Session) -> List[Role]:
        """Get system-wide default roles (non-tenant-specific)"""
        query = select(self.model).where(self.model.tenant_id.is_(None))
        return db.exec(query).all()

role = CRUDRole(Role)