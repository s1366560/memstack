"""Queue service for managing episode processing using Redis."""

import asyncio
import json
import logging
import socket
import time
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Optional
from uuid import uuid4

import redis.asyncio as redis
from graphiti_core import Graphiti
from sqlalchemy import select, update

from src.configuration.config import get_settings
from src.infrastructure.adapters.secondary.persistence.database import async_session_factory
from src.infrastructure.adapters.secondary.persistence.models import (
    EdgeType,
    EdgeTypeMap,
    EntityType,
    Memory,
    TaskLog,
)
from src.domain.model.enums import DataStatus, ProcessingStatus
from src.application.tasks.registry import TaskRegistry

logger = logging.getLogger(__name__)


class QueueService:
    """Service for managing persistent episode processing queues using Redis."""

    def __init__(self):
        """Initialize the queue service."""
        self._settings = get_settings()
        self._redis: Optional[redis.Redis] = None
        self._graphiti_client: Optional[Graphiti] = None
        self._schema_loader: Optional[Callable[[str], Awaitable[tuple]]] = None
        self._shutdown_event = asyncio.Event()
        self._workers: list[asyncio.Task] = []
        self._recovery_task: Optional[asyncio.Task] = None
        self._worker_id = f"{socket.gethostname()}-{uuid4().hex[:8]}"
        self._task_registry = TaskRegistry()

    async def initialize(
        self,
        graphiti_client: Graphiti,
        schema_loader: Optional[Callable[[str], Awaitable[tuple]]] = None,
        run_workers: bool = True,
    ) -> None:
        """Initialize the queue service with a graphiti client and redis connection.

        Args:
            graphiti_client: The graphiti client instance
            schema_loader: Async function to load schema (entity_types, edge_types, edge_type_map) by project_id
            run_workers: Whether to start worker loops. Set to False for API-only instances.
        """
        self._graphiti_client = graphiti_client
        self._schema_loader = schema_loader

        # Initialize Redis connection
        logger.info(f"Connecting to Redis at {self._settings.redis_url}")
        self._redis = redis.from_url(
            self._settings.redis_url, encoding="utf-8", decode_responses=True
        )

        if run_workers:
            # Register default tasks here to avoid circular imports if they were top-level
            # We will handle registration in the worker entrypoint or here if we can import them safely
            # For now, let's assume the worker entrypoint or a setup function registers them.
            # OR we can import them here inside the method.
            from src.application.tasks.episode import EpisodeTaskHandler
            from src.application.tasks.community import RebuildCommunityTaskHandler
            
            self._task_registry.register(EpisodeTaskHandler())
            self._task_registry.register(RebuildCommunityTaskHandler())

            # Start workers
            num_workers = self._settings.max_async_workers
            logger.info(
                f"Initializing QueueService with {num_workers} workers (ID: {self._worker_id})"
            )

            for i in range(num_workers):
                task = asyncio.create_task(self._worker_loop(i))
                self._workers.append(task)

            # Start recovery task
            self._recovery_task = asyncio.create_task(self._recovery_loop())
        else:
            logger.info("QueueService initialized in producer-only mode (no workers started)")

        logger.info("QueueService initialized")

    async def close(self) -> None:
        """Shutdown the queue service."""
        logger.info("Shutting down QueueService")
        self._shutdown_event.set()

        if self._workers:
            for task in self._workers:
                task.cancel()
            await asyncio.gather(*self._workers, return_exceptions=True)
            self._workers.clear()

        if self._recovery_task:
            self._recovery_task.cancel()
            try:
                await self._recovery_task
            except asyncio.CancelledError:
                pass
            self._recovery_task = None

        if self._redis:
            await self._redis.close()

        logger.info("QueueService shutdown complete")

    async def _update_memory_status(self, memory_id: str, status: ProcessingStatus) -> None:
        """Update memory processing status in database."""
        if not memory_id:
            return

        try:
            async with async_session_factory() as session:
                async with session.begin():
                    result = await session.execute(
                        update(Memory)
                        .where(Memory.id == memory_id)
                        .values(processing_status=status.value)
                    )
                    if result.rowcount == 0:
                        logger.warning(
                            f"Memory {memory_id} not found when updating status to {status.value}"
                        )
        except Exception as e:
            logger.error(f"Failed to update memory status {memory_id} to {status}: {e}")

    async def _create_task_log(
        self,
        group_id: str,
        task_type: str,
        payload: dict,
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        parent_task_id: Optional[str] = None,
    ) -> str:
        """Create a new task log entry."""
        task_id = str(uuid4())
        try:
            async with async_session_factory() as session:
                async with session.begin():
                    task_log = TaskLog(
                        id=task_id,
                        group_id=group_id,
                        task_type=task_type,
                        status="PENDING",
                        payload=payload,
                        created_at=datetime.now(timezone.utc),
                        entity_id=entity_id,
                        entity_type=entity_type,
                        parent_task_id=parent_task_id,
                    )
                    session.add(task_log)
            return task_id
        except Exception as e:
            logger.error(f"Failed to create task log: {e}")
            return task_id  # Return generated ID even if DB fails, to continue if possible

    async def _update_task_log(
        self,
        task_id: str,
        status: str,
        worker_id: Optional[str] = None,
        error_message: Optional[str] = None,
        increment_retry: bool = False,
    ) -> None:
        """Update task log status."""
        try:
            async with async_session_factory() as session:
                async with session.begin():
                    stmt = update(TaskLog).where(TaskLog.id == task_id).values(status=status)

                    if status == "PROCESSING":
                        stmt = stmt.values(started_at=datetime.now(timezone.utc))
                    if status in ["COMPLETED", "FAILED"]:
                        stmt = stmt.values(completed_at=datetime.now(timezone.utc))

                    if status == "FAILED" or status == "STOPPED":
                        if status == "STOPPED":
                            stmt = stmt.values(stopped_at=datetime.now(timezone.utc))

                    if worker_id:
                        stmt = stmt.values(worker_id=worker_id)
                    if error_message:
                        stmt = stmt.values(error_message=error_message)
                    if increment_retry:
                        # SQLAlchemy supports expression: TaskLog.retry_count + 1
                        stmt = stmt.values(retry_count=TaskLog.retry_count + 1)

                    await session.execute(stmt)
        except Exception as e:
            logger.error(f"Failed to update task log {task_id}: {e}")

    async def _sync_schema_from_graph_result(
        self,
        nodes: list[Any],
        edges: list[Any],
        project_id: str,
    ) -> None:
        """Sync schema from Graphiti processing result."""
        if not project_id:
            return

        try:
            async with async_session_factory() as session:
                async with session.begin():
                    # 1. Sync Entity Types
                    processed_entity_types = set()
                    for node in nodes:
                        labels = getattr(node, "labels", [])
                        for label in labels:
                            if label == "Entity" or label.startswith("Entity_"):
                                continue

                            if label in processed_entity_types:
                                continue
                            processed_entity_types.add(label)

                            # Check if exists
                            stmt = select(EntityType).where(
                                EntityType.project_id == project_id, EntityType.name == label
                            )
                            result = await session.execute(stmt)
                            existing = result.scalar_one_or_none()

                            if not existing:
                                new_type = EntityType(
                                    id=str(uuid4()),
                                    project_id=project_id,
                                    name=label,
                                    description="Auto-generated entity type from Graphiti",
                                    schema={},
                                    status=DataStatus.ENABLED,
                                    source="generated",
                                )
                                session.add(new_type)
                                logger.info(
                                    f"Auto-generated EntityType {label} for project {project_id}"
                                )

                    # 2. Sync Edge Types and Maps
                    # First build a map of node uuid -> type
                    node_type_map = {}
                    for node in nodes:
                        labels = getattr(node, "labels", [])
                        # Find specific label
                        specific_label = next(
                            (l for l in labels if l != "Entity" and not l.startswith("Entity_")),
                            "Entity",
                        )
                        node_type_map[node.uuid] = specific_label

                    processed_edge_types = set()
                    processed_edge_maps = set()

                    for edge in edges:
                        edge_name = getattr(edge, "name", None)
                        if not edge_name:
                            continue

                        # Sync EdgeType
                        if edge_name not in processed_edge_types:
                            processed_edge_types.add(edge_name)
                            stmt = select(EdgeType).where(
                                EdgeType.project_id == project_id, EdgeType.name == edge_name
                            )
                            result = await session.execute(stmt)
                            existing = result.scalar_one_or_none()

                            if not existing:
                                new_edge_type = EdgeType(
                                    id=str(uuid4()),
                                    project_id=project_id,
                                    name=edge_name,
                                    description="Auto-generated edge type from Graphiti",
                                    schema={},
                                    status=DataStatus.ENABLED,
                                    source="generated",
                                )
                                session.add(new_edge_type)
                                logger.info(
                                    f"Auto-generated EdgeType {edge_name} for project {project_id}"
                                )

                        # Sync EdgeTypeMap
                        source_uuid = getattr(edge, "source_node_uuid", None)
                        target_uuid = getattr(edge, "target_node_uuid", None)

                        if source_uuid and target_uuid:
                            # We can only map if we know the nodes.
                            # Ideally nodes are in the 'nodes' list.
                            source_type = node_type_map.get(source_uuid)
                            target_type = node_type_map.get(target_uuid)

                            if source_type and target_type:
                                map_key = (source_type, target_type, edge_name)
                                if map_key not in processed_edge_maps:
                                    processed_edge_maps.add(map_key)

                                    stmt = select(EdgeTypeMap).where(
                                        EdgeTypeMap.project_id == project_id,
                                        EdgeTypeMap.source_type == source_type,
                                        EdgeTypeMap.target_type == target_type,
                                        EdgeTypeMap.edge_type == edge_name,
                                    )
                                    result = await session.execute(stmt)
                                    existing_map = result.scalar_one_or_none()

                                    if not existing_map:
                                        new_map = EdgeTypeMap(
                                            id=str(uuid4()),
                                            project_id=project_id,
                                            source_type=source_type,
                                            target_type=target_type,
                                            edge_type=edge_name,
                                            status=DataStatus.ENABLED,
                                            source="generated",
                                        )
                                        session.add(new_map)
                                        logger.info(
                                            f"Auto-generated EdgeTypeMap {source_type}->{edge_name}->{target_type}"
                                        )

        except Exception as e:
            logger.error(f"Failed to sync schema from graph result: {e}")

    async def add_episode(
        self,
        group_id: str,
        name: str,
        content: str,
        source_description: str,
        episode_type: Any,
        entity_types: Any,  # Kept for compatibility
        uuid: str | None,
        tenant_id: Optional[str] = None,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
        memory_id: Optional[str] = None,
        edge_types: Optional[Any] = None,
        edge_type_map: Optional[Any] = None,
    ) -> int:
        """Add an episode processing task to the queue."""
        if not self._redis:
            raise RuntimeError("Queue service not initialized")

        # Prepare payload
        payload = {
            "group_id": group_id,
            "task_type": "add_episode",
            "name": name,
            "content": content,
            "source_description": source_description,
            "episode_type": episode_type.value if hasattr(episode_type, "value") else episode_type,
            "uuid": uuid,
            "tenant_id": tenant_id,
            "project_id": project_id,
            "user_id": user_id,
            "memory_id": memory_id,
            "timestamp": time.time(),
        }

        # Create Task Log
        task_id = await self._create_task_log(
            group_id, "add_episode", payload, entity_id=memory_id, entity_type="memory"
        )
        payload["task_id"] = task_id

        # Add to Redis
        await self._redis.sadd("queue:active_groups", group_id)
        queue_key = f"queue:group:{group_id}"
        await self._redis.rpush(queue_key, json.dumps(payload))

        logger.info(f"Task {task_id} added to queue {queue_key}")
        return await self._redis.llen(queue_key)

    async def rebuild_communities(self, group_id: str = "global") -> int:
        """Add a rebuild communities task to the queue."""
        if not self._redis:
            raise RuntimeError("Queue service not initialized")

        payload = {
            "group_id": group_id,
            "task_type": "rebuild_communities",
            "timestamp": time.time(),
        }

        # Create Task Log
        entity_id = group_id if group_id != "global" else None
        entity_type = "group" if entity_id else None

        task_id = await self._create_task_log(
            group_id, "rebuild_communities", payload, entity_id=entity_id, entity_type=entity_type
        )
        payload["task_id"] = task_id

        # Add to Redis
        await self._redis.sadd("queue:active_groups", group_id)
        queue_key = f"queue:group:{group_id}"
        await self._redis.rpush(queue_key, json.dumps(payload))

        logger.info(f"Task {task_id} (rebuild_communities) added to queue {queue_key}")
        return await self._redis.llen(queue_key)

    async def _worker_loop(self, worker_index: int) -> None:
        """Worker loop to process tasks from Redis."""
        logger.info(f"Worker {worker_index} started")

        processing_queue = "queue:processing:global"

        while not self._shutdown_event.is_set():
            try:
                # 1. Get active groups
                active_groups = await self._redis.smembers("queue:active_groups")
                if not active_groups:
                    await asyncio.sleep(1)
                    continue

                # 2. Pick a group (Random for simple load balancing)
                candidate_groups = await self._redis.srandmember("queue:active_groups", 5)
                if not candidate_groups:
                    await asyncio.sleep(1)
                    continue

                if isinstance(candidate_groups, str):
                    candidate_groups = [candidate_groups]

                group_id = None
                lock_acquired = False
                lock_key = None

                for candidate in candidate_groups:
                    candidate_lock_key = f"lock:queue:group:{candidate}"
                    # Use set with nx=True (set if not exists)
                    if await self._redis.set(candidate_lock_key, self._worker_id, nx=True, ex=3600):
                        group_id = candidate
                        lock_key = candidate_lock_key
                        lock_acquired = True
                        break

                if not lock_acquired:
                    await asyncio.sleep(0.5)
                    continue

                queue_key = f"queue:group:{group_id}"

                # 3. Move task from pending to processing atomically
                raw_task = None
                try:
                    raw_task = await self._redis.rpoplpush(queue_key, processing_queue)

                    if raw_task:
                        payload = json.loads(raw_task)
                        task_id = payload.get("task_id")

                        logger.info(f"Worker {worker_index} processing task {task_id}")

                        # Update Task Log
                        if task_id:
                            await self._update_task_log(
                                task_id, "PROCESSING", worker_id=self._worker_id
                            )

                        try:
                            task_type = payload.get("task_type", "add_episode")
                            handler = self._task_registry.get_handler(task_type)

                            if handler:
                                await handler.process(payload, self)
                            else:
                                logger.warning(f"No handler found for task type: {task_type}")

                            # Success: Remove from processing queue
                            await self._redis.lrem(processing_queue, 1, raw_task)

                            if task_id:
                                await self._update_task_log(task_id, "COMPLETED")

                        except Exception as e:
                            logger.error(f"Error processing task {task_id}: {e}")
                            # Failure
                            await self._redis.lrem(processing_queue, 1, raw_task)

                            if task_id:
                                await self._update_task_log(task_id, "FAILED", error_message=str(e))
                    else:
                        # Queue empty, remove from active set
                        qlen = await self._redis.llen(queue_key)
                        if qlen == 0:
                            await self._redis.srem("queue:active_groups", group_id)

                finally:
                    # Always release lock
                    if lock_acquired and lock_key:
                        await self._redis.delete(lock_key)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Unexpected error in worker {worker_index}: {e}")
                await asyncio.sleep(5)

        logger.info(f"Worker {worker_index} stopped")

    async def _recovery_loop(self) -> None:
        """Background loop to recover stalled tasks."""
        logger.info("Recovery task started")
        processing_queue = "queue:processing:global"

        # Default timeout
        default_timeout = 600

        while not self._shutdown_event.is_set():
            try:
                tasks = await self._redis.lrange(processing_queue, 0, -1)
                now = time.time()

                for raw_task in tasks:
                    try:
                        payload = json.loads(raw_task)
                        timestamp = payload.get("timestamp", 0)
                        task_type = payload.get("task_type", "add_episode")

                        # Get dynamic timeout from handler
                        handler = self._task_registry.get_handler(task_type)
                        timeout_seconds = handler.timeout_seconds if handler else default_timeout

                        if now - timestamp > timeout_seconds:
                            task_id = payload.get("task_id")
                            logger.warning(
                                f"Recovering stalled task {task_id} (Type: {task_type}, Timeout: {timeout_seconds}s)"
                            )

                            # Remove from processing
                            await self._redis.lrem(processing_queue, 1, raw_task)

                            # Update timestamp
                            payload["timestamp"] = now
                            new_raw_task = json.dumps(payload)

                            # Update DB log
                            if task_id:
                                await self._update_task_log(
                                    task_id, "PENDING", increment_retry=True
                                )

                            # Re-enqueue
                            group_id = payload.get("group_id")
                            if group_id:
                                await self._redis.sadd("queue:active_groups", group_id)
                                await self._redis.lpush(f"queue:group:{group_id}", new_raw_task)

                    except Exception as e:
                        logger.error(f"Error checking task for recovery: {e}")

                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in recovery loop: {e}")
                await asyncio.sleep(60)

    async def retry_task(self, task_id: str) -> bool:
        """Retry a failed task."""
        if not self._redis:
            return False

        try:
            async with async_session_factory() as session:
                async with session.begin():
                    # Check task status
                    result = await session.execute(select(TaskLog).where(TaskLog.id == task_id))
                    task = result.scalar_one_or_none()

                    if not task:
                        logger.warning(f"Task {task_id} not found for retry")
                        return False

                    # Allow retry if FAILED, STOPPED, or PENDING (for stuck tasks)
                    if task.status not in ["FAILED", "STOPPED", "PENDING"]:
                        logger.warning(
                            f"Task {task_id} is not FAILED/STOPPED/PENDING (status: {task.status}), skipping retry"
                        )
                        return False

                    # Reset status
                    task.status = "PENDING"
                    task.retry_count += 1
                    task.error_message = None
                    task.started_at = None
                    task.completed_at = None
                    task.stopped_at = None

                    payload = task.payload
                    group_id = task.group_id

            # Re-enqueue
            if payload and group_id:
                if "task_id" not in payload:
                    payload["task_id"] = task_id

                await self._redis.sadd("queue:active_groups", group_id)
                await self._redis.lpush(f"queue:group:{group_id}", json.dumps(payload))

                logger.info(f"Retrying task {task_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to retry task {task_id}: {e}")
            return False

    async def stop_task(self, task_id: str) -> bool:
        """Stop a task (mark as STOPPED)."""
        # Note: We cannot easily interrupt a running asyncio task on another worker.
        # But we can mark it as STOPPED in DB.
        # If it's PENDING, we can try to remove it from Redis (hard due to race conditions).
        # For now, we just update the DB status.
        try:
            await self._update_task_log(task_id, "STOPPED")
            logger.info(f"Task {task_id} marked as STOPPED")
            return True
        except Exception as e:
            logger.error(f"Failed to stop task {task_id}: {e}")
            return False

    async def get_queue_size(self, group_id: str) -> int:
        """Get the current queue size for a group_id."""
        if not self._redis:
            return 0
        return await self._redis.llen(f"queue:group:{group_id}")
