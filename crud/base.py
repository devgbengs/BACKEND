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
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        date_filters: Optional[Dict[str, Tuple[str, datetime]]] = None,
        status: Optional[str] = None,
        payment_status: Optional[str] = None,
        transaction_type: Optional[str] = None,
        tenant_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        user_id: Optional[int] = None,
        warehouse_id: Optional[int] = None,
        product_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        search_query: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_desc: bool = False
    ) -> List[ModelType]:
        """
        Get multiple records with flexible filtering, sorting and pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Dictionary of field-value pairs to filter by (exact match)
            date_filters: Dictionary of date filters with field and operator ('gte' or 'lte')
                Example: {'created_at': ('gte', datetime_value)}
            sort_by: Field to sort by
            sort_desc: Sort in descending order if True
            tenant_id: Optional tenant ID filter
        """
        conditions = []

        # Apply common filters if the model has the fields
        if tenant_id is not None and hasattr(self.model, "tenant_id"):
            conditions.append(self.model.tenant_id == tenant_id)
        if customer_id is not None and hasattr(self.model, "customer_id"):
            conditions.append(self.model.customer_id == customer_id)
        if user_id is not None and hasattr(self.model, "user_id"):
            conditions.append(self.model.user_id == user_id)
        if warehouse_id is not None and hasattr(self.model, "warehouse_id"):
            conditions.append(self.model.warehouse_id == warehouse_id)
        if product_id is not None and hasattr(self.model, "product_id"):
            conditions.append(self.model.product_id == product_id)
        
        # Status filters
        if status is not None and hasattr(self.model, "status"):
            conditions.append(self.model.status == status)
        if payment_status is not None and hasattr(self.model, "payment_status"):
            conditions.append(self.model.payment_status == payment_status)
        if transaction_type is not None and hasattr(self.model, "transaction_type"):
            conditions.append(self.model.transaction_type == transaction_type)

        # Active status and price range filters
        if is_active is not None and hasattr(self.model, "is_active"):
            conditions.append(self.model.is_active == is_active)
        if min_price is not None and hasattr(self.model, "price"):
            conditions.append(self.model.price >= min_price)
        if max_price is not None and hasattr(self.model, "price"):
            conditions.append(self.model.price <= max_price)

        # Text search in name/description
        if search_query:
            search_conditions = []
            if hasattr(self.model, "name"):
                search_conditions.append(self.model.name.ilike(f"%{search_query}%"))
            if hasattr(self.model, "description"):
                search_conditions.append(self.model.description.ilike(f"%{search_query}%"))
            if search_conditions:
                conditions.append(or_(*search_conditions))

        # Apply exact match filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    if value is not None:  # Only apply filter if value is not None
                        if isinstance(value, list):
                            conditions.append(getattr(self.model, field).in_(value))
                        else:
                            conditions.append(getattr(self.model, field) == value)

        # Apply date range filters
        if date_filters:
            for field, (operator, value) in date_filters.items():
                if hasattr(self.model, field) and value is not None:
                    if operator == "gte":
                        conditions.append(getattr(self.model, field) >= value)
                    elif operator == "lte":
                        conditions.append(getattr(self.model, field) <= value)

        # Build query
        query = select(self.model)
        if conditions:
            query = query.where(and_(*conditions))

        # Apply sorting
        if sort_by and hasattr(self.model, sort_by):
            sort_field = getattr(self.model, sort_by)
            if sort_desc:
                sort_field = sort_field.desc()
            query = query.order_by(sort_field)

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
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
        filters: Optional[Dict[str, Any]] = None,
        date_filters: Optional[Dict[str, Tuple[str, datetime]]] = None,
        status: Optional[str] = None,
        payment_status: Optional[str] = None,
        transaction_type: Optional[str] = None,
        tenant_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        user_id: Optional[int] = None,
        warehouse_id: Optional[int] = None,
        product_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        search_query: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_desc: bool = False
    ) -> Tuple[List[ModelType], int]:
        """
        Get multiple records with comprehensive filtering, sorting, pagination and total count.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Dictionary of field-value pairs to filter by (exact match)
            date_filters: Dictionary of date filters with operator ('gte' or 'lte')
            status: Filter by status field
            payment_status: Filter by payment status
            transaction_type: Filter by transaction type
            tenant_id: Filter by tenant
            customer_id: Filter by customer
            user_id: Filter by user
            warehouse_id: Filter by warehouse
            product_id: Filter by product
            is_active: Filter by active status
            min_price: Minimum price filter
            max_price: Maximum price filter
            search_query: Text search in name/description fields
            sort_by: Field to sort by
            sort_desc: Sort in descending order if True
        """
        conditions = []

        # Apply common filters if the model has the fields
        if tenant_id is not None and hasattr(self.model, "tenant_id"):
            conditions.append(self.model.tenant_id == tenant_id)
        if customer_id is not None and hasattr(self.model, "customer_id"):
            conditions.append(self.model.customer_id == customer_id)
        if user_id is not None and hasattr(self.model, "user_id"):
            conditions.append(self.model.user_id == user_id)
        if warehouse_id is not None and hasattr(self.model, "warehouse_id"):
            conditions.append(self.model.warehouse_id == warehouse_id)
        if product_id is not None and hasattr(self.model, "product_id"):
            conditions.append(self.model.product_id == product_id)
        
        # Status filters
        if status is not None and hasattr(self.model, "status"):
            conditions.append(self.model.status == status)
        if payment_status is not None and hasattr(self.model, "payment_status"):
            conditions.append(self.model.payment_status == payment_status)
        if transaction_type is not None and hasattr(self.model, "transaction_type"):
            conditions.append(self.model.transaction_type == transaction_type)

        # Active status and price range filters
        if is_active is not None and hasattr(self.model, "is_active"):
            conditions.append(self.model.is_active == is_active)
        if min_price is not None and hasattr(self.model, "price"):
            conditions.append(self.model.price >= min_price)
        if max_price is not None and hasattr(self.model, "price"):
            conditions.append(self.model.price <= max_price)

        # Text search in name/description
        if search_query:
            search_conditions = []
            if hasattr(self.model, "name"):
                search_conditions.append(self.model.name.ilike(f"%{search_query}%"))
            if hasattr(self.model, "description"):
                search_conditions.append(self.model.description.ilike(f"%{search_query}%"))
            if search_conditions:
                conditions.append(or_(*search_conditions))

        # Apply exact match filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    if value is not None:
                        if isinstance(value, list):
                            conditions.append(getattr(self.model, field).in_(value))
                        else:
                            conditions.append(getattr(self.model, field) == value)

        # Apply date range filters
        if date_filters:
            for field, (operator, value) in date_filters.items():
                if hasattr(self.model, field) and value is not None:
                    if operator == "gte":
                        conditions.append(getattr(self.model, field) >= value)
                    elif operator == "lte":
                        conditions.append(getattr(self.model, field) <= value)

        # Build base query
        query = select(self.model)
        if conditions:
            query = query.where(and_(*conditions))

        # Apply sorting
        if sort_by and hasattr(self.model, sort_by):
            sort_field = getattr(self.model, sort_by)
            if sort_desc:
                sort_field = sort_field.desc()
            query = query.order_by(sort_field)
        elif hasattr(self.model, "created_at"):  # Default sort by created_at if available
            query = query.order_by(
                self.model.created_at.desc() if sort_desc else self.model.created_at
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query) or 0

        # Apply pagination and get results
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