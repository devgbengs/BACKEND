import asyncio
from sqlmodel.ext.asyncio.session import AsyncSession
from core.database import get_async_session
from crud.tenant.crud_tenant import tenant
from crud.user.crud_user import user
from schema.tenant import TenantCreate
from schema.user import UserCreate

async def create_users():
    async for db in get_async_session():
        try:
            # Create tenant
            tenant_data = TenantCreate(
                name="Test Company",
                domain="testcompany.com",
                contact_email="admin@testcompany.com",
                description="Test Company for Inventory Management",
                is_active=True
            )
            new_tenant = await tenant.create(db, obj_in=tenant_data)
            await db.commit()
            
            # Create users with different roles
            users_data = [
                {
                    "email": "admin@testcompany.com",
                    "password": "Admin123#",
                    "full_name": "Admin User",
                    "user_name": "admin",
                    "is_active": True,
                    "is_superuser": True,
                    "role_names": ["admin"],
                    "permissions": ["admin:all"],
                    "tenant_id": new_tenant.id
                },
                {
                    "email": "manager@testcompany.com",
                    "password": "Manager123#",
                    "full_name": "Manager User",
                    "user_name": "manager",
                    "is_active": True,
                    "role_names": ["manager"],
                    "permissions": ["manage:items", "view:reports", "manage:staff", "view:analytics"],
                    "tenant_id": new_tenant.id
                },
                {
                    "email": "staff@testcompany.com",
                    "password": "Staff123#",
                    "full_name": "Staff User",
                    "user_name": "staff",
                    "is_active": True,
                    "role_names": ["staff"],
                    "permissions": ["create:items", "edit:items", "view:items", "basic:reports"],
                    "tenant_id": new_tenant.id
                },
                {
                    "email": "user@testcompany.com",
                    "password": "User123#",
                    "full_name": "Basic User",
                    "user_name": "user",
                    "is_active": True,
                    "role_names": ["user"],
                    "permissions": ["view:items", "view:basic"],
                    "tenant_id": new_tenant.id
                }
            ]
            
            for user_data in users_data:
                user_in = UserCreate(**user_data)
                await user.create(db, obj_in=user_in)
                await db.commit()
                print(f"Created user: {user_data['email']}")
            
            print("\nAll users created successfully!")
            print("\nUser Credentials:")
            print("------------------")
            for user_data in users_data:
                print(f"\nRole: {user_data['role_names'][0]}")
                print(f"Email: {user_data['email']}")
                print(f"Password: {user_data['password']}")
            
            break  # We only need one session
            
        except Exception as e:
            print(f"Error: {str(e)}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(create_users())