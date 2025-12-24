
from unittest.mock import AsyncMock, Mock, patch

import pytest

from server.services.graphiti_service import GraphitiService


@pytest.fixture
def mock_graphiti_core():
    with patch("server.services.graphiti_service.Graphiti") as mock:
        yield mock

@pytest.fixture
def mock_qwen_client():
    with patch("server.services.graphiti_service.QwenClient") as mock:
        yield mock

@pytest.mark.asyncio
async def test_initialize_qwen(mock_graphiti_core, mock_qwen_client):
    service = GraphitiService()
    
    # Mock settings
    with patch("server.services.graphiti_service.settings") as mock_settings:
        mock_settings.qwen_api_key = "test"
        mock_settings.qwen_model = "qwen-plus"
        mock_settings.qwen_embedding_model = "text-embedding-v3"
        mock_settings.qwen_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        
        await service.initialize(provider="qwen")
        
        mock_qwen_client.assert_called()
        mock_graphiti_core.assert_called()

@pytest.mark.asyncio
async def test_get_graph_data(mock_graphiti_core):
    mock_client = Mock()
    mock_driver = Mock()
    mock_client.driver = mock_driver
    mock_graphiti_core.return_value = mock_client
    
    service = GraphitiService()
    service._client = mock_client
    
    # Mock Neo4j result
    mock_record = {
        "source_id": "n1",
        "source_labels": ["Entity"],
        "source_props": {"name": "Node1"},
        "edge_id": "e1",
        "edge_type": "LINKS_TO",
        "edge_props": {},
        "target_id": "n2",
        "target_labels": ["Entity"],
        "target_props": {"name": "Node2"},
    }
    
    mock_result = Mock()
    mock_result.records = [mock_record]
    mock_driver.execute_query = AsyncMock(return_value=mock_result)
    
    data = await service.get_graph_data(limit=10)
    
    assert len(data["elements"]["nodes"]) == 2
    assert len(data["elements"]["edges"]) == 1
    assert data["elements"]["nodes"][0]["data"]["id"] == "n1"

@pytest.mark.asyncio
async def test_search_extended(mock_graphiti_core):
    mock_client = Mock()
    mock_graphiti_core.return_value = mock_client
    
    service = GraphitiService()
    service._client = mock_client
    
    # Mock search results
    mock_episode = Mock()
    mock_episode.name = "ep1"
    mock_episode.content = "content"
    
    mock_results = Mock()
    mock_results.episodes = [mock_episode]
    mock_results.episode_reranker_scores = [0.9]
    mock_results.nodes = []
    mock_results.edges = []
    
    mock_client.search_ = AsyncMock(return_value=mock_results)
    
    # Mock Neo4j check for filters (passed)
    mock_client.driver.execute_query = AsyncMock(return_value=Mock(records=[{"props": {}}]))

    results = await service.search(query="test")
    
    assert len(results) == 1
    assert results[0].content == "content"
    assert results[0].metadata["type"] == "episode"
