from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field
from datetime import datetime
from pydantic import EmailStr, validator
from model.models import (
    OrderStatus, User, Order, OrderItem, Product, 
    Role, Tenant, StockLevel
)

# Base Schemas - Used for shared validation rules
class UserBase(SQLModel):
    email: Optional[EmailStr] = Field(None, description="User's email address")
    user_name: Optional[str] = Field(None, min_length=3, max_length=50, description="Username for login")
    full_name: Optional[str] = Field(None, max_length=100, description="User's full name")
    phone_number: Optional[str] = Field(None, max_length=20, description="User's phone number")
    role_names: List[str] = Field(default=[], description="List of role names assigned to user")
    permissions: List[str] = Field(default=[], description="List of individual permissions")
    tenant_id: Optional[int] = Field(None, description="ID of the tenant this user belongs to")
    is_active: bool = Field(default=True, description="Whether the user account is active")

    @validator('user_name')
    def username_alphanumeric(cls, v):
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError('Username must be alphanumeric with only _ and - allowed')
        return v

class TenantBase(SQLModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Name of the tenant")
    description: Optional[str] = Field(None, max_length=500, description="Tenant description")
    domain: Optional[str] = Field(None, min_length=3, max_length=255, description="Tenant's domain name")
    settings: Dict[str, Any] = Field(default={}, description="Tenant-specific settings")
    is_active: bool = Field(default=True, description="Whether the tenant is active")

    @validator('domain')
    def domain_format(cls, v):
        if not all(c.isalnum() or c in '.-' for c in v):
            raise ValueError('Domain must contain only alphanumeric characters, dots, and hyphens')
        return v.lower()

class ProductBase(SQLModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Product name")
    description: Optional[str] = Field(None, max_length=1000, description="Product description")
    sku: Optional[str] = Field(None, min_length=3, max_length=50, description="Stock Keeping Unit")
    price: Optional[float] = Field(None, gt=0, description="Product price")
    quantity: Optional[int] = Field(None, ge=0, description="Available quantity")
    category_id: Optional[int] = Field(None, description="ID of the product category")
    metadata: Dict[str, Any] = Field(default={}, description="Additional product metadata")
    is_active: bool = Field(default=True, description="Whether the product is active")
    tenant_id: Optional[int] = Field(None, description="ID of the tenant this product belongs to")

    @validator('sku')
    def sku_format(cls, v):
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError('SKU must contain only alphanumeric characters, hyphens, and underscores')
        return v.upper()

    @validator('price')
    def price_precision(cls, v):
        return round(v, 2)

class StockLevelBase(SQLModel):
    tenant_id: Optional[int] = Field(None, description="ID of the tenant this stock level belongs to")
    product_id: int = Field(..., description="ID of the product")
    warehouse_id: int = Field(..., description="ID of the warehouse")
    quantity: int = Field(..., ge=0, description="Current stock quantity")

class InventoryTransactionBase(SQLModel):
    tenant_id: Optional[int] = Field(None, description="ID of the tenant this transaction belongs to")
    product_id: int = Field(..., description="ID of the product")
    transaction_type: str = Field(..., description="Type of transaction (in, out, adjustment)")
    quantity: int = Field(..., gt=0, description="Quantity of items")
    reference_id: Optional[str] = Field(None, max_length=100, description="Reference ID for the transaction")
    reference_type: Optional[str] = Field(None, max_length=50, description="Type of reference (order, adjustment, etc.)")
    notes: Optional[str] = Field(None, max_length=255, description="Additional notes")

class CategoryBase(SQLModel):
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, max_length=500, description="Category description")
    parent_id: Optional[int] = Field(None, description="ID of the parent category")
    metadata: Dict[str, Any] = Field(default={}, description="Additional category metadata")
    is_active: bool = Field(default=True, description="Whether the category is active")
    tenant_id: Optional[int] = Field(None, description="ID of the tenant this category belongs to")

class OrderBase(SQLModel):
    user_id: Optional[int] = Field(None, description="ID of the user placing the order")
    order_number: Optional[str] = Field(None, min_length=3, max_length=50, description="Unique order number")
    total_amount: Optional[float] = Field(None, ge=0, description="Total order amount")
    status: OrderStatus = Field(default=OrderStatus.PENDING, description="Current order status")
    shipping_address: Optional[Dict[str, Any]] = Field(None, description="Shipping address details")
    billing_address: Optional[Dict[str, Any]] = Field(None, description="Billing address details")
    metadata: Dict[str, Any] = Field(default={}, description="Additional order metadata")
    tenant_id: Optional[int] = Field(None, description="ID of the tenant this order belongs to")

    @validator('order_number')
    def order_number_format(cls, v):
        if not v.replace("-", "").isalnum():
            raise ValueError('Order number must contain only alphanumeric characters and hyphens')
        return v.upper()

    @validator('total_amount')
    def total_amount_precision(cls, v):
        return round(v, 2)

class OrderItemBase(SQLModel):
    order_id: Optional[int] = Field(None, description="ID of the parent order")
    product_id: Optional[int] = Field(None, description="ID of the ordered product")
    quantity: Optional[int] = Field(None, gt=0, description="Quantity ordered")
    unit_price: Optional[float] = Field(None, gt=0, description="Price per unit")
    total_price: Optional[float] = Field(None, gt=0, description="Total price for this item")
    metadata: Dict[str, Any] = Field(default={}, description="Additional item metadata")

    @validator('total_price')
    def validate_total_price(cls, v, values):
        if 'quantity' in values and 'unit_price' in values:
            expected_total = round(values['quantity'] * values['unit_price'], 2)
            if abs(v - expected_total) > 0.01:  # Allow for small floating-point differences
                raise ValueError('Total price must equal quantity * unit_price')
        return round(v, 2)

class RoleBase(SQLModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50, description="Role name")
    description: Optional[str] = Field(None, max_length=200, description="Role description")
    permissions: List[str] = Field(default=[], description="List of permissions for this role")
    tenant_id: Optional[int] = Field(None, description="ID of the tenant this role belongs to")

    @validator('name')
    def name_format(cls, v):
        if not v.replace("_", "").isalnum():
            raise ValueError('Role name must contain only alphanumeric characters and underscores')
        return v.upper()

# Create Schemas - Used for API input validation

# Create Schemas - Used for API input validation
class UserCreate(UserBase):
    password: Optional[str] = Field(
        None,
        min_length=8,
        max_length=100,
        description="User's password (min 8 characters)"
    )

    @validator('password')
    def password_complexity(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v

class TenantCreate(TenantBase):
    pass

class ProductCreate(ProductBase):
    pass

class StockLevelCreate(StockLevelBase):
    pass

class InventoryTransactionCreate(InventoryTransactionBase):
    pass

class CategoryCreate(CategoryBase):
    pass

class OrderCreate(OrderBase):
    pass

class OrderItemCreate(OrderItemBase):
    pass

class RoleCreate(RoleBase):
    pass

# Update Schemas - Used for partial updates
class UserUpdate(SQLModel):
    email: Optional[EmailStr] = None
    user_name: Optional[str] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=8)
    is_active: Optional[bool] = None
    role_names: Optional[List[str]] = None
    permissions: Optional[List[str]] = None

class TenantUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class ProductUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sku: Optional[str] = None
    price: Optional[float] = Field(default=None, gt=0)
    quantity: Optional[int] = Field(default=None, ge=0)
    category_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class StockLevelUpdate(SQLModel):
    quantity: Optional[int] = Field(default=None, ge=0)

class InventoryTransactionUpdate(SQLModel):
    quantity: Optional[int] = Field(default=None, gt=0)
    notes: Optional[str] = Field(default=None, max_length=255)

class CategoryUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class OrderUpdate(SQLModel):
    status: Optional[OrderStatus] = None
    shipping_address: Optional[Dict[str, Any]] = None
    billing_address: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class OrderItemUpdate(SQLModel):
    quantity: Optional[int] = Field(default=None, gt=0)
    unit_price: Optional[float] = Field(default=None, gt=0)
    total_price: Optional[float] = Field(default=None, gt=0)
    metadata: Optional[Dict[str, Any]] = None

class RoleUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None

# Response Schemas - Used for reading data
class UserRead(UserBase):
    id: int = Field(..., description="User's unique identifier")
    created_at: datetime = Field(..., description="Timestamp of user creation")
    updated_at: datetime = Field(..., description="Timestamp of last update")

class TenantRead(TenantBase):
    id: int = Field(..., description="Tenant's unique identifier")
    created_at: datetime = Field(..., description="Timestamp of tenant creation")
    updated_at: datetime = Field(..., description="Timestamp of last update")

class ProductRead(ProductBase):
    id: int = Field(..., description="Product's unique identifier")
    created_at: datetime = Field(..., description="Timestamp of product creation")
    updated_at: datetime = Field(..., description="Timestamp of last update")

class StockLevelRead(StockLevelBase):
    id: int = Field(..., description="StockLevel's unique identifier")

class InventoryTransactionRead(InventoryTransactionBase):
    id: int = Field(..., description="InventoryTransaction's unique identifier")
    created_at: datetime = Field(..., description="Timestamp of transaction creation")
    updated_at: datetime = Field(..., description="Timestamp of last update")

class CategoryRead(CategoryBase):
    id: int = Field(..., description="Category's unique identifier")
    created_at: datetime = Field(..., description="Timestamp of category creation")
    updated_at: datetime = Field(..., description="Timestamp of last update")

class OrderRead(OrderBase):
    id: int = Field(..., description="Order's unique identifier")
    created_at: datetime = Field(..., description="Timestamp of order creation")
    updated_at: datetime = Field(..., description="Timestamp of last update")
    items: List['OrderItemRead'] = Field(default=[], description="List of order items")

class OrderItemRead(OrderItemBase):
    id: int = Field(..., description="Order item's unique identifier")
    created_at: datetime = Field(..., description="Timestamp of order item creation")
    updated_at: datetime = Field(..., description="Timestamp of last update")
    product: ProductRead = Field(..., description="Associated product details")

class RoleRead(RoleBase):
    id: int = Field(..., description="Role's unique identifier")
    created_at: datetime = Field(..., description="Timestamp of role creation")
    updated_at: datetime = Field(..., description="Timestamp of last update")

# Authentication Schemas
class Token(SQLModel):
    access_token: str = Field(...)
    token_type: str = "bearer"

class TokenData(SQLModel):
    sub: str = Field(...)  # user id or email
    exp: datetime = Field(...)
    tenant_id: Optional[int] = None
    scopes: List[str] = Field(default=[])

class LoginRequest(SQLModel):
    email: EmailStr = Field(...)
    password: str = Field(...)
    tenant_id: Optional[int] = None

# Query Params Schemas
class PaginationParams(SQLModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, le=1000)

class ProductFilterParams(PaginationParams):
    category_id: Optional[int] = None
    is_active: Optional[bool] = None
    min_price: Optional[float] = Field(default=None, ge=0)
    max_price: Optional[float] = Field(default=None, ge=0)
    search: Optional[str] = None

class OrderFilterParams(PaginationParams):
    status: Optional[OrderStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_id: Optional[int] = None

# Public List Response Schemas
class BaseListResponse(SQLModel):
    total: int = Field(..., description="Total number of items")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum number of items per page")

class UserListResponse(BaseListResponse):
    items: List[UserRead] = Field(..., description="List of users")

class TenantListResponse(BaseListResponse):
    items: List[TenantRead] = Field(..., description="List of tenants")

class ProductListResponse(BaseListResponse):
    items: List[ProductRead] = Field(..., description="List of products")

class CategoryListResponse(BaseListResponse):
    items: List[CategoryRead] = Field(..., description="List of categories")

class OrderListResponse(BaseListResponse):
    items: List[OrderRead] = Field(..., description="List of orders")

class RoleListResponse(BaseListResponse):
    items: List[RoleRead] = Field(..., description="List of roles")

# Public Response Schemas
class BaseResponse(SQLModel):
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")

class DataResponse(BaseResponse):
    data: Optional[Any] = Field(None, description="Response data")

class ErrorResponse(BaseResponse):
    error_code: str = Field(..., description="Error code for the failure")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

# Update forward refs for response schemas with nested relationships
from typing import ForwardRef
OrderItemRead.model_rebuild()
OrderRead.model_rebuild()