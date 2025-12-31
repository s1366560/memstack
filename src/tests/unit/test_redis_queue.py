"""
Unit tests for Redis Queue Service.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from src.infrastructure.adapters.secondary.queue.redis_queue import QueueService


@pytest.mark.unit
class TestQueueService:
    """Test cases for QueueService."""

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test queue initialization."""
        with patch('src.infrastructure.adapters.secondary.queue.redis_queue.redis.from_url') as mock_redis:
            from graphiti_core import Graphiti
            mock_graphiti = Mock(spec=Graphiti)
            mock_client = Mock()
            mock_redis.return_value = mock_client

            service = QueueService()
            await service.initialize(graphiti_client=mock_graphiti, run_workers=False)

            assert service._redis is not None
            assert service._graphiti_client == mock_graphiti

    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing the queue connection."""
        with patch('src.infrastructure.adapters.secondary.queue.redis_queue.redis.from_url') as mock_redis:
            from graphiti_core import Graphiti
            mock_graphiti = Mock(spec=Graphiti)
            mock_client = Mock()
            mock_redis.return_value = mock_client
            mock_client.close = AsyncMock()

            service = QueueService()
            await service.initialize(graphiti_client=mock_graphiti, run_workers=False)
            await service.close()

            mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_episode(self):
        """Test adding an episode to the queue."""
        with patch('src.infrastructure.adapters.secondary.queue.redis_queue.redis.from_url') as mock_redis:
            from graphiti_core import Graphiti
            mock_graphiti = Mock(spec=Graphiti)
            mock_client = Mock()
            mock_redis.return_value = mock_client
            mock_client.sadd = AsyncMock()
            mock_client.rpush = AsyncMock()
            mock_client.llen = AsyncMock(return_value=1)

            service = QueueService()
            await service.initialize(graphiti_client=mock_graphiti, run_workers=False)

            result = await service.add_episode(
                group_id="group_123",
                name="Test Episode",
                content="Test content",
                source_description="text",
                episode_type="text",
                entity_types=[],
                uuid="episode_123",
                tenant_id="tenant_123",
                project_id="project_123",
                user_id="user_123",
                memory_id="memory_123",
            )

            # Verify redis calls were made
            mock_client.sadd.assert_called_once()
            mock_client.rpush.assert_called_once()
            assert result == 1

    @pytest.mark.asyncio
    async def test_get_queue_size(self):
        """Test getting queue size for a group."""
        with patch('src.infrastructure.adapters.secondary.queue.redis_queue.redis.from_url') as mock_redis:
            from graphiti_core import Graphiti
            mock_graphiti = Mock(spec=Graphiti)
            mock_client = Mock()
            mock_redis.return_value = mock_client
            mock_client.llen = AsyncMock(return_value=5)

            service = QueueService()
            await service.initialize(graphiti_client=mock_graphiti, run_workers=False)

            size = await service.get_queue_size("group_123")

            assert size == 5
            mock_client.llen.assert_called_once_with("queue:group:group_123")

    @pytest.mark.asyncio
    async def test_rebuild_communities(self):
        """Test adding rebuild communities task to queue."""
        with patch('src.infrastructure.adapters.secondary.queue.redis_queue.redis.from_url') as mock_redis:
            from graphiti_core import Graphiti
            mock_graphiti = Mock(spec=Graphiti)
            mock_client = Mock()
            mock_redis.return_value = mock_client
            mock_client.sadd = AsyncMock()
            mock_client.rpush = AsyncMock()
            mock_client.llen = AsyncMock(return_value=1)

            service = QueueService()
            await service.initialize(graphiti_client=mock_graphiti, run_workers=False)

            result = await service.rebuild_communities(task_group_id="group_123")

            # Verify redis calls were made
            mock_client.sadd.assert_called_once()
            mock_client.rpush.assert_called_once()
            # result should be a task_id (UUID string), not queue length
            assert isinstance(result, str)
            assert len(result) == 36  # UUID format

    @pytest.mark.asyncio
    async def test_retry_task_no_redis(self):
        """Test retrying when redis not initialized."""
        service = QueueService()
        result = await service.retry_task("task_123")

        assert result is False

    @pytest.mark.asyncio
    async def test_retry_task_exception_handling(self):
        """Test retry task handles exceptions gracefully."""
        with patch('src.infrastructure.adapters.secondary.queue.redis_queue.redis.from_url') as mock_redis:
            from graphiti_core import Graphiti
            mock_graphiti = Mock(spec=Graphiti)
            mock_client = Mock()
            mock_redis.return_value = mock_client

            service = QueueService()
            await service.initialize(graphiti_client=mock_graphiti, run_workers=False)

            # Force an exception by not properly mocking database
            # The method should catch and return False
            result = await service.retry_task("task_123")

            # Should return False on error rather than raising
            assert result is False

    @pytest.mark.asyncio
    async def test_stop_task(self):
        """Test stopping a task."""
        with patch('src.infrastructure.adapters.secondary.queue.redis_queue.redis.from_url') as mock_redis:
            from graphiti_core import Graphiti
            mock_graphiti = Mock(spec=Graphiti)
            mock_client = Mock()
            mock_redis.return_value = mock_client

            service = QueueService()
            await service.initialize(graphiti_client=mock_graphiti, run_workers=False)

            with patch.object(service, '_update_task_log', AsyncMock()):
                result = await service.stop_task("task_123")

                assert result is True

    @pytest.mark.asyncio
    async def test_get_queue_size_no_redis(self):
        """Test getting queue size when redis not initialized."""
        service = QueueService()
        size = await service.get_queue_size("group_123")

        assert size == 0

    @pytest.mark.asyncio
    async def test_add_episode_no_redis(self):
        """Test adding episode when redis not initialized."""
        service = QueueService()

        with pytest.raises(RuntimeError, match="Queue service not initialized"):
            await service.add_episode(
                group_id="group_123",
                name="Test Episode",
                content="Test content",
                source_description="text",
                episode_type="text",
                entity_types=[],
                uuid="episode_123",
            )
