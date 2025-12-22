"""
VIP Memory Python SDK
Enterprise-grade AI Memory Cloud Platform Client
"""

from sdk.python.vip_memory.async_client import VipMemoryAsyncClient
from sdk.python.vip_memory.client import VipMemoryClient
from sdk.python.vip_memory.exceptions import (
    APIError,
    AuthenticationError,
    RateLimitError,
    VipMemoryError,
)
from sdk.python.vip_memory.models import Episode, EpisodeCreate, MemoryQuery, MemoryResult

__version__ = "0.1.0"
__all__ = [
    "VipMemoryClient",
    "VipMemoryAsyncClient",
    "Episode",
    "EpisodeCreate",
    "MemoryQuery",
    "MemoryResult",
    "VipMemoryError",
    "AuthenticationError",
    "APIError",
    "RateLimitError",
]
