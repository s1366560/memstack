"""
Tests for SDK client.
"""

# Add SDK to path
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sdk_path = Path(__file__).parent.parent / "sdk" / "python"
sys.path.insert(0, str(sdk_path))

from vip_memory import VipMemoryAsyncClient, VipMemoryClient  # noqa: E402
from vip_memory.exceptions import AuthenticationError  # noqa: E402
from vip_memory.models import EpisodeResponse, MemoryResponse  # noqa: E402


class TestVipMemoryClient:
    """Tests for synchronous client."""

    def test_init_with_valid_key(self):
        """Test client initialization with valid API key."""
        client = VipMemoryClient(api_key="vpm_sk_test123")
        assert client.api_key == "vpm_sk_test123"

    def test_init_with_invalid_key(self):
        """Test client initialization with invalid API key."""
        with pytest.raises(AuthenticationError):
            VipMemoryClient(api_key="invalid_key")

    def test_get_headers(self):
        """Test header generation."""
        client = VipMemoryClient(api_key="vpm_sk_test123")
        headers = client._get_headers()

        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer vpm_sk_test123"
        assert headers["Content-Type"] == "application/json"

    @patch("httpx.Client.request")
    def test_create_episode_success(self, mock_request):
        """Test successful episode creation."""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.json.return_value = {
            "id": "ep_123",
            "status": "processing",
            "message": "Episode queued",
            "created_at": "2024-01-01T00:00:00",
        }
        mock_request.return_value = mock_response

        client = VipMemoryClient(api_key="vpm_sk_test123")
        response = client.create_episode(
            name="Test Episode",
            content="Test content",
        )

        assert isinstance(response, EpisodeResponse)
        assert response.id == "ep_123"
        assert response.status == "processing"

    @patch("httpx.Client.request")
    def test_create_episode_auth_error(self, mock_request):
        """Test episode creation with auth error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_request.return_value = mock_response

        client = VipMemoryClient(api_key="vpm_sk_test123")

        with pytest.raises(AuthenticationError):
            client.create_episode(name="Test", content="Content")

    @patch("httpx.Client.request")
    def test_search_memory_success(self, mock_request):
        """Test successful memory search."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "res_1",
                    "content": "Test result",
                    "score": 0.95,
                    "type": "episode",
                }
            ],
            "total": 1,
            "query": "test query",
        }
        mock_request.return_value = mock_response

        client = VipMemoryClient(api_key="vpm_sk_test123")
        response = client.search_memory(query="test query")

        assert isinstance(response, MemoryResponse)
        assert response.total == 1
        assert len(response.results) == 1

    def test_context_manager(self):
        """Test client as context manager."""
        with VipMemoryClient(api_key="vpm_sk_test123") as client:
            assert client.api_key == "vpm_sk_test123"


@pytest.mark.asyncio
class TestVipMemoryAsyncClient:
    """Tests for asynchronous client."""

    async def test_init_with_valid_key(self):
        """Test async client initialization with valid API key."""
        client = VipMemoryAsyncClient(api_key="vpm_sk_test123")
        assert client.api_key == "vpm_sk_test123"
        await client.close()

    async def test_init_with_invalid_key(self):
        """Test async client initialization with invalid API key."""
        with pytest.raises(AuthenticationError):
            VipMemoryAsyncClient(api_key="invalid_key")

    async def test_context_manager(self):
        """Test async client as context manager."""
        async with VipMemoryAsyncClient(api_key="vpm_sk_test123") as client:
            assert client.api_key == "vpm_sk_test123"
