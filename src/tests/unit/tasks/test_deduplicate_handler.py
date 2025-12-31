"""
Unit tests for DeduplicateEntitiesTaskHandler.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from graphiti_core.nodes import EntityNode


@pytest.mark.unit
class TestDeduplicateEntitiesTaskHandler:
    """Test cases for DeduplicateEntitiesTaskHandler."""

    def test_task_type_property(self):
        """Test task_type property returns correct value."""
        from src.application.tasks.deduplicate_entities import DeduplicateEntitiesTaskHandler

        handler = DeduplicateEntitiesTaskHandler()

        assert handler.task_type == "deduplicate_entities"

    def test_timeout_seconds_property(self):
        """Test timeout_seconds property returns correct value."""
        from src.application.tasks.deduplicate_entities import DeduplicateEntitiesTaskHandler

        handler = DeduplicateEntitiesTaskHandler()

        assert handler.timeout_seconds == 1800  # 30 minutes

    @pytest.mark.asyncio
    async def test_process_dry_run_mode(self):
        """Test deduplication in dry run mode."""
        from src.application.tasks.deduplicate_entities import DeduplicateEntitiesTaskHandler

        handler = DeduplicateEntitiesTaskHandler()

        # Mock queue service
        queue_service = Mock()
        queue_service._graphiti_client = Mock()
        queue_service._graphiti_client.driver = Mock()

        # Create mock entities
        entity1 = Mock(spec=EntityNode)
        entity1.uuid = "uuid1"
        entity1.name = "Test Entity"

        entity2 = Mock(spec=EntityNode)
        entity2.uuid = "uuid2"
        entity2.name = "Test Entity"  # Duplicate name

        # Mock EntityNode.get_by_group_ids
        with patch('src.application.tasks.deduplicate_entities.EntityNode.get_by_group_ids', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = [entity1, entity2]

            # Mock deduplication helpers
            with patch('src.application.tasks.deduplicate_entities._build_candidate_indexes') as mock_indexes, \
                 patch('src.application.tasks.deduplicate_entities._resolve_with_similarity') as mock_resolve:

                mock_indexes.return_value = {}

                # _resolve_with_similarity modifies state in-place, not by return value
                def side_effect_resolve(entities, indexes, state):
                    # No duplicates found - keep uuid_map empty
                    state.uuid_map = {}

                mock_resolve.side_effect = side_effect_resolve

                payload = {
                    "group_id": "test_group",
                    "similarity_threshold": 0.9,
                    "dry_run": True,
                    "project_id": "test_project",
                }

                # Should not raise
                await handler.process(payload, queue_service)

                # Verify entities were fetched
                mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_merge_mode(self):
        """Test actual merging in non-dry run mode."""
        from src.application.tasks.deduplicate_entities import DeduplicateEntitiesTaskHandler

        handler = DeduplicateEntitiesTaskHandler()

        queue_service = Mock()
        queue_service._graphiti_client = Mock()
        queue_service._graphiti_client.driver = Mock()
        queue_service._graphiti_client.driver.execute_query = AsyncMock()

        # Create mock entities with duplicates
        entity1 = Mock(spec=EntityNode)
        entity1.uuid = "original_uuid"
        entity1.name = "Entity"

        entity2 = Mock(spec=EntityNode)
        entity2.uuid = "duplicate_uuid"
        entity2.name = "Entity"

        with patch('src.application.tasks.deduplicate_entities.EntityNode.get_by_group_ids', new_callable=AsyncMock) as mock_get, \
             patch('src.application.tasks.deduplicate_entities._build_candidate_indexes') as mock_indexes, \
             patch('src.application.tasks.deduplicate_entities._resolve_with_similarity') as mock_resolve:

            mock_get.return_value = [entity1, entity2]
            mock_indexes.return_value = {}

            # _resolve_with_similarity modifies state in-place
            def side_effect_resolve(entities, indexes, state):
                # Simulate finding one duplicate: duplicate_uuid should be merged into original_uuid
                state.uuid_map = {"duplicate_uuid": "original_uuid"}

            mock_resolve.side_effect = side_effect_resolve

            payload = {
                "group_id": "test_group",
                "similarity_threshold": 0.9,
                "dry_run": False,  # Actual merge
                "project_id": "test_project",
            }

            # Patch _merge_entities to verify it's called
            with patch.object(handler, '_merge_entities', new_callable=AsyncMock) as mock_merge:
                await handler.process(payload, queue_service)

                # Verify merge was called - should be called once for duplicate_uuid -> original_uuid
                assert mock_merge.call_count == 1, f"Expected 1 merge call, got {mock_merge.call_count}"

                # Verify it was called with correct parameters
                mock_merge.assert_called_once_with(
                    queue_service._graphiti_client.driver,
                    "duplicate_uuid",
                    "original_uuid",
                    "test_project"
                )

    @pytest.mark.asyncio
    async def test_merge_entities_redirects_relationships(self):
        """Test that _merge_entities redirects relationships correctly."""
        from src.application.tasks.deduplicate_entities import DeduplicateEntitiesTaskHandler

        handler = DeduplicateEntitiesTaskHandler()

        mock_driver = Mock()
        mock_driver.execute_query = AsyncMock()

        duplicate_uuid = "duplicate_uuid"
        original_uuid = "original_uuid"
        project_id = "test_project"

        await handler._merge_entities(mock_driver, duplicate_uuid, original_uuid, project_id)

        # Verify execute_query was called for relationship redirection
        assert mock_driver.execute_query.call_count >= 3  # redirect, community, delete

    @pytest.mark.asyncio
    async def test_process_handles_insufficient_entities(self):
        """Test that process handles case with insufficient entities."""
        from src.application.tasks.deduplicate_entities import DeduplicateEntitiesTaskHandler

        handler = DeduplicateEntitiesTaskHandler()

        queue_service = Mock()
        queue_service._graphiti_client = Mock()
        queue_service._graphiti_client.driver = Mock()

        # Mock only one entity (not enough to deduplicate)
        entity1 = Mock(spec=EntityNode)
        entity1.uuid = "uuid1"
        entity1.name = "Only Entity"

        with patch('src.application.tasks.deduplicate_entities.EntityNode.get_by_group_ids', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = [entity1]

            payload = {
                "group_id": "test_group",
                "similarity_threshold": 0.9,
                "dry_run": True,
                "project_id": None,
            }

            # Should not raise
            await handler.process(payload, queue_service)

            # Should return early without processing
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_handles_merge_failure(self):
        """Test that merge failure is logged but doesn't stop other merges."""
        from src.application.tasks.deduplicate_entities import DeduplicateEntitiesTaskHandler

        handler = DeduplicateEntitiesTaskHandler()

        queue_service = Mock()
        queue_service._graphiti_client = Mock()
        queue_service._graphiti_client.driver = Mock()

        # Create mock entities
        entity1 = Mock(spec=EntityNode)
        entity1.uuid = "uuid1"
        entity1.name = "Entity 1"

        entity2 = Mock(spec=EntityNode)
        entity2.uuid = "uuid2"
        entity2.name = "Entity 2"

        entity3 = Mock(spec=EntityNode)
        entity3.uuid = "uuid3"
        entity3.name = "Entity 3"

        with patch('src.application.tasks.deduplicate_entities.EntityNode.get_by_group_ids', new_callable=AsyncMock) as mock_get, \
             patch('src.application.tasks.deduplicate_entities._build_candidate_indexes') as mock_indexes, \
             patch('src.application.tasks.deduplicate_entities._resolve_with_similarity') as mock_resolve:

            mock_get.return_value = [entity1, entity2, entity3]
            mock_indexes.return_value = {}

            # _resolve_with_similarity modifies state in-place
            def side_effect_resolve(entities, indexes, state):
                # Simulate two duplicate pairs (uuid2 and uuid3 both map to uuid1)
                state.uuid_map = {"uuid2": "uuid1", "uuid3": "uuid1"}

            mock_resolve.side_effect = side_effect_resolve

            payload = {
                "group_id": "test_group",
                "similarity_threshold": 0.9,
                "dry_run": False,
                "project_id": None,
            }

            # Mock _merge_entities to fail on first call, succeed on second
            call_count = [0]

            async def side_effect(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    raise Exception("Merge failed")
                # Second call succeeds

            with patch.object(handler, '_merge_entities', side_effect=side_effect):
                # Should not raise despite merge failure
                await handler.process(payload, queue_service)

                # Both merge attempts should have been made (uuid2->uuid1 and uuid3->uuid1)
                # Even though first fails, the handler logs and continues
                assert call_count[0] == 2, f"Expected 2 merge calls, got {call_count[0]}"

    @pytest.mark.asyncio
    async def test_process_preserves_project_metadata(self):
        """Test that project_id metadata is preserved during merge."""
        from src.application.tasks.deduplicate_entities import DeduplicateEntitiesTaskHandler

        handler = DeduplicateEntitiesTaskHandler()

        mock_driver = Mock()
        mock_driver.execute_query = AsyncMock()

        duplicate_uuid = "duplicate_uuid"
        original_uuid = "original_uuid"
        project_id = "test_project"

        await handler._merge_entities(mock_driver, duplicate_uuid, original_uuid, project_id)

        # Verify all three queries were called
        assert mock_driver.execute_query.call_count == 3

        # Check that the metadata query includes project_id preservation
        last_call_args = mock_driver.execute_query.call_args_list[-1]
        assert "project_id" in last_call_args[1]

    @pytest.mark.asyncio
    async def test_process_without_project_id(self):
        """Test merge behavior when project_id is None."""
        from src.application.tasks.deduplicate_entities import DeduplicateEntitiesTaskHandler

        handler = DeduplicateEntitiesTaskHandler()

        mock_driver = Mock()
        mock_driver.execute_query = AsyncMock()

        duplicate_uuid = "duplicate_uuid"
        original_uuid = "original_uuid"
        project_id = None  # No project_id

        await handler._merge_entities(mock_driver, duplicate_uuid, original_uuid, project_id)

        # Verify all three queries were still called
        assert mock_driver.execute_query.call_count == 3
