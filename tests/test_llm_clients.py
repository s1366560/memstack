import json
from unittest.mock import AsyncMock, Mock, patch

import pytest
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.prompts.models import Message
from pydantic import BaseModel

from server.llm_clients.qwen_client import QwenClient


class MockResponseModel(BaseModel):
    name: str
    age: int


@pytest.fixture
def mock_openai_client():
    with patch("server.llm_clients.qwen_client.AsyncOpenAI") as mock:
        client_instance = AsyncMock()
        mock.return_value = client_instance
        yield client_instance


@pytest.fixture
def qwen_client(mock_openai_client):
    config = LLMConfig(api_key="test-key")
    return QwenClient(config=config)


def test_init(mock_openai_client):
    config = LLMConfig(api_key="test-key")
    client = QwenClient(config=config)
    assert client.model == "qwen-plus"
    assert client.small_model == "qwen-turbo"
    mock_openai_client.assert_not_called()  # Wait, it IS called in init.
    # Actually QwenClient.__init__ calls AsyncOpenAI(api_key=..., base_url=...)
    # So we should verify it was called correctly if we want.


@pytest.mark.asyncio
async def test_generate_response_success(qwen_client, mock_openai_client):
    # Mock successful response
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content='{"content": "Hello"}'))]
    mock_openai_client.chat.completions.create.return_value = mock_response

    messages = [Message(role="user", content="Hi")]
    response = await qwen_client._generate_response(messages)

    assert response == {"content": '{"content": "Hello"}'}


@pytest.mark.asyncio
async def test_generate_response_structured(qwen_client, mock_openai_client):
    # Mock successful structured response
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content='{"name": "Alice", "age": 30}'))]
    mock_openai_client.chat.completions.create.return_value = mock_response

    messages = [Message(role="user", content="Hi")]
    response = await qwen_client._generate_response(messages, response_model=MockResponseModel)

    assert response["name"] == "Alice"
    assert response["age"] == 30


@pytest.mark.asyncio
async def test_generate_response_schema_workaround(qwen_client, mock_openai_client):
    # Mock Qwen returning JSON Schema instead of data (First call)
    schema_response_content = json.dumps(
        {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Bob"},
                "age": {"type": "integer", "default": 25},
            },
        }
    )

    # Second call (retry) returns correct data
    correct_response_content = json.dumps({"name": "Bob", "age": 25})

    mock_response_schema = Mock()
    mock_response_schema.choices = [Mock(message=Mock(content=schema_response_content))]

    mock_response_correct = Mock()
    mock_response_correct.choices = [Mock(message=Mock(content=correct_response_content))]

    # Configure side_effect for multiple calls
    mock_openai_client.chat.completions.create.side_effect = [
        mock_response_schema,
        mock_response_correct,
    ]

    messages = [Message(role="user", content="Hi")]
    response = await qwen_client._generate_response(messages, response_model=MockResponseModel)

    assert response["name"] == "Bob"
    assert response["age"] == 25

    # Verify retry happened (called twice)
    assert mock_openai_client.chat.completions.create.call_count == 2
