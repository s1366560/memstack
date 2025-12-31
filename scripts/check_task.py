#!/usr/bin/env python3
"""Check task status in database."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from src.infrastructure.adapters.secondary.persistence.database import async_session_factory
from src.infrastructure.adapters.secondary.persistence.models import TaskLog


async def check_task(task_id: str):
    """Check task status in database."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(TaskLog).where(TaskLog.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            print(f"❌ Task {task_id} not found in database")
            return

        print(f"✅ Task found: {task_id}")
        print(f"   Status: {task.status}")
        print(f"   Task Type: {task.task_type}")
        print(f"   Progress: {getattr(task, 'progress', 0)}%")
        print(f"   Message: {getattr(task, 'message', 'N/A')}")
        print(f"   Created: {task.created_at}")
        print(f"   Started: {task.started_at}")
        print(f"   Completed: {task.completed_at}")
        print(f"   Error: {task.error_message}")

        if hasattr(task, 'result') and task.result:
            print(f"   Result: {task.result}")

        # Check if task is stuck
        if task.status == "PENDING":
            from datetime import datetime, timezone, timedelta
            if task.created_at < datetime.now(timezone.utc) - timedelta(seconds=30):
                print(f"\n⚠️  WARNING: Task has been PENDING for over 30 seconds!")
                print(f"   This suggests workers are not running.")
                print(f"   Check if queue workers are started.")
        elif task.status == "PROCESSING":
            if getattr(task, 'progress', 0) == 0:
                print(f"\n⚠️  WARNING: Task is PROCESSING but progress is 0%")
                print(f"   This suggests the task handler is not calling update_progress()")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_task.py <task_id>")
        sys.exit(1)

    asyncio.run(check_task(sys.argv[1]))
