from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

class User(SQLModel, table=True):
    # Basic Information
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: Optional[int] = Field(default=None, foreign_key="tenants.id")
    user_name: Optional[str] = Field(default=None, max_length=80)

    email: Optional[str] = Field(default=None, max_length=120)
    phone_number: Optional[str] = Field(default=None, max_length=30)
    full_name: Optional[str] = Field(default=None, max_length=100)
    
    # Relationships
    tenant: Optional["Tenant"] = Relationship(back_populates="users")
    roles: Optional[List["Role"]] = Relationship(
        back_populates="users",
        sa_relationship_kwargs={
            "secondary": "user_roles",
            "cascade": "all, delete",
            "lazy": "joined"
        }
    )
    tokens: Optional[List["Token"]] = Relationship(back_populates="user")
    sessions: Optional[List["Session"]] = Relationship(back_populates="user")
    security_logs: Optional[List["SecurityLog"]] = Relationship(back_populates="user")
    audit_logs: Optional[List["AuditLog"]] = Relationship(back_populates="user")
    
    # Authentication
    hashed_password: Optional[str] = Field(default=None)
    password_changed_at: Optional[datetime] = Field(default=None)
    password_reset_token: Optional[str] = Field(default=None)
    password_reset_expires: Optional[datetime] = Field(default=None)
    
    # Access Control
    status: Optional[str] = Field(default="pending", max_length=20)
    is_active: Optional[bool] = Field(default=True)
    role_names: Optional[List[str]] = Field(default=[])
    permissions: Optional[List[str]] = Field(default=[])
    
    # Session and Security Management
    last_login: Optional[datetime] = Field(default=None)
    failed_login_attempts: Optional[int] = Field(default=0)
    locked_until: Optional[datetime] = Field(default=None)
    last_password_change: Optional[datetime] = Field(default=None)
    require_password_change: Optional[bool] = Field(default=False)
    mfa_enabled: Optional[bool] = Field(default=False)
    mfa_secret: Optional[str] = Field(default=None)
    security_questions: Optional[Dict[str, str]] = Field(default={})

class Tenant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(default=None, max_length=150)
    plan: Optional[str] = Field(default="free", max_length=50)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # Relationships
    users: Optional[List["User"]] = Relationship(back_populates="tenant")
    roles: Optional[List["Role"]] = Relationship(back_populates="tenant")
    products: Optional[List["Product"]] = Relationship(back_populates="tenant")
    warehouses: Optional[List["Warehouse"]] = Relationship(back_populates="tenant")
    stock_levels: Optional[List["StockLevel"]] = Relationship(back_populates="tenant")
    orders: Optional[List["Order"]] = Relationship(back_populates="tenant")
    purchase_orders: Optional[List["PurchaseOrder"]] = Relationship(back_populates="tenant")
    sales_orders: Optional[List["SalesOrder"]] = Relationship(back_populates="tenant")
    suppliers: Optional[List["Supplier"]] = Relationship(back_populates="tenant")
    inventory_transactions: Optional[List["InventoryTransaction"]] = Relationship(back_populates="tenant")
    audit_logs: Optional[List["AuditLog"]] = Relationship(back_populates="tenant")
    
class Role(SQLModel, table=True):
    # Basic Information
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: Optional[int] = Field(default=None, foreign_key="tenants.id")
    name: Optional[str] = Field(default=None, max_length=80)
    description: Optional[str] = Field(default=None)
    
    # Permissions
    permissions: Optional[List[str]] = Field(default=[])

    # Timestamps
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # Relationships
    tenant: Optional["Tenant"] = Relationship(back_populates="roles")
    users: Optional[List["User"]] = Relationship(
        sa_relationship_kwargs={
            "secondary": "user_roles",
            "back_populates": "roles",
            "cascade": "all, delete",
            "lazy": "joined"
        }
    )

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: Optional[int] = Field(default=None, foreign_key="tenants.id")
    name: Optional[str] = Field(default=None, max_length=255)
    sku: Optional[str] = Field(default=None, max_length=50, unique=True)
    description: Optional[str] = Field(default=None)
    category: Optional[str] = Field(default=None, max_length=100)
    supplier: Optional[str] = Field(default=None, max_length=100)
    price: Optional[float] = Field(default=None)
    cost: Optional[float] = Field(default=None)
    stock: Optional[int] = Field(default=0)
    min_stock: Optional[int] = Field(default=None)
    max_stock: Optional[int] = Field(default=None)
    weight: Optional[float] = Field(default=None)
    dimensions: Optional[str] = Field(default=None, max_length=50)
    barcode: Optional[str] = Field(default=None, max_length=100)
    tags: Optional[List[str]] = Field(default=[])
    status: Optional[str] = Field(default="In Stock", max_length=20)
    is_active: Optional[bool] = Field(default=True)
    last_updated: Optional[datetime] = Field(default_factory=datetime.utcnow)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # Relationships
    tenant: Optional["Tenant"] = Relationship(back_populates="products")
    inventory_transactions: Optional[List["InventoryTransaction"]] = Relationship(back_populates="product")
    order_items: Optional[List["OrderItem"]] = Relationship(back_populates="product")
    purchase_order_items: Optional[List["PurchaseOrderItem"]] = Relationship(back_populates="product")
    stock_levels: Optional[List["StockLevel"]] = Relationship(back_populates="product")
 
