from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
import logging

from src.configuration.config import get_settings
from src.infrastructure.adapters.secondary.persistence.migrations import apply_migrations as apply_db_migrations

logger = logging.getLogger(__name__)
settings = get_settings()

engine = create_async_engine(settings.postgres_url, echo=settings.log_level.upper() == "DEBUG")

async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db():
    async with async_session_factory() as session:
        yield session


async def apply_migrations():
    """
    Apply incremental database migrations.

    This function:
    1. Creates any missing tables using SQLAlchemy metadata
    2. Applies incremental column additions using the migration system
    """
    from src.infrastructure.adapters.secondary.persistence.models import Base

    # Step 1: Create any missing tables
    logger.info("Ensuring all tables exist...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Tables verified")

    # Step 2: Apply incremental column migrations
    logger.info("Applying incremental migrations...")
    async with async_session_factory() as session:
        await apply_db_migrations(session)
    logger.info("✅ Migrations applied")


async def get_migration_status():
    """
    Get the current migration status.

    Returns:
        Dict with migration status information
    """
    from src.infrastructure.adapters.secondary.persistence.migrations import get_migration_status as get_status

    async with async_session_factory() as session:
        return await get_status(session)


