#!/usr/bin/env python3
"""Add task_id column to memories table."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from src.infrastructure.adapters.secondary.persistence.database import engine


async def add_task_id_column():
    """Add task_id column to memories table if it doesn't exist."""

    async with engine.begin() as conn:
        # Check if column exists
        result = await conn.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'memories' AND column_name = 'task_id'
            """)
        )

        if result.fetchone():
            print("✅ Column 'task_id' already exists in 'memories' table")
            return

        # Add column
        print("📝 Adding 'task_id' column to 'memories' table...")
        await conn.execute(
            text("ALTER TABLE memories ADD COLUMN task_id VARCHAR NULL")
        )
        print("✅ Column 'task_id' added successfully")

        # Verify
        result = await conn.execute(
            text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'memories' AND column_name = 'task_id'
            """)
        )
        row = result.fetchone()
        if row:
            print(f"✅ Verification successful:")
            print(f"   Column: {row[0]}")
            print(f"   Type: {row[1]}")
            print(f"   Nullable: {row[2]}")
        else:
            print("❌ Verification failed - column not found after creation")


if __name__ == "__main__":
    asyncio.run(add_task_id_column())
