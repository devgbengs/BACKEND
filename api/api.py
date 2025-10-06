from fastapi import APIRouter
from api.endpoints import auth, users
from api.v1.endpoints import inventory, sales, tenant

api_router = APIRouter()

# V1 API endpoints
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)
api_router.include_router(
    sales.sales_router,
    prefix="/sales",
    tags=["Sales Management"],
)
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["User Management"],
)
api_router.include_router(
    tenant.tenant_router,
    prefix="/tenants",
    tags=["Tenant Management"],
)
api_router.include_router(
    inventory.inventory_router,
    prefix="/inventory",
    tags=["Inventory Management"],
)
