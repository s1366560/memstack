"""Worker entry point for MemStack.

This script runs the QueueService in worker mode to process background tasks.
It should be run separately from the API server to avoid blocking the API event loop.
"""

import asyncio
import signal
import sys
import os

# Add project root to path if running as script
sys.path.append(os.getcwd())

from server.config import get_settings
from server.database import Base, engine
from server.logging_config import get_logger, setup_colored_logging, setup_logging

# Configure logging
settings = get_settings()
if settings.log_level.upper() == "DEBUG":
    setup_colored_logging()
else:
    setup_logging()

logger = get_logger("server.worker")

# Force enable workers for this process
# We must do this before initializing GraphitiService
settings.run_background_workers = True

from server.services.graphiti_service import graphiti_service

async def shutdown(signal_enum=None):
    """Cleanup tasks tied to the service's shutdown."""
    if signal_enum:
        logger.info(f"Received exit signal {signal_enum.name}...")
    
    logger.info("Shutting down worker...")
    await graphiti_service.close()
    
    # Cancel all running tasks
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    if tasks:
        logger.info(f"Cancelling {len(tasks)} outstanding tasks")
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        
    logger.info("Worker shutdown complete")
    # Stop the loop
    asyncio.get_running_loop().stop()

async def main():
    """Main worker entry point."""
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
        # Initialize Graphiti Service (which starts QueueService workers)
        await graphiti_service.initialize(provider=settings.llm_provider)
        logger.info("Graphiti service (Worker Mode) initialized successfully")
        logger.info(f"Worker is running with {settings.max_async_workers} concurrency")
    except Exception as e:
        logger.error(f"Failed to initialize Graphiti service: {e}")
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
