from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.database import get_db
from server.db_models import TaskLog

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskStatsResponse(BaseModel):
    total: int
    pending: int
    processing: int
    completed: int
    failed: int
    throughput_per_minute: float
    error_rate: float


class TaskLogResponse(BaseModel):
    id: str
    name: str  # mapped from task_type
    status: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error: Optional[str]  # mapped from error_message
    worker_id: Optional[str]
    retries: int  # mapped from retry_count
    duration: Optional[str]  # formatted string like "450ms" or "2.4s"


class QueueDepthPoint(BaseModel):
    timestamp: str  # HH:mm
    depth: int


@router.get("/stats", response_model=TaskStatsResponse)
async def get_task_stats(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    one_day_ago = now - timedelta(days=1)
    one_hour_ago = now - timedelta(hours=1)

    # Total tasks (24h)
    total_24h = (
        await db.scalar(select(func.count(TaskLog.id)).where(TaskLog.created_at >= one_day_ago))
        or 0
    )

    # Completed (24h)
    completed_24h = (
        await db.scalar(
            select(func.count(TaskLog.id)).where(
                TaskLog.status == "COMPLETED", TaskLog.created_at >= one_day_ago
            )
        )
        or 0
    )

    # Failed (24h) - for error rate
    failed_24h = (
        await db.scalar(
            select(func.count(TaskLog.id)).where(
                TaskLog.status == "FAILED", TaskLog.created_at >= one_day_ago
            )
        )
        or 0
    )

    # Failed (1h) - for dashboard card
    failed_1h = (
        await db.scalar(
            select(func.count(TaskLog.id)).where(
                TaskLog.status == "FAILED", TaskLog.completed_at >= one_hour_ago
            )
        )
        or 0
    )

    # Pending & Processing (Active)
    pending = (
        await db.scalar(select(func.count(TaskLog.id)).where(TaskLog.status == "PENDING")) or 0
    )
    processing = (
        await db.scalar(select(func.count(TaskLog.id)).where(TaskLog.status == "PROCESSING")) or 0
    )

    # Throughput (completed per minute in last hour)
    completed_1h = (
        await db.scalar(
            select(func.count(TaskLog.id)).where(
                TaskLog.status == "COMPLETED", TaskLog.completed_at >= one_hour_ago
            )
        )
        or 0
    )
    throughput = completed_1h / 60

    # Error Rate
    error_rate = (failed_24h / total_24h * 100) if total_24h > 0 else 0.0

    return TaskStatsResponse(
        total=total_24h,
        pending=pending,
        processing=processing,
        completed=completed_24h,
        failed=failed_1h,
        throughput_per_minute=throughput,
        error_rate=error_rate,
    )


@router.get("/queue-depth", response_model=List[QueueDepthPoint])
async def get_queue_depth(db: AsyncSession = Depends(get_db)):
    # Return simulated or real history.
    # For now, let's construct a simple history based on current pending + some noise or query db if possible.
    # Since we don't store snapshots, we'll estimate "past pending" by looking at tasks created before T but not completed before T.

    now = datetime.now(timezone.utc)
    points = []

    # Generate points for 00:00, 06:00, 12:00, 18:00, Now
    # Adjust to 4-hour intervals for smoother graph: 0, 4, 8, 12, 16, 20, 24

    times = []
    current_hour = now.hour
    # Snap to nearest 6 hours? Or just last 24h points.
    # Let's do every 3 hours for the last 24 hours.
    for i in range(8, -1, -1):
        t = now - timedelta(hours=i * 3)
        times.append(t)

    for t in times:
        # Count tasks that were created <= t AND (completed > t OR completed is NULL)
        # This is roughly "pending or processing" at time t
        count = (
            await db.scalar(
                select(func.count(TaskLog.id)).where(
                    TaskLog.created_at <= t,
                    (TaskLog.completed_at > t) | (TaskLog.completed_at.is_(None)),
                )
            )
            or 0
        )

        points.append(QueueDepthPoint(timestamp=t.strftime("%H:%M"), depth=count))

    return points


@router.get("/recent", response_model=List[TaskLogResponse])
async def get_recent_tasks(
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    query = select(TaskLog).order_by(desc(TaskLog.created_at))

    if status and status != "All Statuses":
        query = query.where(TaskLog.status == status.upper())

    if task_type and task_type != "All Types":
        query = query.where(TaskLog.task_type == task_type)

    if search:
        query = query.where(
            (TaskLog.id.ilike(f"%{search}%")) | (TaskLog.worker_id.ilike(f"%{search}%"))
        )

    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    tasks = result.scalars().all()

    response = []
    for t in tasks:
        duration_str = "-"
        if t.started_at and t.completed_at:
            ms = int((t.completed_at - t.started_at).total_seconds() * 1000)
            if ms < 1000:
                duration_str = f"{ms}ms"
            else:
                duration_str = f"{ms / 1000:.1f}s"
        elif t.status == "FAILED" and t.started_at and t.completed_at:
            # Even if failed, we might have duration
            ms = int((t.completed_at - t.started_at).total_seconds() * 1000)
            duration_str = f"{ms / 1000:.1f}s"

        response.append(
            TaskLogResponse(
                id=t.id,
                name=t.task_type,
                status=t.status.lower().capitalize(),  # "Completed", "Processing"
                created_at=t.created_at,
                started_at=t.started_at,
                completed_at=t.completed_at,
                error=t.error_message,
                worker_id=t.worker_id or "-",
                retries=t.retry_count,
                duration=duration_str,
            )
        )

    return response


@router.get("/status-breakdown")
async def get_status_breakdown(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    one_day_ago = now - timedelta(days=1)

    query = (
        select(TaskLog.status, func.count(TaskLog.id))
        .where(TaskLog.created_at >= one_day_ago)
        .group_by(TaskLog.status)
    )

    result = await db.execute(query)
    # Result is list of (status, count)
    breakdown = {row[0]: row[1] for row in result.all()}

    return {
        "Completed": breakdown.get("COMPLETED", 0),
        "Processing": breakdown.get("PROCESSING", 0),
        "Failed": breakdown.get("FAILED", 0),
        "Pending": breakdown.get("PENDING", 0),
    }


from server.services.graphiti_service import graphiti_service


@router.post("/{task_id}/retry")
async def retry_task_endpoint(task_id: str):
    success = await graphiti_service.queue_service.retry_task(task_id)
    if not success:
        raise HTTPException(
            status_code=400, detail="Failed to retry task or task not found/not failed"
        )
    return {"message": "Task retried successfully"}
