from typing import List, Optional
from sqlmodel import Session, select
from model.models import Category
from schema import CategoryCreate, CategoryUpdate
from ..base import CRUDBase

class CRUDCategory(CRUDBase[Category, CategoryCreate, CategoryUpdate]):
    def get_by_name(
        self, 
        db: Session, 
        *, 
        name: str,
        tenant_id: Optional[int] = None
    ) -> Optional[Category]:
        query = select(self.model).where(self.model.name == name)
        if tenant_id:
            query = query.where(self.model.tenant_id == tenant_id)
        return db.exec(query).first()

    def get_subcategories(
        self, 
        db: Session, 
        *, 
        parent_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Category]:
        query = (
            select(self.model)
            .where(self.model.parent_id == parent_id)
            .offset(skip)
            .limit(limit)
        )
        return db.exec(query).all()

    def get_root_categories(
        self,
        db: Session,
        *,
        tenant_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Category]:
        query = select(self.model).where(self.model.parent_id.is_(None))
        if tenant_id:
            query = query.where(self.model.tenant_id == tenant_id)
        query = query.offset(skip).limit(limit)
        return db.exec(query).all()

    def get_active_categories(
        self,
        db: Session,
        *,
        tenant_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Category]:
        query = select(self.model).where(self.model.is_active == True)
        if tenant_id:
            query = query.where(self.model.tenant_id == tenant_id)
        query = query.offset(skip).limit(limit)
        return db.exec(query).all()

category = CRUDCategory(Category)