from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from api.deps import get_async_session, get_current_user
from crud.user.crud_user import user
from schema.user import UserCreate, UserUpdate, User

router = APIRouter()

@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get information about the currently authenticated user."""
    return current_user

@router.get("/", response_model=List[User])
async def get_users(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
    role: str = None,
    skip: int = 0,
    limit: int = 100
    
) -> Any:
    """
    Retrieve users from the same tenant as the current user.
    Required roles: ["admin", "manager"] or is_superuser=True
    Optional query parameter: role - Filter users by role
    """
    # Check if user has required roles or is superuser
    if not (current_user.is_superuser or 
            any(role in ["admin", "manager"] for role in current_user.role_names)):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions. Required roles: admin or manager"
        )
    
    try:
        if role:
            # Get users with specific role
            users = await user.get_users_by_role(
                db,
                tenant_id=current_user.tenant_id,
                role=role,
                skip=skip,
                limit=limit
            )
        else:
            # Get all users from the same tenant
            users = await user.get_multi_by_tenant(
                db,
                tenant_id=current_user.tenant_id,
                skip=skip,
                limit=limit
            )
        return users
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving users: {str(e)}"
        )

@router.post("/", response_model=User)
async def create_user(
    *,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
    user_in: UserCreate
) -> Any:
    """
    Create new user in the same tenant as the current user.
    Only accessible by authenticated users within the same tenant.
    """
    try:
        # Check if email exists in the same tenant
        db_user = await user.get_by_email(db, email=user_in.email)
        if db_user:
            raise HTTPException(
                status_code=400,
                detail="A user with this email already exists."
            )
        
        # Ignore tenant_id from input and use current user's tenant
        user_data = user_in.dict(exclude={"tenant_id"})
        user_data["tenant_id"] = current_user.tenant_id
        
        # Ensure required fields
        if not user_data.get("email"):
            raise HTTPException(
                status_code=400,
                detail="Email is required"
            )
        if not user_data.get("password"):
            raise HTTPException(
                status_code=400,
                detail="Password is required"
            )
        if not user_data.get("full_name"):
            raise HTTPException(
                status_code=400,
                detail="Full name is required"
            )
        
        new_user = await user.create(db, obj_in=user_data)
        await db.commit()
        return new_user
        
    except ValueError as ve:
        raise HTTPException(
            status_code=400,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating user: {str(e)}"
        )

@router.get("/{user_id}", response_model=User)
async def get_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get a specific user by id from the same tenant.
    Only accessible by authenticated users within the same tenant.
    """
    db_user = await user.get(db, id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    if db_user.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Access invalid. User does not exist in your business."
        )
    return db_user

@router.put("/{user_id}", response_model=User)
async def update_user(
    *,
    db: AsyncSession = Depends(get_async_session),
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update a user from the same tenant.
    Role requirements:
    - Regular users can only update their own profile (excluding roles and permissions)
    - Managers can update user profiles in their tenant (excluding roles and permissions)
    - Admins can update all user details including roles and permissions
    - Superusers can do everything
    """
    try:
        db_user = await user.get(db, id=user_id)
        if not db_user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # Check tenant access
        if db_user.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=403,
                detail="Access invalid. User does not exist in your business."
            )

        # Determine update permissions
        is_self_update = db_user.id == current_user.id
        is_admin = "admin" in current_user.role_names
        is_manager = "manager" in current_user.role_names
        
        # Convert input to dict for easier manipulation
        update_data = user_in.dict(exclude_unset=True)
        
        # Role and permission update restrictions
        if "role_names" in update_data or "permissions" in update_data:
            if not (current_user.is_superuser or is_admin):
                raise HTTPException(
                    status_code=403,
                    detail="Only admins and superusers can modify roles and permissions"
                )
        
        # Prevent changing tenant_id
        if "tenant_id" in update_data:
            raise HTTPException(
                status_code=400,
                detail="Cannot change user's tenant"
            )
        
        # Regular users can only update their own non-sensitive fields
        if not (current_user.is_superuser or is_admin or is_manager):
            if not is_self_update:
                raise HTTPException(
                    status_code=403,
                    detail="You can only update your own profile"
                )
            # Restrict fields for self-update
            allowed_fields = {"full_name", "phone_number", "password"}
            update_data = {k: v for k, v in update_data.items() if k in allowed_fields}
        
        # Prevent non-superusers from modifying superuser status
        if "is_superuser" in update_data and not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="Only superusers can modify superuser status"
            )
        
        updated_user = await user.update(db, db_obj=db_user, obj_in=update_data)
        await db.commit()
        return updated_user
        
    except ValueError as ve:
        raise HTTPException(
            status_code=400,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating user: {str(e)}"
        )

@router.delete("/{user_id}", response_model=User, deprecated=True)
async def delete_user(
    *,
    db: AsyncSession = Depends(get_async_session),
    user_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Delete a user from the same tenant.
    Required roles: ["admin"] or is_superuser=True
    """
    # Check if user has required roles or is superuser
    if not (current_user.is_superuser or "admin" in current_user.role_names):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions. Required role: admin"
        )
    
    db_user = await user.get(db, id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Check tenant ownership
    if db_user.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied. User belongs to a different tenant."
        )
    
    # Prevent deletion of superusers by non-superusers
    if db_user.is_superuser and not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Only superusers can delete other superusers"
        )
    
    # Prevent self-deletion
    if db_user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete yourself"
        )
    
    deleted_user = await user.remove(db, id=user_id)
    return deleted_user