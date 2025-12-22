"""Graphiti integration service for VIP Memory."""

import os

# 禁用 Graphiti 的 PostHog 遥测 - 必须在导入 graphiti_core 之前设置
os.environ["GRAPHITI_TELEMETRY_ENABLED"] = "false"
# 同时设置 PostHog 禁用环境变量作为双保险
os.environ["POSTHOG_DISABLED"] = "1"

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from graphiti_core import Graphiti
from graphiti_core.cross_encoder.gemini_reranker_client import GeminiRerankerClient
from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig
from graphiti_core.llm_client import LLMConfig
from graphiti_core.llm_client.gemini_client import GeminiClient
from graphiti_core.nodes import EpisodeType
from graphiti_core.search.search_config_recipes import COMBINED_HYBRID_SEARCH_RRF

from server.config import get_settings
from server.llm_clients.qwen_client import QwenClient
from server.llm_clients.qwen_embedder import QwenEmbedder, QwenEmbedderConfig
from server.llm_clients.qwen_reranker_client import QwenRerankerClient
from server.models.episode import Episode, EpisodeCreate
from server.models.memory import MemoryItem
from server.models.recall import ShortTermRecallResponse

logger = logging.getLogger(__name__)
settings = get_settings()


class GraphitiService:
    """Service for interacting with Graphiti knowledge graph."""

    def __init__(self):
        """Initialize Graphiti service."""
        self._client: Optional[Graphiti] = None

    async def initialize(self, provider: str = "gemini"):
        """
        Initialize Graphiti client.

        Args:
            provider: LLM 提供商，可选 'gemini' 或 'qwen'
        """
        try:
            if provider.lower() == "qwen":
                # 使用 Qwen
                logger.info("Initializing Graphiti with Qwen LLM, Embedder and Reranker")

                # Create Qwen LLM client config
                llm_config = LLMConfig(
                    api_key=settings.qwen_api_key,
                    model=settings.qwen_model,
                    small_model=settings.qwen_small_model,
                    base_url=settings.qwen_base_url,
                )

                # Create Qwen LLM client
                llm_client = QwenClient(config=llm_config)

                # Create Qwen embedder
                embedder_config = QwenEmbedderConfig(
                    api_key=settings.qwen_api_key,
                    embedding_model=settings.qwen_embedding_model,
                    base_url=settings.qwen_base_url,
                )
                embedder = QwenEmbedder(config=embedder_config)

                # Create Qwen reranker with turbo model for efficiency
                reranker_config = LLMConfig(
                    api_key=settings.qwen_api_key,
                    model="qwen-turbo",  # 使用更小的模型以降低成本和延迟
                    base_url=settings.qwen_base_url,
                )
                reranker = QwenRerankerClient(config=reranker_config)

                logger.info("Qwen LLM client, Embedder and Reranker created successfully")
            else:
                # 使用 Gemini（默认）
                logger.info("Initializing Graphiti with Gemini LLM, Embedder and Reranker")

                # Create Gemini LLM client config
                llm_config = LLMConfig(
                    api_key=settings.gemini_api_key,
                    model=settings.gemini_model,
                )

                # Create Gemini LLM client
                llm_client = GeminiClient(config=llm_config)

                # Create Gemini embedder
                embedder_config = GeminiEmbedderConfig(
                    api_key=settings.gemini_api_key,
                    embedding_model=settings.gemini_embedding_model,
                )
                embedder = GeminiEmbedder(config=embedder_config)

                # Create Gemini reranker
                reranker_config = LLMConfig(
                    api_key=settings.gemini_api_key,
                    model="gemini-2.0-flash-lite",  # 使用 lite 版本以降低成本
                )
                reranker = GeminiRerankerClient(config=reranker_config)

                logger.info("Gemini LLM client, Embedder and Reranker created successfully")

            # Initialize Graphiti with selected LLM client, embedder and reranker
            self._client = Graphiti(
                uri=settings.neo4j_uri,
                user=settings.neo4j_user,
                password=settings.neo4j_password,
                llm_client=llm_client,
                embedder=embedder,
                cross_encoder=reranker,
            )
            logger.info(
                f"Graphiti client initialized successfully with {provider.upper()} LLM, Embedder and Reranker"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Graphiti client: {e}")
            raise

    async def close(self):
        """Close Graphiti client connection."""
        if self._client:
            await self._client.close()
            logger.info("Graphiti client connection closed")

    @property
    def client(self) -> Graphiti:
        """Get Graphiti client instance."""
        if not self._client:
            raise RuntimeError("Graphiti client not initialized")
        return self._client

    async def add_episode(self, episode_data: EpisodeCreate) -> Episode:
        """
        Add an episode to the knowledge graph.

        Args:
            episode_data: Episode creation data

        Returns:
            Created episode with ID
        """
        try:
            # Create episode object
            episode = Episode(
                content=episode_data.content,
                source_type=episode_data.source_type,
                metadata=episode_data.metadata or {},
                valid_at=episode_data.valid_at or datetime.utcnow(),
                tenant_id=episode_data.tenant_id,
                project_id=episode_data.project_id,
                user_id=episode_data.user_id,
                name=episode_data.name,
            )

            # Add episode to Graphiti
            # Note: Graphiti will automatically extract entities and relationships
            ep_name = episode.name or str(episode.id)
            await self.client.add_episode(
                name=ep_name,
                episode_body=episode.content,
                source_description=episode_data.source_type or "User input",
                source=EpisodeType.text,
                reference_time=episode.valid_at,
                update_communities=True,
            )

            # Attach multi-tenant/project/user properties to Episodic node
            try:
                await self.client.driver.execute_query(
                    """
                    MATCH (e:Episodic {name: $name})
                    SET e.tenant_id = $tenant_id,
                        e.project_id = $project_id,
                        e.user_id = $user_id
                    RETURN e
                    """,
                    name=ep_name,
                    tenant_id=episode.tenant_id,
                    project_id=episode.project_id,
                    user_id=episode.user_id,
                )
            except Exception as e:
                logger.warning(f"Failed to set episodic properties: {e}")

            logger.info(f"Episode {episode.id} added successfully")
            return episode

        except Exception as e:
            logger.error(f"Failed to add episode: {e}")
            raise

    async def search(
        self,
        query: str,
        limit: int = 10,
        tenant_id: Optional[str] = None,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
        as_of: Optional[datetime] = None,
    ) -> List[MemoryItem]:
        """
        Search the knowledge graph for relevant memories.

        Args:
            query: Search query
            limit: Maximum number of results
            tenant_id: Optional tenant filter

        Returns:
            List of memory items
        """
        try:
            # Perform semantic search using Graphiti's advanced search method
            # Note: search_() returns SearchResults object, while search() returns list[EntityEdge]
            # Using COMBINED_HYBRID_SEARCH_RRF which doesn't require LLM calls for reranking
            search_results = await self.client.search_(
                query=query, config=COMBINED_HYBRID_SEARCH_RRF
            )

            # Convert search results to MemoryItem format
            memory_items = []

            # Helper to check filters via direct property lookup when needed
            async def _passes_filters(node_label: str, name: Optional[str]) -> bool:
                if not (tenant_id or project_id or user_id or as_of):
                    return True
                if not name:
                    return True
                try:
                    cy = "MATCH (n:%s {name: $name}) RETURN properties(n) as props" % node_label
                    res = await self.client.driver.execute_query(cy, name=name)
                    props = res.records[0]["props"] if res.records else {}
                except Exception:
                    props = {}
                if tenant_id and props.get("tenant_id") != tenant_id:
                    return False
                if project_id and props.get("project_id") != project_id:
                    return False
                if user_id and props.get("user_id") != user_id:
                    return False
                if as_of:
                    # valid if created/valid <= as_of and not expired/invalid before as_of
                    from datetime import datetime

                    def to_dt(v):
                        try:
                            return datetime.fromisoformat(v) if isinstance(v, str) else v
                        except Exception:
                            return None

                    created = to_dt(props.get("created_at"))
                    valid = to_dt(props.get("valid_at"))
                    expired = to_dt(props.get("expired_at"))
                    invalid = to_dt(props.get("invalid_at"))
                    if created and created > as_of:
                        return False
                    if valid and valid > as_of:
                        return False
                    if expired and expired <= as_of:
                        return False
                    if invalid and invalid <= as_of:
                        return False
                return True

            # Process episodes from search results
            if hasattr(search_results, "episodes") and search_results.episodes:
                for i, episode in enumerate(search_results.episodes):
                    score = (
                        search_results.episode_reranker_scores[i]
                        if i < len(search_results.episode_reranker_scores)
                        else 0.0
                    )
                    if not await _passes_filters("Episodic", getattr(episode, "name", None)):
                        continue
                    memory_items.append(
                        MemoryItem(
                            content=episode.content,
                            score=score,
                            metadata={"type": "episode", "name": episode.name},
                            source="episode",
                        )
                    )

            # Process nodes (entities) from search results
            if hasattr(search_results, "nodes") and search_results.nodes:
                for i, node in enumerate(search_results.nodes):
                    score = (
                        search_results.node_reranker_scores[i]
                        if i < len(search_results.node_reranker_scores)
                        else 0.0
                    )
                    if not await _passes_filters("Entity", getattr(node, "name", None)):
                        continue
                    memory_items.append(
                        MemoryItem(
                            content=f"{node.name}: {node.summary}"
                            if hasattr(node, "summary")
                            else node.name,
                            score=score,
                            metadata={"type": "entity", "name": node.name},
                            source="entity",
                        )
                    )

            # Process edges (relationships) from search results
            if hasattr(search_results, "edges") and search_results.edges:
                for i, edge in enumerate(search_results.edges):
                    score = (
                        search_results.edge_reranker_scores[i]
                        if i < len(search_results.edge_reranker_scores)
                        else 0.0
                    )
                    # For edges, validating via EntityEdge properties by uuid
                    if not await _passes_filters("Entity", getattr(edge, "source_node_name", None)):
                        continue
                    memory_items.append(
                        MemoryItem(
                            content=edge.fact,
                            score=score,
                            metadata={
                                "type": "relationship",
                                "source": edge.source_node_uuid,
                                "target": edge.target_node_uuid,
                            },
                            source="relationship",
                        )
                    )

            # Sort by score descending and limit results
            memory_items.sort(key=lambda x: x.score, reverse=True)
            memory_items = memory_items[:limit]

            logger.info(f"Search returned {len(memory_items)} results for query: {query}")
            return memory_items

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    async def short_term_recall(
        self, window_minutes: int = 30, limit: int = 50, tenant_id: Optional[str] = None
    ) -> ShortTermRecallResponse:
        """Recall recent episodic memories within a time window."""
        try:
            from datetime import datetime, timedelta

            since = datetime.utcnow() - timedelta(minutes=window_minutes)
            query = """
            MATCH (e:Episodic)
            WHERE (
                ($tenant_id IS NULL OR e.tenant_id = $tenant_id)
                AND (
                    ($since IS NULL) OR (
                        (exists(e.updated_at) AND datetime(e.updated_at) >= datetime($since)) OR
                        (exists(e.created_at) AND datetime(e.created_at) >= datetime($since)) OR
                        (exists(e.valid_at)   AND datetime(e.valid_at)   >= datetime($since))
                    )
                )
            )
            OPTIONAL MATCH (e)-[r:MENTIONS|RELATES_TO]->(m)
            RETURN e as episode, collect({edge: r, target: m}) as links
            ORDER BY coalesce(e.updated_at, e.created_at, e.valid_at) DESC
            LIMIT $limit
            """

            params = {
                "tenant_id": tenant_id,
                "since": since.isoformat(),
                "limit": limit,
            }

            result = await self.client.driver.execute_query(query, **params)
            records = result.records

            items: List[MemoryItem] = []
            for r in records:
                ep = r["episode"].properties
                items.append(
                    MemoryItem(
                        content=ep.get("content", ""),
                        score=1.0,
                        metadata={"type": "episode", "name": ep.get("name", "")},
                        source="episode",
                    )
                )

            return ShortTermRecallResponse(results=items[:limit], total=len(items), since=since)
        except Exception as e:
            logger.error(f"Short-term recall failed: {e}")
            raise

    async def rebuild_communities(self):
        """Trigger community rebuild using Graphiti's community builder."""
        try:
            await self.client.build_communities()
            logger.info("Communities rebuild triggered successfully")
        except Exception as e:
            logger.error(f"Failed to rebuild communities: {e}")
            raise

    async def get_graph_data(
        self,
        limit: int = 100,
        since: Optional[datetime] = None,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get graph data for visualization with optional temporal and tenant filters."""
        try:
            query = """
            MATCH (n)
            WHERE 'Entity' IN labels(n) OR 'Episodic' IN labels(n) OR 'Community' IN labels(n)
            OPTIONAL MATCH (n)-[r]->(m)
            WHERE ('Entity' IN labels(m) OR 'Episodic' IN labels(m) OR 'Community' IN labels(m))
            AND (
                $tenant_id IS NULL OR
                coalesce(n.tenant_id, m.tenant_id) = $tenant_id
            )
            AND (
                $since IS NULL OR
                (
                    (
                        exists(n.updated_at) OR exists(n.created_at) OR exists(n.valid_at)
                    ) AND datetime(coalesce(n.updated_at, n.created_at, n.valid_at)) >= datetime($since)
                ) OR (
                    r IS NOT NULL AND (
                        exists(r.updated_at) OR exists(r.created_at) OR exists(r.valid_at)
                    ) AND datetime(coalesce(r.updated_at, r.created_at, r.valid_at)) >= datetime($since)
                ) OR (
                    m IS NOT NULL AND (
                        exists(m.updated_at) OR exists(m.created_at) OR exists(m.valid_at)
                    ) AND datetime(coalesce(m.updated_at, m.created_at, m.valid_at)) >= datetime($since)
                )
            )
            RETURN 
                elementId(n) as source_id, labels(n) as source_labels, properties(n) as source_props,
                elementId(r) as edge_id, type(r) as edge_type, properties(r) as edge_props,
                elementId(m) as target_id, labels(m) as target_labels, properties(m) as target_props
            LIMIT $limit
            """

            params: Dict[str, Any] = {
                "limit": limit,
                "tenant_id": tenant_id,
                "since": since.isoformat() if since else None,
            }

            result = await self.client.driver.execute_query(query, **params)
            records = result.records

            nodes_map = {}
            edges_list = []

            for r in records:
                s_id = r["source_id"]
                if s_id not in nodes_map:
                    nodes_map[s_id] = {
                        "data": {
                            "id": s_id,
                            "label": r["source_labels"][0] if r["source_labels"] else "Entity",
                            "name": r["source_props"].get("name", "Unknown"),
                            **r["source_props"],
                        }
                    }

                if r["target_id"]:
                    t_id = r["target_id"]
                    if t_id not in nodes_map:
                        nodes_map[t_id] = {
                            "data": {
                                "id": t_id,
                                "label": r["target_labels"][0] if r["target_labels"] else "Entity",
                                "name": r["target_props"].get("name", "Unknown"),
                                **r["target_props"],
                            }
                        }

                    if r["edge_id"]:
                        edges_list.append(
                            {
                                "data": {
                                    "id": r["edge_id"],
                                    "source": s_id,
                                    "target": t_id,
                                    "label": r["edge_type"],
                                    **r["edge_props"],
                                }
                            }
                        )

            return {"elements": {"nodes": list(nodes_map.values()), "edges": edges_list}}
        except Exception as e:
            logger.error(f"Failed to get graph data: {e}")
            # Return empty graph on error
            return {"elements": {"nodes": [], "edges": []}}

    async def health_check(self) -> bool:
        """
        Check if Graphiti service is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Simple health check - verify connection
            if not self._client:
                return False

            # You could add more sophisticated health checks here
            return True

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


# Global service instance
graphiti_service = GraphitiService()


async def get_graphiti_service() -> GraphitiService:
    """Get Graphiti service instance."""
    return graphiti_service
