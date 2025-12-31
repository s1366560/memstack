"""Integration tests for Graphiti adapter."""

import pytest
from datetime import datetime
from graphiti_core import Graphiti
from graphiti_core.llm_client import LLMClient

from src.infrastructure.adapters.secondary.graphiti.graphiti_adapter import GraphitiAdapter
from src.domain.model.memory.episode import Episode, SourceType


@pytest.mark.integration
@pytest.mark.slow
class TestGraphitiAdapterIntegration:
    """Integration tests for GraphitiAdapter with real Graphiti client."""

    @pytest.fixture
    async def graphiti_client(self):
        """Create a real Graphiti client for testing."""
        # Note: This requires a running Neo4j instance
        # For CI/CD, use test containers or mock
        import os
        import asyncio

        client = Graphiti(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            user=os.getenv("NEO4J_USER", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "password"),
            llm_client=MockLLMClient(),
        )
        yield client

        # Cleanup: Cancel all pending tasks before closing
        try:
            # Get all tasks
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            if tasks:
                # Cancel pending tasks
                for task in tasks:
                    task.cancel()
                # Wait for cancellations to complete
                await asyncio.gather(*tasks, return_exceptions=True)
        except Exception:
            pass  # Ignore errors during cleanup

        # Small delay to allow cleanup
        await asyncio.sleep(0.1)

        try:
            await client.close()
        except RuntimeError as e:
            # Ignore "Event loop is closed" errors during teardown
            if "Event loop is closed" not in str(e):
                raise

    @pytest.fixture
    def graphiti_adapter(self, graphiti_client):
        """Create GraphitiAdapter instance."""
        return GraphitiAdapter(client=graphiti_client)

    @pytest.mark.asyncio
    async def test_add_episode_integration(self, graphiti_adapter):
        """Test adding an episode to Graphiti."""
        episode = Episode(
            name="Integration Test Episode",
            content="This is a test episode for integration testing.",
            source_type=SourceType.TEXT,
            valid_at=datetime.utcnow(),
            tenant_id="test_tenant",
            project_id="test_project",
            user_id="test_user",
            metadata={"test": "integration"},
        )

        # Add episode
        result = await graphiti_adapter.add_episode(episode)

        # Assert
        assert result is not None
        assert result.name == "Integration Test Episode"
        assert result.content == "This is a test episode for integration testing."

    @pytest.mark.asyncio
    async def test_search_integration(self, graphiti_adapter):
        """Test searching memories in Graphiti."""
        # First, add an episode
        episode = Episode(
            name="Search Test Episode",
            content="The quick brown fox jumps over the lazy dog.",
            source_type=SourceType.TEXT,
            valid_at=datetime.utcnow(),
            tenant_id="test_tenant",
            project_id="test_project",
            user_id="test_user",
        )

        await graphiti_adapter.add_episode(episode)

        # Wait a bit for indexing
        import asyncio
        await asyncio.sleep(2)

        # Now search
        results = await graphiti_adapter.search(
            query="fox",
            project_id="test_project",
            limit=5
        )

        # Assert
        assert isinstance(results, list)
        # Note: May not find results immediately due to processing time

    @pytest.mark.asyncio
    async def test_get_graph_data_integration(self, graphiti_adapter):
        """Test getting graph data from Graphiti."""
        # Get graph data
        data = await graphiti_adapter.get_graph_data(
            project_id="test_project",
            limit=50
        )

        # Assert
        assert isinstance(data, dict)
        assert "elements" in data

    @pytest.mark.asyncio
    async def test_delete_episode_integration(self, graphiti_adapter):
        """Test deleting an episode from Graphiti."""
        # Add an episode
        episode = Episode(
            name="Delete Test Episode",
            content="This episode will be deleted.",
            source_type=SourceType.TEXT,
            valid_at=datetime.utcnow(),
            tenant_id="test_tenant",
            project_id="test_project",
            user_id="test_user",
        )

        await graphiti_adapter.add_episode(episode)

        # Delete the episode
        deleted = await graphiti_adapter.delete_episode("Delete Test Episode")

        # Assert
        assert deleted is True

    @pytest.mark.asyncio
    async def test_episode_workflow_integration(self, graphiti_adapter):
        """Test complete episode workflow: add -> search -> delete."""
        import asyncio

        # 1. Add episode
        episode = Episode(
            name="Workflow Test Episode",
            content="Testing complete workflow.",
            source_type=SourceType.TEXT,
            valid_at=datetime.utcnow(),
            tenant_id="test_tenant",
            project_id="test_project",
            user_id="test_user",
        )

        result = await graphiti_adapter.add_episode(episode)
        assert result is not None

        # 2. Search for the episode
        await asyncio.sleep(2)  # Wait for processing

        results = await graphiti_adapter.search(
            query="workflow",
            project_id="test_project",
            limit=5
        )

        # 3. Delete the episode
        deleted = await graphiti_adapter.delete_episode("Workflow Test Episode")
        assert deleted is True


# Mock LLM Client for testing
class MockLLMClient(LLMClient):
    """Mock LLM client for testing."""

    def __init__(self):
        from graphiti_core.llm_client import LLMConfig
        super().__init__(config=LLMConfig(), cache=False)

    async def _generate_response(self, messages, response_model=None, max_tokens=1000):
        """Generate a mock response."""
        return "Mock LLM response"

    async def generate_embedding(self, text):
        """Generate a mock embedding."""
        import numpy as np
        return np.random.rand(1536).tolist()
