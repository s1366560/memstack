from unittest.mock import AsyncMock
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
    service.perform_incremental_refresh.return_value = {"status": "success"}
    service.deduplicate_entities.return_value = {"duplicates": 0}
    service.invalidate_stale_edges.return_value = {"removed": 0}
    service.get_maintenance_status.return_value = {"status": "healthy"}
    service.rebuild_communities.return_value = None
    return service


@pytest.mark.asyncio
async def test_incremental_refresh(mock_api_key_dependency, mock_graphiti_service):
    app.dependency_overrides[verify_api_key_dependency] = lambda: mock_api_key_dependency
    app.dependency_overrides[get_graphiti_service] = lambda: mock_graphiti_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/maintenance/refresh/incremental", json={"rebuild_communities": True}
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "success"}
    mock_graphiti_service.perform_incremental_refresh.assert_called_once()

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_deduplicate(mock_api_key_dependency, mock_graphiti_service):
    app.dependency_overrides[verify_api_key_dependency] = lambda: mock_api_key_dependency
    app.dependency_overrides[get_graphiti_service] = lambda: mock_graphiti_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/maintenance/deduplicate", json={"dry_run": True})

    assert response.status_code == status.HTTP_200_OK

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_optimize(mock_api_key_dependency, mock_graphiti_service):
    app.dependency_overrides[verify_api_key_dependency] = lambda: mock_api_key_dependency
    app.dependency_overrides[get_graphiti_service] = lambda: mock_graphiti_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/maintenance/optimize",
            json={
                "operations": ["incremental_refresh", "deduplicate", "rebuild_communities"],
                "dry_run": False,
            },
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["operations_run"]) == 3

    app.dependency_overrides = {}
