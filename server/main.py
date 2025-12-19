"""Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.api import episodes, memory
from server.config import get_settings
from server.logging_config import get_logger, setup_colored_logging, setup_logging
from server.services.graphiti_service import graphiti_service
from server.telemetry import telemetry

# 设置日志
settings = get_settings()
if settings.log_level.upper() == "DEBUG":
    setup_colored_logging()  # 开发环境使用彩色日志
else:
    setup_logging()  # 生产环境使用标准日志

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting VIP Memory application...")

    # 初始化 OpenTelemetry
    if settings.enable_telemetry:
        try:
            telemetry.initialize(app)
            logger.info("OpenTelemetry initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize telemetry: {e}")

    # 初始化 Graphiti 服务
    try:
        await graphiti_service.initialize(provider=settings.llm_provider)
        logger.info("Graphiti service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down VIP Memory application...")

    # 关闭 Graphiti 服务
    try:
        await graphiti_service.close()
        logger.info("Graphiti service closed")
    except Exception as e:
        logger.error(f"Error closing Graphiti service: {e}")

    # 关闭 OpenTelemetry
    if settings.enable_telemetry:
        try:
            telemetry.shutdown()
            logger.info("OpenTelemetry shut down")
        except Exception as e:
            logger.error(f"Error shutting down telemetry: {e}")


# Create FastAPI application
app = FastAPI(
    title="VIP Memory API",
    description="Enterprise-grade AI Memory Cloud Platform based on Graphiti",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(episodes.router, prefix="/api/v1")
app.include_router(memory.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "VIP Memory API",
        "version": "0.1.0",
        "description": "Enterprise-grade AI Memory Cloud Platform",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "vip-memory",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
