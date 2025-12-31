import logging
from typing import Any, Dict
from asyncio import gather

from graphiti_core.utils.maintenance.community_operations import (
    remove_communities,
    build_communities
)

from src.domain.tasks.base import TaskHandler

logger = logging.getLogger(__name__)

class RebuildCommunityTaskHandler(TaskHandler):
    @property
    def task_type(self) -> str:
        return "rebuild_communities"

    @property
    def timeout_seconds(self) -> int:
        return 3600  # 1 hour timeout for community rebuilding

    async def process(self, payload: Dict[str, Any], context: Any) -> None:
        """Process rebuild_communities task using full rebuild logic.

        This mirrors the do_rebuild() function from graphiti.py, including:
        1. Remove existing communities
        2. Detect new communities using Louvain algorithm
        3. Generate community summaries and embeddings
        4. Set project_id = group_id for proper project association
        5. Calculate member_count using Neo4j 5.x compatible syntax
        """
        queue_service = context
        group_id = payload.get("group_id")
        graphiti_client = queue_service._graphiti_client

        try:
            logger.info("Starting community rebuild...")

            # Step 1: Remove existing communities
            logger.info("Removing existing communities...")
            await remove_communities(graphiti_client.driver)

            # Step 2: Build new communities using Louvain algorithm
            logger.info("Building new communities...")
            community_nodes, community_edges = await build_communities(
                driver=graphiti_client.driver,
                llm_client=graphiti_client.llm_client,
                group_ids=None  # Rebuild all groups
            )

            # Step 3: Generate embeddings and save communities with project_id
            logger.info(f"Generating embeddings for {len(community_nodes)} communities...")

            async def generate_and_save_community(community_node):
                """Generate embedding and save community with project_id."""
                # Generate embedding before saving to avoid null vector error
                await community_node.generate_name_embedding(graphiti_client.embedder)
                await community_node.save(graphiti_client.driver)

                # CRITICAL: Set project_id = group_id for proper project association
                await graphiti_client.driver.execute_query(
                    """
                    MATCH (c:Community {uuid: $uuid})
                    SET c.project_id = c.group_id
                    """,
                    uuid=community_node.uuid
                )

                logger.debug(f"Saved community {community_node.uuid} with project_id={community_node.group_id}")
                return community_node

            # Save all communities with embeddings
            logger.info("Saving communities to database...")
            saved_communities = await gather(*[
                generate_and_save_community(node) for node in community_nodes
            ])

            # Step 4: Save all edges (HAS_MEMBER relationships)
            logger.info("Saving community edges...")

            async def save_edge(community_edge):
                """Save community edge."""
                return await community_edge.save(graphiti_client.driver)

            saved_edges = await gather(*[save_edge(edge) for edge in community_edges])

            # Step 5: Calculate and set member_count for all communities (after edges are created)
            # Use Neo4j 5.x compatible syntax (COUNT instead of size() with pattern expression)
            logger.info("Calculating member counts...")
            for community_node in saved_communities:
                await graphiti_client.driver.execute_query(
                    """
                    MATCH (c:Community {uuid: $uuid})
                    SET c.member_count = (
                        MATCH (c)-[:HAS_MEMBER]->(e:Entity)
                        RETURN count(e)
                    )
                    """,
                    uuid=community_node.uuid
                )
                logger.debug(f"Set member_count for community {community_node.uuid}")

            logger.info(f"Successfully rebuilt {len(saved_communities)} communities with {len(saved_edges)} edges")

        except Exception as e:
            logger.error(f"Failed to rebuild communities: {e}")
            raise e
