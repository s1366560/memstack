"""Memory search models for Graphiti integration."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MemoryQuery(BaseModel):
    query: str = Field(...)
    limit: int = Field(default=10, ge=1, le=100)
    tenant_id: Optional[str] = None
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    as_of: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None


class MemoryItem(BaseModel):
    content: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source: str


class MemoryResponse(BaseModel):
    results: List[MemoryItem]
    total: int
    query: str
