from fastapi import APIRouter
from .endpoints import inventory

api_router = APIRouter()

# Include all API endpoints
api_router.include_router(
    inventory.router,
    prefix="/inventory",
    tags=["inventory"]
)