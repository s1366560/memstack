"""Queue service for managing episode processing."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any, Optional

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class QueueService:
    """Service for managing sequential episode processing queues by group_id."""

    def __init__(self):
        """Initialize the queue service."""
        # Dictionary to store queues for each group_id
        self._episode_queues: dict[str, asyncio.Queue] = {}
        # Dictionary to track if a worker is running for each group_id
        self._queue_workers: dict[str, bool] = {}
        # Store the graphiti client after initialization
        self._graphiti_client: Optional[Graphiti] = None

    async def add_episode_task(
        self, group_id: str, process_func: Callable[[], Awaitable[None]]
    ) -> int:
        """Add an episode processing task to the queue.

        Args:
            group_id: The group ID for the episode
            process_func: The async function to process the episode

        Returns:
            The position in the queue
        """
        # Initialize queue for this group_id if it doesn't exist
        if group_id not in self._episode_queues:
            self._episode_queues[group_id] = asyncio.Queue()

        # Add the episode processing function to the queue
        await self._episode_queues[group_id].put(process_func)

        # Start a worker for this queue if one isn't already running
        if not self._queue_workers.get(group_id, False):
            asyncio.create_task(self._process_episode_queue(group_id))

        return self._episode_queues[group_id].qsize()

    async def _process_episode_queue(self, group_id: str) -> None:
        """Process episodes for a specific group_id sequentially.

        This function runs as a long-lived task that processes episodes
        from the queue one at a time.
        """
        logger.info(f'Starting episode queue worker for group_id: {group_id}')
        self._queue_workers[group_id] = True

        try:
            while True:
                # Get the next episode processing function from the queue
                # This will wait if the queue is empty
                process_func = await self._episode_queues[group_id].get()

                try:
                    # Process the episode
                    await process_func()
                except Exception as e:
                    logger.error(
                        f'Error processing queued episode for group_id {group_id}: {str(e)}'
                    )
                finally:
                    # Mark the task as done regardless of success/failure
                    self._episode_queues[group_id].task_done()
        except asyncio.CancelledError:
            logger.info(f'Episode queue worker for group_id {group_id} was cancelled')
        except Exception as e:
            logger.error(f'Unexpected error in queue worker for group_id {group_id}: {str(e)}')
        finally:
            self._queue_workers[group_id] = False
            logger.info(f'Stopped episode queue worker for group_id: {group_id}')

    def get_queue_size(self, group_id: str) -> int:
        """Get the current queue size for a group_id."""
        if group_id not in self._episode_queues:
            return 0
        return self._episode_queues[group_id].qsize()

    def is_worker_running(self, group_id: str) -> bool:
        """Check if a worker is running for a group_id."""
        return self._queue_workers.get(group_id, False)

    async def initialize(self, graphiti_client: Graphiti) -> None:
        """Initialize the queue service with a graphiti client.

        Args:
            graphiti_client: The graphiti client instance to use for processing episodes
        """
        self._graphiti_client = graphiti_client
        logger.info('Queue service initialized with graphiti client')

    async def add_episode(
        self,
        group_id: str,
        name: str,
        content: str,
        source_description: str,
        episode_type: EpisodeType,
        entity_types: Any,
        uuid: str | None,
        tenant_id: Optional[str] = None,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> int:
        """Add an episode for processing.

        Args:
            group_id: The group ID for the episode
            name: Name of the episode
            content: Episode content
            source_description: Description of the episode source
            episode_type: Type of the episode
            entity_types: Entity types for extraction
            uuid: Episode UUID
            tenant_id: Tenant ID for metadata
            project_id: Project ID for metadata
            user_id: User ID for metadata

        Returns:
            The position in the queue
        """
        if self._graphiti_client is None:
            raise RuntimeError('Queue service not initialized. Call initialize() first.')

        async def process_episode():
            """Process the episode using the graphiti client."""
            try:
                logger.info(f'Processing episode {uuid} for group {group_id}')

                # Process the episode using the graphiti client
                from graphiti_core.utils.maintenance.community_operations import update_community
                from graphiti_core.helpers import semaphore_gather

                add_result = await self._graphiti_client.add_episode(
                    name=name,
                    episode_body=content,
                    source_description=source_description,
                    source=episode_type,
                    group_id=group_id,
                    reference_time=datetime.now(timezone.utc),
                    update_communities=False, 
                    entity_types=entity_types,
                    uuid=uuid,
                )

                # Propagate metadata to extracted entities
                if tenant_id or project_id or user_id:
                    try:
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
                            user_id=user_id
                        )
                        logger.info(f"Metadata propagated to entities for episode {uuid}")
                    except Exception as e:
                        logger.warning(f"Failed to propagate metadata for episode {uuid}: {e}")
                else:
                     # If no metadata to propagate, still update status to Synced
                     try:
                        query = """
                        MATCH (ep:Episodic {uuid: $uuid})
                        SET ep.status = 'Synced'
                        """
                        await self._graphiti_client.driver.execute_query(query, uuid=uuid)
                     except Exception as e:
                        logger.warning(f"Failed to update status for episode {uuid}: {e}")
                
                # Manual community update
                if add_result and add_result.nodes:
                    try:
                        await semaphore_gather(
                            *[
                                update_community(self._graphiti_client.driver, self._graphiti_client.llm_client, self._graphiti_client.embedder, node)
                                for node in add_result.nodes
                            ],
                            max_coroutines=self._graphiti_client.max_coroutines,
                        )
                        logger.info(f"Communities updated successfully for episode {uuid}")

                        # Propagate metadata to communities
                        if tenant_id or project_id:
                            query = """
                            MATCH (ep:Episodic {uuid: $uuid})-[:MENTIONS]->(e:Entity)-[:BELONGS_TO]->(c:Community)
                            SET c.tenant_id = $tenant_id,
                                c.project_id = $project_id
                            """
                            await self._graphiti_client.driver.execute_query(
                                query,
                                uuid=uuid,
                                tenant_id=tenant_id,
                                project_id=project_id
                            )
                    except Exception as e:
                        logger.warning(f"Failed to update communities for episode {uuid}: {e}")

                logger.info(f'Successfully processed episode {uuid} for group {group_id}')

            except Exception as e:
                logger.error(f'Failed to process episode {uuid} for group {group_id}: {str(e)}')
                raise

        # Use the existing add_episode_task method to queue the processing
        return await self.add_episode_task(group_id, process_episode)
