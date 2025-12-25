"""
Test fixtures for server tests.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from server.auth import create_api_key, create_user


@pytest.fixture
async def mock_db_session():
    """Mock database session."""
    session = AsyncMock()
    # Mock execute result
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalars.return_value.all.return_value = []
    session.execute = AsyncMock(return_value=mock_result)
    return session


@pytest.fixture
async def test_user(mock_db_session):
    """Create a test user."""
    # Mock DB behavior if needed, but create_user just adds to session
    # and checks existence.

    user = await create_user(
        mock_db_session,
        email="test@example.com",
        name="Test User",
        password="testpassword",
    )
    return user


@pytest.fixture
async def test_api_key(test_user, mock_db_session):
    """Create a test API key."""
    plain_key, api_key_obj = await create_api_key(
        mock_db_session,
        user_id=test_user.id,
        name="Test API Key",
        permissions=["read", "write"],
    )
    return plain_key, api_key_obj


@pytest.fixture
def mock_graphiti_service():
    """Mock Graphiti service."""
    service = Mock()
    service.initialize = AsyncMock()
    service.close = AsyncMock()
    service.add_episode = AsyncMock()
    service.search = AsyncMock(return_value=[])
    service.get_graph_data = AsyncMock(return_value={"elements": {"nodes": [], "edges": []}})
    service.health_check = AsyncMock(return_value=True)
    return service
