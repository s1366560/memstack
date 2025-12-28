import logging
from typing import Any, Dict

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
        """Process rebuild_communities task."""
        queue_service = context
        group_id = payload.get("group_id")
        
        try:
            # Graphiti's build_communities automatically removes old communities
            # Pass group_ids to scope the rebuild to the specific project/group
            group_ids = [group_id] if group_id and group_id != "global" else None
            
            logger.info(f"Starting community rebuild for group: {group_id}")
            await queue_service._graphiti_client.build_communities(group_ids=group_ids)

            # After rebuilding, we should re-apply tenant/project/user IDs to the new communities
            query = """
            MATCH (c:Community)-[:HAS_MEMBER]->(e:Entity)
            WITH c, e
            WHERE e.tenant_id IS NOT NULL
            WITH c, e.tenant_id as tid, count(*) as count
            ORDER BY count DESC
            WITH c, collect(tid)[0] as major_tenant
            SET c.tenant_id = major_tenant
            """
            await queue_service._graphiti_client.driver.execute_query(query)

            query_proj = """
            MATCH (c:Community)-[:HAS_MEMBER]->(e:Entity)
            WITH c, e
            WHERE e.project_id IS NOT NULL
            WITH c, e.project_id as pid, count(*) as count
            ORDER BY count DESC
            WITH c, collect(pid)[0] as major_project
            SET c.project_id = major_project
            """
            await queue_service._graphiti_client.driver.execute_query(query_proj)

            # Count members for each community
            count_query = """
            MATCH (c:Community)-[:HAS_MEMBER]->(e:Entity)
            WITH c, count(e) as member_count
            SET c.member_count = member_count
            """
            await queue_service._graphiti_client.driver.execute_query(count_query)

            logger.info("Communities rebuild triggered successfully and properties updated")
        except Exception as e:
            logger.error(f"Failed to rebuild communities: {e}")
            raise e
