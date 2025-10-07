from typing import List, Optional, Dict, Any, Union
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from datetime import datetime

from model.models import User, Role, UserSession
from schema.user import UserCreate, UserUpdate
from ..base import CRUDBase
from core.security import get_password_hash, verify_password


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    async def get(self, db: Session, id: int) -> Optional[User]:
        """Get a user by ID with roles preloaded"""
        statement = select(User).options(
            selectinload(User.roles)
        ).where(User.id == id)
        result = await db.execute(statement)
        return result.unique().scalar_one_or_none()

    async def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Get a user by email with roles preloaded"""
        try:
            print(f"Building query to find user with email: {email}")
            statement = select(User).options(
                selectinload(User.roles)
            ).where(User.email == email)
            print(f"Executing query: {statement}")
            result = await db.execute(statement)
            user = result.unique().scalar_one_or_none()
            print(f"Query result: {'User found' if user else 'No user found'}")
            return user
        except Exception as e:
            print(f"Error in get_by_email: {str(e)}")
            raise

    async def create(self, db: Session, *, obj_in: Union[UserCreate, Dict[str, Any]]) -> User:
        """Create a new user with proper password hashing"""
        if isinstance(obj_in, dict):
            create_data = obj_in
        else:
            create_data = obj_in.dict(exclude_unset=True)
            
        if not create_data.get("tenant_id"):
            raise ValueError("tenant_id is required when creating a user")
        
        if not create_data.get("password"):
            raise ValueError("password is required when creating a user")
            
        try:
            hashed_password = get_password_hash(create_data["password"])
            del create_data["password"]
            
            db_obj = User(
                email=create_data["email"],
                user_name=create_data.get("user_name"),
                full_name=create_data["full_name"],
                hashed_password=hashed_password,
                phone_number=create_data.get("phone_number"),
                role_names=create_data.get("role_names", []),
                permissions=create_data.get("permissions", []),
                tenant_id=create_data["tenant_id"],
                is_active=create_data.get("is_active", True),
                is_superuser=create_data.get("is_superuser", False),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
            
        except Exception as e:
            await db.rollback()
            raise ValueError(f"Error creating user: {str(e)}")

    async def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password"""
        try:
            print(f"Looking up user by email: {email}")
            user = await self.get_by_email(db, email=email)
            if not user:
                print(f"No user found with email: {email}")
                return None
            print(f"User found with email {email}, verifying password")
            
            if not verify_password(password, user.hashed_password):
                print(f"Password verification failed for user: {email}")
                return None
                
            print(f"Password verified successfully for user: {email}")
            return user
        except Exception as e:
            print(f"Error in authenticate method: {str(e)}")
            raise

    def is_active(self, user: User) -> bool:
        """Check if a user is active"""
        return user.is_active

    async def get_multi_by_tenant(
        self, 
        db: Session, 
        *, 
        tenant_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        """Get multiple users for a specific tenant with pagination"""
        statement = (
            select(User)
            .options(selectinload(User.roles))
            .where(User.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def update(
        self,
        db: Session,
        *,
        db_obj: User,
        obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        """Update a user with proper handling of password hashing"""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password

        update_data["updated_at"] = datetime.utcnow()
        return await super().update(db, db_obj=db_obj, obj_in=update_data)

    async def get_users_by_role(
        self,
        db: Session,
        *,
        tenant_id: int,
        role: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Get users with a specific role in a tenant"""
        from sqlalchemy import text
        
        # Using a raw SQL expression for proper JSON array containment check
        statement = (
            select(User)
            .options(selectinload(User.roles))
            .where(
                User.tenant_id == tenant_id,
                text("role_names::jsonb ? :role")
            )
            .params(role=role)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def remove(self, db: Session, *, id: int) -> Optional[User]:
        """Delete a user and clean up related data."""
        try:
            # Get the user first so we can return it after deletion
            from sqlalchemy import text
            user_query = await db.execute(
                text("""
                    SELECT id, tenant_id, email, user_name, hashed_password, 
                           full_name, is_active, is_superuser, role_names,
                           created_at, updated_at
                    FROM users 
                    WHERE id = :user_id
                """),
                {"user_id": id}
            )
            user_data = user_query.mappings().one_or_none()
            if not user_data:
                return None

            print(f"Starting deletion of user {id} and related data...")
            
            # Remove related data
            from sqlalchemy import text
            # 1. Delete user sessions
            await db.execute(
                text("DELETE FROM user_sessions WHERE user_id = :user_id"),
                {"user_id": id}
            )
            
            # 2. First delete order items
            await db.execute(
                text("""
                    DELETE FROM order_items 
                    WHERE order_id IN (
                        SELECT id FROM orders WHERE user_id = :user_id
                    )
                """),
                {"user_id": id}
            )
            
            # 3. Then delete orders
            await db.execute(
                text("DELETE FROM orders WHERE user_id = :user_id"),
                {"user_id": id}
            )
            
            # 4. Delete sale items
            await db.execute(
                text("""
                    DELETE FROM sale_items 
                    WHERE sale_id IN (
                        SELECT id FROM sales WHERE customer_id = :user_id
                    )
                """),
                {"user_id": id}
            )
            
            # 5. Delete sales
            await db.execute(
                text("DELETE FROM sales WHERE customer_id = :user_id"),
                {"user_id": id}
            )
            
            # Finally, delete the user
            await db.execute(
                text("DELETE FROM users WHERE id = :user_id"),
                {"user_id": id}
            )
            await db.commit()
            
            print(f"Successfully deleted user {id} and all related data")
            
            # Construct and return a User object with the data we fetched
            return User(
                id=user_data['id'],
                tenant_id=user_data['tenant_id'],
                email=user_data['email'],
                user_name=user_data['user_name'],
                hashed_password=user_data['hashed_password'],
                full_name=user_data['full_name'],
                is_active=user_data['is_active'],
                is_superuser=user_data['is_superuser'],
                role_names=user_data['role_names'],
                created_at=user_data['created_at'],
                updated_at=user_data['updated_at']
            )
        except Exception as e:
            await db.rollback()
            error_msg = str(e)
            if "violates foreign key constraint" in error_msg:
                # Try to identify which constraint was violated
                if "sale_items_sale_id_fkey" in error_msg:
                    raise ValueError(f"Error deleting user: Could not delete sales due to existing sale items")
                elif "orders_customer_id_fkey" in error_msg:
                    raise ValueError(f"Error deleting user: Could not delete orders due to existing references")
            raise ValueError(f"Error deleting user: {error_msg}")

    async def update_roles(
        self,
        db: Session,
        *,
        db_obj: User,
        roles_to_add: List[str]
    ) -> User:
        """
        Update a user's roles and associated permissions.
        
        Args:
            db: Database session
            db_obj: User object to update
            roles_to_add: List of role names to add to the user
            
        Returns:
            Updated user object
            
        Raises:
            ValueError: If any of the roles are invalid
        """
        from schema.role import ROLE_PERMISSIONS, Role
        
        try:
            # Validate roles
            valid_roles = {role.value for role in Role}
            invalid_roles = [role for role in roles_to_add if role not in valid_roles]
            if invalid_roles:
                raise ValueError(f"Invalid roles: {invalid_roles}")
            
            # Update role_names - Keep existing roles and add new ones
            current_roles = set(db_obj.role_names)
            new_roles = set(roles_to_add)
            updated_roles = list(current_roles.union(new_roles))
            
            # Update permissions based on all roles
            all_permissions = set()
            for role in updated_roles:
                role_enum = Role(role)
                role_permissions = ROLE_PERMISSIONS.get(role_enum, [])
                all_permissions.update(role_permissions)
            
            # Update the user
            update_data = {
                "role_names": updated_roles,
                "permissions": list(all_permissions),
                "updated_at": datetime.utcnow()
            }
            
            return await super().update(db, db_obj=db_obj, obj_in=update_data)
            
        except Exception as e:
            raise ValueError(f"Error updating user roles: {str(e)}")

    async def promote_user_role(
        self,
        db: Session,
        *,
        user_id: int,
        new_roles: List[str],
        current_user: User
        ) -> User:
        """
        Promote a user by adding new roles while preserving existing ones
        """
        try:
            # Get user with current roles
            user = await self.get(db, id=user_id)
            if not user:
                raise ValueError("User not found")
                
            # Check tenant isolation
            if user.tenant_id != current_user.tenant_id:
                raise ValueError("Cannot manage roles across different tenants")
                
            # Check promotion permissions
            if "admin" in new_roles and not current_user.is_superuser:
                raise ValueError("Only superusers can promote to admin role")
                
            # Add new roles while preserving existing ones
            updated_roles = list(set(user.role_names + new_roles))
            
            # Update user with new roles
            return await self.update(
                db,
                db_obj=user,
                obj_in={"role_names": updated_roles}
            )
                
        except Exception as e:
            await db.rollback()
            raise ValueError(f"Error promoting user role: {str(e)}")

    async def revoke_user_role(
        self,
        db: Session,
        *,
        user_id: int,
        roles_to_revoke: List[str],
        current_user: User
    ) -> User:
        """
        Revoke specific roles from a user while maintaining others
        """
        try:
            # Get user with current roles
            user = await self.get(db, id=user_id)
            if not user:
                raise ValueError("User not found")
                
            # Check tenant isolation
            if user.tenant_id != current_user.tenant_id:
                raise ValueError("Cannot manage roles across different tenants")
                
            # Check revocation permissions
            if "admin" in roles_to_revoke and not current_user.is_superuser:
                raise ValueError("Only superusers can revoke admin role")
                
            # Remove specified roles
            updated_roles = [
                role for role in user.role_names 
                if role not in roles_to_revoke
            ]
            
            # Ensure user has at least one role
            if not updated_roles:
                raise ValueError("Cannot revoke all roles from user")
                
            # Update user with remaining roles
            return await self.update(
                db,
                db_obj=user,
                obj_in={"role_names": updated_roles}
            )
                
        except Exception as e:
            await db.rollback()
            raise ValueError(f"Error revoking user role: {str(e)}")

    async def revoke_roles(
        self,
        db: Session,
        *,
        db_obj: User,
        roles_to_remove: List[str]
    ) -> User:
        """
        Revoke roles from a user and update their permissions accordingly.
        
        Args:
            db: Database session
            db_obj: User object to update
            roles_to_remove: List of role names to remove from the user
            
        Returns:
            Updated user object
            
        Raises:
            ValueError: If any of the roles are invalid or if trying to remove all roles
        """
        from schema.role import ROLE_PERMISSIONS, Role
        
        try:
            # Validate roles
            valid_roles = {role.value for role in Role}
            invalid_roles = [role for role in roles_to_remove if role not in valid_roles]
            if invalid_roles:
                raise ValueError(f"Invalid roles: {invalid_roles}")
            
            # Get current roles and validate removal
            current_roles = set(db_obj.role_names)
            roles_to_remove_set = set(roles_to_remove)
            
            # Ensure at least one role remains
            remaining_roles = current_roles - roles_to_remove_set
            if not remaining_roles:
                raise ValueError("Cannot remove all roles from a user")
            
            # Update permissions based on remaining roles
            all_permissions = set()
            for role in remaining_roles:
                role_enum = Role(role)
                role_permissions = ROLE_PERMISSIONS.get(role_enum, [])
                all_permissions.update(role_permissions)
            
            # Update the user
            update_data = {
                "role_names": list(remaining_roles),
                "permissions": list(all_permissions),
                "updated_at": datetime.utcnow()
            }
            
            return await super().update(db, db_obj=db_obj, obj_in=update_data)
            
        except Exception as e:
            raise ValueError(f"Error revoking user roles: {str(e)}")


# Create singleton instance
user = CRUDUser(User)

