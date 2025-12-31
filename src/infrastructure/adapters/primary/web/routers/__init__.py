"""FastAPI routers for the MemStack API."""

from src.infrastructure.adapters.primary.web.routers import auth
from src.infrastructure.adapters.primary.web.routers import tenants
from src.infrastructure.adapters.primary.web.routers import projects
from src.infrastructure.adapters.primary.web.routers import memories
from src.infrastructure.adapters.primary.web.routers import graphiti
from src.infrastructure.adapters.primary.web.routers import schema
from src.infrastructure.adapters.primary.web.routers import episodes
from src.infrastructure.adapters.primary.web.routers import recall
from src.infrastructure.adapters.primary.web.routers import enhanced_search
from src.infrastructure.adapters.primary.web.routers import data_export
from src.infrastructure.adapters.primary.web.routers import maintenance
from src.infrastructure.adapters.primary.web.routers import tasks
from src.infrastructure.adapters.primary.web.routers import memos
from src.infrastructure.adapters.primary.web.routers import ai_tools

__all__ = [
    "auth",
    "tenants",
    "projects",
    "memories",
    "graphiti",
    "schema",
    "episodes",
    "recall",
    "enhanced_search",
    "data_export",
    "maintenance",
    "tasks",
    "memos",
    "ai_tools",
]
