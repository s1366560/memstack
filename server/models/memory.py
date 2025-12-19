"""Memory query and response models."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class MemoryQuery(BaseModel):
    """Query model for memory retrieval."""

    query: str = Field(..., description="Search query text")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    tenant_id: Optional[str] = Field(default=None, description="Tenant identifier")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional filters")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "What are the user preferences?",
                "limit": 10,
                "filters": {"entity_type": "Person"},
            }
        }
    )


class MemoryItem(BaseModel):
    """Individual memory item in search results."""

    content: str = Field(..., description="Memory content")
    score: float = Field(..., description="Relevance score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Memory metadata")
    source: str = Field(..., description="Memory source (episode, entity, or relation)")


class MemoryResponse(BaseModel):
    """Response model for memory queries."""

    results: List[MemoryItem] = Field(..., description="Search results")
    total: int = Field(..., description="Total number of results")
    query: str = Field(..., description="Original query")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "results": [
                    {
                        "content": "User John prefers dark mode in the application.",
                        "score": 0.95,
                        "metadata": {"entity": "John", "type": "preference"},
                        "source": "episode",
                    }
                ],
                "total": 1,
                "query": "What are the user preferences?",
            }
        }
    )
