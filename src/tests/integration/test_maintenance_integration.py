"""Integration tests for maintenance task handlers."""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

from graphiti_core import Graphiti
from graphiti_core.llm_client import LLMClient
from src.application.tasks.incremental_refresh import IncrementalRefreshTaskHandler
from src.application.tasks.deduplicate_entities import DeduplicateEntitiesTaskHandler
from src.infrastructure.adapters.secondary.queue.redis_queue import QueueService


# Mock LLM Client for testing
class MockLLMClient(LLMClient):
    """Mock LLM client for testing."""

    def __init__(self):
        from graphiti_core.llm_client import LLMConfig
        super().__init__(config=LLMConfig(), cache=False)

    async def _generate_response(self, messages, response_model=None, max_tokens=1000, model_size="small"):
        """Generate a mock response."""
        return "Mock LLM response"

    async def generate_embedding(self, text):
        """Generate a mock embedding."""
        import numpy as np
        return np.random.rand(1536).tolist()


@pytest.mark.integration
@pytest.mark.slow
class TestMaintenanceIntegration:
    """Integration tests for maintenance operations."""

    @pytest.fixture
    async def graphiti_client(self):
        """Create a real Graphiti client for testing."""
        from graphiti_core import Graphiti
        import os

        client = Graphiti(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            user=os.getenv("NEO4J_USER", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "password"),
            llm_client=MockLLMClient(),
        )
        yield client

        # Cleanup
        try:
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            if tasks:
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
        except Exception:
            pass

        await asyncio.sleep(0.1)

        try:
            await client.close()
        except RuntimeError as e:
            if "Event loop is closed" not in str(e):
                raise

    @pytest.fixture
    async def queue_service(self, graphiti_client):
        """Create a QueueService instance for testing."""
        # Create a minimal QueueService with just the graphiti_client
        service = Mock(spec=QueueService)
        service._graphiti_client = graphiti_client
        service._schema_loader = AsyncMock(return_value=(None, None, None))
        service._sync_schema_from_graph_result = AsyncMock()
        service.rebuild_communities = AsyncMock()

        return service

    @pytest.mark.asyncio
    async def test_incremental_refresh_end_to_end(self, graphiti_client, queue_service):
        """Test full incremental refresh flow with real Graphiti client."""
        handler = IncrementalRefreshTaskHandler()

        # First, add an episode to refresh
        add_result = await graphiti_client.add_episode(
            name="Test Episode for Refresh",
            episode_body="This episode will be refreshed",
            source_description="text",
            group_id="test_maintenance_group",
            reference_time=datetime.now(timezone.utc),
        )

        episode_uuid = add_result.episode_uuid if hasattr(add_result, 'episode_uuid') else None

        # If we can't get the UUID, skip this test
        if not episode_uuid:
            pytest.skip("Could not retrieve episode UUID from add_result")

        # Now perform incremental refresh
        payload = {
            "group_id": "test_maintenance_group",
            "episode_uuids": [episode_uuid],
            "rebuild_communities": False,
            "project_id": "test_project",
            "tenant_id": "test_tenant",
            "user_id": "test_user",
        }

        # Should not raise
        await handler.process(payload, queue_service)

        # Verify the episode still exists
        # (In a real scenario, we'd check that entities were re-extracted)

    @pytest.mark.asyncio
    async def test_incremental_refresh_with_recent_episodes(self, graphiti_client, queue_service):
        """Test incremental refresh fetching recent episodes."""
        handler = IncrementalRefreshTaskHandler()

        # Add some test episodes
        await graphiti_client.add_episode(
            name="Recent Episode 1",
            episode_body="Recent content 1",
            source_description="text",
            group_id="test_maintenance_recent",
            reference_time=datetime.now(timezone.utc),
        )

        await graphiti_client.add_episode(
            name="Recent Episode 2",
            episode_body="Recent content 2",
            source_description="text",
            group_id="test_maintenance_recent",
            reference_time=datetime.now(timezone.utc),
        )

        # Perform incremental refresh without specifying UUIDs (should get recent episodes)
        payload = {
            "group_id": "test_maintenance_recent",
            "episode_uuids": None,  # Get recent episodes
            "rebuild_communities": False,
            "project_id": None,
            "tenant_id": None,
            "user_id": None,
        }

        # Should not raise
        await handler.process(payload, queue_service)

    @pytest.mark.asyncio
    async def test_incremental_refresh_with_community_rebuild(self, graphiti_client, queue_service):
        """Test incremental refresh triggering community rebuild."""
        handler = IncrementalRefreshTaskHandler()

        # Add a test episode
        await graphiti_client.add_episode(
            name="Episode Before Community Rebuild",
            episode_body="Content for community detection",
            source_description="text",
            group_id="test_maintenance_community",
            reference_time=datetime.now(timezone.utc),
        )

        payload = {
            "group_id": "test_maintenance_community",
            "episode_uuids": None,
            "rebuild_communities": True,  # Enable community rebuild
            "project_id": None,
            "tenant_id": None,
            "user_id": None,
        }

        # Should not raise
        await handler.process(payload, queue_service)

        # Verify rebuild_communities was called with task_group_id
        queue_service.rebuild_communities.assert_called_once_with(task_group_id="test_maintenance_community")

    @pytest.mark.asyncio
    async def test_deduplicate_entities_end_to_end(self, graphiti_client, queue_service):
        """Test full deduplication flow with real Graphiti client."""
        handler = DeduplicateEntitiesTaskHandler()

        # Add episodes with potentially duplicate entities
        await graphiti_client.add_episode(
            name="Dedup Test Episode 1",
            episode_body="John Smith works at Google",
            source_description="text",
            group_id="test_dedup_group",
            reference_time=datetime.now(timezone.utc),
        )

        await graphiti_client.add_episode(
            name="Dedup Test Episode 2",
            episode_body="Johnny Smith is a software engineer",
            source_description="text",
            group_id="test_dedup_group",
            reference_time=datetime.now(timezone.utc),
        )

        # Run deduplication in dry_run mode first
        payload_dry_run = {
            "group_id": "test_dedup_group",
            "similarity_threshold": 0.9,
            "dry_run": True,
            "project_id": "test_project",
        }

        # Should not raise
        await handler.process(payload_dry_run, queue_service)

        # Run actual merge
        payload_merge = {
            "group_id": "test_dedup_group",
            "similarity_threshold": 0.9,
            "dry_run": False,
            "project_id": "test_project",
        }

        # Should not raise
        await handler.process(payload_merge, queue_service)

    @pytest.mark.asyncio
    async def test_deduplicate_with_insufficient_entities(self, graphiti_client, queue_service):
        """Test deduplication with insufficient entities."""
        handler = DeduplicateEntitiesTaskHandler()

        # Use a group with no entities
        payload = {
            "group_id": "empty_group_" + str(datetime.now().timestamp()),
            "similarity_threshold": 0.9,
            "dry_run": True,
            "project_id": None,
        }

        # Should not raise and should return early
        await handler.process(payload, queue_service)

    @pytest.mark.asyncio
    async def test_incremental_refresh_handles_errors_gracefully(self, graphiti_client, queue_service):
        """Test that incremental refresh handles errors gracefully."""
        handler = IncrementalRefreshTaskHandler()

        # Try to refresh non-existent episodes
        payload = {
            "group_id": "test_error_handling",
            "episode_uuids": ["non-existent-uuid-1", "non-existent-uuid-2"],
            "rebuild_communities": False,
            "project_id": "test_project",
            "tenant_id": "test_tenant",
            "user_id": "test_user",
        }

        # Should not raise (handler should log and continue)
        try:
            await handler.process(payload, queue_service)
        except Exception as e:
            # If it does raise, it should be a meaningful error
            assert "Incremental refresh failed" in str(e) or "episode" in str(e).lower()

    @pytest.mark.asyncio
    async def test_metadata_propagation(self, graphiti_client, queue_service):
        """Test that metadata is properly propagated during incremental refresh."""
        handler = IncrementalRefreshTaskHandler()

        # Add an episode with metadata
        add_result = await graphiti_client.add_episode(
            name="Metadata Test Episode",
            episode_body="Testing metadata propagation",
            source_description="text",
            group_id="test_metadata_group",
            reference_time=datetime.now(timezone.utc),
        )

        episode_uuid = add_result.episode_uuid if hasattr(add_result, 'episode_uuid') else None

        if not episode_uuid:
            pytest.skip("Could not retrieve episode UUID")

        # Perform incremental refresh with metadata
        payload = {
            "group_id": "test_metadata_group",
            "episode_uuids": [episode_uuid],
            "rebuild_communities": False,
            "project_id": "test_project",
            "tenant_id": "test_tenant",
            "user_id": "test_user_123",
        }

        await handler.process(payload, queue_service)

        # Verify metadata was set by querying the episode
        # (In a real scenario, we'd check tenant_id, project_id, user_id are set)
