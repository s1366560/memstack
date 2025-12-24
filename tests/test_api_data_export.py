from unittest.mock import AsyncMock, Mock
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
def mock_graphiti_service():
    service = AsyncMock()
    service.export_data.return_value = {"episodes": []}
    service.get_graph_stats.return_value = {"entities": 10}

    # Mock the client driver for cleanup
    mock_driver = AsyncMock()

    # Mock result records
    mock_record = {"count": 5, "deleted": 5}
    mock_result = Mock()
    mock_result.records = [mock_record]

    mock_driver.execute_query.return_value = mock_result

    service.client.driver = mock_driver
    return service


@pytest.mark.asyncio
async def test_export_data(mock_api_key_dependency, mock_graphiti_service):
    app.dependency_overrides[verify_api_key_dependency] = lambda: mock_api_key_dependency
    app.dependency_overrides[get_graphiti_service] = lambda: mock_graphiti_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/data/export", json={"include_episodes": True})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"episodes": []}
    mock_graphiti_service.export_data.assert_called_once()

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_get_stats(mock_api_key_dependency, mock_graphiti_service):
    app.dependency_overrides[verify_api_key_dependency] = lambda: mock_api_key_dependency
    app.dependency_overrides[get_graphiti_service] = lambda: mock_graphiti_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/data/stats")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"entities": 10}

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_cleanup_dry_run(mock_api_key_dependency, mock_graphiti_service):
    app.dependency_overrides[verify_api_key_dependency] = lambda: mock_api_key_dependency
    app.dependency_overrides[get_graphiti_service] = lambda: mock_graphiti_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/data/cleanup?dry_run=true&older_than_days=30")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["dry_run"] is True
    assert data["would_delete"] == 5

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_cleanup_execute(mock_api_key_dependency, mock_graphiti_service):
    app.dependency_overrides[verify_api_key_dependency] = lambda: mock_api_key_dependency
    app.dependency_overrides[get_graphiti_service] = lambda: mock_graphiti_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/data/cleanup?dry_run=false&older_than_days=30")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["dry_run"] is False
    assert data["deleted"] == 5

    app.dependency_overrides = {}
