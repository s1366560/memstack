from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class MemoCreate(BaseModel):
    content: str
    visibility: str = "PRIVATE"
    tags: List[str] = Field(default_factory=list)


class MemoUpdate(BaseModel):
    content: Optional[str] = None
    visibility: Optional[str] = None
    tags: Optional[List[str]] = None


class MemoResponse(BaseModel):
    id: str
    content: str
    visibility: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    tags: List[str]
    user_id: str

    class Config:
        from_attributes = True
