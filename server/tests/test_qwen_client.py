import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.prompts.models import Message
from pydantic import BaseModel

from server.llm_clients.qwen_client import QwenClient


class TestModel(BaseModel):
    name: str
    value: int


@pytest.fixture
def qwen_client():
    config = LLMConfig(api_key="test-key", model="qwen-plus")
    # We need to mock AsyncOpenAI before it's instantiated in __init__?
    # Or we can just let it init (since we have fake key) and then replace it.
    # But AsyncOpenAI might check connection or something? No, usually lazy.
    client = QwenClient(config=config)
    # Replace client with AsyncMock
    client.client = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_generate_response_success(qwen_client):
    # Mock OpenAI response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='{"name": "test", "value": 123}'))]
    qwen_client.client.chat.completions.create.return_value = mock_response

    response = await qwen_client.generate_response(
        messages=[Message(role="user", content="Hello")], response_model=TestModel
    )

    assert response["name"] == "test"
    assert response["value"] == 123

    # Verify call arguments
    call_kwargs = qwen_client.client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "qwen-plus"
    assert call_kwargs["response_format"] == {"type": "json_object"}
    assert "messages" in call_kwargs
    # Check that system prompt was injected
    assert any(m["role"] == "system" and "JSON" in m["content"] for m in call_kwargs["messages"])


@pytest.mark.asyncio
async def test_retry_on_json_failure(qwen_client):
    # First response is invalid JSON (Schema), second is valid
    schema_response = json.dumps(
        {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}
    )

    mock_response_1 = MagicMock()
    mock_response_1.choices = [MagicMock(message=MagicMock(content=schema_response))]

    mock_response_2 = MagicMock()
    mock_response_2.choices = [
        MagicMock(message=MagicMock(content='{"name": "success", "value": 42}'))
    ]

    qwen_client.client.chat.completions.create.side_effect = [mock_response_1, mock_response_2]

    response = await qwen_client.generate_response(
        messages=[Message(role="user", content="Hello")], response_model=TestModel
    )

    assert response["name"] == "success"
    assert qwen_client.client.chat.completions.create.call_count == 2

    # Verify second call had feedback
    call_kwargs_2 = qwen_client.client.chat.completions.create.call_args_list[1].kwargs
    messages_2 = call_kwargs_2["messages"]
    # Should have: System, User, Assistant (Schema), User (Correction)
    # Note: System prompt is injected if not present
    assert len(messages_2) >= 3
    assert messages_2[-2]["role"] == "assistant"
    assert messages_2[-1]["role"] == "user"
    assert "You returned the JSON Schema" in messages_2[-1]["content"]
