from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from server.auth import verify_api_key_dependency
from server.db_models import APIKey
from server.main import app
from server.services import get_graphiti_service


@pytest.fixture
def mock_api_key_dependency(test_user):
    return APIKey(
        id=str(uuid4()),
        key_hash="hash",
        name="test-key",
        user_id=test_user.id,
        permissions=["read", "write"],
    )


@pytest.fixture
def mock_episode_data():
    return {
        "content": "Test Episode Content",
        "source": "web",
        "source_id": "test-source",
        "context": {"key": "value"},
    }


@pytest.mark.asyncio
async def test_create_episode(mock_graphiti_service, mock_api_key_dependency, mock_episode_data):
    app.dependency_overrides[get_graphiti_service] = lambda: mock_graphiti_service
    app.dependency_overrides[verify_api_key_dependency] = lambda: mock_api_key_dependency

    # Mock return value of add_episode
    mock_episode_response = Mock()
    mock_episode_response.id = str(uuid4())
    mock_episode_response.created_at = "2023-01-01T00:00:00Z"
    mock_graphiti_service.add_episode.return_value = mock_episode_response

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/episodes/", json=mock_episode_data)

    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.json()
    assert data["id"] == str(mock_episode_response.id)
    assert data["status"] == "processing"

    assert mock_graphiti_service.add_episode.called

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_health_check(mock_graphiti_service):
    app.dependency_overrides[get_graphiti_service] = lambda: mock_graphiti_service

    mock_graphiti_service.health_check.return_value = True

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/episodes/health")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "healthy"

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_health_check_unhealthy(mock_graphiti_service):
    app.dependency_overrides[get_graphiti_service] = lambda: mock_graphiti_service

    mock_graphiti_service.health_check.return_value = False

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/episodes/health")

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    app.dependency_overrides = {}
