"""Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import server.db_models  # noqa: F401
from server.api import episodes, episodes_list, memory, recall
from server.api.auth import router as auth_router
from server.api.health import router as health_router
from server.api.memories import router as memories_router
from server.api.memos import router as memos_router
from server.api.projects import router as projects_router
from server.api.tenants import router as tenants_router
from server.auth import initialize_default_credentials
from server.config import get_settings
from server.database import Base, engine
from server.logging_config import get_logger, setup_colored_logging, setup_logging
from server.services.graphiti_service import graphiti_service

# Setup logging
settings = get_settings()
if settings.log_level.upper() == "DEBUG":
    setup_colored_logging()
else:
    setup_logging()

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting VIP Memory application...")
    
    # Create tables
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
        
        # Initialize default credentials
        await initialize_default_credentials()
    except Exception as e:
        logger.error(f"Failed to create database tables or initialize credentials: {e}")
        # Don't raise here to allow app to start even if DB is not ready yet (e.g. in tests)
    
    # Initialize Graphiti service
    try:
        await graphiti_service.initialize(provider=settings.llm_provider)
        logger.info("Graphiti service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Graphiti service: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down VIP Memory application...")
    
    # Close Graphiti service
    try:
        await graphiti_service.close()
        logger.info("Graphiti service closed successfully")
    except Exception as e:
        logger.error(f"Failed to close Graphiti service: {e}")


def setup_app() -> FastAPI:
    """Setup FastAPI app."""
    app = FastAPI(
        title="VIP Memory API",
        description="Enterprise-grade AI Memory Cloud Platform based on Graphiti",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register routes
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(episodes.router, prefix="/api/v1")
    app.include_router(episodes_list.router, prefix="/api/v1")
    app.include_router(memory.router, prefix="/api/v1")
    app.include_router(recall.router, prefix="/api/v1")
    app.include_router(memos_router, prefix="/api/v1")
    app.include_router(memories_router)  # Already has prefix
    app.include_router(projects_router)  # Already has prefix
    app.include_router(tenants_router)   # Already has prefix
    
    return app


app = setup_app()


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "status_code": 500},
    )
