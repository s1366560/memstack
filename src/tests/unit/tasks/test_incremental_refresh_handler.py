"""
Unit tests for IncrementalRefreshTaskHandler.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from src.application.tasks.incremental_refresh import IncrementalRefreshTaskHandler
from graphiti_core.nodes import EpisodicNode


@pytest.mark.unit
class TestIncrementalRefreshTaskHandler:
    """Test cases for IncrementalRefreshTaskHandler."""

    def test_task_type_property(self):
        """Test task_type property returns correct value."""
        handler = IncrementalRefreshTaskHandler()

        assert handler.task_type == "incremental_refresh"

    def test_timeout_seconds_property(self):
        """Test timeout_seconds property returns correct value."""
        handler = IncrementalRefreshTaskHandler()

        assert handler.timeout_seconds == 3600  # 1 hour

    @pytest.mark.asyncio
    async def test_process_with_specific_episode_uuids(self):
        """Test processing specific episode UUIDs."""
        handler = IncrementalRefreshTaskHandler()

        # Mock queue service
        queue_service = Mock()
        queue_service._graphiti_client = Mock()
        queue_service._graphiti_client.driver = Mock()
        queue_service._graphiti_client.driver.execute_query = AsyncMock()
        queue_service._graphiti_client.add_episode = AsyncMock()
        queue_service._schema_loader = AsyncMock(return_value=(None, None, None))
        queue_service._sync_schema_from_graph_result = AsyncMock()

        # Mock episode from database
        mock_episode = Mock(spec=EpisodicNode)
        mock_episode.uuid = "episode_uuid_1"
        mock_episode.name = "Test Episode"
        mock_episode.content = "Test content"
        mock_episode.source_description = "text"
        mock_episode.source = "text"
        mock_episode.valid_at = datetime.now(timezone.utc)

        # Mock add_episode result
        mock_add_result = Mock()
        mock_add_result.nodes = []
        mock_add_result.edges = []
        queue_service._graphiti_client.add_episode.return_value = mock_add_result

        # Mock EpisodicNode.get_by_uuids to return our mock episode
        with patch('src.application.tasks.incremental_refresh.EpisodicNode.get_by_uuids', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = [mock_episode]

            payload = {
                "group_id": "test_group",
                "episode_uuids": ["episode_uuid_1"],
                "rebuild_communities": False,
                "project_id": "test_project",
                "tenant_id": "test_tenant",
                "user_id": "test_user",
            }

            # Should not raise
            await handler.process(payload, queue_service)

            # Verify add_episode was called
            queue_service._graphiti_client.add_episode.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_with_recent_episodes(self):
        """Test processing recent episodes when no UUIDs provided."""
        handler = IncrementalRefreshTaskHandler()

        queue_service = Mock()
        queue_service._graphiti_client = Mock()
        queue_service._graphiti_client.driver = Mock()
        queue_service._graphiti_client.driver.execute_query = AsyncMock()
        queue_service._graphiti_client.add_episode = AsyncMock()
        queue_service._schema_loader = AsyncMock(return_value=(None, None, None))
        queue_service._sync_schema_from_graph_result = AsyncMock()

        # Mock retrieve_episodes result
        mock_episode = Mock(spec=EpisodicNode)
        mock_episode.uuid = "episode_uuid_1"
        mock_episode.name = "Recent Episode"
        mock_episode.content = "Recent content"
        mock_episode.source_description = "text"
        mock_episode.source = "text"
        mock_episode.valid_at = datetime.now(timezone.utc)

        mock_add_result = Mock()
        mock_add_result.nodes = []
        mock_add_result.edges = []
        queue_service._graphiti_client.add_episode.return_value = mock_add_result

        with patch('src.application.tasks.incremental_refresh.retrieve_episodes', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = [mock_episode]

            payload = {
                "group_id": "test_group",
                "episode_uuids": None,  # No specific UUIDs
                "rebuild_communities": False,
                "project_id": None,
                "tenant_id": None,
                "user_id": None,
            }

            await handler.process(payload, queue_service)

            # Verify retrieve_episodes was called
            mock_retrieve.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_with_rebuild_communities(self):
        """Test processing with community rebuild enabled."""
        handler = IncrementalRefreshTaskHandler()

        queue_service = Mock()
        queue_service._graphiti_client = Mock()
        queue_service._graphiti_client.driver = Mock()
        queue_service._graphiti_client.driver.execute_query = AsyncMock()
        queue_service._graphiti_client.add_episode = AsyncMock()
        queue_service.rebuild_communities = AsyncMock()
        queue_service._schema_loader = AsyncMock(return_value=(None, None, None))
        queue_service._sync_schema_from_graph_result = AsyncMock()

        mock_episode = Mock(spec=EpisodicNode)
        mock_episode.uuid = "episode_uuid_1"
        mock_episode.name = "Test Episode"
        mock_episode.content = "Test content"
        mock_episode.source_description = "text"
        mock_episode.source = "text"
        mock_episode.valid_at = datetime.now(timezone.utc)

        mock_add_result = Mock()
        mock_add_result.nodes = []
        mock_add_result.edges = []
        queue_service._graphiti_client.add_episode.return_value = mock_add_result

        with patch('src.application.tasks.incremental_refresh.retrieve_episodes', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = [mock_episode]

            payload = {
                "group_id": "test_group",
                "episode_uuids": None,
                "rebuild_communities": True,  # Enable community rebuild
                "project_id": None,
                "tenant_id": None,
                "user_id": None,
            }

            await handler.process(payload, queue_service)

            # Verify rebuild_communities was called with task_group_id
            queue_service.rebuild_communities.assert_called_once_with(task_group_id="test_group")

    @pytest.mark.asyncio
    async def test_propagate_metadata(self):
        """Test that metadata is propagated to episodes and entities."""
        handler = IncrementalRefreshTaskHandler()

        queue_service = Mock()
        queue_service._graphiti_client = Mock()
        queue_service._graphiti_client.driver = Mock()
        queue_service._graphiti_client.driver.execute_query = AsyncMock()
        queue_service._graphiti_client.add_episode = AsyncMock()
        queue_service._schema_loader = AsyncMock(return_value=(None, None, None))
        queue_service._sync_schema_from_graph_result = AsyncMock()

        mock_episode = Mock(spec=EpisodicNode)
        mock_episode.uuid = "episode_uuid_1"
        mock_episode.name = "Test Episode"
        mock_episode.content = "Test content"
        mock_episode.source_description = "text"
        mock_episode.source = "text"
        mock_episode.valid_at = datetime.now(timezone.utc)

        mock_add_result = Mock()
        mock_add_result.nodes = []
        mock_add_result.edges = []
        queue_service._graphiti_client.add_episode.return_value = mock_add_result

        with patch('src.application.tasks.incremental_refresh.retrieve_episodes', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = [mock_episode]

            payload = {
                "group_id": "test_group",
                "episode_uuids": None,
                "rebuild_communities": False,
                "project_id": "test_project",
                "tenant_id": "test_tenant",
                "user_id": "test_user",
            }

            await handler.process(payload, queue_service)

            # Verify metadata propagation query was executed
            # Should be called once for each episode
            execute_query_calls = [
                call for call in queue_service._graphiti_client.driver.execute_query.call_args_list
                if len(call[0]) > 0 and 'MATCH (ep:Episodic' in str(call[0][0])
            ]

            assert len(execute_query_calls) > 0, "Metadata propagation query should be executed"

    @pytest.mark.asyncio
    async def test_process_handles_schema_load_failure(self):
        """Test that schema load failure doesn't stop processing."""
        handler = IncrementalRefreshTaskHandler()

        queue_service = Mock()
        queue_service._graphiti_client = Mock()
        queue_service._graphiti_client.driver = Mock()
        queue_service._graphiti_client.driver.execute_query = AsyncMock()
        queue_service._graphiti_client.add_episode = AsyncMock()
        queue_service._sync_schema_from_graph_result = AsyncMock()
        queue_service._schema_loader = AsyncMock(side_effect=Exception("Schema load failed"))

        mock_episode = Mock(spec=EpisodicNode)
        mock_episode.uuid = "episode_uuid_1"
        mock_episode.name = "Test Episode"
        mock_episode.content = "Test content"
        mock_episode.source_description = "text"
        mock_episode.source = "text"
        mock_episode.valid_at = datetime.now(timezone.utc)

        mock_add_result = Mock()
        mock_add_result.nodes = []
        mock_add_result.edges = []
        queue_service._graphiti_client.add_episode.return_value = mock_add_result

        with patch('src.application.tasks.incremental_refresh.retrieve_episodes', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = [mock_episode]

            payload = {
                "group_id": "test_group",
                "episode_uuids": None,
                "rebuild_communities": False,
                "project_id": "test_project",
                "tenant_id": None,
                "user_id": None,
            }

            # Should not raise despite schema load failure
            await handler.process(payload, queue_service)

            # Verify processing continued
            queue_service._graphiti_client.add_episode.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_handles_add_episode_failure(self):
        """Test that add_episode failure is properly propagated."""
        handler = IncrementalRefreshTaskHandler()

        queue_service = Mock()
        queue_service._graphiti_client = Mock()
        queue_service._graphiti_client.driver = Mock()
        queue_service._graphiti_client.driver.execute_query = AsyncMock()
        queue_service._graphiti_client.add_episode = AsyncMock(side_effect=Exception("Add episode failed"))
        queue_service._schema_loader = AsyncMock(return_value=(None, None, None))

        mock_episode = Mock(spec=EpisodicNode)
        mock_episode.uuid = "episode_uuid_1"
        mock_episode.name = "Test Episode"
        mock_episode.content = "Test content"
        mock_episode.source_description = "text"
        mock_episode.source = "text"
        mock_episode.valid_at = datetime.now(timezone.utc)

        with patch('src.application.tasks.incremental_refresh.retrieve_episodes', new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = [mock_episode]

            payload = {
                "group_id": "test_group",
                "episode_uuids": None,
                "rebuild_communities": False,
                "project_id": None,
                "tenant_id": None,
                "user_id": None,
            }

            # Should raise the exception
            with pytest.raises(Exception, match="Add episode failed"):
                await handler.process(payload, queue_service)
