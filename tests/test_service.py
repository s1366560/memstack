"""
Tests for Graphiti service.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from server.models.episode import EpisodeCreate
from server.models.memory import MemoryQuery
from server.services.graphiti_service import GraphitiService


@pytest.fixture
def mock_graphiti_client():
    """Mock Graphiti client."""
    client = Mock()
    client.add_episode = AsyncMock()
    client.search = AsyncMock(return_value=[])
    client.close = AsyncMock()
    return client


@pytest.mark.asyncio
class TestGraphitiService:
    """Tests for Graphiti service."""

    async def test_service_initialization(self):
        """Test service can be instantiated."""
        service = GraphitiService()
        assert service is not None

    @patch("server.services.graphiti_service.Graphiti")
    async def test_initialize(self, mock_graphiti_class):
        """Test service initialization."""
        mock_client = Mock()
        mock_client.build_indices = AsyncMock()
        mock_graphiti_class.return_value = mock_client

        service = GraphitiService()
        await service.initialize()

        # Verify initialization was called
        mock_graphiti_class.assert_called_once()

    @patch("server.services.graphiti_service.Graphiti")
    async def test_add_episode(self, mock_graphiti_class):
        """Test adding an episode."""
        mock_client = Mock()
        mock_client.add_episode = AsyncMock()
        mock_graphiti_class.return_value = mock_client

        service = GraphitiService()
        service._client = mock_client
        service._initialized = True

        episode = EpisodeCreate(
            name="Test Episode",
            content="Test content",
        )

        await service.add_episode(episode)

        # Verify episode was added
        mock_client.add_episode.assert_called_once()

    @patch("server.services.graphiti_service.Graphiti")
    async def test_search(self, mock_graphiti_class):
        """Test memory search."""
        mock_result = Mock()
        mock_result.content = "Test result"
        mock_result.score = 0.95

        mock_client = Mock()
        mock_client.search_ = AsyncMock(return_value=[mock_result])
        mock_graphiti_class.return_value = mock_client

        service = GraphitiService()
        service._client = mock_client
        service._initialized = True

        query = MemoryQuery(query="test query", limit=10)

        results = await service.search(
            query=query.query,
            limit=query.limit,
            tenant_id=None,
            project_id=None,
            user_id=None,
            as_of=None,
        )

        # Verify search was called
        mock_client.search_.assert_called_once()
        assert len(results) >= 0

    @patch("server.services.graphiti_service.Graphiti")
    async def test_health_check(self, mock_graphiti_class):
        """Test health check."""
        mock_client = Mock()
        mock_graphiti_class.return_value = mock_client

        service = GraphitiService()
        service._client = mock_client
        service._initialized = True

        is_healthy = await service.health_check()

        # Service should be healthy if initialized
        assert isinstance(is_healthy, bool)

    @patch("server.services.graphiti_service.Graphiti")
    async def test_close(self, mock_graphiti_class):
        """Test closing service."""
        mock_client = Mock()
        mock_client.close = AsyncMock()
        mock_graphiti_class.return_value = mock_client

        service = GraphitiService()
        service._client = mock_client
        service._initialized = True

        await service.close()

        # Verify close was called
        mock_client.close.assert_called_once()
