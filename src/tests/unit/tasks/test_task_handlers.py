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
    async def test_process_calls_remove_and_build_communities(self):
        """Test that process calls remove_communities and build_communities with project isolation."""
        from unittest.mock import patch
        from graphiti_core.utils.maintenance.community_operations import (
            remove_communities,
            build_communities,
        )

        handler = RebuildCommunityTaskHandler()

        queue_service = Mock()
        mock_graphiti_client = Mock()
        mock_graphiti_client.driver = Mock()
        mock_graphiti_client.driver.execute_query = AsyncMock()
        mock_graphiti_client.llm_client = Mock()
        mock_graphiti_client.embedder = Mock()

        # Mock community nodes and edges
        mock_community_node = Mock()
        mock_community_node.uuid = "test_uuid"
        mock_community_node.group_id = "global"
        mock_community_node.generate_name_embedding = AsyncMock()
        mock_community_node.save = AsyncMock()

        mock_edge = Mock()
        mock_edge.save = AsyncMock()

        queue_service._graphiti_client = mock_graphiti_client

        payload = {"group_id": "global"}

        with (
            patch(
                "src.application.tasks.community.remove_communities", new_callable=AsyncMock
            ) as mock_remove,
            patch(
                "src.application.tasks.community.build_communities", new_callable=AsyncMock
            ) as mock_build,
        ):
            mock_build.return_value = ([mock_community_node], [mock_edge])

            # Should not raise
            await handler.process(payload, queue_service)

            # Verify remove_communities was called with group_ids for project isolation
            mock_remove.assert_called_once_with(mock_graphiti_client.driver, group_ids=["global"])

            # Verify build_communities was called with group_ids for project isolation
            mock_build.assert_called_once_with(
                driver=mock_graphiti_client.driver,
                llm_client=mock_graphiti_client.llm_client,
                group_ids=["global"],
            )

    @pytest.mark.asyncio
    async def test_process_generates_embeddings_and_saves_communities(self):
        """Test that process generates embeddings and sets project_id."""
        from unittest.mock import patch, AsyncMock as ImportedAsyncMock

        handler = RebuildCommunityTaskHandler()

        queue_service = Mock()
        mock_graphiti_client = Mock()
        mock_graphiti_client.driver = Mock()
        mock_graphiti_client.driver.execute_query = AsyncMock()
        mock_graphiti_client.llm_client = Mock()
        mock_graphiti_client.embedder = Mock()

        # Mock community node
        mock_community_node = Mock()
        mock_community_node.uuid = "test_uuid"
        mock_community_node.group_id = "test_group"
        mock_community_node.generate_name_embedding = AsyncMock()
        mock_community_node.save = AsyncMock()

        mock_edge = Mock()
        mock_edge.save = AsyncMock()

        queue_service._graphiti_client = mock_graphiti_client

        payload = {"group_id": "test_group"}

        with (
            patch("src.application.tasks.community.remove_communities", new_callable=AsyncMock),
            patch(
                "src.application.tasks.community.build_communities", new_callable=AsyncMock
            ) as mock_build,
        ):
            mock_build.return_value = ([mock_community_node], [mock_edge])

            await handler.process(payload, queue_service)

            # Verify embedding was generated
            mock_community_node.generate_name_embedding.assert_called_once_with(
                mock_graphiti_client.embedder
            )

            # Verify community was saved
            mock_community_node.save.assert_called_once()

            # Verify project_id was set
            mock_graphiti_client.driver.execute_query.assert_called()

    @pytest.mark.asyncio
    async def test_process_calculates_member_count(self):
        """Test that process calculates member_count with Neo4j 5.x syntax."""
        from unittest.mock import patch

        handler = RebuildCommunityTaskHandler()

        queue_service = Mock()
        mock_graphiti_client = Mock()
        mock_graphiti_client.driver = Mock()
        mock_graphiti_client.driver.execute_query = AsyncMock()
        mock_graphiti_client.llm_client = Mock()
        mock_graphiti_client.embedder = Mock()

        mock_community_node = Mock()
        mock_community_node.uuid = "community_uuid"
        mock_community_node.group_id = "test_group"
        mock_community_node.generate_name_embedding = AsyncMock()
        mock_community_node.save = AsyncMock()

        mock_edge = Mock()
        mock_edge.save = AsyncMock()

        queue_service._graphiti_client = mock_graphiti_client

        payload = {"group_id": "test_group"}

        with (
            patch("src.application.tasks.community.remove_communities", new_callable=AsyncMock),
            patch(
                "src.application.tasks.community.build_communities", new_callable=AsyncMock
            ) as mock_build,
        ):
            mock_build.return_value = ([mock_community_node], [mock_edge])

            await handler.process(payload, queue_service)

            # Verify execute_query was called to set member_count
            # Should be called at least once (for project_id and member_count)
            assert mock_graphiti_client.driver.execute_query.call_count >= 2
