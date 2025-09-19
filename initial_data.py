import asyncio
from datetime import datetime
from sqlmodel.ext.asyncio.session import AsyncSession

from core.config import settings
from crud.user.crud_user import user, role
from core.database import get_async_session

async def create_initial_data() -> None:
    async for db in get_async_session():
        # Create admin role if it doesn't exist
        admin_role_data = {
            "name": "admin",
            "description": "Administrator role with all permissions",
            "permissions": ["*"]  # All permissions
        }
        
        # Create first superuser if it doesn't exist
        superuser_data = {
            "email": settings.FIRST_SUPERUSER,
            "full_name": "Initial Superuser",
            "user_name": "admin",
            "password": settings.FIRST_SUPERUSER_PASSWORD,
            "role_names": ["admin"],
            "is_active": True,
            "permissions": ["*"]  # All permissions
        }

        # Create super user
        db_user = await user.get_user_by_email(db, email=settings.FIRST_SUPERUSER)
        if not db_user:
            await user.create_user(db, user_data=superuser_data)
            print(f"Created superuser: {settings.FIRST_SUPERUSER}")
        
        break  # We only need one session

async def main() -> None:
    await create_initial_data()

if __name__ == "__main__":
    asyncio.run(main())