from typing import List, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from api.deps import get_async_session, get_current_user
from crud.tenant.crud_tenant import tenant
from crud.user.crud_user import user
from schema.tenant import TenantBase, TenantCreate, TenantUpdate
from model.models import Tenant
from schema.user import User, UserCreate
from schema.role import Role, RoleResponse, ROLE_PERMISSIONS, ROLE_DESCRIPTIONS
import logging

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Tenant Management Endpoints

@router.get("/", response_model=List[Tenant])
async def get_tenants(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Retrieve tenants. Only accessible by authenticated users.
    """
    # Only superusers can list all tenants
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Only superusers can list all tenants"
        )
    tenants = await tenant.get_multi(db, skip=skip, limit=limit)
    return tenants

@router.post("/register", response_model=dict)
async def register_tenant_with_admin(
    *,
    db: AsyncSession = Depends(get_async_session),
    tenant_in: TenantCreate,
    admin_email: str,
    admin_password: str,
    admin_full_name: str,
    admin_username: str
) -> Any:
    """
    Register a new tenant and create its first admin user (superuser).
    The first user of a tenant automatically becomes a superuser for that tenant.
    """
    try:
        # Check if tenant domain already exists
        if tenant_in.domain:
            existing_tenant = await tenant.get_by_domain(db, domain=tenant_in.domain)
            if existing_tenant:
                raise HTTPException(
                    status_code=400,
                    detail="A tenant with this domain already exists"
                )

        # Check if admin email already exists
        existing_user = await user.get_by_email(db, email=admin_email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="A user with this email already exists"
            )

        # Create the tenant
        new_tenant = await tenant.create(db, obj_in=tenant_in)
        await db.commit()
        await db.refresh(new_tenant)

        # Create the tenant's admin user (superuser)
        admin_data = UserCreate(
            email=admin_email,
            password=admin_password,
            full_name=admin_full_name,
            user_name=admin_username,
            is_active=True,
            is_superuser=True,
            role_names=["admin", "superuser"],
            permissions=["admin:all"],
            tenant_id=new_tenant.id
        )

        new_admin = await user.create(db, obj_in=admin_data)
        await db.commit()

        logger.info(f"Created tenant {new_tenant.name} with admin user {new_admin.email}")

        return {
            "message": "Tenant and admin user created successfully",
            "tenant": {
                "id": new_tenant.id,
                "name": new_tenant.name,
                "domain": new_tenant.domain
            },
            "admin_user": {
                "id": new_admin.id,
                "email": new_admin.email,
                "user_name": new_admin.user_name
            }
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error registering tenant: {str(e)}"
        )

@router.get("/{tenant_id}", response_model=Tenant)
async def get_tenant_by_id(
    tenant_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get a specific tenant by id. Only accessible by authenticated users.
    """
    # Users can only view their own tenant unless they're a superuser
    if not current_user.is_superuser and current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Can only view your own tenant"
        )
    
    db_tenant = await tenant.get(db, id=tenant_id)
    if not db_tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found"
        )
    return db_tenant

@router.put("/{tenant_id}", response_model=Tenant)
async def update_tenant(
    *,
    db: AsyncSession = Depends(get_async_session),
    tenant_id: int,
    tenant_in: TenantUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update a tenant. Only accessible by tenant superusers for their own tenant.
    """
    # Check permissions
    if not current_user.is_superuser or current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Only tenant superusers can update their own tenant"
        )
    
    db_tenant = await tenant.get(db, id=tenant_id)
    if not db_tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found"
        )
    
    if tenant_in.domain:
        existing_tenant = await tenant.get_by_domain(db, domain=tenant_in.domain)
        if existing_tenant and existing_tenant.id != tenant_id:
            raise HTTPException(
                status_code=400,
                detail="A tenant with this domain already exists."
            )
            
    updated_tenant = await tenant.update(db, db_obj=db_tenant, obj_in=tenant_in)
    return updated_tenant

@router.delete("/{tenant_id}", response_model=Tenant)
async def delete_tenant(
    *,
    db: AsyncSession = Depends(get_async_session),
    tenant_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Delete a tenant. Only accessible by system superusers.
    """
    # Only system superusers can delete tenants
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Only system superusers can delete tenants"
        )
    
    db_tenant = await tenant.get(db, id=tenant_id)
    if not db_tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found"
        )
    
    # Check for existing users in this tenant
    tenant_users = await user.get_by_tenant(db, tenant_id=tenant_id)
    if tenant_users:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete tenant with existing users"
        )
    
    deleted_tenant = await tenant.remove(db, id=tenant_id)
    return deleted_tenant

# Role Management Endpoints

@router.post("/{tenant_id}/users/{user_id}/roles/{role}", response_model=User)
async def promote_user_role(
    *,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
    tenant_id: int,
    user_id: int,
    role: Role
) -> Any:
    """
    Promote a user to a specific role within the tenant.
    """
    logger.info(f"Attempting to promote user {user_id} to role {role} in tenant {tenant_id}")

    # Verify permissions
    if not current_user.is_superuser or current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Only tenant superusers can promote users in their tenant"
        )

    try:
        # Get and validate user
        db_user = await user.get(db, id=user_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
            
        if db_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot promote users from different tenants"
            )

        # Add the new role
        current_roles = db_user.role_names or []
        if role not in current_roles:
            current_roles.append(role)

        # Update user roles and permissions
        update_data = {
            "role_names": current_roles
        }

        # Add role-specific permissions
        if role in ROLE_PERMISSIONS:
            current_permissions = set(db_user.permissions or [])
            new_permissions = current_permissions.union(ROLE_PERMISSIONS[role])
            update_data["permissions"] = list(new_permissions)

        updated_user = await user.update(db, db_obj=db_user, obj_in=update_data)
        await db.commit()

        logger.info(f"User {updated_user.email} promoted to {role}")
        return updated_user

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error promoting user: {str(e)}"
        )

@router.delete("/{tenant_id}/users/{user_id}/roles/{role}", response_model=User)
async def revoke_user_role(
    *,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
    tenant_id: int,
    user_id: int,
    role: Role
) -> Any:
    """
    Revoke a role from a user within the tenant.
    """
    # Verify permissions
    if not current_user.is_superuser or current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Only tenant superusers can revoke roles in their tenant"
        )

    try:
        # Get and validate user
        db_user = await user.get(db, id=user_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
            
        if db_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=403,
                detail="Cannot modify users from different tenants"
            )

        # Prevent revoking roles from tenant superuser
        if db_user.is_superuser and user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Cannot modify roles of other tenant superusers"
            )

        # Remove the role
        current_roles = db_user.role_names or []
        if role in current_roles:
            current_roles.remove(role)

            # Update user roles
            update_data = {
                "role_names": current_roles
            }

            updated_user = await user.update(db, db_obj=db_user, obj_in=update_data)
            await db.commit()

            logger.info(f"Role {role} revoked from user {updated_user.email}")
            return updated_user
        else:
            raise HTTPException(
                status_code=400,
                detail=f"User does not have role {role}"
            )

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error revoking role: {str(e)}"
        )

@router.get("/{tenant_id}/roles", response_model=List[RoleResponse])
async def list_available_roles(
    *,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
    tenant_id: int,
) -> Any:
    """
    List all available roles and their permissions in a tenant.
    Only accessible by tenant superusers.
    """
    if not current_user.is_superuser or current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Only tenant superusers can view available roles"
        )
    
    return [
        RoleResponse(
            role=role,
            permissions=permissions,
            description=ROLE_DESCRIPTIONS[role]
        )
        for role, permissions in ROLE_PERMISSIONS.items()
    ]