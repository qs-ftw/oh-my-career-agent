"""Shared pytest fixtures for the CareerAgent backend test suite."""

from __future__ import annotations

import asyncio

import pytest

# We import the FastAPI app.  Adjust the import path once main.py exists.
# from src.main import app


@pytest.fixture(scope="session")
def event_loop() -> asyncio.AbstractEventLoop:
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Uncomment once src.main.app is available:
#
# @pytest_asyncio.fixture
# async def client() -> AsyncGenerator[AsyncClient, None]:
#     """Provide an async HTTP test client wired to the FastAPI app."""
#     transport = ASGITransport(app=app)
#     async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
#         yield ac
#
#
# @pytest_asyncio.fixture
# async def test_db():
#     """Provide a clean test database (rollback after each test)."""
#     # Will be implemented once database.py and models are in place.
#     yield
