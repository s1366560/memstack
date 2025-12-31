"""
Unit tests for RebuildCommunityTaskHandler.

These tests verify project isolation in community operations.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, call
from graphiti_core.nodes import CommunityNode
from graphiti_core.edges import CommunityEdge


@pytest.mark.unit
class TestRebuildCommunityTaskHandler:
    """Test cases for RebuildCommunityTaskHandler."""

    def test_task_type_property(self):
        """Test task_type property returns correct value."""
        from src.application.tasks.community import RebuildCommunityTaskHandler

        handler = RebuildCommunityTaskHandler()

        assert handler.task_type == "rebuild_communities"

    def test_timeout_seconds_property(self):
        """Test timeout_seconds property returns correct value."""
        from src.application.tasks.community import RebuildCommunityTaskHandler

        handler = RebuildCommunityTaskHandler()

        assert handler.timeout_seconds == 3600  # 1 hour

    @pytest.mark.asyncio
    async def test_process_requires_task_group_id(self):
        """Test that task_group_id (project_id) is required."""
        from src.application.tasks.community import RebuildCommunityTaskHandler

        handler = RebuildCommunityTaskHandler()
        queue_service = Mock()

        # Test with missing task_group_id
        payload = {}  # No task_group_id

        with pytest.raises(ValueError, match="task_group_id.*is required"):
            await handler.process(payload, queue_service)

    @pytest.mark.asyncio
    async def test_project_isolation_in_remove_communities(self):
        """Test that remove query is called with correct group_id for project isolation."""
        from src.application.tasks.community import RebuildCommunityTaskHandler

        handler = RebuildCommunityTaskHandler()

        # Mock queue service
        queue_service = Mock()
        queue_service._graphiti_client = Mock()
        queue_service._graphiti_client.driver = Mock()
        queue_service._graphiti_client.driver.execute_query = AsyncMock()
        queue_service._graphiti_client.embedder = Mock()
        queue_service._graphiti_client.embedder.create = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
        queue_service._graphiti_client.llm_client = Mock()

        # Create mock community nodes
        mock_community = Mock(spec=CommunityNode)
        mock_community.uuid = "community_uuid_1"
        mock_community.group_id = "project_a"
        mock_community.generate_name_embedding = AsyncMock()
        mock_community.save = AsyncMock()

        # Mock the build_communities function
        with patch(
            "src.application.tasks.community.build_communities", new_callable=AsyncMock
        ) as mock_build:
            mock_build.return_value = ([mock_community], [])

            payload = {
                "task_group_id": "project_a",  # Renamed from group_id
                "project_id": "project_a",
                "tenant_id": "tenant_1",
            }

            await handler.process(payload, queue_service)

            # Verify that execute_query was called to remove communities for project_a
            # This ensures only communities from project_a are removed
            execute_query_calls = queue_service._graphiti_client.driver.execute_query.call_args_list
            remove_query_found = False
            for call_args in execute_query_calls:
                query_str = call_args[0][0] if call_args[0] else ""
                if "WHERE c.group_id = $group_id" in query_str and "DETACH DELETE c" in query_str:
                    remove_query_found = True
                    assert call_args[1]["group_id"] == "project_a"
                    break

            assert remove_query_found, "Should execute query to remove communities from project_a"

    @pytest.mark.asyncio
    async def test_project_isolation_in_build_communities(self):
        """Test that build_communities is called with correct group_ids for project isolation."""
        from src.application.tasks.community import RebuildCommunityTaskHandler

        handler = RebuildCommunityTaskHandler()

        # Mock queue service
        queue_service = Mock()
        queue_service._graphiti_client = Mock()
        queue_service._graphiti_client.driver = Mock()
        queue_service._graphiti_client.driver.execute_query = AsyncMock()
        queue_service._graphiti_client.embedder = Mock()
        queue_service._graphiti_client.embedder.create = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
        queue_service._graphiti_client.llm_client = Mock()

        # Create mock community nodes
        mock_community = Mock(spec=CommunityNode)
        mock_community.uuid = "community_uuid_1"
        mock_community.group_id = "project_b"
        mock_community.generate_name_embedding = AsyncMock()
        mock_community.save = AsyncMock()

        # Mock the build_communities function
        with patch(
            "src.application.tasks.community.build_communities", new_callable=AsyncMock
        ) as mock_build:
            mock_build.return_value = ([mock_community], [])

            payload = {
                "task_group_id": "project_b",  # Renamed from group_id
                "project_id": "project_b",
                "tenant_id": "tenant_2",
            }

            await handler.process(payload, queue_service)

            # Verify build_communities was called with group_ids=["project_b"]
            # This ensures only communities from project_b are built
            mock_build.assert_called_once_with(
                driver=queue_service._graphiti_client.driver,
                llm_client=queue_service._graphiti_client.llm_client,
                group_ids=["project_b"],
            )

    @pytest.mark.asyncio
    async def test_communities_do_not_affect_other_projects(self):
        """Test that rebuilding communities for one project doesn't affect another project."""
        from src.application.tasks.community import RebuildCommunityTaskHandler

        handler = RebuildCommunityTaskHandler()

        # Mock queue service
        queue_service = Mock()
        queue_service._graphiti_client = Mock()
        queue_service._graphiti_client.driver = Mock()
        queue_service._graphiti_client.driver.execute_query = AsyncMock()
        queue_service._graphiti_client.embedder = Mock()
        queue_service._graphiti_client.embedder.create = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
        queue_service._graphiti_client.llm_client = Mock()

        # Create mock community nodes for project_a
        mock_community_a = Mock(spec=CommunityNode)
        mock_community_a.uuid = "community_a_1"
        mock_community_a.group_id = "project_a"
        mock_community_a.generate_name_embedding = AsyncMock()
        mock_community_a.save = AsyncMock()

        # Mock the build_communities function
        with patch(
            "src.application.tasks.community.build_communities", new_callable=AsyncMock
        ) as mock_build:
            mock_build.return_value = ([mock_community_a], [])

            # Rebuild communities for project_a
            payload_a = {
                "task_group_id": "project_a",  # Renamed from group_id
                "project_id": "project_a",
                "tenant_id": "tenant_1",
            }

            await handler.process(payload_a, queue_service)

            # Verify that only project_a communities were affected
            # The remove query should filter by group_id = "project_a"
            execute_query_calls = queue_service._graphiti_client.driver.execute_query.call_args_list
            remove_query_found = False
            for call_args in execute_query_calls:
                query_str = call_args[0][0] if call_args[0] else ""
                if "WHERE c.group_id = $group_id" in query_str and "DETACH DELETE c" in query_str:
                    remove_query_found = True
                    assert call_args[1]["group_id"] == "project_a"
                    break

            assert remove_query_found, "Should only remove communities from project_a"

            # build_communities should be called with group_ids=["project_a"]
            build_call_args = mock_build.call_args
            assert build_call_args[1]["group_ids"] == ["project_a"], (
                "Should only build communities for project_a"
            )

            # project_b communities should not be affected
            # (This is verified by the scoped group_ids parameter)

    @pytest.mark.asyncio
    async def test_project_id_set_on_communities(self):
        """Test that project_id is correctly set on communities."""
        from src.application.tasks.community import RebuildCommunityTaskHandler

        handler = RebuildCommunityTaskHandler()

        # Mock queue service
        queue_service = Mock()
        queue_service._graphiti_client = Mock()
        queue_service._graphiti_client.driver = Mock()
        queue_service._graphiti_client.driver.execute_query = AsyncMock()
        queue_service._graphiti_client.embedder = Mock()
        queue_service._graphiti_client.embedder.create = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
        queue_service._graphiti_client.llm_client = Mock()

        # Create mock community node
        mock_community = Mock(spec=CommunityNode)
        mock_community.uuid = "community_uuid_1"
        mock_community.group_id = "test_project"
        mock_community.generate_name_embedding = AsyncMock()
        mock_community.save = AsyncMock()

        with patch(
            "src.application.tasks.community.build_communities", new_callable=AsyncMock
        ) as mock_build:
            mock_build.return_value = ([mock_community], [])

            payload = {
                "task_group_id": "test_project",  # Renamed from group_id
                "project_id": "test_project",
                "tenant_id": "test_tenant",
            }

            await handler.process(payload, queue_service)

            # Verify that project_id is set (via execute_query)
            execute_query_calls = (
                queue_service._graphiti_client.driver.execute_query.call_args_list
            )

            # Find the query that sets project_id
            project_id_query_found = False
            for call_args in execute_query_calls:
                query_str = call_args[0][0] if call_args[0] else ""
                if "c.project_id = c.group_id" in query_str:
                    project_id_query_found = True
                    # Verify it's called with the correct uuid
                    assert call_args[1]["uuid"] == mock_community.uuid
                    break

            assert project_id_query_found, "project_id should be set on community"

    @pytest.mark.asyncio
    async def test_member_count_calculation(self):
        """Test that member_count is calculated correctly."""
        from src.application.tasks.community import RebuildCommunityTaskHandler

        handler = RebuildCommunityTaskHandler()

        # Mock queue service
        queue_service = Mock()
        queue_service._graphiti_client = Mock()
        queue_service._graphiti_client.driver = Mock()
        queue_service._graphiti_client.driver.execute_query = AsyncMock()
        queue_service._graphiti_client.embedder = Mock()
        queue_service._graphiti_client.embedder.create = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
        queue_service._graphiti_client.llm_client = Mock()

        # Create mock community and edges
        mock_community = Mock(spec=CommunityNode)
        mock_community.uuid = "community_uuid_1"
        mock_community.group_id = "test_project"
        mock_community.generate_name_embedding = AsyncMock()
        mock_community.save = AsyncMock()

        mock_edge = Mock(spec=CommunityEdge)
        mock_edge.save = AsyncMock()

        with patch(
            "src.application.tasks.community.build_communities", new_callable=AsyncMock
        ) as mock_build:
            mock_build.return_value = ([mock_community], [mock_edge])

            payload = {
                "task_group_id": "test_project",  # Renamed from group_id
                "project_id": "test_project",
                "tenant_id": "test_tenant",
            }

            await handler.process(payload, queue_service)

            # Verify member_count query is executed
            execute_query_calls = (
                queue_service._graphiti_client.driver.execute_query.call_args_list
            )

            # Find the member_count calculation query
            member_count_query_found = False
            for call_args in execute_query_calls:
                query_str = call_args[0][0] if call_args[0] else ""
                if "c.member_count = member_count" in query_str:
                    member_count_query_found = True
                    assert call_args[1]["uuid"] == mock_community.uuid
                    break

            assert member_count_query_found, "member_count should be calculated"

    @pytest.mark.asyncio
    async def test_logging_messages_include_project_context(self):
        """Test that log messages include project context for debugging."""
        from src.application.tasks.community import RebuildCommunityTaskHandler
        import logging
        from unittest.mock import MagicMock

        handler = RebuildCommunityTaskHandler()

        # Mock queue service
        queue_service = Mock()
        queue_service._graphiti_client = Mock()
        queue_service._graphiti_client.driver = Mock()
        queue_service._graphiti_client.driver.execute_query = AsyncMock()
        queue_service._graphiti_client.embedder = Mock()
        queue_service._graphiti_client.embedder.create = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
        queue_service._graphiti_client.llm_client = Mock()

        # Create mock community
        mock_community = Mock(spec=CommunityNode)
        mock_community.uuid = "community_uuid_1"
        mock_community.group_id = "my_project"
        mock_community.generate_name_embedding = AsyncMock()
        mock_community.save = AsyncMock()

        with patch(
            "src.application.tasks.community.build_communities", new_callable=AsyncMock
        ) as mock_build:
            mock_build.return_value = ([mock_community], [])

            payload = {
                "task_group_id": "my_project",  # Renamed from group_id
                "project_id": "my_project",
                "tenant_id": "tenant_1",
            }

            # Capture log output
            with patch("src.application.tasks.community.logger") as mock_logger:
                await handler.process(payload, queue_service)

                # Verify that log messages include project context
                log_calls = mock_logger.info.call_args_list

                # Check that at least one log message mentions the project
                project_mentioned = any("my_project" in str(call) for call in log_calls)

                assert project_mentioned, "Log messages should include project context"
