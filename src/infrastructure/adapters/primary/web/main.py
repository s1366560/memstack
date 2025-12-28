from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from src.configuration.config import get_settings
from src.configuration.container import DIContainer
from src.configuration.factories import create_graphiti_client
from src.infrastructure.adapters.secondary.persistence.database import async_session_factory, engine
from src.infrastructure.adapters.secondary.persistence.models import Base
from src.infrastructure.adapters.secondary.queue.redis_queue import QueueService
from src.infrastructure.adapters.primary.web.dependencies import initialize_default_credentials
from src.infrastructure.adapters.primary.web.routers import (
    auth,
    tenants,
    projects,
    memories,
    graphiti,
    schema,
    episodes,
    recall,
    enhanced_search,
    data_export,
    maintenance,
    tasks,
    memos,
    ai_tools,
)

logger = logging.getLogger(__name__)
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting MemStack (Hexagonal) application...")
    
    # Initialize Database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Initialize Default Credentials (Admin/User/Tenant)
    await initialize_default_credentials()
    
    # Initialize Graphiti
    graphiti_client = create_graphiti_client()
    try:
        await graphiti_client.build_indices_and_constraints()
    except Exception as e:
        logger.warning(f"Failed to build indices: {e}")

    # Initialize QueueService (Producer Mode)
    queue_service = QueueService()
    await queue_service.initialize(
        graphiti_client=graphiti_client,
        run_workers=False
    )
    
    # Initialize Container
    container = DIContainer(
        session_factory=async_session_factory,
        graphiti_client=graphiti_client
    )
    
    app.state.container = container
    app.state.queue_service = queue_service
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await queue_service.close()
    await graphiti_client.close()

def create_app() -> FastAPI:
    app = FastAPI(
        title="MemStack API (Hexagonal)",
        version="0.2.0",
        lifespan=lifespan
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/health")
    async def health_check():
        return {"status": "ok", "version": "0.2.0"}
        
    # Register Routers
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(tenants.router)
    app.include_router(projects.router)
    app.include_router(memories.router)
    app.include_router(graphiti.router)
    app.include_router(schema.router)

    # New routers - feature parity with server/
    app.include_router(episodes.router)
    app.include_router(recall.router)
    app.include_router(enhanced_search.router)
    app.include_router(data_export.router)
    app.include_router(maintenance.router)
    app.include_router(tasks.router)
    app.include_router(memos.router)
    app.include_router(ai_tools.router)
    
    return app

app = create_app()
