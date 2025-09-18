from typing import List, Optional
from sqlmodel import Session, select
from model.models import User
from schema import UserCreate, UserUpdate
from ..base import CRUDBase
from core.security import get_password_hash, verify_password

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        query = select(self.model).where(self.model.email == email)
        return db.exec(query).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        db_obj = User(
            email=obj_in.email,
            user_name=obj_in.user_name,
            full_name=obj_in.full_name,
            hashed_password=get_password_hash(obj_in.password) if obj_in.password else None,
            phone_number=obj_in.phone_number,
            role_names=obj_in.role_names,
            permissions=obj_in.permissions,
            tenant_id=obj_in.tenant_id,
            is_active=obj_in.is_active
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        return user.is_active

    def get_by_tenant(self, db: Session, *, tenant_id: int, skip: int = 0, limit: int = 100) -> List[User]:
        query = (
            select(self.model)
            .where(self.model.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
        )
        return db.exec(query).all()

user = CRUDUser(User)