"""Entity data models."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Entity(BaseModel):
    """Entity model representing semantic entities extracted from episodes."""

    id: UUID = Field(..., description="Entity unique identifier")
    name: str = Field(..., description="Entity name")
    entity_type: str = Field(..., description="Entity type (e.g., Person, Product, Organization)")
    summary: Optional[str] = Field(default=None, description="Entity summary")
    properties: Dict[str, Any] = Field(
        default_factory=dict, description="Entity properties and attributes"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    tenant_id: Optional[str] = Field(default=None, description="Tenant identifier")

    model_config = ConfigDict(from_attributes=True)


class EntityResponse(BaseModel):
    """Response model for entity queries."""

    entities: List[Entity] = Field(..., description="List of entities")
    total: int = Field(..., description="Total number of entities")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "entities": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "John",
                        "entity_type": "Person",
                        "summary": "User who prefers dark mode",
                        "properties": {"preference": "dark_mode"},
                        "created_at": "2024-01-15T10:30:00Z",
                    }
                ],
                "total": 1,
            }
        }
    )
