from unittest.mock import AsyncMock, Mock

import pytest

from server.services.graphiti_service import GraphitiService


@pytest.mark.asyncio
async def test_get_graph_data_filters():
    service = GraphitiService()
    mock_driver = Mock()
    # Simulate records with properties and labels
    mock_result = Mock()
    mock_result.records = [
        {
            "source_id": "n1",
            "source_labels": ["Episodic"],
            "source_props": {"name": "ep1", "tenant_id": "t1", "created_at": "2025-01-01T00:00:00Z"},
            "edge_id": "e1",
            "edge_type": "RELATES_TO",
            "edge_props": {"created_at": "2025-01-01T00:00:00Z"},
            "target_id": "n2",
            "target_labels": ["Entity"],
            "target_props": {"name": "Alice"},
        }
    ]
    mock_driver.execute_query = AsyncMock(return_value=mock_result)

    service._client = Mock()
    service._client.driver = mock_driver

    data = await service.get_graph_data(limit=10, since=None, tenant_id="t1")
    assert "elements" in data
    assert len(data["elements"]["nodes"]) == 2
    assert len(data["elements"]["edges"]) == 1


@pytest.mark.asyncio
async def test_get_graph_data_with_project_filter():
    service = GraphitiService()
    mock_driver = Mock()
    mock_result = Mock()
    mock_result.records = [
        {
            "source_id": "n1",
            "source_labels": ["Episodic"],
            "source_props": {"name": "ep1", "project_id": "p1"},
            "edge_id": None,
            "edge_type": None,
            "edge_props": None,
            "target_id": None,
            "target_labels": None,
            "target_props": None,
        }
    ]
    mock_driver.execute_query = AsyncMock(return_value=mock_result)

    service._client = Mock()
    service._client.driver = mock_driver

    data = await service.get_graph_data(limit=10, project_id="p1")
    
    # Verify that project_id was passed to execute_query
    call_args = mock_driver.execute_query.call_args
    assert call_args is not None
    _, kwargs = call_args
    assert kwargs.get("project_id") == "p1"
    
    assert "elements" in data
    assert len(data["elements"]["nodes"]) == 1


@pytest.mark.asyncio
async def test_short_term_recall():
    service = GraphitiService()
    mock_driver = Mock()
    mock_result = Mock()
    class Node(dict):
        def __init__(self, props):
            super().__init__(props)
            self.properties = props
            
    mock_result.records = [{"episode": Node({"content": "hello", "name": "ep1"}), "links": []}]
    mock_driver.execute_query = AsyncMock(return_value=mock_result)

    service._client = Mock()
    service._client.driver = mock_driver

    resp = await service.short_term_recall(window_minutes=30, limit=5, tenant_id=None)
    assert resp.total == 1
    assert resp.results[0].content == "hello"


@pytest.mark.asyncio
async def test_search_with_filters():
    service = GraphitiService()

    # Mock SearchResults shape
    class SearchResults:
        def __init__(self):
            self.episodes = [Mock(name="ep1", content="hello")]
            self.episode_reranker_scores = [0.9]
            self.nodes = [Mock(name="Alice", summary="person")]
            self.node_reranker_scores = [0.8]
            self.edges = []
            self.edge_reranker_scores = []

    mock_driver = Mock()
    # property lookup for filters
    props_result = Mock()
    props_result.records = [{"props": {"tenant_id": "t1", "created_at": "2024-12-31T00:00:00Z"}}]
    mock_driver.execute_query = AsyncMock(return_value=props_result)

    mock_client = Mock()
    mock_client.search_ = AsyncMock(return_value=SearchResults())
    mock_client.driver = mock_driver

    service._client = mock_client

    results = await service.search(
        query="hello",
        limit=10,
        tenant_id="t1",
        project_id=None,
        user_id=None,
        as_of=None,
    )
    assert len(results) >= 1