class Warehouse(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: Optional[int] = Field(default=None, foreign_key="tenants.id")
    name: Optional[str] = Field(default=None, max_length=100)
    code: Optional[str] = Field(default=None, max_length=20)
    location: Optional[str] = Field(default=None, max_length=200)
    status: Optional[str] = Field(default="active", max_length=20)
    is_active: Optional[bool] = Field(default=True)
    
  
    # Contact Information
    contact_name: Optional[str] = Field(default=None, max_length=100)
    contact_email: Optional[str] = Field(default=None, max_length=120)
    contact_phone: Optional[str] = Field(default=None, max_length=30)
    
    # Additional Details
    address: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    capacity: Optional[int] = Field(default=None)
    warehouse_metadata: Optional[Dict[str, Any]] = Field(default={})
    
    # Timestamps
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # Relationships
    tenant: Optional["Tenant"] = Relationship(back_populates="warehouses")
    stock_levels: Optional[List["StockLevel"]] = Relationship(back_populates="warehouse")
    
class InventoryTransaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: Optional[int] = Field(default=None, foreign_key="tenants.id")
    product_id: Optional[int] = Field(default=None, foreign_key="products.id")
    transaction_type: Optional[str] = Field(default=None, max_length=50)  # in, out, adjustment
    quantity: Optional[int] = Field(default=None)
    reference_id: Optional[str] = Field(default=None, max_length=100)
    reference_type: Optional[str] = Field(default=None, max_length=50)
    notes: Optional[str] = Field(default=None, max_length=255)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # Relationships
    tenant: Optional["Tenant"] = Relationship(back_populates="inventory_transactions")
    product: Optional["Product"] = Relationship(back_populates="inventory_transactions")

class PurchaseOrder(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: Optional[int] = Field(default=None, foreign_key="tenants.id")
    supplier_id: Optional[int] = Field(default=None, foreign_key="suppliers.id")
    order_date: Optional[datetime] = Field(default_factory=datetime.utcnow)
    received_date: Optional[datetime] = Field(default=None)
    status: Optional[str] = Field(default=None, max_length=50)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # Relationships
    tenant: Optional["Tenant"] = Relationship(back_populates="purchase_orders")
    supplier: Optional["Supplier"] = Relationship(back_populates="purchase_orders")
    items: Optional[List["PurchaseOrderItem"]] = Relationship(back_populates="purchase_order")

class PurchaseOrderItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    purchase_order_id: Optional[int] = Field(default=None, foreign_key="purchase_orders.id")
    product_id: Optional[int] = Field(default=None, foreign_key="products.id")
    quantity: Optional[int] = Field(default=None)
    unit_price: Optional[float] = Field(default=None)
    
    # Relationships
    product: Optional["Product"] = Relationship(back_populates="purchase_order_items")
    purchase_order: Optional["PurchaseOrder"] = Relationship(back_populates="items")

class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: Optional[int] = Field(default=None, foreign_key="tenants.id")
    order_number: Optional[str] = Field(default=None, max_length=50, unique=True)
    order_date: Optional[datetime] = Field(default_factory=datetime.utcnow)
    order_type: Optional[str] = Field(default=None, max_length=50)
    status: Optional[str] = Field(default="pending", max_length=50)
    customer_name: Optional[str] = Field(default=None, max_length=255)
    total_amount: Optional[float] = Field(default=None)
    notes: Optional[str] = Field(default=None, max_length=500)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # Relationships
    tenant: Optional["Tenant"] = Relationship(back_populates="orders")
    order_items: Optional[List["OrderItem"]] = Relationship(back_populates="order")

class OrderItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: Optional[int] = Field(default=None, foreign_key="orders.id")
    product_id: Optional[int] = Field(default=None, foreign_key="products.id")
    quantity: Optional[int] = Field(default=None)
    unit_price: Optional[float] = Field(default=None)
    total_price: Optional[float] = Field(default=None)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # Relationships
    order: Optional["Order"] = Relationship(back_populates="order_items")
    product: Optional["Product"] = Relationship(back_populates="order_items")

class StockLevel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: Optional[int] = Field(default=None, foreign_key="tenants.id")
    product_id: Optional[int] = Field(default=None, foreign_key="products.id")
    quantity: Optional[int] = Field(default=0)
    
    # Relationships
    tenant: Optional["Tenant"] = Relationship(back_populates="stock_levels")
    product: Optional["Product"] = Relationship(back_populates="stock_levels")

class Supplier(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: Optional[int] = Field(default=None, foreign_key="tenants.id")
    name: Optional[str] = Field(default=None, max_length=150)
    contact_name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=120)
    phone: Optional[str] = Field(default=None, max_length=20)
    address: Optional[str] = Field(default=None, max_length=200)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # Relationships
    tenant: Optional["Tenant"] = Relationship(back_populates="suppliers")
    purchase_orders: Optional[List["PurchaseOrder"]] = Relationship(back_populates="supplier")

class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: Optional[int] = Field(default=None, foreign_key="tenants.id")
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    operation: Optional[str] = Field(default=None, max_length=30)
    table_name: Optional[str] = Field(default=None, max_length=100)
    record_id: Optional[str] = Field(default=None, max_length=120)
    old_value: Optional[Dict[str, Any]] = Field(default=None)
    new_value: Optional[Dict[str, Any]] = Field(default=None)
    metadata: Optional[Dict[str, Any]] = Field(default={})

    # Relationships
    user: Optional["User"] = Relationship(back_populates="audit_logs")
    tenant: Optional["Tenant"] = Relationship(back_populates="audit_logs")

class Token(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: Optional[str] = Field(default=None, foreign_key="users.id")
    token_type: Optional[str] = Field(default=None)
    expires_at: Optional[datetime] = Field(default=None)
    revoked: Optional[bool] = Field(default=False)
    revoked_at: Optional[datetime] = Field(default=None)
    revocation_reason: Optional[str] = Field(default=None)

    # Relationships
    user: Optional["User"] = Relationship(back_populates="tokens")

class Session(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: Optional[str] = Field(default=None, foreign_key="users.id")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    last_active: Optional[datetime] = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(default=None)
    ip_address: Optional[str] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)
    device_info: Optional[Dict[str, Any]] = Field(default=None)
    is_active: Optional[bool] = Field(default=True)

    # Relationships
    user: Optional["User"] = Relationship(back_populates="sessions")

class SecurityLog(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    event_type: Optional[str] = Field(default=None)
    user_id: Optional[str] = Field(default=None, foreign_key="users.id")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None)
    details: Optional[Dict[str, Any]] = Field(default=None)

    # Relationships
    user: Optional["User"] = Relationship(back_populates="security_logs")

class RateLimit(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    key: Optional[str] = Field(default=None)
    requests: Optional[int] = Field(default=0)
    window_start: Optional[datetime] = Field(default=None)
    window_size: Optional[int] = Field(default=None)  # in seconds

class SalesOrder(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: Optional[int] = Field(default=None, foreign_key="tenants.id")
    order_date: Optional[datetime] = Field(default_factory=datetime.utcnow)
    customer_name: Optional[str] = Field(default=None, max_length=100)
    status: Optional[str] = Field(default="pending", max_length=50)
    total_amount: Optional[float] = Field(default=0.0)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # Relationships
    items: Optional[List["SalesOrderItem"]] = Relationship(back_populates="sales_order")

class SalesOrderItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sales_order_id: Optional[int] = Field(default=None, foreign_key="sales_orders.id")
    product_id: Optional[int] = Field(default=None, foreign_key="products.id")
    quantity: Optional[int] = Field(default=None)
    unit_price: Optional[float] = Field(default=None)
    total_price: Optional[float] = Field(default=None)
    
    # Relationships
    sales_order: Optional["SalesOrder"] = Relationship(back_populates="items")
    product: Optional["Product"] = Relationship()