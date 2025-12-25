import os
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from graphiti_core.llm_client.config import LLMConfig
from server.llm_clients.openai_client import OpenAIClient, DEFAULT_MODEL, DEFAULT_SMALL_MODEL


@pytest.fixture
def mock_env_vars():
    with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key", "OPENAI_BASE_URL": "env-url"}):
        yield


def test_init_defaults():
    with patch("graphiti_core.llm_client.openai_client.AsyncOpenAI") as mock_openai:
        client = OpenAIClient(config=LLMConfig(api_key="test-key"))
        assert client.model == DEFAULT_MODEL
        assert client.small_model == DEFAULT_SMALL_MODEL
        assert client.config.api_key == "test-key"
        
        # Verify AsyncOpenAI was called with config values
        mock_openai.assert_called()
        call_kwargs = mock_openai.call_args[1]
        assert call_kwargs["api_key"] == "test-key"


def test_init_with_env_vars(mock_env_vars):
    with patch("graphiti_core.llm_client.openai_client.AsyncOpenAI") as mock_openai:
        # Pass empty config, should pick up env vars
        client = OpenAIClient()
        
        assert client.config.api_key == "env-key"
        assert client.config.base_url == "env-url"
        
        # Verify AsyncOpenAI was called with env values
        mock_openai.assert_called()
        call_kwargs = mock_openai.call_args[1]
        assert call_kwargs["api_key"] == "env-key"
        assert call_kwargs["base_url"] == "env-url"


def test_init_override_defaults():
    with patch("graphiti_core.llm_client.openai_client.AsyncOpenAI"):
        config = LLMConfig(
            api_key="test-key",
            model="custom-model",
            small_model="custom-small"
        )
        client = OpenAIClient(config=config)
        assert client.model == "custom-model"
        assert client.small_model == "custom-small"
