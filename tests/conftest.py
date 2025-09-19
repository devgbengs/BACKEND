# pytest configuration file
import os
import sys
import asyncio
from typing import AsyncGenerator, Generator
from sqlmodel.ext.asyncio.session import AsyncSession
import pytest
from sqlalchemy.orm import selectinload

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_async_session

@pytest.fixture(scope="session")
def event_loop():
    """Override pytest-asyncio event loop to prevent it from closing."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def setup_test_loop(event_loop):
    """Set up the test loop for each test case."""
    asyncio.set_event_loop(event_loop)
    yield
    # No need to close loop here, it will be handled by event_loop fixture

@pytest.fixture(scope="function")
async def db_session(event_loop) -> AsyncGenerator[AsyncSession, None]:
    """Get a test database session."""
    async for session in get_async_session():
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()