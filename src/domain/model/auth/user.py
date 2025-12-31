from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from src.domain.shared_kernel import Entity


@dataclass(kw_only=True)
class User(Entity):
    """User domain entity representing a system user"""
    email: str
    name: str
    password_hash: str
    is_active: bool = True
    profile: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
