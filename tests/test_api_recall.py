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


@pytest.mark.asyncio
async def test_short_term_recall(mock_graphiti_service, mock_api_key_dependency):
    app.dependency_overrides[get_graphiti_service] = lambda: mock_graphiti_service
    app.dependency_overrides[verify_api_key_dependency] = lambda: mock_api_key_dependency

    # Mock response
    from datetime import datetime

    mock_response = {
        "results": [{"content": "mem1", "score": 1.0, "source": "episode", "metadata": {}}],
        "total": 1,
        "since": datetime.utcnow().isoformat(),
    }
    mock_graphiti_service.short_term_recall = AsyncMock(return_value=mock_response)

    payload = {"window_minutes": 60, "limit": 10, "tenant_id": "tenant-1"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/recall/short", json=payload)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == mock_response
    assert mock_graphiti_service.short_term_recall.called

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_rebuild_communities(mock_graphiti_service, mock_api_key_dependency):
    app.dependency_overrides[get_graphiti_service] = lambda: mock_graphiti_service
    app.dependency_overrides[verify_api_key_dependency] = lambda: mock_api_key_dependency

    mock_graphiti_service.rebuild_communities = AsyncMock(return_value=None)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/recall/communities/rebuild")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "ok"
    assert mock_graphiti_service.rebuild_communities.called

    app.dependency_overrides = {}
