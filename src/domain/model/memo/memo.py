from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from src.domain.shared_kernel import Entity


@dataclass(kw_only=True)
class Memo(Entity):
    """Memo domain entity for user notes"""
    content: str
    user_id: str
    visibility: str = "PRIVATE"  # PRIVATE, PUBLIC, PROTECTED
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
