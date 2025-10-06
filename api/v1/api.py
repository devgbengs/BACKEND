from fastapi import APIRouter
from .endpoints import inventory, tenant, sales

api_router = APIRouter()

# Include all API endpoints
api_router.include_router(
    inventory.router,
    prefix="/inventory",
    tags=["inventory"]
)

api_router.include_router(
    tenant.router,
    prefix="/tenants",
    tags=["tenant-management"]
)

api_router.include_router(
    sales.router,
    prefix="/sales",
    tags=["sales-management"]
)