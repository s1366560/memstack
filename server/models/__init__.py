"""Models package."""

from server.models.auth import APIKeyCreate, APIKeyResponse, UserCreate, UserResponse
from server.models.entity import Entity, EntityCreate, EntityResponse
from server.models.episode import Episode, EpisodeCreate, EpisodeResponse
from server.models.memory import MemoryItem, MemoryQuery
from server.models.memory_app import (
    Entity as MemoryEntity,
)
from server.models.memory_app import (
    GraphConfig,
    MemoryCreate,
    MemoryRelationship,
    MemoryRule,
    MemorySearchResponse,
    MemoryUpdate,
)
from server.models.memory_app import (
    MemoryResponse as AppMemoryResponse,
)
from server.models.project import (
    GraphConfig as ProjectGraphConfig,
)
from server.models.project import (
    MemoryRulesConfig,
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectStats,
    ProjectUpdate,
)
from server.models.recall import (
    CommunityRebuildResponse,
    ShortTermRecallQuery,
    ShortTermRecallResponse,
)
from server.models.tenant import (
    TenantCreate,
    TenantListResponse,
    TenantResponse,
    TenantUpdate,
)

__all__ = [
    # Auth models
    "APIKeyCreate",
    "APIKeyResponse",
    "UserCreate",
    "UserResponse",
    # Entity models
    "Entity",
    "EntityCreate",
    "EntityResponse",
    # Episode models
    "Episode",
    "EpisodeCreate",
    "EpisodeResponse",
    # Memory models
    "MemoryCreate",
    "MemoryUpdate",
    "MemoryResponse",
    "MemoryQuery",
    "MemoryItem",
    "MemorySearchResponse",
    "MemoryEntity",
    "MemoryRelationship",
    "MemoryRule",
    "GraphConfig",
    # Project models
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectStats",
    "ProjectListResponse",
    "MemoryRulesConfig",
    "ProjectGraphConfig",
    # Tenant models
    "TenantCreate",
    "TenantUpdate",
    "TenantResponse",
    "TenantListResponse",
    # Recall models
    "ShortTermRecallQuery",
    "ShortTermRecallResponse",
    "CommunityRebuildResponse",
]

# Alias for app memory response to keep import names stable
# We want MemoryResponse to refer to AppMemoryResponse when imported from server.models
# But MemoryResponse is also imported from server.models.memory above.
# The export list __all__ contains "MemoryResponse".
# If we assign MemoryResponse = AppMemoryResponse, then imports of MemoryResponse from this package will get AppMemoryResponse.
MemoryResponse = AppMemoryResponse
