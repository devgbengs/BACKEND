import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from tests.utils.auth import create_test_user, create_test_superuser
from model.models import User

@pytest.mark.asyncio
async def test_delete_user_success(
    client: AsyncClient,
    session: AsyncSession
):
    """Test successful user deletion by admin"""
    # Create admin user
    admin = await create_test_user(
        session, 
        role_names=["admin"],
        email="admin@test.com"
    )
    
    # Create regular user to delete
    user_to_delete = await create_test_user(
        session,
        tenant_id=admin.tenant_id,
        email="delete@test.com"
    )
    
    # Delete user
    response = await client.delete(
        f"/api/endpoints/users/{user_to_delete.id}",
        headers={"Authorization": f"Bearer {admin.token}"}
    )
    assert response.status_code == 200
    
    # Verify user is deleted
    statement = select(User).where(User.id == user_to_delete.id)
    result = await session.execute(statement)
    assert result.first() is None

@pytest.mark.asyncio
async def test_delete_user_by_superuser(
    client: AsyncClient,
    session: AsyncSession
):
    """Test successful user deletion by superuser"""
    # Create superuser
    superuser = await create_test_superuser(session)
    
    # Create regular user to delete
    user_to_delete = await create_test_user(
        session,
        tenant_id=superuser.tenant_id,
        email="delete@test.com"
    )
    
    # Delete user
    response = await client.delete(
        f"/api/endpoints/users/{user_to_delete.id}",
        headers={"Authorization": f"Bearer {superuser.token}"}
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_delete_superuser_by_admin_fails(
    client: AsyncClient,
    session: AsyncSession
):
    """Test that admin cannot delete superuser"""
    # Create admin user
    admin = await create_test_user(
        session, 
        role_names=["admin"],
        email="admin@test.com"
    )
    
    # Create superuser to attempt to delete
    superuser = await create_test_superuser(
        session,
        tenant_id=admin.tenant_id
    )
    
    # Attempt to delete superuser
    response = await client.delete(
        f"/api/endpoints/users/{superuser.id}",
        headers={"Authorization": f"Bearer {admin.token}"}
    )
    assert response.status_code == 403
    assert "Only superusers can delete other superusers" in response.json()["detail"]

@pytest.mark.asyncio
async def test_delete_user_from_different_tenant_fails(
    client: AsyncClient,
    session: AsyncSession
):
    """Test that users cannot be deleted from different tenants"""
    # Create admin user in tenant 1
    admin = await create_test_user(
        session, 
        role_names=["admin"],
        tenant_id=1,
        email="admin@test.com"
    )
    
    # Create user in tenant 2
    user_to_delete = await create_test_user(
        session,
        tenant_id=2,
        email="delete@test.com"
    )
    
    # Attempt to delete user from different tenant
    response = await client.delete(
        f"/api/endpoints/users/{user_to_delete.id}",
        headers={"Authorization": f"Bearer {admin.token}"}
    )
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]

@pytest.mark.asyncio
async def test_delete_self_fails(
    client: AsyncClient,
    session: AsyncSession
):
    """Test that users cannot delete themselves"""
    # Create admin user
    admin = await create_test_user(
        session, 
        role_names=["admin"],
        email="admin@test.com"
    )
    
    # Attempt to delete self
    response = await client.delete(
        f"/api/endpoints/users/{admin.id}",
        headers={"Authorization": f"Bearer {admin.token}"}
    )
    assert response.status_code == 400
    assert "Cannot delete yourself" in response.json()["detail"]