import pytest
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from core.config import settings
from crud.user.crud_user import user
from tests.utils import async_client

pytestmark = pytest.mark.asyncio

# Using async_client fixture from utils.py

@pytest.fixture(autouse=True)
async def cleanup(db_session: AsyncSession):
    # Setup
    await db_session.execute("TRUNCATE users CASCADE")
    await db_session.commit()
    
    yield  # This is where the test runs

    # Teardown
    await db_session.execute("TRUNCATE users CASCADE")
    await db_session.commit()

async def test_login_access_token_success(async_client: AsyncClient, db_session: AsyncSession):
    # First, try to find and delete the existing user if it exists
    existing_user = await user.get_user_by_email(db_session, "test@example.com")
    if existing_user:
        await db_session.delete(existing_user)
        await db_session.commit()
    
    # Create a test user
    test_user_data = {
        "email": "test@example.com",
        "user_name": "testuser",
        "password": "testpassword",
        "is_active": True
    }
    await user.create_user(db=db_session, user_data=test_user_data)
    
    # Try to login
    response = await async_client.post(
        f"{settings.API_V1_STR}/auth/login/access-token",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
    )
    
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"

async def test_login_access_token_invalid_credentials(async_client: AsyncClient):
    response = await async_client.post(
        f"{settings.API_V1_STR}/auth/login/access-token",
        data={
            "username": "wrong@example.com",
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect email or password"

async def test_login_access_token_inactive_user(async_client: AsyncClient, db_session: AsyncSession):
    # Create an inactive test user
    test_user_data = {
        "email": "inactive@example.com",
        "user_name": "inactiveuser",
        "password": "testpassword",
        "is_active": False
    }
    await user.create_user(db=db_session, user_data=test_user_data)
    
    # Try to login
    response = await async_client.post(
        f"{settings.API_V1_STR}/auth/login/access-token",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
    )
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Inactive user"