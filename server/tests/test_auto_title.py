import pytest
from unittest.mock import AsyncMock, MagicMock
from server.api.episodes import create_episode
from server.models.episode import EpisodeCreate
from server.db_models import APIKey

@pytest.mark.asyncio
async def test_auto_title_generation():
    # Mock GraphitiService and LLMClient
    mock_llm_client = AsyncMock()
    # Mock response as dict with content
    mock_llm_client.generate_response.return_value = {"content": "Generated Title"}
    
    mock_graphiti = MagicMock()
    mock_graphiti.client.llm_client = mock_llm_client
    mock_graphiti.add_episode = AsyncMock()
    
    # Mock return value of add_episode
    mock_episode = MagicMock()
    mock_episode.id = "12345678-1234-5678-1234-567812345678"
    mock_episode.created_at = "2024-01-01T00:00:00Z"
    mock_graphiti.add_episode.return_value = mock_episode
    
    # Mock API Key
    mock_api_key = APIKey(user_id="test-user", name="test", key_hash="hashed")
    
    # Create episode request without title
    episode_data = EpisodeCreate(
        content="This is some content that needs a title.",
        source_type="text"
    )
    
    # Call the API function
    response = await create_episode(
        episode=episode_data,
        graphiti=mock_graphiti,
        api_key=mock_api_key
    )
    
    # Verify LLM was called
    mock_llm_client.generate_response.assert_called_once()
    
    # Verify add_episode was called with generated title
    # Note: episode_data is modified in place
    assert episode_data.name == "Generated Title"
    mock_graphiti.add_episode.assert_called_once_with(episode_data)
    
    # Verify response
    assert str(response.id) == "12345678-1234-5678-1234-567812345678"
    assert response.status == "processing"

@pytest.mark.asyncio
async def test_auto_title_fallback():
    # Mock GraphitiService and LLMClient to fail
    mock_llm_client = AsyncMock()
    mock_llm_client.generate_response.side_effect = Exception("LLM Error")
    
    mock_graphiti = MagicMock()
    mock_graphiti.client.llm_client = mock_llm_client
    mock_graphiti.add_episode = AsyncMock()
    
    mock_episode = MagicMock()
    mock_episode.id = "12345678-1234-5678-1234-567812345678"
    mock_episode.created_at = "2024-01-01T00:00:00Z"
    mock_graphiti.add_episode.return_value = mock_episode
    
    mock_api_key = APIKey(user_id="test-user", name="test", key_hash="hashed")
    
    episode_data = EpisodeCreate(
        content="This is some content that needs a title.",
        source_type="text"
    )
    
    # Call the API function
    response = await create_episode(
        episode=episode_data,
        graphiti=mock_graphiti,
        api_key=mock_api_key
    )
    
    # Verify fallback title
    assert episode_data.name == "This is some content that needs a title...."
    assert response.status == "processing"
