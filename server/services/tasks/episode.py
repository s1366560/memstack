import logging
from datetime import datetime, timezone
from typing import Any, Dict

from graphiti_core.helpers import semaphore_gather
from graphiti_core.nodes import EpisodeType
from graphiti_core.utils.maintenance.community_operations import update_community

from server.models.enums import ProcessingStatus
from server.services.tasks.base import TaskHandler

logger = logging.getLogger(__name__)

class EpisodeTaskHandler(TaskHandler):
    @property
    def task_type(self) -> str:
        return "add_episode"

    async def process(self, payload: Dict[str, Any], context: Any) -> None:
        """Process add_episode task."""
        # Context is expected to be the QueueService instance
        queue_service = context
        
        uuid = payload.get("uuid")
        group_id = payload.get("group_id")
        memory_id = payload.get("memory_id")
        project_id = payload.get("project_id")

        try:
            if memory_id:
                await queue_service._update_memory_status(memory_id, ProcessingStatus.PROCESSING)

            # Re-fetch schema if possible
            entity_types = None
            edge_types = None
            edge_type_map = None

            if queue_service._schema_loader and project_id:
                try:
                    entity_types, edge_types, edge_type_map = await queue_service._schema_loader(project_id)
                except Exception as e:
                    logger.warning(f"Failed to load schema for project {project_id}: {e}")

            # Call Graphiti
            add_result = await queue_service._graphiti_client.add_episode(
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
                await queue_service._sync_schema_from_graph_result(
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
                await queue_service._graphiti_client.driver.execute_query(
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
                await queue_service._graphiti_client.driver.execute_query(query, uuid=uuid)

            # Community updates
            if add_result and add_result.nodes:
                try:
                    await semaphore_gather(
                        *[
                            update_community(
                                queue_service._graphiti_client.driver,
                                queue_service._graphiti_client.llm_client,
                                queue_service._graphiti_client.embedder,
                                node,
                            )
                            for node in add_result.nodes
                        ],
                        max_coroutines=queue_service._graphiti_client.max_coroutines,
                    )

                    # Propagate metadata to communities
                    if tenant_id or project_id:
                        query = """
                        MATCH (ep:Episodic {uuid: $uuid})-[:MENTIONS]->(e:Entity)-[:BELONGS_TO]->(c:Community)
                        SET c.tenant_id = $tenant_id,
                            c.project_id = $project_id
                        """
                        await queue_service._graphiti_client.driver.execute_query(
                            query, uuid=uuid, tenant_id=tenant_id, project_id=project_id
                        )
                except Exception as e:
                    logger.warning(f"Failed to update communities for episode {uuid}: {e}")

            if memory_id:
                await queue_service._update_memory_status(memory_id, ProcessingStatus.COMPLETED)

        except Exception as e:
            if memory_id:
                await queue_service._update_memory_status(memory_id, ProcessingStatus.FAILED)
            raise e
