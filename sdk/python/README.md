# VIP Memory Python SDK

Official Python client library for VIP Memory - Enterprise-grade AI Memory Cloud Platform based on Graphiti.

## Installation

```bash
pip install vip-memory-sdk
```

Or install from source:

```bash
cd sdk/python
pip install -e .
```

## Quick Start

### Synchronous Client

```python
from vip_memory import VipMemoryClient

# Initialize client with API key
client = VipMemoryClient(
    api_key="vpm_sk_your_api_key_here",
    base_url="https://api.vipmemory.com"  # Optional, defaults to localhost
)

# Create an episode
episode = client.create_episode(
    name="User Preference",
    content="User loves hiking in the mountains and prefers outdoor activities",
    source_type="text",
    group_id="user_123"
)
print(f"Created episode: {episode.id}")

# Search memories
results = client.search_memory(
    query="What outdoor activities does the user enjoy?",
    limit=10
)

for result in results.results:
    print(f"Score: {result.score}, Content: {result.content}")

# Close the client
client.close()
```

### Asynchronous Client

```python
import asyncio
from vip_memory import VipMemoryAsyncClient

async def main():
    # Use async context manager
    async with VipMemoryAsyncClient(api_key="vpm_sk_your_api_key_here") as client:
        # Create episode
        episode = await client.create_episode(
            name="User Conversation",
            content="User mentioned they enjoy photography and travel",
        )
        
        # Search memories
        results = await client.search_memory(
            query="What are the user's hobbies?",
            limit=5
        )
        
        print(f"Found {results.total} results")
        for result in results.results:
            print(f"- {result.content}")

asyncio.run(main())
```

## Features

- ✅ **Synchronous and Asynchronous Clients**: Choose the client that fits your use case
- ✅ **Type Hints**: Full type annotations with Pydantic models
- ✅ **Automatic Retries**: Built-in retry logic with exponential backoff
- ✅ **Error Handling**: Comprehensive exception hierarchy
- ✅ **Authentication**: Secure API key authentication
- ✅ **Context Managers**: Clean resource management

## API Reference

### VipMemoryClient / VipMemoryAsyncClient

#### Constructor

```python
client = VipMemoryClient(
    api_key: str,              # Your VIP Memory API key (required)
    base_url: str = "http://localhost:8000",  # API base URL
    timeout: float = 60.0,     # Request timeout in seconds
    max_retries: int = 3,      # Maximum retry attempts
    retry_delay: float = 1.0,  # Initial retry delay
)
```

#### Methods

**create_episode()**

Create a new episode in the knowledge graph.

```python
episode = client.create_episode(
    name: str,                        # Episode name (required)
    content: str,                     # Episode content (required)
    source_type: str = "text",        # 'text' or 'json'
    source_description: Optional[str] = None,  # Source description
    group_id: Optional[str] = None,   # Group ID for organization
    metadata: Optional[dict] = None,  # Additional metadata
) -> EpisodeResponse
```

**search_memory()**

Search the knowledge graph for relevant memories.

```python
results = client.search_memory(
    query: str,                       # Search query (required)
    limit: int = 10,                  # Max results (1-100)
    tenant_id: Optional[str] = None,  # Tenant ID for multi-tenancy
    filters: Optional[dict] = None,   # Additional filters
) -> MemoryResponse
```

**health_check()**

Check API health status.

```python
health = client.health_check() -> dict
```

## Error Handling

The SDK provides a comprehensive exception hierarchy:

```python
from vip_memory import (
    VipMemoryError,      # Base exception
    AuthenticationError,  # Authentication failed
    APIError,             # API request error
    RateLimitError,       # Rate limit exceeded
    ValidationError,      # Input validation error
    NetworkError,         # Network request failed
)

try:
    client.create_episode(name="Test", content="Content")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except APIError as e:
    print(f"API error: {e.status_code} - {e.response_body}")
```

## Advanced Usage

### Custom Retry Logic

```python
client = VipMemoryClient(
    api_key="vpm_sk_...",
    max_retries=5,        # Try up to 5 times
    retry_delay=2.0,      # Start with 2 second delay
)
```

### Using with Environment Variables

```python
import os
from vip_memory import VipMemoryClient

client = VipMemoryClient(
    api_key=os.getenv("VIP_MEMORY_API_KEY"),
    base_url=os.getenv("VIP_MEMORY_BASE_URL", "http://localhost:8000"),
)
```

### Batch Operations

```python
episodes = [
    {"name": "Episode 1", "content": "Content 1"},
    {"name": "Episode 2", "content": "Content 2"},
    {"name": "Episode 3", "content": "Content 3"},
]

for episode_data in episodes:
    try:
        episode = client.create_episode(**episode_data)
        print(f"Created: {episode.id}")
    except Exception as e:
        print(f"Failed: {e}")
```

## Development

### Setup Development Environment

```bash
cd sdk/python
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/ --cov=vip_memory --cov-report=term-missing
```

### Format Code

```bash
black vip_memory/ tests/
ruff check --fix vip_memory/ tests/
```

### Type Checking

```bash
mypy vip_memory/
```

## License

MIT License - see LICENSE file for details.

## Support

- Documentation: https://docs.vipmemory.com
- Issues: https://github.com/vipmemory/vip-memory/issues
- Email: support@vipmemory.com
