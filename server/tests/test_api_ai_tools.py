import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from server.api.ai_tools import optimize_content, generate_title, OptimizeRequest, TitleRequest
from server.db_models import APIKey

@pytest.mark.asyncio
async def test_optimize_content():
    # Mock GraphitiService and LLMClient
    mock_llm_client = AsyncMock()
    mock_llm_client.generate_response.return_value = "Optimized Content"
    
    mock_graphiti = MagicMock()
    mock_graphiti.client.llm_client = mock_llm_client
    
    mock_api_key = APIKey(user_id="test-user", name="test", key_hash="hashed")
    
    request = OptimizeRequest(content="Original Content", instruction="Fix grammar")
    
    response = await optimize_content(
        request=request,
        graphiti=mock_graphiti,
        api_key=mock_api_key
    )
    
    assert response.content == "Optimized Content"
    mock_llm_client.generate_response.assert_called_once()

@pytest.mark.asyncio
async def test_generate_title_api():
    # Mock GraphitiService and LLMClient
    mock_llm_client = AsyncMock()
    mock_llm_client.generate_response.return_value = '"Generated Title"'
    
    mock_graphiti = MagicMock()
    mock_graphiti.client.llm_client = mock_llm_client
    
    mock_api_key = APIKey(user_id="test-user", name="test", key_hash="hashed")
    
    request = TitleRequest(content="Some long content...")
    
    response = await generate_title(
        request=request,
        graphiti=mock_graphiti,
        api_key=mock_api_key
    )
    
    assert response.title == "Generated Title"
    mock_llm_client.generate_response.assert_called_once()
