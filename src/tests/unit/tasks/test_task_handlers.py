"""
Unit tests for task handlers and registry.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from src.application.tasks.registry import TaskRegistry
from src.application.tasks.episode import EpisodeTaskHandler
from src.application.tasks.community import RebuildCommunityTaskHandler


@pytest.mark.unit
class TestTaskRegistry:
    """Test cases for TaskRegistry."""

    def test_register_handler(self):
        """Test registering a task handler."""
        registry = TaskRegistry()
        handler = Mock()
        handler.task_type = "test_task"

        registry.register(handler)

        assert registry.get_handler("test_task") == handler

    def test_register_multiple_handlers(self):
        """Test registering multiple task handlers."""
        registry = TaskRegistry()
        handler1 = Mock()
        handler1.task_type = "task1"
        handler2 = Mock()
        handler2.task_type = "task2"

        registry.register(handler1)
        registry.register(handler2)

        assert registry.get_handler("task1") == handler1
        assert registry.get_handler("task2") == handler2

    def test_get_handler_not_found(self):
        """Test getting a non-existent handler."""
        registry = TaskRegistry()
        handler = registry.get_handler("nonexistent")

        assert handler is None

    def test_get_all_handlers(self):
        """Test getting all registered handlers."""
        registry = TaskRegistry()
        handler1 = Mock()
        handler1.task_type = "task1"
        handler2 = Mock()
        handler2.task_type = "task2"

        registry.register(handler1)
        registry.register(handler2)

        handlers = registry.get_all_handlers()

        assert len(handlers) == 2
        assert handlers["task1"] == handler1
        assert handlers["task2"] == handler2


@pytest.mark.unit
class TestEpisodeTaskHandler:
    """Test cases for EpisodeTaskHandler."""

    def test_task_type_property(self):
        """Test task_type property returns correct value."""
        handler = EpisodeTaskHandler()

        assert handler.task_type == "add_episode"

    @pytest.mark.asyncio
    async def test_process_basic_episode(self):
        """Test processing a basic episode task."""
        handler = EpisodeTaskHandler()

        # Mock queue service
        queue_service = Mock()
        queue_service._graphiti_client = AsyncMock()
        queue_service._graphiti_client.add_episode = AsyncMock()
        queue_service._graphiti_client.driver = Mock()
        queue_service._graphiti_client.driver.execute_query = AsyncMock()
        queue_service._update_memory_status = AsyncMock()
        queue_service._sync_schema_from_graph_result = AsyncMock()
        queue_service._schema_loader = None

        # Mock add_episode result
        mock_result = Mock()
        mock_result.nodes = []
        mock_result.edges = []
        queue_service._graphiti_client.add_episode.return_value = mock_result

        payload = {
            "uuid": "test_uuid",
            "group_id": "test_group",
            "name": "Test Episode",
            "content": "Test content",
            "source_description": "text",
            "episode_type": "text",
        }

        # Should not raise
        await handler.process(payload, queue_service)

        # Verify add_episode was called
        queue_service._graphiti_client.add_episode.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_with_memory_id(self):
        """Test processing episode with memory_id updates status."""
        handler = EpisodeTaskHandler()

        queue_service = Mock()
        queue_service._graphiti_client = AsyncMock()
        queue_service._graphiti_client.add_episode = AsyncMock()
        queue_service._graphiti_client.driver = Mock()
        queue_service._graphiti_client.driver.execute_query = AsyncMock()
        queue_service._update_memory_status = AsyncMock()
        queue_service._sync_schema_from_graph_result = AsyncMock()
        queue_service._schema_loader = None

        mock_result = Mock()
        mock_result.nodes = []
        mock_result.edges = []
        queue_service._graphiti_client.add_episode.return_value = mock_result

        payload = {
            "uuid": "test_uuid",
            "group_id": "test_group",
            "memory_id": "memory_123",
            "name": "Test",
            "content": "Content",
            "source_description": "text",
            "episode_type": "text",
        }

        await handler.process(payload, queue_service)

        # Verify memory status was updated
        queue_service._update_memory_status.assert_called()


@pytest.mark.unit
class TestRebuildCommunityTaskHandler:
    """Test cases for RebuildCommunityTaskHandler."""

    def test_task_type_property(self):
        """Test task_type property returns correct value."""
        handler = RebuildCommunityTaskHandler()

        assert handler.task_type == "rebuild_communities"

    def test_timeout_seconds_property(self):
        """Test timeout_seconds property returns correct value."""
        handler = RebuildCommunityTaskHandler()

        assert handler.timeout_seconds == 3600

    @pytest.mark.asyncio
    async def test_process_global_group(self):
        """Test processing rebuild_communities for global group."""
        handler = RebuildCommunityTaskHandler()

        queue_service = Mock()
        queue_service._graphiti_client = Mock()
        queue_service._graphiti_client.build_communities = AsyncMock()
        queue_service._graphiti_client.driver = Mock()
        queue_service._graphiti_client.driver.execute_query = AsyncMock()

        payload = {"group_id": "global"}

        # Should not raise
        await handler.process(payload, queue_service)

        # Verify build_communities was called with None (for all groups)
        queue_service._graphiti_client.build_communities.assert_called_once_with(group_ids=None)

    @pytest.mark.asyncio
    async def test_process_specific_group(self):
        """Test processing rebuild_communities for specific group."""
        handler = RebuildCommunityTaskHandler()

        queue_service = Mock()
        queue_service._graphiti_client = Mock()
        queue_service._graphiti_client.build_communities = AsyncMock()
        queue_service._graphiti_client.driver = Mock()
        queue_service._graphiti_client.driver.execute_query = AsyncMock()

        payload = {"group_id": "project_123"}

        await handler.process(payload, queue_service)

        # Verify build_communities was called with specific group
        queue_service._graphiti_client.build_communities.assert_called_once_with(group_ids=["project_123"])

    @pytest.mark.asyncio
    async def test_process_executes_metadata_queries(self):
        """Test that metadata queries are executed after rebuild."""
        handler = RebuildCommunityTaskHandler()

        queue_service = Mock()
        queue_service._graphiti_client = Mock()
        queue_service._graphiti_client.build_communities = AsyncMock()
        queue_service._graphiti_client.driver = Mock()
        queue_service._graphiti_client.driver.execute_query = AsyncMock()

        payload = {"group_id": "global"}

        await handler.process(payload, queue_service)

        # Verify multiple queries were executed (tenant, project, member_count)
        assert queue_service._graphiti_client.driver.execute_query.call_count == 3
