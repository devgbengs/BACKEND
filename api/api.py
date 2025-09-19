from fastapi import APIRouter
from api.endpoints import auth, users
from api.v1.endpoints import tenant, inventory

api_router = APIRouter()

# V1 API endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(tenant.router, prefix="/tenants", tags=["tenant-management"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])