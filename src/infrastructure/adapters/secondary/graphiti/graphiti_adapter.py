import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from graphiti_core.search.search_config import SearchConfig
from graphiti_core.search.search_config_recipes import COMBINED_HYBRID_SEARCH_RRF

from src.domain.ports.services.graph_service_port import GraphServicePort
from src.domain.ports.services.queue_port import QueuePort
from src.domain.model.memory.episode import Episode

logger = logging.getLogger(__name__)

class GraphitiAdapter(GraphServicePort):
    def __init__(self, client: Graphiti, queue_port: Optional[QueuePort] = None):
        self.client = client
        self.queue_port = queue_port

    async def add_episode(self, episode: Episode) -> Episode:
        try:
            group_id = episode.project_id or "global"
            
            # 1. Create initial node in Graphiti/Neo4j (Synchronous part)
            query = """
                MERGE (e:Episodic {uuid: $uuid})
                SET e:Node,
                    e.name = $name,
                    e.content = $content,
                    e.source_description = $source_description,
                    e.source = $source,
                    e.created_at = datetime($created_at),
                    e.valid_at = datetime($valid_at),
                    e.group_id = $group_id,
                    e.tenant_id = $tenant_id,
                    e.project_id = $project_id,
                    e.user_id = $user_id,
                    e.memory_id = $memory_id,
                    e.status = 'Processing'
            """
            
            params = {
                "uuid": episode.id,
                "name": episode.name or episode.id,
                "content": episode.content,
                "source_description": episode.source_type.value,
                "source": EpisodeType.text.value,
                "created_at": datetime.utcnow().isoformat(),
                "valid_at": episode.valid_at.isoformat() if episode.valid_at else datetime.utcnow().isoformat(),
                "group_id": group_id,
                "tenant_id": episode.tenant_id,
                "project_id": episode.project_id,
                "user_id": episode.user_id,
                "memory_id": episode.metadata.get("memory_id")
            }
            
            await self.client.driver.execute_query(query, **params)
            
            # 2. Trigger Background Processing via Queue (Asynchronous part)
            if self.queue_port:
                await self.queue_port.add_episode(
                    group_id=group_id,
                    name=episode.name or episode.id,
                    content=episode.content,
                    source_description=episode.source_type.value,
                    episode_type=EpisodeType.text.value,
                    uuid=episode.id,
                    tenant_id=episode.tenant_id,
                    project_id=episode.project_id,
                    user_id=episode.user_id,
                    memory_id=episode.metadata.get("memory_id")
                )
            else:
                logger.warning("QueuePort not configured. Episode will not be processed asynchronously.")
            
            return episode
            
        except Exception as e:
            logger.error(f"Failed to add episode to Graphiti: {e}")
            raise

    async def search(self, query: str, project_id: Optional[str] = None, limit: int = 10) -> List[Any]:
        try:
            group_ids = [project_id] if project_id else None
            config = COMBINED_HYBRID_SEARCH_RRF
            
            search_results = await self.client.search_(
                query=query,
                config=config,
                group_ids=group_ids
            )
            
            items = []
            if hasattr(search_results, "episodes") and search_results.episodes:
                for ep in search_results.episodes:
                    items.append({
                        "type": "episode",
                        "content": ep.content,
                        "uuid": ep.uuid
                    })
            
            if hasattr(search_results, "nodes") and search_results.nodes:
                for node in search_results.nodes:
                    items.append({
                        "type": "entity",
                        "name": node.name,
                        "summary": getattr(node, "summary", ""),
                        "uuid": node.uuid
                    })
                    
            return items[:limit]
            
        except Exception as e:
            logger.error(f"Graphiti search failed: {e}")
            raise

    async def get_graph_data(self, project_id: str, limit: int = 100) -> Dict[str, Any]:
        # Implementation of get_graph_data logic
        return {}

    async def delete_episode(self, episode_name: str) -> bool:
        # Implementation
        return True

    async def delete_episode_by_memory_id(self, memory_id: str) -> bool:
        query = "MATCH (e:Episodic {memory_id: $memory_id}) DETACH DELETE e"
        await self.client.driver.execute_query(query, memory_id=memory_id)
        return True
