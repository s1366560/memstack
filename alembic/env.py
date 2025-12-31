"""Alembic Environment Configuration for MemStack."""

from logging.config import fileConfig
from sqlalchemy import create_engine, pool
from alembic import context
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

# Import settings and models
from src.configuration.config import get_settings
from src.infrastructure.adapters.secondary.persistence.models import Base

# Import all models to ensure they're registered
from src.infrastructure.adapters.secondary.persistence.models import (
    User,
    Tenant,
    Project,
    Memory,
    EntityType,
    TaskLog,
    UserProject,
    UserTenant,
)

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get settings and convert async URL to sync URL for Alembic
settings = get_settings()
# Convert postgresql+asyncpg:// to postgresql:// for Alembic
sync_url = settings.postgres_url.replace("+asyncpg", "", 1)
config.set_main_option("sqlalchemy.url", sync_url)

# Add your model's MetaData object for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_engine(
        sync_url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
