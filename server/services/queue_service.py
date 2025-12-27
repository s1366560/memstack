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
from graphiti_core.helpers import semaphore_gather
from graphiti_core.nodes import EpisodeType
from graphiti_core.utils.maintenance.community_operations import update_community
from sqlalchemy import select, update

from server.config import get_settings
from server.database import async_session_factory
from server.db_models import EdgeType, EdgeTypeMap, EntityType, Memory, TaskLog
from server.models.enums import DataStatus, ProcessingStatus

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

    async def _create_task_log(self, group_id: str, task_type: str, payload: dict) -> str:
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

                    if worker_id:
                        stmt = stmt.values(worker_id=worker_id)
                    if error_message:
                        stmt = stmt.values(error_message=error_message)
                    if increment_retry:
                        # This is tricky with simple update, need to read or use expression
                        # But for now let's just use SQL expression if possible or read-update
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
        episode_type: EpisodeType,
        entity_types: Any,  # Kept for compatibility, but might not be serializable
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
        # Note: entity_types, edge_types, edge_type_map are Pydantic models or dicts
        # We cannot easily serialize them if they are classes.
        # However, we have project_id, so the worker can re-fetch the schema.
        # We will NOT include them in the payload to avoid serialization issues.
        payload = {
            "group_id": group_id,
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
        task_id = await self._create_task_log(group_id, "add_episode", payload)
        payload["task_id"] = task_id

        # Add to Redis
        # 1. Add group_id to active groups set
        await self._redis.sadd("queue:active_groups", group_id)
        # 2. Push task to group queue
        queue_key = f"queue:group:{group_id}"
        await self._redis.rpush(queue_key, json.dumps(payload))

        logger.info(f"Task {task_id} added to queue {queue_key}")
        return await self._redis.llen(queue_key)

    async def _process_episode_task(self, payload: dict) -> None:
        """Process the episode task logic."""
        uuid = payload.get("uuid")
        group_id = payload.get("group_id")
        memory_id = payload.get("memory_id")
        project_id = payload.get("project_id")

        try:
            if memory_id:
                await self._update_memory_status(memory_id, ProcessingStatus.PROCESSING)

            # Re-fetch schema if possible
            entity_types = None
            edge_types = None
            edge_type_map = None

            if self._schema_loader and project_id:
                try:
                    entity_types, edge_types, edge_type_map = await self._schema_loader(project_id)
                except Exception as e:
                    logger.warning(f"Failed to load schema for project {project_id}: {e}")

            # Call Graphiti
            add_result = await self._graphiti_client.add_episode(
                name=payload.get("name"),
                episode_body=payload.get("content"),
                source_description=payload.get("source_description"),
                source=EpisodeType(payload.get("episode_type", "text")),
                group_id=group_id,
                reference_time=datetime.now(timezone.utc),
                update_communities=False,
                entity_types=entity_types,
                edge_types=edge_types,
                edge_type_map=edge_type_map,
                uuid=uuid,
            )

            # Sync Schema from Graphiti result
            if add_result and project_id:
                await self._sync_schema_from_graph_result(
                    add_result.nodes, add_result.edges, project_id
                )

            # Metadata propagation logic
            tenant_id = payload.get("tenant_id")
            user_id = payload.get("user_id")

            if tenant_id or project_id or user_id:
                query = """
                MATCH (ep:Episodic {uuid: $uuid})
                SET ep.tenant_id = $tenant_id,
                    ep.project_id = $project_id,
                    ep.user_id = $user_id,
                    ep.status = 'Synced'
                WITH ep
                MATCH (ep)-[:MENTIONS]->(e:Entity)
                SET e.tenant_id = ep.tenant_id,
                    e.project_id = ep.project_id,
                    e.user_id = ep.user_id
                """
                await self._graphiti_client.driver.execute_query(
                    query,
                    uuid=uuid,
                    tenant_id=tenant_id,
                    project_id=project_id,
                    user_id=user_id,
                )
            else:
                query = """
                MATCH (ep:Episodic {uuid: $uuid})
                SET ep.status = 'Synced'
                """
                await self._graphiti_client.driver.execute_query(query, uuid=uuid)

            # Community updates
            if add_result and add_result.nodes:
                try:
                    await semaphore_gather(
                        *[
                            update_community(
                                self._graphiti_client.driver,
                                self._graphiti_client.llm_client,
                                self._graphiti_client.embedder,
                                node,
                            )
                            for node in add_result.nodes
                        ],
                        max_coroutines=self._graphiti_client.max_coroutines,
                    )

                    # Propagate metadata to communities
                    if tenant_id or project_id:
                        query = """
                        MATCH (ep:Episodic {uuid: $uuid})-[:MENTIONS]->(e:Entity)-[:BELONGS_TO]->(c:Community)
                        SET c.tenant_id = $tenant_id,
                            c.project_id = $project_id
                        """
                        await self._graphiti_client.driver.execute_query(
                            query, uuid=uuid, tenant_id=tenant_id, project_id=project_id
                        )
                except Exception as e:
                    logger.warning(f"Failed to update communities for episode {uuid}: {e}")

            if memory_id:
                await self._update_memory_status(memory_id, ProcessingStatus.COMPLETED)

        except Exception as e:
            if memory_id:
                await self._update_memory_status(memory_id, ProcessingStatus.FAILED)
            raise e

    async def _worker_loop(self, worker_index: int) -> None:
        """Worker loop to process tasks from Redis."""
        logger.info(f"Worker {worker_index} started")

        # Processing queue key for this worker (or global if we want simple recovery)
        # Using a global processing queue simplifies recovery logic.
        processing_queue = "queue:processing:global"

        while not self._shutdown_event.is_set():
            try:
                # 1. Get active groups
                active_groups = await self._redis.smembers("queue:active_groups")
                if not active_groups:
                    await asyncio.sleep(1)
                    continue

                # 2. Pick a group (Random for simple load balancing)
                # Redis SET is unordered, so iterating or popping is random-ish.
                # To prevent starvation, we could cycle through them, but random is often enough.
                # Let's pick one randomly using SRANDMEMBER
                group_id = await self._redis.srandmember("queue:active_groups")
                if not group_id:
                    continue

                queue_key = f"queue:group:{group_id}"

                # 3. Move task from pending to processing atomically
                # RPOPLPUSH (or LMOVE)
                # source: queue:group:{group_id}
                # dest: queue:processing:global
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
                        await self._process_episode_task(payload)

                        # Success: Remove from processing queue
                        await self._redis.lrem(processing_queue, 1, raw_task)

                        if task_id:
                            await self._update_task_log(task_id, "COMPLETED")

                    except Exception as e:
                        logger.error(f"Error processing task {task_id}: {e}")
                        # Failure: Remove from processing queue?
                        # If we remove it, it won't be retried.
                        # If we keep it, recovery loop will pick it up.
                        # For now, let's remove it and mark FAILED in DB.
                        # If we want retries, we should re-enqueue it with incremented retry count.

                        await self._redis.lrem(processing_queue, 1, raw_task)

                        if task_id:
                            await self._update_task_log(task_id, "FAILED", error_message=str(e))
                else:
                    # Queue empty, remove from active set
                    # Use watch/multi for strict correctness, but here it's fine
                    # If we check and it's empty, remove. If someone added in between, it will be added back.
                    qlen = await self._redis.llen(queue_key)
                    if qlen == 0:
                        await self._redis.srem("queue:active_groups", group_id)

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
        timeout_seconds = 600  # 10 minutes

        while not self._shutdown_event.is_set():
            try:
                # Check tasks in processing queue
                # This is O(N) where N is number of processing tasks. Should be small.
                tasks = await self._redis.lrange(processing_queue, 0, -1)

                now = time.time()
                for raw_task in tasks:
                    try:
                        payload = json.loads(raw_task)
                        timestamp = payload.get("timestamp", 0)

                        if now - timestamp > timeout_seconds:
                            task_id = payload.get("task_id")
                            logger.warning(f"Recovering stalled task {task_id}")

                            # Remove from processing
                            await self._redis.lrem(processing_queue, 1, raw_task)

                            # Update timestamp to avoid immediate re-recovery
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

                    if task.status != "FAILED":
                        logger.warning(
                            f"Task {task_id} is not FAILED (status: {task.status}), skipping retry"
                        )
                        return False

                    # Reset status
                    task.status = "PENDING"
                    task.retry_count += 1
                    task.error_message = None
                    task.started_at = None
                    task.completed_at = None

                    payload = task.payload
                    group_id = task.group_id

            # Re-enqueue
            if payload and group_id:
                # Ensure payload has task_id
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

    async def get_queue_size(self, group_id: str) -> int:
        """Get the current queue size for a group_id."""
        if not self._redis:
            return 0
        return await self._redis.llen(f"queue:group:{group_id}")
