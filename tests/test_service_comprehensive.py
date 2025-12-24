from unittest.mock import AsyncMock, Mock

import pytest

from server.services.graphiti_service import GraphitiService


@pytest.fixture
def mock_neo4j_driver():
    driver = AsyncMock()
    # Default query response
    mock_result = Mock()
    mock_result.records = []
    driver.execute_query = AsyncMock(return_value=mock_result)
    return driver


@pytest.fixture
def mock_llm_client():
    client = AsyncMock()
    client.generate_response = AsyncMock(return_value="Mocked LLM Response")
    return client


@pytest.fixture
def graphiti_service(mock_neo4j_driver, mock_llm_client):
    service = GraphitiService()
    # Mock the client wrapper
    service._client = Mock()
    service._client.driver = mock_neo4j_driver
    service._client.build_communities = AsyncMock()  # Fix for await error
    service.llm_client = mock_llm_client
    return service


@pytest.mark.asyncio
async def test_perform_incremental_refresh(graphiti_service):
    # Mock finding episodes
    mock_ep_record = {"uuid": "ep1", "created_at": "2023-01-01"}

    # Mock counts
    mock_count_record = {"entity_count": 5, "rel_count": 10}

    async def side_effect(query, **kwargs):
        mock_res = Mock()
        if "MATCH (e:Episodic)" in query and "uuid" not in kwargs:  # Listing episodes
            mock_res.records = [mock_ep_record]
        elif "MATCH (e:Episodic {uuid: $uuid})" in query:  # Get episode details
            mock_res.records = [{"props": {"name": "Ep1", "content": "Content"}}]
        elif "MATCH (n:Entity)" in query:
            mock_res.records = [{"entity_count": 5}]
        elif "MATCH ()-[r]->()" in query:
            mock_res.records = [{"rel_count": 10}]
        else:
            mock_res.records = []
        return mock_res

    graphiti_service.client.driver.execute_query.side_effect = side_effect

    # Mock process_episode (actually add_episode)
    graphiti_service.client.add_episode = AsyncMock()

    result = await graphiti_service.perform_incremental_refresh(rebuild_communities=True)

    assert "refreshed_at" in result
    assert result["episodes_processed"] == 1
    assert result["entities_updated"] == 5
    assert result["relationships_updated"] == 10


@pytest.mark.asyncio
async def test_deduplicate_entities(graphiti_service):
    # Mock finding duplicates
    mock_record = {
        "uuid1": "id1",
        "name1": "E1",
        "type1": "T1",
        "uuid2": "id2",
        "name2": "E1",
        "type2": "T1",
    }
    graphiti_service.client.driver.execute_query.return_value.records = [mock_record]

    result = await graphiti_service.deduplicate_entities(dry_run=True)

    assert result["duplicates_found"] == 1
    assert result["dry_run"] is True


@pytest.mark.asyncio
async def test_invalidate_stale_edges(graphiti_service):
    mock_record = {"count": 10, "deleted": 10}

    async def side_effect(query, **kwargs):
        mock_res = Mock()
        if "RETURN count(r) as count" in query:
            mock_res.records = [{"count": 10}]
        elif "DELETE r" in query:
            mock_res.records = [{"deleted": 10}]
        else:
            mock_res.records = []
        return mock_res

    graphiti_service.client.driver.execute_query.side_effect = side_effect

    result = await graphiti_service.invalidate_stale_edges(dry_run=False)

    assert result["deleted"] == 10
    assert result["dry_run"] is False


@pytest.mark.asyncio
async def test_get_maintenance_status(graphiti_service):
    # Mock counts
    async def execute_query_side_effect(query, **kwargs):
        mock_res = Mock()
        if "MATCH (n:Entity" in query:
            mock_res.records = [{"count": 100}]
        elif "MATCH (n:Episodic" in query:
            mock_res.records = [{"count": 50}]
        elif "MATCH (n:Community" in query:
            mock_res.records = [{"count": 5}]
        elif "MATCH ()-[r]-(n" in query:  # Edge count
            mock_res.records = [{"count": 500}]
        elif "MATCH (e:Episodic)" in query and "count(e)" in query:  # Old data check
            mock_res.records = [{"count": 0}]
        else:
            mock_res.records = [{"count": 0}]
        return mock_res

    graphiti_service.client.driver.execute_query.side_effect = execute_query_side_effect

    result = await graphiti_service.get_maintenance_status()

    assert result["metrics"]["entity_count"] == 100
    assert result["metrics"]["edge_count"] == 500
    # Check recommendations for health status
    assert any(r["type"] == "info" and "healthy" in r["message"] for r in result["recommendations"])


@pytest.mark.asyncio
async def test_rebuild_communities(graphiti_service):
    await graphiti_service.rebuild_communities()
    graphiti_service.client.build_communities.assert_called_once()
