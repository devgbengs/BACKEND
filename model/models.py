from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from sqlalchemy import JSON, Column
from enum import Enum
from pydantic import EmailStr
from model.user_role import UserRole

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class Tenant(SQLModel, table=True):
    __tablename__ = "tenants"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    plan: Optional[str] = Field(default="free", max_length=50)
    domain: Optional[str] = Field(default=None, index=True)
    contact_email: EmailStr
    is_active: bool = Field(default=True)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    users: List["User"] = Relationship(back_populates="tenant")
    roles: List["Role"] = Relationship(back_populates="tenant")
    products: List["Product"] = Relationship(back_populates="tenant")
    orders: List["Order"] = Relationship(back_populates="tenant")
    warehouses: List["Warehouse"] = Relationship(back_populates="tenant")

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    user_name: Optional[str] = Field(default=None, max_length=80)
    email: str = Field(index=True, unique=True)
    phone_number: Optional[str] = Field(default=None, max_length=30)
    full_name: str = Field()
    hashed_password: str = Field()
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    role_names: List[str] = Field(default=[], sa_column=Column(JSON))
    permissions: List[str] = Field(default=[], sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Authentication and Security
    password_changed_at: Optional[datetime] = Field(default=None)
    password_reset_token: Optional[str] = Field(default=None)
    password_reset_expires: Optional[datetime] = Field(default=None)
    last_login: Optional[datetime] = Field(default=None)
    failed_login_attempts: Optional[int] = Field(default=0)
    locked_until: Optional[datetime] = Field(default=None)
    require_password_change: Optional[bool] = Field(default=False)
    mfa_enabled: Optional[bool] = Field(default=False)
    mfa_secret: Optional[str] = Field(default=None)

    # Relationships
    tenant: Optional["Tenant"] = Relationship(back_populates="users")
    roles: List["Role"] = Relationship(
        back_populates="users",
        link_model=UserRole,
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "User.id == UserRole.user_id",
            "secondaryjoin": "UserRole.role_id == Role.id"
        }
    )
    tokens: Optional[List["Token"]] = Relationship(back_populates="user")
    sessions: Optional[List["Session"]] = Relationship(back_populates="user")
    orders: List["Order"] = Relationship(back_populates="user")

class Role(SQLModel, table=True):
    __tablename__ = "roles"
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: Optional[int] = Field(default=None, foreign_key="tenants.id")
    name: Optional[str] = Field(default=None, max_length=80)
    description: Optional[str] = Field(default=None)
    permissions: List[str] = Field(default=[], sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    tenant: Optional["Tenant"] = Relationship(back_populates="roles")
    users: List[User] = Relationship(
        back_populates="roles",
        link_model=UserRole,
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "Role.id == UserRole.role_id",
            "secondaryjoin": "UserRole.user_id == User.id"
        }
    )

class Token(SQLModel, table=True):
    __tablename__ = "tokens"
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    token_type: Optional[str] = Field(default=None)
    expires_at: Optional[datetime] = Field(default=None)
    revoked: Optional[bool] = Field(default=False)
    revoked_at: Optional[datetime] = Field(default=None)
    revocation_reason: Optional[str] = Field(default=None)

    # Relationships
    user: Optional[User] = Relationship(back_populates="tokens")

class Session(SQLModel, table=True):
    __tablename__ = "sessions"
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    last_active: Optional[datetime] = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(default=None)
    ip_address: Optional[str] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)
    device_info: Dict[str, Any] = Field(default=None, sa_column=Column(JSON))
    is_active: Optional[bool] = Field(default=True)

    # Relationships
    user: Optional[User] = Relationship(back_populates="sessions")

class Product(SQLModel, table=True):
    __tablename__ = "products"
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    name: str = Field(index=True)
    sku: str = Field(unique=True, index=True)
    description: Optional[str] = None
    price: float = Field(default=0.0)
    category: str = Field(index=True)
    quantity: int = Field(default=0)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    tenant: Optional[Tenant] = Relationship(back_populates="products")
    stock_levels: List["StockLevel"] = Relationship(back_populates="product")

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class Order(SQLModel, table=True):
    __tablename__ = "orders"
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    order_number: str = Field(unique=True, index=True)
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    total_amount: float = Field(default=0.0)
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    tenant: Optional[Tenant] = Relationship(back_populates="orders")
    user: Optional[User] = Relationship(back_populates="orders")
    items: List["OrderItem"] = Relationship(back_populates="order")

class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", index=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    quantity: int = Field(default=1)
    unit_price: float = Field(default=0.0)
    total_price: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    order: Order = Relationship(back_populates="items")
    product: Product = Relationship()

class Warehouse(SQLModel, table=True):
    __tablename__ = "warehouses"
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    name: str = Field(index=True)
    code: str = Field(unique=True, index=True)
    location: Optional[str] = None
    address: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    tenant: Optional[Tenant] = Relationship(back_populates="warehouses")
    stock_levels: List["StockLevel"] = Relationship(back_populates="warehouse")

class StockLevel(SQLModel, table=True):
    __tablename__ = "stock_levels"
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    warehouse_id: int = Field(foreign_key="warehouses.id", index=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    quantity: int = Field(default=0)
    minimum_level: Optional[int] = Field(default=0)
    maximum_level: Optional[int] = Field(default=None)
    reorder_point: Optional[int] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    warehouse: Warehouse = Relationship(back_populates="stock_levels")
    product: Product = Relationship(back_populates="stock_levels")
    tenant: Optional[Tenant] = Relationship()

class InventoryTransactionType(str, Enum):
    PURCHASE = "purchase"
    SALE = "sale"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"
    RETURN = "return"

class InventoryTransaction(SQLModel, table=True):
    __tablename__ = "inventory_transactions"
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    warehouse_id: int = Field(foreign_key="warehouses.id", index=True)
    reference_number: str = Field(unique=True, index=True)
    transaction_type: InventoryTransactionType
    quantity: int
    previous_quantity: int
    new_quantity: int
    unit_price: Optional[float] = None
    transaction_date: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    warehouse: Optional[Warehouse] = Relationship()
    product: Optional[Product] = Relationship()
    tenant: Optional[Tenant] = Relationship()
