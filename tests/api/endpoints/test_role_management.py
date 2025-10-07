import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from tests.utils.auth import create_test_user, create_test_superuser
from model.models import User

@pytest.mark.asyncio
async def test_promote_user_roles_success(
    client: AsyncClient,
    session: AsyncSession
):
    """Test successful role promotion by admin"""
    # Create admin user
    admin = await create_test_user(
        session, 
        role_names=["admin"],
        email="admin@test.com"
    )
    
    # Create regular user to promote
    user_to_promote = await create_test_user(
        session,
        tenant_id=admin.tenant_id,
        email="promote@test.com",
        role_names=["user"]
    )
    
    # Add manager role
    response = await client.post(
        f"/api/endpoints/users/{user_to_promote.id}/roles",
        json={"roles_to_add": ["manager"]},
        headers={"Authorization": f"Bearer {admin.token}"}
    )
    assert response.status_code == 200
    
    # Verify user has both roles
    updated_user = response.json()
    assert "user" in updated_user["role_names"]
    assert "manager" in updated_user["role_names"]
    assert len(updated_user["role_names"]) == 2

@pytest.mark.asyncio
async def test_promote_to_admin_by_non_admin_fails(
    client: AsyncClient,
    session: AsyncSession
):
    """Test that non-admin users cannot promote to admin role"""
    # Create manager user
    manager = await create_test_user(
        session, 
        role_names=["manager"],
        email="manager@test.com"
    )
    
    # Create regular user
    user_to_promote = await create_test_user(
        session,
        tenant_id=manager.tenant_id,
        email="promote@test.com",
        role_names=["user"]
    )
    
    # Attempt to add admin role
    response = await client.post(
        f"/api/endpoints/users/{user_to_promote.id}/roles",
        json={"roles_to_add": ["admin"]},
        headers={"Authorization": f"Bearer {manager.token}"}
    )
    assert response.status_code == 403
    assert "Only admins can grant admin role" in response.json()["detail"]

@pytest.mark.asyncio
async def test_revoke_user_roles_success(
    client: AsyncClient,
    session: AsyncSession
):
    """Test successful role revocation by admin"""
    # Create admin user
    admin = await create_test_user(
        session, 
        role_names=["admin"],
        email="admin@test.com"
    )
    
    # Create user with multiple roles
    user_to_update = await create_test_user(
        session,
        tenant_id=admin.tenant_id,
        email="update@test.com",
        role_names=["user", "staff", "manager"]
    )
    
    # Remove manager role
    response = await client.delete(
        f"/api/endpoints/users/{user_to_update.id}/roles",
        json={"roles_to_remove": ["manager"]},
        headers={"Authorization": f"Bearer {admin.token}"}
    )
    assert response.status_code == 200
    
    # Verify roles were updated correctly
    updated_user = response.json()
    assert "user" in updated_user["role_names"]
    assert "staff" in updated_user["role_names"]
    assert "manager" not in updated_user["role_names"]
    assert len(updated_user["role_names"]) == 2

@pytest.mark.asyncio
async def test_revoke_all_roles_fails(
    client: AsyncClient,
    session: AsyncSession
):
    """Test that removing all roles from a user fails"""
    # Create admin user
    admin = await create_test_user(
        session, 
        role_names=["admin"],
        email="admin@test.com"
    )
    
    # Create user with single role
    user_to_update = await create_test_user(
        session,
        tenant_id=admin.tenant_id,
        email="update@test.com",
        role_names=["user"]
    )
    
    # Attempt to remove only role
    response = await client.delete(
        f"/api/endpoints/users/{user_to_update.id}/roles",
        json={"roles_to_remove": ["user"]},
        headers={"Authorization": f"Bearer {admin.token}"}
    )
    assert response.status_code == 400
    assert "Cannot remove all roles from a user" in response.json()["detail"]

@pytest.mark.asyncio
async def test_superuser_can_manage_admin_roles(
    client: AsyncClient,
    session: AsyncSession
):
    """Test that superusers can manage admin roles"""
    # Create superuser
    superuser = await create_test_superuser(session)
    
    # Create user to promote
    user_to_promote = await create_test_user(
        session,
        tenant_id=superuser.tenant_id,
        email="promote@test.com",
        role_names=["user"]
    )
    
    # Add admin role
    response = await client.post(
        f"/api/endpoints/users/{user_to_promote.id}/roles",
        json={"roles_to_add": ["admin"]},
        headers={"Authorization": f"Bearer {superuser.token}"}
    )
    assert response.status_code == 200
    
    # Verify admin role was added
    updated_user = response.json()
    assert "admin" in updated_user["role_names"]
    
    # Remove admin role
    response = await client.delete(
        f"/api/endpoints/users/{user_to_promote.id}/roles",
        json={"roles_to_remove": ["admin"]},
        headers={"Authorization": f"Bearer {superuser.token}"}
    )
    assert response.status_code == 200
    
    # Verify admin role was removed
    updated_user = response.json()
    assert "admin" not in updated_user["role_names"]

@pytest.mark.asyncio
async def test_cross_tenant_role_management_fails(
    client: AsyncClient,
    session: AsyncSession
):
    """Test that users cannot manage roles across tenants"""
    # Create admin in tenant 1
    admin = await create_test_user(
        session, 
        role_names=["admin"],
        tenant_id=1,
        email="admin@test.com"
    )
    
    # Create user in tenant 2
    other_tenant_user = await create_test_user(
        session,
        tenant_id=2,
        email="user@test.com",
        role_names=["user"]
    )
    
    # Attempt to add role
    response = await client.post(
        f"/api/endpoints/users/{other_tenant_user.id}/roles",
        json={"roles_to_add": ["manager"]},
        headers={"Authorization": f"Bearer {admin.token}"}
    )
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]