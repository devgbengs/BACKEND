import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.api import api_router
from core.config import settings

# Configure logging with more detailed formatting
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG level
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    # 🏪 Inventory Management System API Documentation
    
    ## 🔐 Authentication Steps
    1. Locate the **/api/v1/auth/login/access-token** endpoint under **auth**
    2. Click "Try it out" and enter:
       ```
       username: test@example.com
       password: testpassword
       ```
    3. Click "Execute" and copy the access_token (NOT the refresh_token)
    4. Click the 🔓 **Authorize** button at the top
    5. Enter: `Bearer <your_access_token>` (replace with actual token)
    6. Click "Authorize" then "Close"
    
    ## 🚀 Quick Start
    After authenticating:
    1. Try the **/api/v1/users/me** endpoint to verify authentication
    2. You should see your user information
    
    ## 📌 Important Notes
    - Always include "Bearer " before your token
    - Use access_token, not refresh_token
    - Tokens expire after 30 minutes
    - If you get "Not authenticated" errors, repeat authentication steps
    """,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "tryItOutEnabled": True
    }
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with actual frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "api_version": "v1"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to Inventory Management System API"}

@app.on_event("shutdown")
async def shutdown_event():
    """Proper cleanup on application shutdown"""
    from core.database import dispose_db
    logger.info("Shutting down application...")
    await dispose_db()
    logger.info("Database connections disposed")

# Initialize default tenant and test user
@app.on_event("startup")
async def init_default_data():
    from crud.user.crud_user import user
    from crud.tenant.crud_tenant import tenant
    from sqlalchemy.ext.asyncio import AsyncSession
    from core.database import async_session
    from schema.tenant import TenantCreate
    from schema.user import UserCreate
    from core.config import settings

    logger.info("Starting application initialization...")
    
    async with async_session() as session:
        # Initialize database if needed
        from core.database import init_db
        await init_db()
        logger.debug("Database initialized")
        
        try:
            logging.info("Starting database operations...")
            
            # Create default tenant if it doesn't exist
            default_tenant_data = {
                "name": "Default Tenant",
                "domain": "default.example.com",
                "contact_email": "admin@example.com",
                "is_active": True,
                "description": "Default tenant for the system"
            }
            
            try:
                logging.info("Checking for existing tenant...")
                db_tenant = await tenant.get_by_domain(db=session, domain=default_tenant_data["domain"])
                logging.info(f"Tenant lookup result: {db_tenant}")
            except Exception as e:
                logging.error(f"Error checking for tenant: {str(e)}")
                raise
            
            if not db_tenant:
                try:
                    logging.info("Creating default tenant...")
                    # Convert to TenantCreate for proper validation
                    tenant_in = TenantCreate(**default_tenant_data)
                    db_tenant = await tenant.create(db=session, obj_in=tenant_in)
                    await session.commit()
                    logging.info(f"Default tenant created with ID: {db_tenant.id}")
                except Exception as e:
                    logging.error(f"Error creating tenant: {str(e)}")
                    raise
            
            # Create test user if it doesn't exist
            test_user_data = {
                "email": "test@example.com",
                "user_name": "testuser",
                "password": "testpassword",
                "full_name": "Test User",
                "is_active": True,
                "role_names": [],
                "permissions": [],
                "tenant_id": db_tenant.id  # Use the actual tenant ID
            }
            
            try:
                logging.info("Checking for existing user...")
                # Check if user exists
                existing_user = await user.get_by_email(session, email=test_user_data["email"])
                logging.info(f"User lookup result: {existing_user}")
            except Exception as e:
                logging.error(f"Error checking for user: {str(e)}")
                raise
            
            if not existing_user:
                try:
                    logging.info("Creating test user...")
                    # Convert to UserCreate for proper validation
                    user_in = UserCreate(**test_user_data)
                    await user.create(db=session, obj_in=user_in)
                    await session.commit()
                    logging.info("Test user created successfully")
                except Exception as e:
                    logging.error(f"Error creating user: {str(e)}")
                    raise
        
        except Exception as e:
            logging.error(f"Error during initialization: {str(e)}")
            raise  # Re-raise the exception to see it in the server logs
