#!/usr/bin/env python3
"""
Migration script to add progress tracking fields to task_logs table.
Run this script to update existing database schema.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text
from src.infrastructure.adapters.secondary.persistence.database import engine


async def migrate():
    """Add progress, result, and message columns to task_logs table."""

    sql_commands = [
        # Add progress column
        """ALTER TABLE task_logs ADD COLUMN IF NOT EXISTS progress INTEGER DEFAULT 0;""",

        # Add result column
        """ALTER TABLE task_logs ADD COLUMN IF NOT EXISTS result JSONB;""",

        # Add message column
        """ALTER TABLE task_logs ADD COLUMN IF NOT EXISTS message VARCHAR;""",

        # Add index on progress
        """CREATE INDEX IF NOT EXISTS idx_task_logs_progress ON task_logs(progress);""",

        # Update existing records
        """UPDATE task_logs SET progress = 0 WHERE progress IS NULL;""",
    ]

    async with engine.begin() as conn:
        for i, sql in enumerate(sql_commands, 1):
            print(f"Executing migration step {i}/{len(sql_commands)}...")
            try:
                await conn.execute(text(sql))
                print(f"✓ Step {i} completed successfully")
            except Exception as e:
                if "already exists" in str(e) or "duplicate column" in str(e):
                    print(f"✓ Step {i} skipped (column/index already exists)")
                else:
                    print(f"✗ Step {i} failed: {e}")
                    raise

    print("\n✅ Migration completed successfully!")
    print("The task_logs table now supports progress tracking.")


if __name__ == "__main__":
    print("Starting database migration...")
    print("This will add progress, result, and message fields to task_logs table")
    print("-" * 60)

    asyncio.run(migrate())
