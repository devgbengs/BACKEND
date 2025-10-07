from typing import Optional, List, Dict
from sqlmodel import SQLModel
from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    STAFF = "staff"
    USER = "user"

# Role permissions mapping
ROLE_PERMISSIONS: Dict[Role, List[str]] = {
    Role.ADMIN: ["admin:all", "manage:users", "manage:roles", "manage:system"],
    Role.MANAGER: ["manage:items", "view:reports", "manage:staff", "view:analytics"],
    Role.STAFF: ["create:items", "edit:items", "view:items", "basic:reports"],
    Role.USER: ["view:items", "view:basic"]
}

# Role descriptions
ROLE_DESCRIPTIONS: Dict[Role, str] = {
    Role.ADMIN: "Full administrative access within the tenant",
    Role.MANAGER: "Can manage items, staff, and view reports",
    Role.STAFF: "Can create and edit items, view basic reports",
    Role.USER: "Basic access with item viewing permissions"
}

# Permission descriptions for documentation
PERMISSION_DESCRIPTIONS: Dict[str, str] = {
    "admin:all": "Full administrative access",
    "manage:users": "Can manage user accounts",
    "manage:roles": "Can assign and revoke roles",
    "manage:system": "Can configure system settings",
    "manage:items": "Can manage inventory items",
    "view:reports": "Can view all reports",
    "manage:staff": "Can manage staff members",
    "view:analytics": "Can view analytics data",
    "create:items": "Can create new items",
    "edit:items": "Can edit existing items",
    "view:items": "Can view items",
    "basic:reports": "Can view basic reports",
    "view:basic": "Basic viewing permissions"
}

class RoleCreate(SQLModel):
    name: str
    description: Optional[str] = None
    tenant_id: Optional[int] = None
    permissions: List[str] = []

class RoleUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    
class RoleResponse(SQLModel):
    role: Role
    permissions: List[str]
    description: str

    class Config:
        json_schema_extra = {
            "example": {
                "role": "admin",
                "permissions": ["admin:all", "manage:users", "manage:roles"],
                "description": "Full administrative access within the tenant"
            }
        }

class UserRoleUpdate(SQLModel):
    """Schema for updating user roles"""
    roles_to_add: List[Role]

    class Config:
        json_schema_extra = {
            "example": {
                "roles_to_add": ["manager", "staff"]
            }
        }

class UserRoleRevoke(SQLModel):
    """Schema for revoking user roles"""
    roles_to_remove: List[Role]

    class Config:
        json_schema_extra = {
            "example": {
                "roles_to_remove": ["manager", "staff"]
            }
        }