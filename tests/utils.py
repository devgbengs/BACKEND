import pytest
from typing import AsyncGenerator
import httpx
from httpx import AsyncClient
from fastapi import FastAPI
from main import app

@pytest.fixture(scope="function")
async def async_client(event_loop) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for your FastAPI application."""
    async with AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
        await ac.aclose()