"""Worker entry point for MemStack (Hexagonal).

This script runs the QueueService in worker mode to process background tasks.
It should be run separately from the API server to avoid blocking the API event loop.
"""

import asyncio
import signal
import sys
import os

# Add project root to path if running as script
sys.path.append(os.getcwd())

from src.configuration.config import get_settings
from src.infrastructure.adapters.secondary.persistence.database import engine
from src.infrastructure.adapters.secondary.persistence.models import Base
from src.configuration.factories import create_graphiti_client
from src.infrastructure.adapters.secondary.queue.redis_queue import QueueService
from src.infrastructure.adapters.secondary.schema.dynamic_schema import get_project_schema

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("src.worker")

settings = get_settings()

# Force enable workers for this process
settings.run_background_workers = True

queue_service = QueueService()
graphiti_client = None

async def shutdown(signal_enum=None):
    """Cleanup tasks tied to the service's shutdown."""
    if signal_enum:
        logger.info(f"Received exit signal {signal_enum.name}...")
    
    logger.info("Shutting down worker...")
    await queue_service.close()
    
    if graphiti_client:
        await graphiti_client.close()
    
    # Cancel all running tasks
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    if tasks:
        logger.info(f"Cancelling {len(tasks)} outstanding tasks")
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        
    logger.info("Worker shutdown complete")
    # Stop the loop
    try:
        loop = asyncio.get_running_loop()
        loop.stop()
    except RuntimeError:
        pass

async def main():
    """Main worker entry point."""
    global graphiti_client
    logger.info(f"Starting MemStack Worker (ID: {os.getpid()})...")

    # Create tables (ensure DB is ready)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database connection verified")
    except Exception as e:
        logger.error(f"Failed to verify database connection: {e}")
        sys.exit(1)

    try:
        # Initialize Graphiti Client
        graphiti_client = create_graphiti_client()
        
        # Initialize Queue Service
        await queue_service.initialize(
            graphiti_client=graphiti_client,
            schema_loader=get_project_schema,
            run_workers=True
        )
        logger.info("Queue Service initialized successfully")
        logger.info(f"Worker is running with {settings.max_async_workers} concurrency")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        sys.exit(1)

    # Install signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s)))

    logger.info("Worker is ready and waiting for tasks...")
    
    try:
        # Keep alive until shutdown signal
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        logger.info("Worker main loop cancelled")
    except Exception as e:
        logger.error(f"Unexpected error in worker main loop: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except RuntimeError as e:
        # Ignore "Event loop is closed" error on exit
        if str(e) != "Event loop is closed":
            raise
