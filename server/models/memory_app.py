from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from server.models.enums import DataStatus, ProcessingStatus


class MemoryRule(BaseModel):
    name: str = Field(...)
    description: Optional[str] = None
    enabled: bool = True
    conditions: dict = Field(default_factory=dict)
    actions: dict = Field(default_factory=dict)


class GraphConfig(BaseModel):
    layout_algorithm: str = Field(default="force-directed")
    node_size: int = Field(default=20, ge=10, le=100)
    edge_width: int = Field(default=2, ge=1, le=10)
    colors: dict = Field(default_factory=dict)
    animations: bool = True
    max_nodes: int = Field(default=1000, ge=100, le=10000)


class Entity(BaseModel):
    id: str
    name: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(..., ge=0.0, le=1.0)


class Relationship(BaseModel):
    id: str
    source_id: str
    target_id: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(..., ge=0.0, le=1.0)


MemoryRelationship = Relationship


class MemoryCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(...)
    content_type: str = Field(default="text")
    project_id: str = Field(...)
    tags: List[str] = Field(default_factory=list)
    entities: List[Entity] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    collaborators: List[str] = Field(default_factory=list)
    is_public: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemoryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    entities: Optional[List[Entity]] = None
    relationships: Optional[List[Relationship]] = None
    collaborators: Optional[List[str]] = None
    is_public: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class MemoryItem(BaseModel):
    id: str
    title: str
    content: str
    content_type: str
    project_id: str
    tags: List[str] = Field(default_factory=list)
    entities: List[Entity] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    author_id: str
    collaborators: List[str] = Field(default_factory=list)
    is_public: bool
    status: str = DataStatus.ENABLED
    processing_status: str = ProcessingStatus.PENDING
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None


class MemoryResponse(BaseModel):
    id: str
    title: str
    content: str
    content_type: str
    project_id: str
    tags: List[str] = Field(default_factory=list)
    entities: List[Entity] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    version: int
    author_id: str
    collaborators: List[str] = Field(default_factory=list)
    is_public: bool
    status: str = DataStatus.ENABLED
    processing_status: str = ProcessingStatus.PENDING
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class MemoryListResponse(BaseModel):
    memories: List[MemoryResponse]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)


class MemorySearchResponse(BaseModel):
    results: List[MemoryItem]
    total: int
    query: str
    filters_applied: Dict[str, Any] = Field(default_factory=dict)
    search_metadata: Dict[str, Any] = Field(default_factory=dict)
