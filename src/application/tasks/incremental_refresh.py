"""Incremental refresh task handler for reprocessing episodes."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from graphiti_core.nodes import EpisodeType, EpisodicNode
from graphiti_core.utils.maintenance.graph_data_operations import retrieve_episodes

from src.domain.tasks.base import TaskHandler

logger = logging.getLogger(__name__)


class IncrementalRefreshTaskHandler(TaskHandler):
    """Handler for incremental refresh tasks."""

    @property
    def task_type(self) -> str:
        return "incremental_refresh"

    @property
    def timeout_seconds(self) -> int:
        return 3600  # 1 hour

    async def process(self, payload: Dict[str, Any], context: Any) -> None:
        """Reprocess specified episodes to refresh graph knowledge."""
        queue_service = context
        graphiti_client = queue_service._graphiti_client

        episode_uuids = payload.get("episode_uuids")
        group_id = payload.get("group_id", "global")
        rebuild_communities = payload.get("rebuild_communities", False)
        project_id = payload.get("project_id")
        tenant_id = payload.get("tenant_id")
        user_id = payload.get("user_id")

        try:
            # Step 1: Get episodes to refresh
            if episode_uuids:
                episodes = await self._get_episodes_by_uuids(graphiti_client.driver, episode_uuids)
            else:
                # Get recent episodes (last 24 hours)
                reference_time = datetime.now(timezone.utc)
                episodes = await retrieve_episodes(
                    driver=graphiti_client.driver,
                    reference_time=reference_time,
                    last_n=100,
                    group_ids=[group_id] if group_id != "global" else None
                )

            logger.info(f"Incremental refresh: processing {len(episodes)} episodes")

            # Step 2: Load schema if available
            entity_types = None
            edge_types = None
            edge_type_map = None

            if queue_service._schema_loader and project_id:
                try:
                    entity_types, edge_types, edge_type_map = await queue_service._schema_loader(project_id)
                except Exception as e:
                    logger.warning(f"Failed to load schema: {e}")

            # Step 3: Reprocess each episode
            for episode in episodes:
                await self._reprocess_episode(
                    graphiti_client, episode, group_id, project_id,
                    entity_types, edge_types, edge_type_map,
                    tenant_id, user_id, queue_service
                )

            # Step 4: Optionally rebuild communities
            if rebuild_communities:
                logger.info("Triggering community rebuild after incremental refresh")
                await queue_service.rebuild_communities(task_group_id=group_id)

            logger.info(f"Incremental refresh completed: {len(episodes)} episodes processed")

        except Exception as e:
            logger.error(f"Incremental refresh failed: {e}")
            raise

    async def _get_episodes_by_uuids(self, driver, uuids: list[str]) -> list[EpisodicNode]:
        """Fetch specific episodes by UUIDs."""
        if not uuids:
            return []

        episodes = await EpisodicNode.get_by_uuids(driver, uuids)
        return episodes if episodes else []

    async def _reprocess_episode(
        self, graphiti_client, episode: EpisodicNode, group_id: str,
        project_id: str, entity_types, edge_types, edge_type_map,
        tenant_id: str, user_id: str, queue_service
    ):
        """Reprocess a single episode."""
        add_result = await graphiti_client.add_episode(
            name=episode.name,
            episode_body=episode.content,
            source_description=episode.source_description,
            source=EpisodeType(episode.source) if episode.source else EpisodeType.text,
            group_id=group_id,
            reference_time=episode.valid_at,
            update_communities=False,
            entity_types=entity_types,
            edge_types=edge_types,
            edge_type_map=edge_type_map,
            uuid=episode.uuid,
        )

        # Sync schema
        if add_result and project_id:
            await queue_service._sync_schema_from_graph_result(
                add_result.nodes, add_result.edges, project_id
            )

        # Propagate metadata
        await self._propagate_metadata(
            graphiti_client.driver, episode.uuid, tenant_id, project_id, user_id
        )

    async def _propagate_metadata(
        self, driver, episode_uuid: str,
        tenant_id: str, project_id: str, user_id: str
    ):
        """Propagate tenant/project/user metadata to graph entities."""
        query = """
        MATCH (ep:Episodic {uuid: $uuid})
        SET ep.tenant_id = $tenant_id,
            ep.project_id = $project_id,
            ep.user_id = $user_id
        WITH ep
        MATCH (ep)-[:MENTIONS]->(e:Entity)
        SET e.tenant_id = $tenant_id,
            e.project_id = $project_id,
            e.user_id = $user_id
        """
        await driver.execute_query(
            query,
            uuid=episode_uuid,
            tenant_id=tenant_id,
            project_id=project_id,
            user_id=user_id
        )
