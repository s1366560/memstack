from abc import ABC, abstractmethod
from typing import Any, Dict

class TaskHandler(ABC):
    """Abstract base class for task handlers."""

    @property
    @abstractmethod
    def task_type(self) -> str:
        """Return the task type string."""
        pass

    @property
    def timeout_seconds(self) -> int:
        """Return the timeout in seconds for this task type. Default is 600 (10 mins)."""
        return 600

    @abstractmethod
    async def process(self, payload: Dict[str, Any], context: Any) -> None:
        """Process the task.
        
        Args:
            payload: The task payload dictionary.
            context: Context object containing dependencies (graphiti_client, etc.)
        """
        pass
