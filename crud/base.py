from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, Tuple
from datetime import datetime
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlmodel import SQLModel, select, func, and_, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import SelectOfScalar
from sqlalchemy.future import select as async_select
from core.exceptions import NotFoundException, ValidationError

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        **Parameters**
        * `model`: A SQLModel class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        Get a single record by ID.
        """
        statement = select(self.model).where(self.model.id == id)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Get multiple records with pagination.
        """
        statement = select(self.model).offset(skip).limit(limit)
        result = await db.execute(statement)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record.
        """
        obj_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_data)  # type: ignore
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update a record.
        """
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: Any) -> ModelType:
        """
        Delete a record.
        """
        statement = select(self.model).where(self.model.id == id)
        result = await db.execute(statement)
        obj = result.scalar_one_or_none()
        if not obj:
            raise NotFoundException(f"{self.model.__name__} not found")
        await db.delete(obj)
        await db.commit()
        return obj

    async def exists(self, db: AsyncSession, *, id: Any) -> bool:
        """
        Check if a record exists.
        """
        statement = select(self.model.id).where(self.model.id == id)
        result = await db.execute(statement)
        return result.scalar_one_or_none() is not None

    async def count(self, db: AsyncSession, *, tenant_id: Optional[int] = None) -> int:
        """
        Count total records, optionally filtered by tenant.
        """
        statement = select(func.count(self.model.id))
        if tenant_id is not None:
            statement = statement.where(self.model.tenant_id == tenant_id)
        result = await db.execute(statement)
        return result.scalar_one() or 0

    async def get_multi_paginated(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        tenant_id: Optional[int] = None
    ) -> Tuple[List[ModelType], int]:
        """
        Get multiple records with pagination and total count.
        """
        query = select(self.model)
        if tenant_id is not None:
            query = query.where(self.model.tenant_id == tenant_id)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query) or 0
        
        # Get paginated results
        result = await db.execute(query.offset(skip).limit(limit))
        items = result.scalars().all()
        
        return items, total

    async def bulk_create(self, db: AsyncSession, *, objs_in: List[CreateSchemaType]) -> List[ModelType]:
        """
        Create multiple records in bulk.
        """
        obj_data = [jsonable_encoder(obj) for obj in objs_in]
        db_objs = [self.model(**data) for data in obj_data]
        db.add_all(db_objs)
        await db.commit()
        for obj in db_objs:
            await db.refresh(obj)
        return db_objs

    async def soft_delete(self, db: AsyncSession, *, id: Any) -> ModelType:
        """
        Soft delete a record by setting is_active to False.
        """
        statement = select(self.model).where(self.model.id == id)
        result = await db.execute(statement)
        obj = result.scalar_one_or_none()
        if not obj:
            raise NotFoundException(f"{self.model.__name__} not found")
        setattr(obj, "is_active", False)
        setattr(obj, "updated_at", datetime.utcnow())
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def get_by_tenant(
        self, db: AsyncSession, *, tenant_id: int, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Get records for a specific tenant with pagination.
        """
        statement = (
            select(self.model)
            .where(self.model.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()