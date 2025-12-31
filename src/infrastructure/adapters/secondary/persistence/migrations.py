"""
Database migration manager.

This module provides a simple migration system for incremental schema updates.
"""

from sqlalchemy import text
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


# Migration registry
# Each migration defines:
# - table: the table to modify
# - column: the column to add
# - type: the SQL type of the column
# - nullable: whether the column allows NULL values
# - default: optional default value
MIGRATIONS: List[Dict[str, Any]] = [
    {
        "table": "memories",
        "column": "task_id",
        "type": "VARCHAR",
        "nullable": True,
        "description": "Task ID for SSE streaming during episode ingestion"
    },
    {
        "table": "task_logs",
        "column": "progress",
        "type": "INTEGER",
        "nullable": True,
        "default": 0,
        "description": "Task progress percentage (0-100)"
    },
    {
        "table": "task_logs",
        "column": "result",
        "type": "JSONB",
        "nullable": True,
        "description": "Task result data"
    },
    {
        "table": "task_logs",
        "column": "message",
        "type": "VARCHAR",
        "nullable": True,
        "description": "Task status message"
    },
]


async def apply_migrations(session):
    """
    Apply all pending database migrations.

    This function checks for missing columns defined in MIGRATIONS
    and adds them to the database schema.

    Args:
        session: SQLAlchemy async session
    """
    logger.info("Checking for pending database migrations...")

    migrations_applied = 0

    for migration in MIGRATIONS:
        table = migration["table"]
        column = migration["column"]
        column_type = migration["type"]
        nullable = migration.get("nullable", True)
        default = migration.get("default", None)
        description = migration.get("description", "")

        # Check if column exists
        result = await session.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = :table AND column_name = :column
            """),
            {"table": table, "column": column}
        )

        if not result.fetchone():
            # Build ALTER TABLE statement
            null_clause = "" if nullable else "NOT NULL"
            default_clause = ""

            if default is not None:
                # Format default value based on type
                if isinstance(default, str):
                    default_clause = f"DEFAULT '{default}'"
                elif isinstance(default, bool):
                    default_clause = f"DEFAULT {str(default).upper()}"
                elif isinstance(default, (int, float)):
                    default_clause = f"DEFAULT {default}"
                elif default is None:
                    default_clause = "DEFAULT NULL"
                else:
                    default_clause = f"DEFAULT {default}"

            alter_sql = f"ALTER TABLE {table} ADD COLUMN {column} {column_type} {null_clause} {default_clause}".strip()

            logger.info(f"Applying migration: {description}")
            logger.debug(f"SQL: {alter_sql}")

            await session.execute(text(alter_sql))
            await session.commit()

            migrations_applied += 1
            logger.info(f"✅ Added column {column} to table {table}")
        else:
            logger.debug(f"Column {table}.{column} already exists - skipping")

    if migrations_applied == 0:
        logger.info("✅ All migrations up to date")
    else:
        logger.info(f"✅ Applied {migrations_applied} migration(s)")


async def check_schema_compatibility(session):
    """
    Check if the database schema is compatible with the current model.

    Returns:
        bool: True if schema is compatible, False otherwise
    """
    # Check that all required tables exist
    required_tables = [
        "users",
        "tenants",
        "projects",
        "memories",
        "entity_types",
        "task_logs",
    ]

    missing_tables = []

    for table in required_tables:
        result = await session.execute(
            text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_name = :table
            """),
            {"table": table}
        )

        if not result.fetchone():
            missing_tables.append(table)

    if missing_tables:
        logger.warning(f"Missing tables: {', '.join(missing_tables)}")
        return False

    return True


async def get_migration_status(session) -> Dict[str, Any]:
    """
    Get the current status of migrations.

    Returns:
        Dict with migration status information
    """
    status = {
        "pending_migrations": [],
        "applied_migrations": [],
        "total_migrations": len(MIGRATIONS),
    }

    for migration in MIGRATIONS:
        table = migration["table"]
        column = migration["column"]

        result = await session.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = :table AND column_name = :column
            """),
            {"table": table, "column": column}
        )

        if result.fetchone():
            status["applied_migrations"].append({
                "table": table,
                "column": column,
                "description": migration.get("description", "")
            })
        else:
            status["pending_migrations"].append({
                "table": table,
                "column": column,
                "description": migration.get("description", "")
            })

    return status
