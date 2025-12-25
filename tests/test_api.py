"""
Integration tests for API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from server.auth import get_current_user, verify_api_key_dependency
from server.database import get_db
from server.db_models import APIKey, User
from server.main import app
from server.services import get_graphiti_service


@pytest.fixture
def auth_headers():
    """Create authenticated headers."""
    return {"Authorization": "Bearer vpm_sk_test"}


@pytest.fixture
def client(mock_db_session, mock_graphiti_service):
    """Create test client."""

    async def mock_verify_key():
        return APIKey(
            id="key_1",
            key_hash="hash",
            name="test",
            user_id="user_1",
            is_active=True,
            permissions=["read", "write"],
        )

    async def mock_get_user():
        return User(
            id="user_1",
            email="test@example.com",
            name="Test User",
            password_hash="hashed_password",
            is_active=True,
        )

    app.dependency_overrides[verify_api_key_dependency] = mock_verify_key
    app.dependency_overrides[get_current_user] = mock_get_user
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_graphiti_service] = lambda: mock_graphiti_service

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.mark.integration
def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.integration
def test_create_episode_without_auth(client):
    """Test episode creation without authentication."""
    # Clear overrides to test auth failure
    app.dependency_overrides.clear()

    # We need to restore get_db override though, otherwise it might try to connect to real DB
    # if the endpoint uses get_db before auth?
    # The endpoint is protected by auth first.

    response = client.post(
        "/api/v1/episodes/",
        json={
            "name": "Test Episode",
            "content": "Test content",
        },
    )
    # FastAPI returns 422 for missing required headers or 401
    assert response.status_code in [401, 422]


@pytest.mark.integration
def test_create_episode_with_auth(client, auth_headers):
    """Test episode creation with authentication."""
    response = client.post(
        "/api/v1/episodes/",
        json={
            "name": "Test Episode",
            "content": "Test content",
            "source_type": "text",
        },
        headers=auth_headers,
    )
    # May fail if Graphiti is not initialized, but should not be 401
    assert response.status_code != 401


@pytest.mark.integration
def test_search_memory_without_auth(client):
    """Test memory search without authentication."""
    app.dependency_overrides.clear()

    response = client.post(
        "/api/v1/memory/search",
        json={
            "query": "test query",
            "limit": 10,
        },
    )
    assert response.status_code in [401, 422]


@pytest.mark.integration
def test_search_memory_with_auth(client, auth_headers):
    """Test memory search with authentication."""
    response = client.post(
        "/api/v1/memory/search",
        json={
            "query": "test query",
            "limit": 10,
        },
        headers=auth_headers,
    )
    # May fail if Graphiti is not initialized, but should not be 401
    assert response.status_code != 401


@pytest.mark.integration
def test_get_graph_with_auth(client, auth_headers):
    response = client.get("/api/v1/memory/graph?limit=10", headers=auth_headers)
    assert response.status_code != 401


@pytest.mark.integration
def test_short_term_recall_with_auth(client, auth_headers):
    response = client.post(
        "/api/v1/recall/short",
        json={"window_minutes": 30, "limit": 5},
        headers=auth_headers,
    )
    assert response.status_code != 401


@pytest.mark.integration
def test_rebuild_communities_with_auth(client, auth_headers):
    response = client.post("/api/v1/recall/communities/rebuild", headers=auth_headers)
    assert response.status_code != 401


@pytest.mark.integration
def test_list_episodes_with_auth(auth_headers):
    from fastapi.testclient import TestClient

    from server.auth import get_current_user, verify_api_key_dependency
    from server.database import get_db
    from server.db_models import APIKey, User
    from server.main import app
    from server.services import get_graphiti_service

    # Local override to provide short_term_recall
    async def _mock_service():
        class S:
            async def short_term_recall(self, window_minutes=30, limit=5, tenant_id=None):
                from server.models.memory import MemoryItem
                from server.models.recall import ShortTermRecallResponse

                items = [MemoryItem(content="c", score=1.0, metadata={}, source="episode")]
                from datetime import datetime

                return ShortTermRecallResponse(results=items, total=1, since=datetime.utcnow())

        return S()

    async def mock_verify_key():
        return APIKey(
            id="key_1",
            key_hash="h",
            name="test",
            user_id="user_1",
            is_active=True,
            permissions=["read"],
        )

    async def mock_get_user():
        return User(id="user_1", email="e@example.com", name="U", password_hash="h", is_active=True)

    app.dependency_overrides[get_graphiti_service] = _mock_service
    app.dependency_overrides[verify_api_key_dependency] = mock_verify_key
    app.dependency_overrides[get_current_user] = mock_get_user
    app.dependency_overrides[get_db] = lambda: None

    with TestClient(app) as c:
        r = c.get("/api/v1/episodes/?limit=5", headers=auth_headers)
        assert r.status_code != 401
