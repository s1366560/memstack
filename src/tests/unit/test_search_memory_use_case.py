import pytest
from unittest.mock import Mock, AsyncMock

from src.application.use_cases.memory.search_memory import SearchMemoryUseCase, SearchMemoryCommand
from src.domain.ports.services.graph_service_port import GraphServicePort

@pytest.fixture
def mock_graph_service():
    return Mock(spec=GraphServicePort)

@pytest.mark.asyncio
async def test_search_memory_delegates_to_service(mock_graph_service):
    # Arrange
    use_case = SearchMemoryUseCase(mock_graph_service)
    command = SearchMemoryCommand(
        query="test query",
        project_id="proj_123",
        limit=5
    )
    
    expected_results = [{"id": "1", "content": "result"}]
    mock_graph_service.search = AsyncMock(return_value=expected_results)
    
    # Act
    results = await use_case.execute(command)
    
    # Assert
    assert results == expected_results
    mock_graph_service.search.assert_called_once_with(
        query="test query",
        project_id="proj_123",
        limit=5
    )
