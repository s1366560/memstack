#!/usr/bin/env python3
"""Setup Alembic migrations."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from src.configuration.config import get_settings

def main():
    """Setup Alembic migration state."""
    settings = get_settings()
    sync_url = settings.postgres_url.replace("+asyncpg", "", 1)

    engine = create_engine(sync_url)

    # Create alembic_version table if it doesn't exist
    with engine.begin() as conn:
        # Check if table exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'alembic_version'
            )
        """))

        table_exists = result.scalar()

        if not table_exists:
            print("Creating alembic_version table...")
            conn.execute(text("""
                CREATE TABLE alembic_version (
                    version_num VARCHAR(32) NOT NULL,
                    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                )
            """))

        # Check current version
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        current_version = result.scalar()

        if current_version:
            print(f"Current database version: {current_version}")
        else:
            print("No version found. Marking database as up-to-date (version 001)...")
            conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('001')"))
            print("✅ Database marked at version 001")

    engine.dispose()

if __name__ == "__main__":
    main()
