
import json
from http import HTTPStatus
from unittest.mock import AsyncMock, Mock, patch

import pytest
from pydantic import BaseModel

from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.prompts.models import Message
from server.llm_clients.qwen_client import QwenClient


class MockResponseModel(BaseModel):
    name: str
    age: int

@pytest.fixture
def mock_dashscope_generation():
    with patch("dashscope.Generation.call") as mock:
        yield mock

@pytest.fixture
def qwen_client():
    config = LLMConfig(api_key="test-key")
    return QwenClient(config=config)

def test_init():
    config = LLMConfig(api_key="test-key")
    client = QwenClient(config=config)
    assert client.model == "qwen-plus"
    assert client.small_model == "qwen-turbo"

@pytest.mark.asyncio
async def test_generate_response_success(qwen_client, mock_dashscope_generation):
    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = HTTPStatus.OK
    mock_response.output.choices = [
        Mock(message=Mock(content='{"content": "Hello"}'))
    ]
    mock_dashscope_generation.return_value = mock_response

    messages = [Message(role="user", content="Hi")]
    response = await qwen_client._generate_response(messages)

    assert response == {"content": '{"content": "Hello"}'}

@pytest.mark.asyncio
async def test_generate_response_structured(qwen_client, mock_dashscope_generation):
    # Mock successful structured response
    mock_response = Mock()
    mock_response.status_code = HTTPStatus.OK
    mock_response.output.choices = [
        Mock(message=Mock(content='{"name": "Alice", "age": 30}'))
    ]
    mock_dashscope_generation.return_value = mock_response

    messages = [Message(role="user", content="Hi")]
    response = await qwen_client._generate_response(messages, response_model=MockResponseModel)

    assert response["name"] == "Alice"
    assert response["age"] == 30

@pytest.mark.asyncio
async def test_generate_response_schema_workaround(qwen_client, mock_dashscope_generation):
    # Mock Qwen returning JSON Schema instead of data
    schema_response = json.dumps({
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Bob"},
            "age": {"type": "integer", "default": 25}
        }
    })
    
    mock_response = Mock()
    mock_response.status_code = HTTPStatus.OK
    mock_response.output.choices = [
        Mock(message=Mock(content=schema_response))
    ]
    mock_dashscope_generation.return_value = mock_response

    messages = [Message(role="user", content="Hi")]
    response = await qwen_client._generate_response(messages, response_model=MockResponseModel)

    assert response["name"] == "Bob"
    assert response["age"] == 25
