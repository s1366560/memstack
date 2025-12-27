from typing import Dict, Type
from server.services.tasks.base import TaskHandler
from server.services.tasks.episode import EpisodeTaskHandler
from server.services.tasks.community import RebuildCommunityTaskHandler

class TaskRegistry:
    def __init__(self):
        self._handlers: Dict[str, TaskHandler] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register(EpisodeTaskHandler())
        self.register(RebuildCommunityTaskHandler())

    def register(self, handler: TaskHandler):
        """Register a task handler."""
        self._handlers[handler.task_type] = handler

    def get_handler(self, task_type: str) -> TaskHandler:
        """Get a handler for a task type."""
        return self._handlers.get(task_type)

    def get_all_handlers(self) -> Dict[str, TaskHandler]:
        return self._handlers
