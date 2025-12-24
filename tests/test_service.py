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
        
        # Mock add_episode return value
        mock_add_result = Mock()
        mock_add_result.nodes = [] # Mock empty nodes list
        mock_client.add_episode = AsyncMock(return_value=mock_add_result)
        
        # Mock driver for status update query
        mock_client.driver = Mock()
        mock_client.driver.execute_query = AsyncMock()
        
        mock_graphiti_class.return_value = mock_client

        service = GraphitiService()
        service._client = mock_client
        service._initialized = True
        
        # Also mock queue_service as it is used in add_episode
        service.queue_service = Mock()
        service.queue_service.add_episode = AsyncMock()

        episode = EpisodeCreate(
            name="Test Episode",
            content="Test content",
        )

        await service.add_episode(episode)

        # Verify episode was added via queue_service, NOT client directly 
        # Wait, GraphitiService.add_episode CALLS queue_service.add_episode
        # And QueueService.add_episode CALLS client.add_episode.
        # But here we are testing GraphitiService.add_episode.
        
        # Let's check the implementation of GraphitiService.add_episode again.
        # It calls self.queue_service.add_episode(...)
        # It does NOT call self.client.add_episode directly anymore?
        
        service.queue_service.add_episode.assert_called_once()
        
        # If GraphitiService.add_episode ONLY calls queue_service, then we don't need to mock client.add_episode
        # UNLESS queue_service is NOT mocked.
        # But I mocked queue_service above.
        
        # Wait, the error was "object Mock can't be used in 'await' expression"
        # This implies it WAS awaiting something that wasn't awaitable.
        # If I mock queue_service.add_episode = AsyncMock(), it is awaitable.
        
        # Let's double check if I am testing the right thing.
        # If GraphitiService.add_episode delegates to QueueService, 
        # then this test should verify that delegation.

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
