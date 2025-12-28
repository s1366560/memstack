from typing import Dict
from src.domain.tasks.base import TaskHandler

class TaskRegistry:
    def __init__(self):
        self._handlers: Dict[str, TaskHandler] = {}

    def register(self, handler: TaskHandler):
        """Register a task handler."""
        self._handlers[handler.task_type] = handler

    def get_handler(self, task_type: str) -> TaskHandler:
        """Get a handler for a task type."""
        return self._handlers.get(task_type)

    def get_all_handlers(self) -> Dict[str, TaskHandler]:
        return self._handlers
