from typing import List, Optional, Dict, Any, Union
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from datetime import datetime

from model.models import User, Role
from schema.user import UserCreate, UserUpdate
from ..base import CRUDBase
from core.security import get_password_hash, verify_password


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    async def get(self, db: Session, id: int) -> Optional[User]:
        """Get a user by ID with roles preloaded"""
        statement = select(User).options(
            selectinload(User.roles)
        ).where(User.id == id)
        result = await db.execute(statement)
        return result.unique().scalar_one_or_none()

    async def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Get a user by email with roles preloaded"""
        statement = select(User).options(
            selectinload(User.roles)
        ).where(User.email == email)
        result = await db.execute(statement)
        return result.unique().scalar_one_or_none()

    async def create(self, db: Session, *, obj_in: Union[UserCreate, Dict[str, Any]]) -> User:
        """Create a new user with proper password hashing"""
        if isinstance(obj_in, dict):
            create_data = obj_in
        else:
            create_data = obj_in.dict(exclude_unset=True)
            
        if not create_data.get("tenant_id"):
            raise ValueError("tenant_id is required when creating a user")
        
        if not create_data.get("password"):
            raise ValueError("password is required when creating a user")
            
        try:
            hashed_password = get_password_hash(create_data["password"])
            del create_data["password"]
            
            db_obj = User(
                email=create_data["email"],
                user_name=create_data.get("user_name"),
                full_name=create_data["full_name"],
                hashed_password=hashed_password,
                phone_number=create_data.get("phone_number"),
                role_names=create_data.get("role_names", []),
                permissions=create_data.get("permissions", []),
                tenant_id=create_data["tenant_id"],
                is_active=create_data.get("is_active", True),
                is_superuser=create_data.get("is_superuser", False),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
            
        except Exception as e:
            await db.rollback()
            raise ValueError(f"Error creating user: {str(e)}")

    async def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password"""
        user = await self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        """Check if a user is active"""
        return user.is_active

    async def get_multi_by_tenant(
        self, 
        db: Session, 
        *, 
        tenant_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        """Get multiple users for a specific tenant with pagination"""
        statement = (
            select(User)
            .options(selectinload(User.roles))
            .where(User.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def update(
        self,
        db: Session,
        *,
        db_obj: User,
        obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        """Update a user with proper handling of password hashing"""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password

        update_data["updated_at"] = datetime.utcnow()
        return await super().update(db, db_obj=db_obj, obj_in=update_data)


# Create singleton instance
user = CRUDUser(User)

