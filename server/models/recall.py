from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from server.models.memory import MemoryItem


class ShortTermRecallQuery(BaseModel):
    window_minutes: int = Field(default=30, ge=1, le=4320)
    tenant_id: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=500)


class ShortTermRecallResponse(BaseModel):
    results: List[MemoryItem]
    total: int
    since: datetime


class CommunityRebuildResponse(BaseModel):
    status: str = Field(default="ok")
    message: str = Field(default="Communities rebuild triggered")
