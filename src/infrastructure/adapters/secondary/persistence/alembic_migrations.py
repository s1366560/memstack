"""
Alembic migration integration for MemStack.

This module provides functions to run Alembic migrations programmatically.
"""

import logging
from pathlib import Path
from sqlalchemy import create_engine
from alembic import command
from alembic.config import Config

logger = logging.getLogger(__name__)


def get_alembic_config() -> Config:
    """
    Get Alembic configuration.

    Returns:
        Configured Alembic Config object
    """
    # Find project root by looking for alembic.ini
    current_path = Path(__file__).resolve()

    # Search upwards for alembic.ini
    project_root = current_path
    for _ in range(6):  # Search up to 6 levels up
        if (project_root / "alembic.ini").exists():
            break
        project_root = project_root.parent

    ini_path = project_root / "alembic.ini"

    if not ini_path.exists():
        raise FileNotFoundError(f"Could not find alembic.ini at {ini_path}")

    config = Config(str(ini_path))

    # Set script location (relative to project root)
    config.set_main_option("script_location", str(project_root / "alembic"))

    return config


async def run_alembic_migrations():
    """
    Run Alembic migrations at startup.

    This function will apply any pending migrations automatically.
    It creates a synchronous connection just for running migrations.
    """
    from src.configuration.config import get_settings

    settings = get_settings()

    # Convert async URL to sync URL
    sync_url = settings.postgres_url.replace("+asyncpg", "", 1)

    config = get_alembic_config()
    config.set_main_option("sqlalchemy.url", sync_url)

    try:
        logger.info("Running Alembic migrations...")

        # Get current revision
        from alembic.script import ScriptDirectory
        script_dir = ScriptDirectory.from_config(config)

        # Create engine for migration
        from sqlalchemy import create_engine
        engine = create_engine(sync_url)

        # Check current version
        with engine.begin() as conn:
            try:
                result = conn.execute(
                    __import__('sqlalchemy').text("SELECT version_num FROM alembic_version")
                )
                current_version = result.scalar()
                logger.info(f"Current database version: {current_version}")
            except Exception:
                logger.info("No alembic_version table found - database is new")
                current_version = None

        # Get head revision
        head = script_dir.get_current_head()
        logger.info(f"Latest migration version: {head}")

        if current_version == head:
            logger.info("✅ Database is already at latest version")
        else:
            # Upgrade to head
            logger.info(f"Upgrading database from {current_version} to {head}...")
            command.upgrade(config, "head")
            logger.info("✅ Migrations applied successfully")

        engine.dispose()

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        # Don't raise - allow application to start even if migration fails
        # Admin can manually fix and retry


def get_migration_status() -> dict:
    """
    Get current migration status.

    Returns:
        Dict with migration status information
    """
    config = get_alembic_config()

    from src.configuration.config import get_settings
    settings = get_settings()
    sync_url = settings.postgres_url.replace("+asyncpg", "", 1)
    config.set_main_option("sqlalchemy.url", sync_url)

    from alembic.script import ScriptDirectory
    script_dir = ScriptDirectory.from_config(config)

    # Get all revisions
    try:
        revisions = list(script_dir.walk_revisions())
        total_revisions = len(revisions)
        head_revision = script_dir.get_current_head()
    except Exception as e:
        logger.warning(f"Could not get revisions: {e}")
        total_revisions = 0
        head_revision = None

    # Get current version from database
    from sqlalchemy import create_engine, text
    engine = create_engine(sync_url)

    current_version = None
    try:
        with engine.begin() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            current_version = result.scalar()
    except Exception:
        # Table doesn't exist yet
        pass

    engine.dispose()

    return {
        "current_revision": current_version,
        "head_revision": head_revision,
        "total_revisions": total_revisions,
        "needs_upgrade": current_version != head_revision if head_revision else False
    }
