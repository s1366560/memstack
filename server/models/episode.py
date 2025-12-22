"""Episode data models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class SourceType(str, Enum):
    """Episode source type enumeration."""

    TEXT = "text"
    JSON = "json"
    DOCUMENT = "document"
    API = "api"


class EpisodeCreate(BaseModel):
    """Request model for creating an episode."""

    name: Optional[str] = Field(default=None, description="Optional episode name")
    content: str = Field(..., description="Episode content")
    source_type: SourceType = Field(default=SourceType.TEXT, description="Source type")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    valid_at: Optional[datetime] = Field(
        default=None, description="Event occurrence time (defaults to current time)"
    )
    tenant_id: Optional[str] = Field(default=None, description="Tenant identifier")
    project_id: Optional[str] = Field(default=None, description="Project identifier")
    user_id: Optional[str] = Field(default=None, description="User identifier")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "User John prefers dark mode in the application.",
                "source_type": "text",
                "metadata": {"user_id": "user_123", "session_id": "session_456"},
                "valid_at": "2024-01-15T10:30:00Z",
            }
        }
    )


class Episode(BaseModel):
    """Episode model representing raw event data."""

    id: UUID = Field(default_factory=uuid4, description="Episode unique identifier")
    name: Optional[str] = Field(default=None, description="Episode name")
    content: str = Field(..., description="Episode content")
    source_type: SourceType = Field(..., description="Source type")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    valid_at: datetime = Field(..., description="Event occurrence time")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Ingestion time")
    tenant_id: Optional[str] = Field(default=None, description="Tenant identifier")
    project_id: Optional[str] = Field(default=None, description="Project identifier")
    user_id: Optional[str] = Field(default=None, description="User identifier")

    model_config = ConfigDict(from_attributes=True)


class EpisodeResponse(BaseModel):
    """Response model for episode operations."""

    id: UUID = Field(..., description="Episode unique identifier")
    status: str = Field(..., description="Processing status")
    message: str = Field(..., description="Status message")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "message": "Episode queued for ingestion",
                "created_at": "2024-01-15T10:30:00Z",
            }
        }
    )
