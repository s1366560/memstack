from abc import ABC
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar, Optional
from datetime import datetime
import uuid

T = TypeVar("T")

@dataclass(kw_only=True)
class Entity(ABC):
    """
    Base class for Domain Entities.
    Entities have a unique identity that persists throughout their lifecycle.
    Equality is based on identity, not attributes.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)

@dataclass(frozen=True)
class ValueObject(ABC):
    """
    Base class for Value Objects.
    Value Objects are immutable and defined by their attributes.
    Equality is based on all attributes.
    """
    pass

@dataclass(frozen=True)
class DomainEvent(ABC):
    """
    Base class for Domain Events.
    Events represent something that happened in the past.
    They are immutable and contain all necessary data.
    """
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))

class DomainException(Exception):
    """Base exception for all domain errors."""
    pass
