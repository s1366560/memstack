import logging
from asyncio import gather
from typing import Any, Dict

from graphiti_core.utils.maintenance.community_operations import build_communities

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
        1. Remove existing communities for the specified project
        2. Detect new communities using Louvain algorithm (scoped to project)
        3. Generate community summaries and embeddings
        4. Set project_id = group_id for proper project association
        5. Calculate member_count using Neo4j 5.x compatible syntax

        Project Isolation:
        - Only processes communities for the specified project_id
        - Does not affect communities from other projects

        Args:
            payload: Contains task_group_id (project UUID) - renamed to avoid conflict with graphiti's group_id
            context: Queue service context
        """
        queue_service = context
        # task_group_id is the project_id from our application domain
        # It maps to group_id in graphiti's data model
        task_group_id = payload.get("task_group_id")
        task_id = payload.get("task_id")  # Get task_id for progress updates
        graphiti_client = queue_service._graphiti_client

        async def update_progress(progress: int, message: str = None):
            """Helper to update task progress."""
            if task_id:
                await queue_service._update_task_log(
                    task_id, "PROCESSING", progress=progress, message=message
                )

        if not task_group_id:
            logger.error("task_group_id (project_id) is required for rebuild_communities task")
            raise ValueError("task_group_id (project_id) is required")

        try:
            logger.info(f"Starting community rebuild for project: {task_group_id}")
            await update_progress(10, "Removing existing communities...")

            # Step 1: Remove existing communities for this project only
            logger.info(f"Removing existing communities for project: {task_group_id}...")
            # Directly remove communities for this project (since installed graphiti doesn't support group_ids)
            await graphiti_client.driver.execute_query(
                """
                MATCH (c:Community)
                WHERE c.group_id = $group_id
                DETACH DELETE c
                """,
                group_id=task_group_id,
            )

            await update_progress(30, "Detecting communities using Louvain algorithm...")

            # Step 2: Build new communities using Louvain algorithm (scoped to this project)
            logger.info(f"Building new communities for project: {task_group_id}...")
            community_nodes, community_edges = await build_communities(
                driver=graphiti_client.driver,
                llm_client=graphiti_client.llm_client,
                group_ids=[task_group_id],  # Map task_group_id to graphiti's group_ids parameter
            )

            await update_progress(50, f"Found {len(community_nodes)} communities. Generating embeddings...")

            # Step 3: Generate embeddings and save communities with project_id
            logger.info(
                f"Generating embeddings for {len(community_nodes)} communities for project: {task_group_id}"
            )

            async def generate_and_save_community(community_node):
                """Generate embedding and save community with project_id."""
                # Generate embedding before saving to avoid null vector error
                await community_node.generate_name_embedding(graphiti_client.embedder)
                await community_node.save(graphiti_client.driver)

                # CRITICAL: Set project_id = group_id for proper project association
                # Also initialize member_count to avoid "property key does not exist" warnings
                await graphiti_client.driver.execute_query(
                    """
                    MATCH (c:Community {uuid: $uuid})
                    SET c.project_id = c.group_id,
                        c.member_count = 0
                    """,
                    uuid=community_node.uuid,
                )

                logger.debug(
                    f"Saved community {community_node.uuid} with project_id={community_node.group_id}"
                )
                return community_node

            # Save all communities with embeddings
            logger.info(
                f"Saving {len(community_nodes)} communities to database for project: {task_group_id}..."
            )
            saved_communities = await gather(
                *[generate_and_save_community(node) for node in community_nodes]
            )

            await update_progress(75, "Saving community relationships...")

            # Step 4: Save all edges (HAS_MEMBER relationships)
            logger.info(f"Saving {len(community_edges)} community edges for project: {task_group_id}...")

            async def save_edge(community_edge):
                """Save community edge."""
                return await community_edge.save(graphiti_client.driver)

            saved_edges = await gather(*[save_edge(edge) for edge in community_edges])

            await update_progress(90, "Calculating member counts...")

            # Step 5: Calculate and set member_count for all communities (after edges are created)
            # Use Neo4j 5.x compatible syntax (COUNT instead of size() with pattern expression)
            logger.info("Calculating member counts...")
            for community_node in saved_communities:
                await graphiti_client.driver.execute_query(
                    """
                    MATCH (c:Community {uuid: $uuid})
                    OPTIONAL MATCH (c)-[:HAS_MEMBER]->(e:Entity)
                    WITH c, count(e) as member_count
                    SET c.member_count = member_count
                    """,
                    uuid=community_node.uuid,
                )
                logger.debug(f"Set member_count for community {community_node.uuid}")

            # Final update with result
            await update_progress(100, "Community rebuild completed")

            # Set final result
            if task_id:
                await queue_service._update_task_log(
                    task_id,
                    "PROCESSING",
                    progress=100,
                    message="Community rebuild completed successfully",
                    result={
                        "communities_count": len(saved_communities),
                        "edges_count": len(saved_edges),
                    }
                )

            logger.info(
                f"Successfully rebuilt {len(saved_communities)} communities with {len(saved_edges)} edges for project: {task_group_id}"
            )

        except Exception as e:
            logger.error(f"Failed to rebuild communities: {e}")
            if task_id:
                await queue_service._update_task_log(
                    task_id, "FAILED", error_message=str(e)
                )
            raise e
