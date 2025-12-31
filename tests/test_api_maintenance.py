import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, Mock

from src.infrastructure.adapters.primary.web.main import app
from src.infrastructure.adapters.primary.web.dependencies import (
    get_current_user,
    get_graphiti_client,
    get_queue_service
)
from src.infrastructure.adapters.secondary.persistence.models import User

@pytest.fixture
def mock_user():
    user = Mock(spec=User)
    user.id = "user-123"
    user.project_id = "project-123"
    user.tenant_id = "tenant-123"
    return user

@pytest.fixture
def mock_graphiti_client():
    client = Mock()
    client.driver = Mock()
    client.driver.execute_query = AsyncMock()
    return client

@pytest.fixture
def mock_queue_service():
    service = Mock()
    service.incremental_refresh = AsyncMock(return_value="task-refresh")
    service.deduplicate_entities = AsyncMock(return_value="task-dedupe")
    service.rebuild_communities = AsyncMock(return_value="task-rebuild")
    return service

@pytest.mark.asyncio
async def test_incremental_refresh(mock_user, mock_graphiti_client, mock_queue_service):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_graphiti_client] = lambda: mock_graphiti_client
    app.dependency_overrides[get_queue_service] = lambda: mock_queue_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/maintenance/refresh/incremental",
            json={"rebuild_communities": True}
        )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["task_id"] == "task-refresh"
    mock_queue_service.incremental_refresh.assert_called_once()

    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_deduplicate_dry_run(mock_user, mock_graphiti_client, mock_queue_service):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_graphiti_client] = lambda: mock_graphiti_client
    app.dependency_overrides[get_queue_service] = lambda: mock_queue_service

    # Mock execute_query for dry run
    mock_result = Mock()
    mock_result.records = []
    mock_graphiti_client.driver.execute_query.return_value = mock_result

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/maintenance/deduplicate",
            json={"dry_run": True}
        )

    assert response.status_code == 200
    assert response.json()["dry_run"] is True
    mock_queue_service.deduplicate_entities.assert_not_called()

    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_deduplicate_actual(mock_user, mock_graphiti_client, mock_queue_service):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_graphiti_client] = lambda: mock_graphiti_client
    app.dependency_overrides[get_queue_service] = lambda: mock_queue_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/maintenance/deduplicate",
            json={"dry_run": False}
        )

    assert response.status_code == 200
    assert response.json()["task_id"] == "task-dedupe"
    mock_queue_service.deduplicate_entities.assert_called_once()

    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_optimize_graph(mock_user, mock_graphiti_client, mock_queue_service):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_graphiti_client] = lambda: mock_graphiti_client
    app.dependency_overrides[get_queue_service] = lambda: mock_queue_service

    # Mock query result for invalidate_edges
    mock_result = Mock()
    mock_result.records = [{"deleted": 5}]
    # We need to ensure records can be accessed by index or iterator
    # Mock return value behavior for execute_query
    
    # Since execute_query is called multiple times (potentially), we can make it return a generic mock
    # that has .records which is a list of dict-like objects
    mock_graphiti_client.driver.execute_query.return_value = mock_result

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/maintenance/optimize",
            json={
                "operations": ["incremental_refresh", "deduplicate", "invalidate_edges", "rebuild_communities"],
                "dry_run": False
            }
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["operations_run"]) == 4
    
    # Verify calls
    mock_queue_service.incremental_refresh.assert_called()
    mock_queue_service.deduplicate_entities.assert_called()
    mock_queue_service.rebuild_communities.assert_called()
    mock_graphiti_client.driver.execute_query.assert_called()

    app.dependency_overrides = {}
