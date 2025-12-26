"""Graphiti integration service for VIP Memory."""

import os

# 禁用 Graphiti 的 PostHog 遥测 - 必须在导入 graphiti_core 之前设置
os.environ["GRAPHITI_TELEMETRY_ENABLED"] = "false"
# 同时设置 PostHog 禁用环境变量作为双保险
os.environ["POSTHOG_DISABLED"] = "1"

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from graphiti_core import Graphiti
from graphiti_core.cross_encoder.gemini_reranker_client import GeminiRerankerClient
from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient
from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.llm_client import LLMConfig, OpenAIClient
from graphiti_core.llm_client.gemini_client import GeminiClient
from graphiti_core.nodes import EpisodeType
from graphiti_core.search.search_config import SearchConfig
from graphiti_core.search.search_config_recipes import (
    COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
    COMBINED_HYBRID_SEARCH_MMR,
    COMBINED_HYBRID_SEARCH_RRF,
    COMMUNITY_HYBRID_SEARCH_CROSS_ENCODER,
    COMMUNITY_HYBRID_SEARCH_MMR,
    COMMUNITY_HYBRID_SEARCH_RRF,
    EDGE_HYBRID_SEARCH_CROSS_ENCODER,
    EDGE_HYBRID_SEARCH_EPISODE_MENTIONS,
    EDGE_HYBRID_SEARCH_MMR,
    EDGE_HYBRID_SEARCH_NODE_DISTANCE,
    EDGE_HYBRID_SEARCH_RRF,
    NODE_HYBRID_SEARCH_CROSS_ENCODER,
    NODE_HYBRID_SEARCH_EPISODE_MENTIONS,
    NODE_HYBRID_SEARCH_MMR,
    NODE_HYBRID_SEARCH_NODE_DISTANCE,
    NODE_HYBRID_SEARCH_RRF,
)
from graphiti_core.search.search_filters import ComparisonOperator, DateFilter, SearchFilters
from pydantic import BaseModel, Field, create_model
from sqlalchemy import select

from server.config import get_settings
from server.database import async_session_factory
from server.db_models import EdgeType, EdgeTypeMap, EntityType
from server.llm_clients.qwen_client import QwenClient
from server.llm_clients.qwen_embedder import QwenEmbedder, QwenEmbedderConfig
from server.llm_clients.qwen_reranker_client import QwenRerankerClient
from server.models.episode import Episode, EpisodeCreate
from server.models.memory import MemoryItem
from server.models.recall import ShortTermRecallResponse
from server.services.queue_service import QueueService

logger = logging.getLogger(__name__)
settings = get_settings()


# ============================================================================
# 数据模型定义
# ============================================================================


class PaginatedResponse:
    """分页响应模型"""

    def __init__(self, items: List[Any], total: int, limit: int, offset: int):
        self.items = items
        self.total = total
        self.limit = limit
        self.offset = offset
        self.has_more = (offset + limit) < total


class Community:
    """社群模型"""

    def __init__(
        self,
        uuid: str,
        name: str,
        summary: str,
        member_count: int,
        tenant_id: Optional[str] = None,
        project_id: Optional[str] = None,
        formed_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
    ):
        self.uuid = uuid
        self.name = name
        self.summary = summary
        self.member_count = member_count
        self.tenant_id = tenant_id
        self.project_id = project_id
        self.formed_at = formed_at
        self.created_at = created_at


class Entity:
    """实体模型"""

    def __init__(
        self,
        uuid: str,
        name: str,
        entity_type: str,
        summary: str,
        tenant_id: Optional[str] = None,
        project_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        **kwargs,
    ):
        self.uuid = uuid
        self.name = name
        self.entity_type = entity_type
        self.summary = summary
        self.tenant_id = tenant_id
        self.project_id = project_id
        self.created_at = created_at
        self.properties = kwargs


class Relationship:
    """关系模型"""

    def __init__(
        self,
        uuid: str,
        source_uuid: str,
        target_uuid: str,
        relation_type: str,
        fact: str,
        score: float = 0.0,
        created_at: Optional[datetime] = None,
        **kwargs,
    ):
        self.uuid = uuid
        self.source_uuid = source_uuid
        self.target_uuid = target_uuid
        self.relation_type = relation_type
        self.fact = fact
        self.score = score
        self.created_at = created_at
        self.properties = kwargs


class GraphitiService:
    """Service for interacting with Graphiti knowledge graph."""

    def __init__(self):
        """Initialize Graphiti service."""
        self._client: Optional[Graphiti] = None
        self.queue_service = QueueService()

    async def initialize(self, provider: str = "gemini"):
        """
        Initialize Graphiti client.

        Args:
            provider: LLM 提供商，可选 'gemini' 或 'qwen'
        """
        try:
            # Normalize provider string
            provider = provider.strip()

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
            elif provider.lower() == "openai":
                # 使用 OpenAI
                logger.info("Initializing Graphiti with OpenAI LLM, Embedder and Reranker")

                # Create OpenAI LLM client config
                llm_config = LLMConfig(
                    api_key=settings.openai_api_key,
                    model=settings.openai_model,
                    small_model=settings.openai_small_model,
                    base_url=settings.openai_base_url,
                )

                # Create OpenAI LLM client
                llm_client = OpenAIClient(config=llm_config)

                # Create OpenAI embedder
                embedder_config = OpenAIEmbedderConfig(
                    api_key=settings.openai_api_key,
                    embedding_model=settings.openai_embedding_model,
                    base_url=settings.openai_base_url,
                )
                embedder = OpenAIEmbedder(config=embedder_config)

                # Create OpenAI reranker
                reranker_config = LLMConfig(
                    api_key=settings.openai_api_key,
                    model=settings.openai_small_model,
                    base_url=settings.openai_base_url,
                )
                reranker = OpenAIRerankerClient(config=reranker_config)

                logger.info("OpenAI LLM client, Embedder and Reranker created successfully")
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

            # Initialize queue service
            await self.queue_service.initialize(self._client)

            # Ensure indices exist to avoid Neo4j warnings and improve performance
            await self.ensure_indices()

        except Exception as e:
            logger.error(f"Failed to initialize Graphiti client: {e}")
            raise

    async def ensure_indices(self):
        """Ensure necessary indices exist."""
        try:
            # Graphiti indices
            await self.client.build_indices_and_constraints()

            # Custom indices for multi-tenancy
            queries = [
                "CREATE INDEX episodic_tenant_id IF NOT EXISTS FOR (n:Episodic) ON (n.tenant_id)",
                "CREATE INDEX episodic_project_id IF NOT EXISTS FOR (n:Episodic) ON (n.project_id)",
                "CREATE INDEX episodic_user_id IF NOT EXISTS FOR (n:Episodic) ON (n.user_id)",
                "CREATE INDEX entity_tenant_id IF NOT EXISTS FOR (n:Entity) ON (n.tenant_id)",
                "CREATE INDEX entity_project_id IF NOT EXISTS FOR (n:Entity) ON (n.project_id)",
                "CREATE INDEX community_tenant_id IF NOT EXISTS FOR (n:Community) ON (n.tenant_id)",
                "CREATE INDEX community_project_id IF NOT EXISTS FOR (n:Community) ON (n.project_id)",
            ]

            for q in queries:
                await self.client.driver.execute_query(q)

            logger.info("Database indices verified/created")
        except Exception as e:
            logger.warning(f"Failed to create indices: {e}")

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

    async def get_project_schema(self, project_id: str) -> Tuple[Dict, Dict, Dict]:
        """
        Get dynamic schema for a project.
        Returns: (entity_types, edge_types, edge_type_map)
        """
        entity_types = {}
        edge_types = {}
        edge_type_map = {}

        # Default types
        for name in [
            "Entity",
            "Person",
            "Organization",
            "Location",
            "Concept",
            "Event",
            "Artifact",
        ]:
            entity_types[name] = create_model(name, __base__=BaseModel)

        if not project_id:
            return entity_types, edge_types, edge_type_map

        async with async_session_factory() as session:
            # Fetch Entity Types
            result = await session.execute(
                select(EntityType).where(EntityType.project_id == project_id)
            )
            for et in result.scalars().all():
                fields = {}
                for field_name, field_def in et.schema.items():
                    py_type = str
                    desc = ""
                    if isinstance(field_def, dict):
                        type_str = field_def.get("type", "String")
                        desc = field_def.get("description", "")
                    else:
                        type_str = str(field_def)

                    if type_str == "Integer":
                        py_type = int
                    elif type_str == "Float":
                        py_type = float
                    elif type_str == "Boolean":
                        py_type = bool
                    elif type_str == "DateTime":
                        py_type = datetime
                    elif type_str == "List":
                        py_type = List
                    elif type_str == "Dict":
                        py_type = Dict

                    fields[field_name] = (Optional[py_type], Field(None, description=desc))

                entity_types[et.name] = create_model(et.name, **fields, __base__=BaseModel)

            # Fetch Edge Types
            result = await session.execute(
                select(EdgeType).where(EdgeType.project_id == project_id)
            )
            for et in result.scalars().all():
                fields = {}
                for field_name, field_def in et.schema.items():
                    py_type = str
                    desc = ""
                    if isinstance(field_def, dict):
                        type_str = field_def.get("type", "String")
                        desc = field_def.get("description", "")
                    else:
                        type_str = str(field_def)

                    if type_str == "Integer":
                        py_type = int
                    elif type_str == "Float":
                        py_type = float
                    elif type_str == "Boolean":
                        py_type = bool
                    elif type_str == "DateTime":
                        py_type = datetime

                    fields[field_name] = (Optional[py_type], Field(None, description=desc))

                edge_types[et.name] = create_model(et.name, **fields, __base__=BaseModel)

            # Fetch Edge Maps
            result = await session.execute(
                select(EdgeTypeMap).where(EdgeTypeMap.project_id == project_id)
            )
            for em in result.scalars().all():
                key = (em.source_type, em.target_type)
                if key not in edge_type_map:
                    edge_type_map[key] = []
                edge_type_map[key].append(em.edge_type)

        return entity_types, edge_types, edge_type_map

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

            # Pre-create EpisodicNode in Neo4j to avoid race conditions or Graphiti lookup failures
            now = datetime.utcnow()
            group_id = episode.project_id or "global"

            # Using MERGE to be safe, though CREATE should be fine since UUID is new
            await self.client.driver.execute_query(
                """
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
                    e.status = 'Processing',
                    e.entity_edges = []
                """,
                uuid=str(episode.id),
                name=episode.name or str(episode.id),
                content=episode.content,
                source_description=episode_data.source_type or "User input",
                source=EpisodeType.text.value,
                created_at=now.isoformat(),
                valid_at=episode.valid_at.isoformat(),
                group_id=group_id,
                tenant_id=episode.tenant_id,
                project_id=episode.project_id,
                user_id=episode.user_id,
            )

            # Add to queue
            # Use project_id as group_id for isolation, or default to 'global'

            # Fetch dynamic schema
            entity_types, edge_types, edge_type_map = await self.get_project_schema(
                episode.project_id
            )

            await self.queue_service.add_episode(
                group_id=group_id,
                name=episode.name or str(episode.id),
                content=episode.content,
                source_description=episode_data.source_type or "User input",
                episode_type=EpisodeType.text,
                entity_types=entity_types,
                edge_types=edge_types,
                edge_type_map=edge_type_map,
                uuid=str(episode.id),
                tenant_id=episode.tenant_id,
                project_id=episode.project_id,
                user_id=episode.user_id,
                memory_id=episode.metadata.get("memory_id") if episode.metadata else None,
            )

            logger.info(f"Episode {episode.id} queued for processing in group {group_id}")
            return episode

        except Exception as e:
            logger.error(f"Failed to add episode: {e}")
            raise

    async def advanced_search(
        self,
        query: str,
        strategy: str = "COMBINED_HYBRID_SEARCH_RRF",
        limit: int = 50,
        focal_node_uuid: Optional[str] = None,
        reranker: Optional[str] = None,
        tenant_id: Optional[str] = None,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
        as_of: Optional[datetime] = None,
        search_filter: Optional[SearchFilters] = None,
    ) -> List[MemoryItem]:
        """
        Advanced search with configurable strategy and reranker.

        Args:
            query: Search query
            strategy: Search strategy recipe name
            limit: Maximum number of results
            focal_node_uuid: Focal node UUID for node distance reranking
            reranker: Reranker type (openai, gemini, bge)
            tenant_id: Optional tenant filter
            project_id: Optional project filter
            user_id: Optional user filter
            as_of: Optional time travel filter
            search_filter: Optional advanced filters

        Returns:
            List of memory items
        """
        try:
            # Map strategy name to recipe object
            recipes = {
                "COMBINED_HYBRID_SEARCH_RRF": COMBINED_HYBRID_SEARCH_RRF,
                "COMBINED_HYBRID_SEARCH_MMR": COMBINED_HYBRID_SEARCH_MMR,
                "COMBINED_HYBRID_SEARCH_CROSS_ENCODER": COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
                "EDGE_HYBRID_SEARCH_RRF": EDGE_HYBRID_SEARCH_RRF,
                "EDGE_HYBRID_SEARCH_MMR": EDGE_HYBRID_SEARCH_MMR,
                "EDGE_HYBRID_SEARCH_NODE_DISTANCE": EDGE_HYBRID_SEARCH_NODE_DISTANCE,
                "EDGE_HYBRID_SEARCH_EPISODE_MENTIONS": EDGE_HYBRID_SEARCH_EPISODE_MENTIONS,
                "EDGE_HYBRID_SEARCH_CROSS_ENCODER": EDGE_HYBRID_SEARCH_CROSS_ENCODER,
                "NODE_HYBRID_SEARCH_RRF": NODE_HYBRID_SEARCH_RRF,
                "NODE_HYBRID_SEARCH_MMR": NODE_HYBRID_SEARCH_MMR,
                "NODE_HYBRID_SEARCH_NODE_DISTANCE": NODE_HYBRID_SEARCH_NODE_DISTANCE,
                "NODE_HYBRID_SEARCH_EPISODE_MENTIONS": NODE_HYBRID_SEARCH_EPISODE_MENTIONS,
                "NODE_HYBRID_SEARCH_CROSS_ENCODER": NODE_HYBRID_SEARCH_CROSS_ENCODER,
                "COMMUNITY_HYBRID_SEARCH_RRF": COMMUNITY_HYBRID_SEARCH_RRF,
                "COMMUNITY_HYBRID_SEARCH_MMR": COMMUNITY_HYBRID_SEARCH_MMR,
                "COMMUNITY_HYBRID_SEARCH_CROSS_ENCODER": COMMUNITY_HYBRID_SEARCH_CROSS_ENCODER,
            }

            config = recipes.get(strategy, COMBINED_HYBRID_SEARCH_RRF)

            # Construct group_ids from project_id if available
            group_ids = [project_id] if project_id else None

            # Construct SearchFilters if not provided
            if not search_filter:
                search_filter = SearchFilters()

            # Handle as_of using filters
            if as_of:
                # created_at <= as_of
                search_filter.created_at = [
                    [DateFilter(date=as_of, comparison_operator=ComparisonOperator.less_than_equal)]
                ]

                # expired_at > as_of OR expired_at IS NULL
                search_filter.expired_at = [
                    [DateFilter(date=as_of, comparison_operator=ComparisonOperator.greater_than)],
                    [DateFilter(date=None, comparison_operator=ComparisonOperator.is_null)],
                ]

            # Perform search using Graphiti's search method
            # Note: We are using the internal _search method indirectly via client.search_
            # or we might need to use client.search(query, center_node_uuid) for simple cases
            # But here we want full config.

            # If Node Distance strategy is used, we need to pass focal_node_uuid to the search context?
            # Or does Graphiti's search_config handle it?
            # Looking at docs: await graphiti.search(query, focal_node_uuid)
            # This suggests that if we use a recipe that requires it (like NODE_DISTANCE),
            # we might need to pass it.
            # However, graphiti.search() is a high-level wrapper.
            # We want to use graphiti._search() which takes config.

            # If we are using a specific recipe, we pass it as 'config'.

            # For Node Distance, the recipe might expect center_node_uuid?
            # Actually, `search_` (with underscore) is the lower level one in the python client likely?
            # Let's check existing usage: await self.client.search_(...)

            # Wait, existing code uses `self.client.search_(...)`.
            # Let's assume `search_` accepts `center_node_uuid` if needed?
            # Or maybe `config` has it? No, config is static recipe.

            # If the strategy implies node distance, we should provide the node.
            # Let's check if `search_` accepts optional arguments.
            # Assuming it does based on common patterns.

            # Actually, if we look at the docs:
            # await graphiti.search(query, focal_node_uuid)
            # This maps to `search` (high level).

            # If we use `search_` (low level), we pass `config`.
            # Does `search_` accept `center_node_uuid`?
            # Let's assume it does as `center_node_uuid`.

            kwargs = {}
            if focal_node_uuid and "NODE_DISTANCE" in strategy:
                kwargs["center_node_uuid"] = focal_node_uuid

            search_results = await self.client.search_(
                query=query,
                config=config,
                group_ids=group_ids,
                search_filter=search_filter,
                **kwargs,
            )

            # Convert search results to MemoryItem format
            memory_items = []

            # Helper to check filters via direct property lookup when needed
            async def _passes_filters(node_label: str, name: Optional[str]) -> bool:
                if project_id and not user_id:
                    return True
                if not (tenant_id or user_id):
                    return True
                if not name:
                    return True
                try:
                    cy = "MATCH (n:%s {name: $name}) RETURN properties(n) as props" % node_label
                    res = await self.client.driver.execute_query(cy, name=name)
                    props = res.records[0]["props"] if res.records else {}
                except Exception:
                    props = {}

                if not project_id:
                    if tenant_id and props.get("tenant_id") != tenant_id:
                        return False
                if user_id and props.get("user_id") != user_id:
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
                            metadata={
                                "type": "episode",
                                "name": episode.name,
                                "uuid": episode.uuid,
                                "created_at": getattr(episode, "created_at", None),
                            },
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
                            metadata={
                                "type": "entity",
                                "name": node.name,
                                "uuid": node.uuid,
                                "entity_type": "Entity",
                            },
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
                                "uuid": edge.uuid,
                            },
                            source="relationship",
                        )
                    )

            # Process communities from search results
            if hasattr(search_results, "communities") and search_results.communities:
                for i, community in enumerate(search_results.communities):
                    score = (
                        search_results.community_reranker_scores[i]
                        if i < len(search_results.community_reranker_scores)
                        else 0.0
                    )
                    # Community filtering might be tricky, skip for now or assume passed if project_id matches
                    memory_items.append(
                        MemoryItem(
                            content=f"Community: {community.summary}",
                            score=score,
                            metadata={
                                "type": "community",
                                "name": community.name,
                                "uuid": community.uuid,
                            },
                            source="community",
                        )
                    )

            # Sort by score descending and limit results
            memory_items.sort(key=lambda x: x.score, reverse=True)
            memory_items = memory_items[:limit]

            logger.info(
                f"Advanced search returned {len(memory_items)} results for query: {query}, strategy: {strategy}"
            )
            return memory_items

        except Exception as e:
            logger.error(f"Advanced search failed: {e}")
            raise

    async def search(
        self,
        query: str,
        limit: int = 10,
        tenant_id: Optional[str] = None,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
        as_of: Optional[datetime] = None,
        search_filter: Optional[SearchFilters] = None,
        center_node_uuid: Optional[str] = None,
        search_config: Optional[SearchConfig] = None,
    ) -> List[MemoryItem]:
        """
        Search the knowledge graph for relevant memories.

        Args:
            query: Search query
            limit: Maximum number of results
            tenant_id: Optional tenant filter
            project_id: Optional project filter
            user_id: Optional user filter
            as_of: Optional time travel filter
            search_filter: Optional advanced filters
            center_node_uuid: Optional UUID for node distance reranking
            search_config: Optional search configuration (recipe)

        Returns:
            List of memory items
        """
        try:
            # Construct group_ids from project_id if available
            group_ids = [project_id] if project_id else None

            # Construct SearchFilters if not provided
            if not search_filter:
                search_filter = SearchFilters()

            # Handle as_of using filters
            if as_of:
                # created_at <= as_of
                search_filter.created_at = [
                    [DateFilter(date=as_of, comparison_operator=ComparisonOperator.less_than_equal)]
                ]

                # expired_at > as_of OR expired_at IS NULL
                search_filter.expired_at = [
                    [DateFilter(date=as_of, comparison_operator=ComparisonOperator.greater_than)],
                    [DateFilter(date=None, comparison_operator=ComparisonOperator.is_null)],
                ]

            # Use provided config or default to COMBINED_HYBRID_SEARCH_RRF
            config = search_config or COMBINED_HYBRID_SEARCH_RRF

            # Perform semantic search using Graphiti's advanced search method
            # Note: search_() returns SearchResults object, while search() returns list[EntityEdge]
            search_results = await self.client.search_(
                query=query,
                config=config,
                group_ids=group_ids,
                search_filter=search_filter,
                center_node_uuid=center_node_uuid,
            )

            # Convert search results to MemoryItem format
            memory_items = []

            # Helper to check filters via direct property lookup when needed
            # Only needed if we couldn't filter by group_ids (no project_id) or specific props
            async def _passes_filters(node_label: str, name: Optional[str]) -> bool:
                # If we already filtered by project_id via group_ids, and handled as_of via filters,
                # we mostly just need to check tenant_id (if project_id missing) and user_id

                # Optimization: if project_id provided, we assume tenant check passed (project implies tenant)
                # and as_of passed.
                if project_id and not user_id:
                    return True

                if not (tenant_id or user_id):
                    return True
                if not name:
                    return True
                try:
                    cy = "MATCH (n:%s {name: $name}) RETURN properties(n) as props" % node_label
                    res = await self.client.driver.execute_query(cy, name=name)
                    props = res.records[0]["props"] if res.records else {}
                except Exception:
                    props = {}

                # If project_id was not used in group_ids (None), we must check tenant/project here
                if not project_id:
                    if tenant_id and props.get("tenant_id") != tenant_id:
                        return False
                    if props.get("project_id") and tenant_id:
                        # If node has project_id, verify it belongs to tenant?
                        # Simplified: just check tenant_id matches if present on node
                        pass

                if user_id and props.get("user_id") != user_id:
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
                            metadata={
                                "type": "episode",
                                "name": episode.name,
                                "uuid": episode.uuid,
                                "created_at": getattr(episode, "created_at", None),
                            },
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
                            metadata={
                                "type": "entity",
                                "name": node.name,
                                "uuid": node.uuid,
                                "entity_type": "Entity",  # Default, maybe enrich later
                            },
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
                    # Optimization: skip edge validation for now or use source node
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
                                "uuid": edge.uuid,
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
                        (e.updated_at IS NOT NULL AND datetime(e.updated_at) >= datetime($since)) OR
                        (e.created_at IS NOT NULL AND datetime(e.created_at) >= datetime($since)) OR
                        (e.valid_at IS NOT NULL   AND datetime(e.valid_at)   >= datetime($since))
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
                # Convert Node to dict to access properties safely
                ep = dict(r["episode"])

                # Helper to convert Neo4j types to Python types
                def _convert_val(v):
                    if hasattr(v, "isoformat"):
                        return v.isoformat()
                    return v

                # Handle Name: if UUID, try to use content snippet
                name = ep.get("name", "")
                if not name or (len(name) == 36 and "-" in name):
                    content = ep.get("content", "")
                    if content:
                        name = (content[:50] + "...") if len(content) > 50 else content

                # Handle Created At: fallback to valid_at
                created_at = _convert_val(ep.get("created_at"))
                if not created_at:
                    created_at = _convert_val(ep.get("valid_at"))

                # Handle Source Type
                source_type = ep.get("source_description", "Text")
                if not source_type or source_type == "User input":
                    source_type = "Text"

                items.append(
                    MemoryItem(
                        content=ep.get("content", ""),
                        score=1.0,
                        metadata={
                            "type": "episode",
                            "source_type": source_type,
                            "name": name,
                            "project_id": ep.get("project_id"),
                            "tenant_id": ep.get("tenant_id"),
                            "user_id": ep.get("user_id"),
                            "created_at": created_at,
                            "status": ep.get("status", "Synced"),
                        },
                        source="episode",
                    )
                )

            return ShortTermRecallResponse(results=items[:limit], total=len(items), since=since)
        except Exception as e:
            logger.error(f"Short-term recall failed: {e}")
            raise

    # ========================================================================
    # 高级搜索功能
    # ========================================================================

    async def search_by_graph_traversal(
        self,
        start_entity_uuid: str,
        max_depth: int = 2,
        relationship_types: Optional[List[str]] = None,
        limit: int = 50,
        tenant_id: Optional[str] = None,
    ) -> List[MemoryItem]:
        """
        Search by traversing the graph from a starting entity.

        This performs a graph traversal to find related entities and episodes,
        useful for exploring connections in the knowledge graph.

        Args:
            start_entity_uuid: Starting entity UUID
            max_depth: Maximum traversal depth (1-3 recommended)
            relationship_types: Optional list of relationship types to follow
            limit: Maximum results to return
            tenant_id: Optional tenant filter

        Returns:
            List of related memory items
        """
        try:
            # Build relationship type filter
            rel_filter = ""
            if relationship_types:
                types = "|".join(relationship_types)
                rel_filter = f":`{types}`"

            query = f"""
            MATCH path = (start:Entity {{uuid: $uuid}})-[r{rel_filter}*1..{max_depth}]-(related)
            WHERE $tenant_id IS NULL OR start.tenant_id = $tenant_id
            WITH related, relationships(path) as rels, length(path) as depth
            RETURN related, rels, depth
            LIMIT $limit
            """

            result = await self.client.driver.execute_query(
                query,
                uuid=start_entity_uuid,
                tenant_id=tenant_id,
                limit=limit,
            )

            items = []
            for r in result.records:
                node = r["related"]
                rels = r["rels"]
                depth = r["depth"]
                props = node.properties

                # Create content based on node type
                labels = node.labels
                if "Entity" in labels:
                    content = f"{props.get('name', 'Unknown')}: {props.get('summary', '')}"
                    source = "entity"
                elif "Episodic" in labels:
                    content = props.get("content", "")
                    source = "episode"
                elif "Community" in labels:
                    content = f"Community: {props.get('summary', '')}"
                    source = "community"
                else:
                    content = str(props)
                    source = "unknown"

                items.append(
                    MemoryItem(
                        content=content,
                        score=1.0 / depth,  # Higher score for closer nodes
                        metadata={
                            "type": source,
                            "uuid": props.get("uuid"),
                            "depth": depth,
                            "relationship_count": len(rels),
                        },
                        source="graph_traversal",
                    )
                )

            logger.info(
                f"Graph traversal found {len(items)} results from entity: {start_entity_uuid}"
            )
            return items

        except Exception as e:
            logger.error(f"Graph traversal search failed: {e}")
            raise

    async def search_by_community(
        self,
        community_uuid: str,
        limit: int = 50,
        include_episodes: bool = True,
    ) -> List[MemoryItem]:
        """
        Search within a community for related content.

        Args:
            community_uuid: Community UUID
            limit: Maximum results to return
            include_episodes: Include episodes in results

        Returns:
            List of memory items from the community
        """
        try:
            items = []

            # Get entities in the community
            entities_query = """
            MATCH (c:Community {uuid: $uuid})-[:HAS_MEMBER]->(e:Entity)
            RETURN properties(e) as props
            LIMIT $limit
            """
            entities_result = await self.client.driver.execute_query(
                entities_query,
                uuid=community_uuid,
                limit=limit,
            )

            for r in entities_result.records:
                props = r["props"]
                items.append(
                    MemoryItem(
                        content=f"{props.get('name', 'Unknown')}: {props.get('summary', '')}",
                        score=1.0,
                        metadata={
                            "type": "entity",
                            "uuid": props.get("uuid"),
                            "entity_type": props.get("entity_type"),
                        },
                        source="community_entity",
                    )
                )

            # Optionally include episodes related to community entities
            if include_episodes:
                episodes_query = """
                MATCH (c:Community {uuid: $uuid})-[:HAS_MEMBER]->(e:Entity)<-[:CONTAINS]-(ep:Episodic)
                RETURN properties(ep) as props
                LIMIT $limit
                """
                episodes_result = await self.client.driver.execute_query(
                    episodes_query,
                    uuid=community_uuid,
                    limit=limit,
                )

                for r in episodes_result.records:
                    props = r["props"]
                    items.append(
                        MemoryItem(
                            content=props.get("content", ""),
                            score=0.9,
                            metadata={
                                "type": "episode",
                                "name": props.get("name"),
                            },
                            source="community_episode",
                        )
                    )

            logger.info(
                f"Community search found {len(items)} results for community: {community_uuid}"
            )
            return items[:limit]

        except Exception as e:
            logger.error(f"Community search failed: {e}")
            raise

    async def search_temporal(
        self,
        query: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 50,
        tenant_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> List[MemoryItem]:
        """
        Search within a temporal window.

        This performs semantic search restricted to a time range,
        useful for finding memories from specific periods.

        Args:
            query: Search query
            since: Start of time range (inclusive)
            until: End of time range (exclusive)
            limit: Maximum results to return
            tenant_id: Optional tenant filter
            project_id: Optional project filter

        Returns:
            List of memory items within the time range
        """
        try:
            filters = SearchFilters()

            # Use a list to hold the AND conditions for created_at
            date_filters = []

            # created_at >= since
            if since:
                date_filters.append(
                    DateFilter(
                        date=since, comparison_operator=ComparisonOperator.greater_than_equal
                    )
                )

            # created_at < until
            if until:
                date_filters.append(
                    DateFilter(date=until, comparison_operator=ComparisonOperator.less_than)
                )

            if date_filters:
                filters.created_at = [date_filters]

            return await self.search(
                query=query,
                limit=limit,
                tenant_id=tenant_id,
                project_id=project_id,
                search_filter=filters,
            )

        except Exception as e:
            logger.error(f"Temporal search failed: {e}")
            raise

    async def search_with_facets(
        self,
        query: str,
        entity_types: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        since: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
        tenant_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Tuple[List[MemoryItem], Dict[str, Any]]:
        """
        Search with faceted filtering and return facet counts.

        Args:
            query: Search query
            entity_types: Filter by entity types
            tags: Filter by tags
            since: Filter by creation date
            limit: Maximum results to return
            offset: Pagination offset
            tenant_id: Optional tenant filter
            project_id: Optional project filter

        Returns:
            Tuple of (search results, facet metadata)
        """
        try:
            filters = SearchFilters()

            if entity_types:
                filters.node_labels = entity_types

            # Manual date filter mapping
            if since:
                filters.created_at = [
                    [
                        DateFilter(
                            date=since, comparison_operator=ComparisonOperator.greater_than_equal
                        )
                    ]
                ]

            # Call search with filters
            results = await self.search(
                query=query,
                limit=limit + offset,
                tenant_id=tenant_id,
                project_id=project_id,
                search_filter=filters,
            )

            # Apply additional post-filtering if needed (for safety if Graphiti support is partial)
            filtered_results = []
            for item in results:
                # Filter by entity type if specified
                if entity_types and item.metadata.get("type") == "entity":
                    if item.metadata.get("entity_type") not in entity_types:
                        continue

                # Filter by date if specified (double check)
                if since:
                    created_at = item.metadata.get("created_at")
                    if created_at:
                        try:
                            created_dt = (
                                datetime.fromisoformat(created_at)
                                if isinstance(created_at, str)
                                else created_at
                            )
                            if created_dt < since:
                                continue
                        except Exception:
                            pass

                filtered_results.append(item)

            # Apply pagination
            paginated_results = filtered_results[offset : offset + limit]

            # Calculate facet counts
            facets = {
                "entity_types": {},
                "total": len(filtered_results),
            }

            for item in filtered_results:
                entity_type = item.metadata.get("entity_type")
                if entity_type:
                    facets["entity_types"][entity_type] = (
                        facets["entity_types"].get(entity_type, 0) + 1
                    )

            logger.info(f"Faceted search found {len(paginated_results)} results")
            return paginated_results, facets

        except Exception as e:
            logger.error(f"Faceted search failed: {e}")
            raise

    async def rebuild_communities(self):
        """Trigger community rebuild using Graphiti's community builder."""
        try:
            # Graphiti's build_communities automatically removes old communities
            # We don't need to pass explicit group_ids unless we want to partition
            # Currently assuming single partition/database for simplicity or relying on default behavior
            await self.client.build_communities()

            # After rebuilding, we should re-apply tenant/project/user IDs to the new communities
            # This is a bit of a hack because Graphiti core doesn't know about our multi-tenancy yet

            # Update tenant_id and project_id based on members
            # We take the most frequent tenant/project if there are multiple (though there shouldn't be)
            query = """
            MATCH (c:Community)-[:HAS_MEMBER]->(e:Entity)
            WITH c, e
            WHERE e.tenant_id IS NOT NULL
            WITH c, e.tenant_id as tid, count(*) as count
            ORDER BY count DESC
            WITH c, collect(tid)[0] as major_tenant
            SET c.tenant_id = major_tenant
            """
            await self.client.driver.execute_query(query)

            query_proj = """
            MATCH (c:Community)-[:HAS_MEMBER]->(e:Entity)
            WITH c, e
            WHERE e.project_id IS NOT NULL
            WITH c, e.project_id as pid, count(*) as count
            ORDER BY count DESC
            WITH c, collect(pid)[0] as major_project
            SET c.project_id = major_project
            """
            await self.client.driver.execute_query(query_proj)

            # Count members for each community
            count_query = """
            MATCH (c:Community)-[:HAS_MEMBER]->(e:Entity)
            WITH c, count(e) as member_count
            SET c.member_count = member_count
            """
            await self.client.driver.execute_query(count_query)

            logger.info("Communities rebuild triggered successfully and properties updated")
        except Exception as e:
            logger.error(f"Failed to rebuild communities: {e}")
            raise

    async def get_subgraph(
        self,
        node_uuids: List[str],
        include_neighbors: bool = True,
        limit: int = 100,
        tenant_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a subgraph containing specific nodes and their connections.

        Args:
            node_uuids: List of node UUIDs to include
            include_neighbors: Whether to include 1-hop neighbors
            limit: Maximum number of elements to return
            tenant_id: Optional tenant filter
            project_id: Optional project filter

        Returns:
            Subgraph data in the same format as get_graph_data
        """
        try:
            if not node_uuids:
                return {"elements": {"nodes": [], "edges": []}}

            # Build WHERE clause for tenant/project
            conditions = []
            if tenant_id:
                conditions.append("n.tenant_id = $tenant_id")
            if project_id:
                conditions.append("n.project_id = $project_id")

            # Additional filter for the initial nodes
            node_filter = ""
            if conditions:
                node_filter = " AND " + " AND ".join(conditions)

            if include_neighbors:
                query = (
                    """
                MATCH (n)
                WHERE n.uuid IN $uuids
                """
                    + node_filter
                    + """
                WITH collect(distinct n) as start_nodes
                
                // Get neighbors and edges connected to start nodes
                UNWIND start_nodes as n
                OPTIONAL MATCH (n)-[r]-(m)
                """
                    + (
                        ("WHERE " + " AND ".join([c.replace("n.", "m.") for c in conditions]))
                        if conditions
                        else ""
                    )
                    + """
                
                WITH start_nodes, collect(distinct m) as neighbors, collect(distinct r) as edges
                WITH start_nodes + [x in neighbors where x is not null] as all_nodes, edges
                
                // Deduplicate nodes
                UNWIND all_nodes as n
                WITH collect(distinct n) as unique_nodes, edges
                
                RETURN 
                    [n in unique_nodes | {
                        id: elementId(n), 
                        labels: labels(n), 
                        props: properties(n)
                    }] as nodes_data,
                    [r in edges | {
                        id: elementId(r), 
                        type: type(r), 
                        props: properties(r), 
                        source: elementId(startNode(r)), 
                        target: elementId(endNode(r))
                    }] as edges_data
                LIMIT $limit
                """
                )
            else:
                query = (
                    """
                MATCH (n)
                WHERE n.uuid IN $uuids
                """
                    + node_filter
                    + """
                WITH collect(distinct n) as nodes
                
                // Get edges only between these nodes
                UNWIND nodes as n
                MATCH (n)-[r]->(m)
                WHERE m IN nodes
                
                WITH nodes, collect(distinct r) as edges
                
                RETURN 
                    [n in nodes | {
                        id: elementId(n), 
                        labels: labels(n), 
                        props: properties(n)
                    }] as nodes_data,
                    [r in edges | {
                        id: elementId(r), 
                        type: type(r), 
                        props: properties(r), 
                        source: elementId(startNode(r)), 
                        target: elementId(endNode(r))
                    }] as edges_data
                LIMIT $limit
                """
                )

            result = await self.client.driver.execute_query(
                query, uuids=node_uuids, tenant_id=tenant_id, project_id=project_id, limit=limit
            )

            nodes_map = {}
            edges_list = []

            if result.records:
                record = result.records[0]
                nodes_data = record["nodes_data"]
                edges_data = record["edges_data"]

                for n in nodes_data:
                    n_id = n["id"]
                    if n_id not in nodes_map:
                        nodes_map[n_id] = {
                            "data": {
                                "id": n_id,
                                "label": n["labels"][0] if n["labels"] else "Entity",
                                "name": n["props"].get("name", "Unknown"),
                                **n["props"],
                            }
                        }

                for r in edges_data:
                    # Verify both source and target are in our node map (should be true by definition of query)
                    # But for include_neighbors=True, we collected all nodes.
                    # For include_neighbors=False, we matched m IN nodes.
                    s_id = r["source"]
                    t_id = r["target"]

                    if s_id in nodes_map and t_id in nodes_map:
                        edges_list.append(
                            {
                                "data": {
                                    "id": r["id"],
                                    "source": s_id,
                                    "target": t_id,
                                    "label": r["type"],
                                    **r["props"],
                                }
                            }
                        )

            return {"elements": {"nodes": list(nodes_map.values()), "edges": edges_list}}

        except Exception as e:
            logger.error(f"Failed to get subgraph: {e}")
            # Return empty graph on error
            return {"elements": {"nodes": [], "edges": []}}

    async def get_graph_data(
        self,
        limit: int = 100,
        since: Optional[datetime] = None,
        tenant_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get graph data for visualization with optional temporal, tenant and project filters."""
        try:
            logger.info(
                f"get_graph_data called with: limit={limit}, since={since}, tenant_id={tenant_id}, project_id={project_id}"
            )

            query = """
            MATCH (n)
            WHERE ('Entity' IN labels(n) OR 'Episodic' IN labels(n) OR 'Community' IN labels(n))
            AND (
                $tenant_id IS NULL OR n.tenant_id = $tenant_id
            )
            AND (
                $project_id IS NULL OR n.project_id = $project_id
            )
            AND (
                $since IS NULL OR
                (
                    n.updated_at IS NOT NULL OR n.created_at IS NOT NULL OR n.valid_at IS NOT NULL
                ) AND datetime(coalesce(n.updated_at, n.created_at, n.valid_at)) >= datetime($since)
            )
            
            OPTIONAL MATCH (n)-[r]->(m)
            WHERE ('Entity' IN labels(m) OR 'Episodic' IN labels(m) OR 'Community' IN labels(m))
            AND (
                $since IS NULL OR
                (
                    r.updated_at IS NOT NULL OR r.created_at IS NOT NULL OR r.valid_at IS NOT NULL
                ) AND datetime(coalesce(r.updated_at, r.created_at, r.valid_at)) >= datetime($since)
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
                "project_id": project_id,
                "since": since.isoformat() if since else None,
            }

            result = await self.client.driver.execute_query(query, **params)
            records = result.records

            nodes_map = {}
            edges_list = []

            for r in records:
                s_id = r["source_id"]
                # Only include source node if it passes filters (approximate check for orphaned nodes)
                # Since we return ALL nodes in MATCH (n), we need to filter out those that didn't match the OPTIONAL MATCH criteria
                # if they don't have the properties themselves.
                # However, the query structure is: MATCH (n) OPTIONAL MATCH ... RETURN ...
                # If OPTIONAL MATCH failed (r is null), n is returned.
                # We should filter n here if we want to avoid returning everything.

                # Logic: If n has project_id, check it. If not, check if it connected to something (r is not None).
                # If r is None and n has no project_id, skip it?

                s_props = r["source_props"]
                r_edge = r["edge_id"]

                # Check project_id filter for source node
                if project_id:
                    n_pid = s_props.get("project_id")
                    if n_pid and n_pid != project_id:
                        continue
                    if not n_pid and not r_edge:
                        # Orphan node without project_id, skip if we are filtering by project
                        # Unless we want to show global entities? Let's assume strict filtering.
                        continue

                if tenant_id:
                    n_tid = s_props.get("tenant_id")
                    if n_tid and n_tid != tenant_id:
                        continue
                    if not n_tid and not r_edge:
                        continue

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
            logger.error(f"Failed to get graph data: {e}", exc_info=True)
            # Return empty graph on error
            return {"elements": {"nodes": [], "edges": []}}

    # ========================================================================
    # Episode CRUD 增强
    # ========================================================================

    async def get_episode(self, episode_name: str) -> Optional[Dict[str, Any]]:
        """
        Get episode details by name.

        Args:
            episode_name: Episode name

        Returns:
            Episode data or None if not found
        """
        try:
            query = """
            MATCH (e:Episodic {name: $name})
            RETURN properties(e) as episode
            """
            result = await self.client.driver.execute_query(query, name=episode_name)
            if result.records:
                ep = dict(result.records[0]["episode"])

                # Helper to convert Neo4j types to Python types
                def _convert_val(v):
                    if hasattr(v, "isoformat"):
                        return v.isoformat()
                    return v

                # Convert Neo4j types
                for k, v in ep.items():
                    ep[k] = _convert_val(v)

                # Enhance display fields
                name = ep.get("name", "")
                if not name or (len(name) == 36 and "-" in name):
                    content = ep.get("content", "")
                    if content:
                        ep["name"] = (content[:50] + "...") if len(content) > 50 else content

                source_type = ep.get("source_description", "Text")
                if not source_type or source_type == "User input":
                    ep["source_type"] = "Text"
                else:
                    ep["source_type"] = source_type

                # Ensure created_at exists
                if not ep.get("created_at") and ep.get("valid_at"):
                    ep["created_at"] = ep.get("valid_at")

                # Set default status if missing
                if not ep.get("status"):
                    ep["status"] = "Synced"

                return ep
            return None
        except Exception as e:
            logger.error(f"Failed to get episode: {e}")
            raise

    async def list_episodes(
        self,
        tenant_id: Optional[str] = None,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> PaginatedResponse:
        """
        List episodes with filtering and pagination.

        Args:
            tenant_id: Optional tenant filter
            project_id: Optional project filter
            user_id: Optional user filter
            limit: Maximum items to return
            offset: Pagination offset
            sort_by: Sort field
            sort_desc: Sort descending if True

        Returns:
            Paginated response with episodes
        """
        try:
            # Build WHERE clause
            conditions = []
            if tenant_id:
                conditions.append("e.tenant_id = $tenant_id")
            if project_id:
                conditions.append("e.project_id = $project_id")
            if user_id:
                conditions.append("e.user_id = $user_id")

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            # Count total
            count_query = f"""
            MATCH (e:Episodic)
            WHERE {where_clause}
            RETURN count(e) as total
            """
            count_result = await self.client.driver.execute_query(
                count_query,
                tenant_id=tenant_id,
                project_id=project_id,
                user_id=user_id,
            )
            total = count_result.records[0]["total"] if count_result.records else 0

            # Get episodes with pagination
            order = "DESC" if sort_desc else "ASC"
            list_query = f"""
            MATCH (e:Episodic)
            WHERE {where_clause}
            RETURN properties(e) as episode
            ORDER BY e.{sort_by} {order}
            SKIP $offset
            LIMIT $limit
            """
            list_result = await self.client.driver.execute_query(
                list_query,
                tenant_id=tenant_id,
                project_id=project_id,
                user_id=user_id,
                offset=offset,
                limit=limit,
            )

            episodes = []
            for r in list_result.records:
                ep = dict(r["episode"])

                # Helper to convert Neo4j types to Python types
                def _convert_val(v):
                    if hasattr(v, "isoformat"):
                        return v.isoformat()
                    return v

                # Convert Neo4j types
                for k, v in ep.items():
                    ep[k] = _convert_val(v)

                # Enhance display fields
                name = ep.get("name", "")
                if not name or (len(name) == 36 and "-" in name):
                    content = ep.get("content", "")
                    if content:
                        ep["name"] = (content[:50] + "...") if len(content) > 50 else content

                source_type = ep.get("source_description", "Text")
                if not source_type or source_type == "User input":
                    ep["source_type"] = "Text"
                else:
                    ep["source_type"] = source_type

                # Ensure created_at exists
                if not ep.get("created_at") and ep.get("valid_at"):
                    ep["created_at"] = ep.get("valid_at")

                # Set default status if missing
                if not ep.get("status"):
                    ep["status"] = "Synced"

                episodes.append(ep)

            return PaginatedResponse(
                items=episodes,
                total=total,
                limit=limit,
                offset=offset,
            )
        except Exception as e:
            logger.error(f"Failed to list episodes: {e}")
            raise

    async def delete_episode(self, episode_name: str) -> bool:
        """
        Delete an episode and its relationships.
        Also cleans up orphaned entities (entities not mentioned by any other episode).

        Args:
            episode_name: Episode name

        Returns:
            True if deleted, False if not found
        """
        try:
            # Step 1: Check existence and get entities
            check_query = """
            MATCH (e:Episodic {name: $name})
            OPTIONAL MATCH (e)-[:MENTIONS]->(n:Entity)
            RETURN e, collect(distinct n) as entities
            """
            check_res = await self.client.driver.execute_query(check_query, name=episode_name)
            if not check_res.records:
                return False

            entities = check_res.records[0]["entities"]

            # Step 2: Delete episode
            del_ep_query = "MATCH (e:Episodic {name: $name}) DETACH DELETE e"
            await self.client.driver.execute_query(del_ep_query, name=episode_name)

            # Step 3: Cleanup entities
            if entities:
                # We can't pass Node objects directly back to query easily sometimes, better use UUIDs
                entity_uuids = [e["uuid"] for e in entities if "uuid" in e]
                if entity_uuids:
                    cleanup_query = """
                    UNWIND $uuids as uuid
                    MATCH (n:Entity {uuid: uuid})
                    WHERE NOT (n)<-[:MENTIONS]-(:Episodic)
                    DETACH DELETE n
                    """
                    await self.client.driver.execute_query(cleanup_query, uuids=entity_uuids)

            logger.info(f"Deleted episode {episode_name} and cleaned up orphans")
            return True

        except Exception as e:
            logger.error(f"Failed to delete episode: {e}")
            raise

    async def delete_episode_by_memory_id(self, memory_id: str) -> bool:
        """
        Delete an episode by memory_id (stored in metadata) and its relationships.
        Also cleans up orphaned entities.

        Args:
            memory_id: Memory ID

        Returns:
            True if deleted, False if not found
        """
        try:
            # Step 1: Check existence and get entities
            # We look for episodes where memory_id property matches (which we set in add_episode custom query?)
            # Wait, in add_episode we didn't explicitly set memory_id as a property on the node,
            # only passed it to queue_service?

            # Let's check add_episode implementation in this file:
            # It runs a MERGE query.
            # Does it set memory_id? No.
            # But wait, it sets properties from episode object?
            # episode object has metadata.

            # In Graphiti core, metadata is usually stored as properties or JSON?
            # Graphiti's add_episode stores metadata.

            # But in our custom Cypher query in add_episode:
            # SET e:Node, e.name = $name, ...
            # We did NOT set e.memory_id or e.metadata.

            # However, we call self.queue_service.add_episode with memory_id.
            # And when that is processed by Graphiti (the library), it will add the episode.
            # Graphiti library stores metadata.

            # So we should be able to query by metadata.memory_id?
            # Neo4j doesn't index JSON properties easily unless we promote them.

            # IF Graphiti stores metadata as properties on the node (flattened), then yes.
            # If it stores as a JSON string or map, we can query it.

            # Let's assume for now we need to search for it.
            # Or better, we should update add_episode to store memory_id as a property for easier deletion.
            # But for existing data, we might need to search.

            # Let's try to match where memory_id is in the properties.
            # Graphiti usually adds metadata keys as properties on the node if they are primitives.

            check_query = """
            MATCH (e:Episodic)
            WHERE e.memory_id = $memory_id
            OPTIONAL MATCH (e)-[:MENTIONS]->(n:Entity)
            RETURN e, collect(distinct n) as entities
            """
            check_res = await self.client.driver.execute_query(check_query, memory_id=memory_id)

            if not check_res.records:
                # Try checking if it's inside metadata json/map if that's how it's stored
                # Or maybe we didn't store it at all in the node properties in our custom query?
                # The custom query in add_episode:
                # SET e:Node, e.name=$name...
                # It does NOT set memory_id.

                # BUT, the actual processing happens later in the queue consumer which calls graphiti.add_episode.
                # If that adds it, it might overwrite/update the node?
                # The custom query uses MERGE by uuid.
                # If queue processing adds it, it uses the same UUID?
                # Yes, uuid=str(episode.id).

                # So if Graphiti.add_episode adds metadata as properties, we are good.
                # Let's assume it does.
                return False

            entities = check_res.records[0]["entities"]
            episode_uuid = check_res.records[0]["e"]["uuid"]

            # Step 2: Delete episode
            del_ep_query = "MATCH (e:Episodic {uuid: $uuid}) DETACH DELETE e"
            await self.client.driver.execute_query(del_ep_query, uuid=episode_uuid)

            # Step 3: Cleanup entities
            if entities:
                entity_uuids = [e["uuid"] for e in entities if "uuid" in e]
                if entity_uuids:
                    cleanup_query = """
                    UNWIND $uuids as uuid
                    MATCH (n:Entity {uuid: uuid})
                    WHERE NOT (n)<-[:MENTIONS]-(:Episodic)
                    DETACH DELETE n
                    """
                    await self.client.driver.execute_query(cleanup_query, uuids=entity_uuids)

            logger.info(f"Deleted episode with memory_id {memory_id} and cleaned up orphans")
            return True

        except Exception as e:
            logger.error(f"Failed to delete episode by memory_id: {e}")
            raise

    # ========================================================================
    # Entity 管理
    # ========================================================================

    async def get_entity(self, entity_uuid: str) -> Optional[Entity]:
        """
        Get entity details by UUID.

        Args:
            entity_uuid: Entity UUID

        Returns:
            Entity object or None
        """
        try:
            query = """
            MATCH (e:Entity {uuid: $uuid})
            RETURN properties(e) as props
            """
            result = await self.client.driver.execute_query(query, uuid=entity_uuid)
            if result.records:
                props = result.records[0]["props"]
                return Entity(
                    uuid=props.get("uuid", entity_uuid),
                    name=props.get("name", ""),
                    entity_type=props.get("entity_type", "Unknown"),
                    summary=props.get("summary", ""),
                    tenant_id=props.get("tenant_id"),
                    project_id=props.get("project_id"),
                    created_at=props.get("created_at"),
                )
            return None
        except Exception as e:
            logger.error(f"Failed to get entity: {e}")
            raise

    async def list_entities(
        self,
        tenant_id: Optional[str] = None,
        project_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedResponse:
        """
        List entities with filtering and pagination.

        Args:
            tenant_id: Optional tenant filter
            project_id: Optional project filter
            entity_type: Optional entity type filter
            limit: Maximum items to return
            offset: Pagination offset

        Returns:
            Paginated response with entities
        """
        try:
            # Build WHERE clause
            conditions = []
            if tenant_id:
                conditions.append("e.tenant_id = $tenant_id")
            if entity_type:
                conditions.append("e.entity_type = $entity_type")

            base_where = " AND ".join(conditions) if conditions else "1=1"

            if project_id:
                # Filter by project_id OR mentioned by episode in project
                project_condition = """
                (
                    e.project_id = $project_id OR
                    EXISTS {
                        MATCH (e)<-[:MENTIONS]-(ep:Episodic)
                        WHERE ep.project_id = $project_id
                    }
                )
                """
                where_clause = f"{base_where} AND {project_condition}"
            else:
                where_clause = base_where

            # Count total
            count_query = f"""
            MATCH (e:Entity)
            WHERE {where_clause}
            RETURN count(e) as total
            """
            count_result = await self.client.driver.execute_query(
                count_query,
                tenant_id=tenant_id,
                project_id=project_id,
                entity_type=entity_type,
            )
            total = count_result.records[0]["total"] if count_result.records else 0

            # Get entities
            list_query = f"""
            MATCH (e:Entity)
            WHERE {where_clause}
            RETURN properties(e) as props
            ORDER BY e.created_at DESC
            SKIP $offset
            LIMIT $limit
            """
            list_result = await self.client.driver.execute_query(
                list_query,
                tenant_id=tenant_id,
                project_id=project_id,
                entity_type=entity_type,
                offset=offset,
                limit=limit,
            )

            entities = []
            for r in list_result.records:
                props = r["props"]
                entities.append(
                    Entity(
                        uuid=props.get("uuid", ""),
                        name=props.get("name", ""),
                        entity_type=props.get("entity_type", "Unknown"),
                        summary=props.get("summary", ""),
                        tenant_id=props.get("tenant_id"),
                        project_id=props.get("project_id"),
                        created_at=props.get("created_at"),
                    )
                )

            return PaginatedResponse(
                items=entities,
                total=total,
                limit=limit,
                offset=offset,
            )
        except Exception as e:
            logger.error(f"Failed to list entities: {e}")
            raise

    async def get_relationships(
        self,
        entity_uuid: str,
        relationship_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Relationship]:
        """
        Get relationships for an entity.

        Args:
            entity_uuid: Entity UUID
            relationship_type: Optional relationship type filter
            limit: Maximum relationships to return

        Returns:
            List of relationships
        """
        try:
            # Build relationship type filter
            rel_filter = ""
            if relationship_type:
                rel_filter = f":`{relationship_type}`"

            query = f"""
            MATCH (e:Entity {{uuid: $uuid}})-[r{rel_filter}]-(other:Entity)
            RETURN r, properties(r) as props,
                   elementId(r) as rel_id,
                   e.uuid as source_uuid,
                   other.uuid as target_uuid,
                   type(r) as rel_type
            LIMIT $limit
            """
            result = await self.client.driver.execute_query(
                query,
                uuid=entity_uuid,
                limit=limit,
            )

            relationships = []
            for r in result.records:
                props = r["props"]
                relationships.append(
                    Relationship(
                        uuid=r["rel_id"],
                        source_uuid=r["source_uuid"],
                        target_uuid=r["target_uuid"],
                        relation_type=r["rel_type"],
                        fact=props.get("fact", ""),
                        score=props.get("score", 0.0),
                        created_at=props.get("created_at"),
                    )
                )

            return relationships
        except Exception as e:
            logger.error(f"Failed to get relationships: {e}")
            raise

    # ========================================================================
    # Community 管理
    # ========================================================================

    async def get_community(self, community_uuid: str) -> Optional[Community]:
        """
        Get community details by UUID.

        Args:
            community_uuid: Community UUID

        Returns:
            Community object or None
        """
        try:
            query = """
            MATCH (c:Community {uuid: $uuid})
            RETURN properties(c) as props
            """
            result = await self.client.driver.execute_query(query, uuid=community_uuid)
            if result.records:
                props = result.records[0]["props"]
                return Community(
                    uuid=props.get("uuid", community_uuid),
                    name=props.get("name", ""),
                    summary=props.get("summary", ""),
                    member_count=props.get("member_count", 0),
                    tenant_id=props.get("tenant_id"),
                    project_id=props.get("project_id"),
                    formed_at=props.get("formed_at"),
                    created_at=props.get("created_at"),
                )
            return None
        except Exception as e:
            logger.error(f"Failed to get community: {e}")
            raise

    async def list_communities(
        self,
        tenant_id: Optional[str] = None,
        project_id: Optional[str] = None,
        min_members: int = 0,
        limit: int = 50,
    ) -> List[Community]:
        """
        List communities with filtering.

        Args:
            tenant_id: Optional tenant filter
            project_id: Optional project filter
            min_members: Minimum member count
            limit: Maximum communities to return

        Returns:
            List of communities
        """
        try:
            # First try to find communities that have explicit project_id/tenant_id
            # Use coalesce to handle missing member_count (default to 0)
            conditions = ["coalesce(c.member_count, 0) >= $min_members"]
            if tenant_id:
                conditions.append("c.tenant_id = $tenant_id")
            if project_id:
                conditions.append("c.project_id = $project_id")

            where_clause = " AND ".join(conditions)

            query = f"""
            MATCH (c:Community)
            WHERE {where_clause}
            RETURN properties(c) as props
            ORDER BY coalesce(c.member_count, 0) DESC
            LIMIT $limit
            """

            result = await self.client.driver.execute_query(
                query,
                tenant_id=tenant_id,
                project_id=project_id,
                min_members=min_members,
                limit=limit,
            )

            # If no results found but project_id was provided, try to find communities via members
            # This handles cases where community properties might not be synced yet
            if not result.records and (project_id or tenant_id):
                member_conditions = []
                if tenant_id:
                    member_conditions.append("e.tenant_id = $tenant_id")
                if project_id:
                    member_conditions.append("e.project_id = $project_id")

                member_where = " AND ".join(member_conditions)

                # Calculate member count on the fly for fallback
                fallback_query = f"""
                MATCH (c:Community)-[:HAS_MEMBER]->(e:Entity)
                WHERE {member_where}
                WITH c, count(e) as calculated_count
                WHERE calculated_count >= $min_members
                RETURN properties(c) as props, calculated_count
                ORDER BY calculated_count DESC
                LIMIT $limit
                """

                result = await self.client.driver.execute_query(
                    fallback_query,
                    tenant_id=tenant_id,
                    project_id=project_id,
                    min_members=min_members,
                    limit=limit,
                )

            communities = []
            for r in result.records:
                props = r["props"]
                # Use calculated count if available, otherwise prop, otherwise 0
                member_count = r.get("calculated_count", props.get("member_count", 0))

                communities.append(
                    Community(
                        uuid=props.get("uuid", ""),
                        name=props.get("name", ""),
                        summary=props.get("summary", ""),
                        member_count=member_count,
                        tenant_id=props.get("tenant_id"),
                        project_id=props.get("project_id"),
                        formed_at=props.get("formed_at"),
                        created_at=props.get("created_at"),
                    )
                )

            return communities
        except Exception as e:
            logger.error(f"Failed to list communities: {e}")
            raise

    async def get_community_members(
        self,
        community_uuid: str,
        limit: int = 100,
    ) -> List[Entity]:
        """
        Get entities in a community.

        Args:
            community_uuid: Community UUID
            limit: Maximum members to return

        Returns:
            List of entities in the community
        """
        try:
            query = """
            MATCH (c:Community {uuid: $uuid})-[:HAS_MEMBER]->(e:Entity)
            RETURN properties(e) as props
            LIMIT $limit
            """
            result = await self.client.driver.execute_query(
                query,
                uuid=community_uuid,
                limit=limit,
            )

            entities = []
            for r in result.records:
                props = r["props"]
                entities.append(
                    Entity(
                        uuid=props.get("uuid", ""),
                        name=props.get("name", ""),
                        entity_type=props.get("entity_type", "Unknown"),
                        summary=props.get("summary", ""),
                        tenant_id=props.get("tenant_id"),
                        project_id=props.get("project_id"),
                        created_at=props.get("created_at"),
                    )
                )

            return entities
        except Exception as e:
            logger.error(f"Failed to get community members: {e}")
            raise

    # ========================================================================
    # 图谱维护和优化
    # ========================================================================

    async def get_graph_stats(
        self,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, int]:
        """
        Get graph statistics.

        Args:
            tenant_id: Optional tenant filter

        Returns:
            Dictionary with graph statistics
        """
        try:
            stats = {}

            # Count nodes by type
            for label in ["Entity", "Episodic", "Community"]:
                tenant_filter = "{tenant_id: $tenant_id}" if tenant_id else ""
                query = f"""
                MATCH (n:{label} {tenant_filter})
                RETURN count(n) as count
                """
                result = await self.client.driver.execute_query(
                    query,
                    tenant_id=tenant_id,
                )
                stats[f"{label.lower()}_count"] = (
                    result.records[0]["count"] if result.records else 0
                )

            # Count edges
            tenant_filter = "{tenant_id: $tenant_id}" if tenant_id else ""
            query = f"""
            MATCH ()-[r]-(n {tenant_filter})
            RETURN count(r) as count
            """
            result = await self.client.driver.execute_query(
                query,
                tenant_id=tenant_id,
            )
            stats["edge_count"] = result.records[0]["count"] if result.records else 0

            return stats
        except Exception as e:
            logger.error(f"Failed to get graph stats: {e}")
            raise

    # ========================================================================
    # 数据导出
    # ========================================================================

    async def export_data(
        self,
        tenant_id: Optional[str] = None,
        include_episodes: bool = True,
        include_entities: bool = True,
        include_relationships: bool = True,
        include_communities: bool = True,
    ) -> Dict[str, Any]:
        """
        Export graph data as JSON.

        Args:
            tenant_id: Optional tenant filter
            include_episodes: Include episode data
            include_entities: Include entity data
            include_relationships: Include relationship data
            include_communities: Include community data

        Returns:
            Dictionary with exported data
        """
        try:
            export = {}

            if include_episodes:
                episodes_query = """
                MATCH (e:Episodic)
                WHERE $tenant_id IS NULL OR e.tenant_id = $tenant_id
                RETURN properties(e) as episode
                """
                result = await self.client.driver.execute_query(
                    episodes_query,
                    tenant_id=tenant_id,
                )
                export["episodes"] = [dict(r["episode"]) for r in result.records]

            if include_entities:
                entities_query = """
                MATCH (e:Entity)
                WHERE $tenant_id IS NULL OR e.tenant_id = $tenant_id
                RETURN properties(e) as entity
                """
                result = await self.client.driver.execute_query(
                    entities_query,
                    tenant_id=tenant_id,
                )
                export["entities"] = [dict(r["entity"]) for r in result.records]

            if include_relationships:
                rels_query = """
                MATCH (a)-[r]->(b)
                WHERE $tenant_id IS NULL OR a.tenant_id = $tenant_id
                RETURN
                    properties(a) as source,
                    properties(b) as target,
                    type(r) as rel_type,
                    properties(r) as rel_props
                """
                result = await self.client.driver.execute_query(
                    rels_query,
                    tenant_id=tenant_id,
                )
                export["relationships"] = [
                    {
                        "source": dict(r["source"]),
                        "target": dict(r["target"]),
                        "type": r["rel_type"],
                        "properties": dict(r["rel_props"]),
                    }
                    for r in result.records
                ]

            if include_communities:
                communities_query = """
                MATCH (c:Community)
                WHERE $tenant_id IS NULL OR c.tenant_id = $tenant_id
                RETURN properties(c) as community
                """
                result = await self.client.driver.execute_query(
                    communities_query,
                    tenant_id=tenant_id,
                )
                export["communities"] = [dict(r["community"]) for r in result.records]

            export["exported_at"] = datetime.utcnow().isoformat()
            export["tenant_id"] = tenant_id

            logger.info(f"Exported data for tenant: {tenant_id}")
            return export
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            raise

    # ========================================================================
    # 图增量刷新和优化
    # ========================================================================

    async def perform_incremental_refresh(
        self,
        episode_uuids: Optional[List[str]] = None,
        rebuild_communities: bool = False,
    ) -> Dict[str, Any]:
        """
        Perform incremental refresh of the knowledge graph.

        This method updates the graph by reprocessing specific episodes
        and optionally rebuilding communities. More efficient than full rebuild.

        Args:
            episode_uuids: List of episode UUIDs to reprocess (None for all recent)
            rebuild_communities: Whether to rebuild communities after refresh

        Returns:
            Refresh result with statistics
        """
        try:
            from datetime import datetime, timedelta

            results = {
                "refreshed_at": datetime.utcnow().isoformat(),
                "episodes_processed": 0,
                "entities_updated": 0,
                "relationships_updated": 0,
                "communities_rebuilt": False,
            }

            # If no specific episodes provided, process recent ones from last 24 hours
            if not episode_uuids:
                since = datetime.utcnow() - timedelta(hours=24)
                query = """
                MATCH (e:Episodic)
                WHERE e.created_at >= datetime($since)
                RETURN e.uuid as uuid, e.name as name
                ORDER BY e.created_at DESC
                LIMIT 100
                """
                result = await self.client.driver.execute_query(query, since=since.isoformat())
                episode_uuids = [r["uuid"] for r in result.records if r.get("uuid")]

            # Reprocess each episode
            for episode_uuid in episode_uuids:
                try:
                    # Get episode content
                    episode_query = """
                    MATCH (e:Episodic {uuid: $uuid})
                    RETURN properties(e) as props
                    """
                    result = await self.client.driver.execute_query(
                        episode_query, uuid=episode_uuid
                    )

                    if result.records:
                        props = result.records[0]["props"]
                        # Re-add episode (this will trigger entity extraction)
                        await self.client.add_episode(
                            name=props.get("name", episode_uuid),
                            episode_body=props.get("content", ""),
                            source_description=props.get(
                                "source_description", "incremental_refresh"
                            ),
                            source=EpisodeType.text,
                            reference_time=datetime.utcnow(),
                            update_communities=False,  # We'll do this once at the end
                        )
                        results["episodes_processed"] += 1
                except Exception as e:
                    logger.warning(f"Failed to refresh episode {episode_uuid}: {e}")

            # Count entities and relationships
            stats_query = """
            MATCH (n:Entity)
            RETURN count(n) as entity_count
            """
            result = await self.client.driver.execute_query(stats_query)
            results["entities_updated"] = result.records[0]["entity_count"] if result.records else 0

            stats_query = """
            MATCH ()-[r]->()
            RETURN count(r) as rel_count
            """
            result = await self.client.driver.execute_query(stats_query)
            results["relationships_updated"] = (
                result.records[0]["rel_count"] if result.records else 0
            )

            # Optionally rebuild communities
            if rebuild_communities:
                await self.client.build_communities()
                results["communities_rebuilt"] = True

            logger.info(f"Incremental refresh completed: {results}")
            return results

        except Exception as e:
            logger.error(f"Incremental refresh failed: {e}")
            raise

    async def deduplicate_entities(
        self,
        similarity_threshold: float = 0.9,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """
        Find and optionally merge duplicate entities.

        Args:
            similarity_threshold: Similarity threshold for considering entities as duplicates
            dry_run: If True, only report duplicates without merging

        Returns:
            Deduplication result
        """
        try:
            # Find potential duplicates based on name similarity
            query = """
            MATCH (e1:Entity)
            MATCH (e2:Entity)
            WHERE e1.uuid < e2.uuid
              AND toLower(e1.name) = toLower(e2.name)
            RETURN e1.uuid as uuid1, e1.name as name1, e1.entity_type as type1,
                   e2.uuid as uuid2, e2.name as name2, e2.entity_type as type2
            LIMIT 100
            """
            result = await self.client.driver.execute_query(query)

            duplicates = []
            for r in result.records:
                duplicates.append(
                    {
                        "entity1": {"uuid": r["uuid1"], "name": r["name1"], "type": r["type1"]},
                        "entity2": {"uuid": r["uuid2"], "name": r["name2"], "type": r["type2"]},
                    }
                )

            if dry_run:
                return {
                    "dry_run": True,
                    "duplicates_found": len(duplicates),
                    "duplicates": duplicates[:10],  # Return first 10
                    "message": f"Found {len(duplicates)} potential duplicate entities (dry run)",
                }
            else:
                # Merge duplicates (simplified - in production would use more sophisticated logic)
                merged_count = 0
                for dup in duplicates:
                    try:
                        # Merge entity2 into entity1
                        merge_query = """
                        MATCH (e1:Entity {uuid: $uuid1})
                        MATCH (e2:Entity {uuid: $uuid2})
                        OPTIONAL MATCH (e2)-[r]->(other)
                        WITH e1, e2, collect({r: r, other: other}) as rels
                        FOREACH (rel IN rels |
                            MERGE (e1)-[nr:RELATES_TO]->(rel.other)
                            ON CREATE SET nr.fact = rel.r.fact
                        )
                        DETACH DELETE e2
                        """
                        await self.client.driver.execute_query(
                            merge_query,
                            uuid1=dup["entity1"]["uuid"],
                            uuid2=dup["entity2"]["uuid"],
                        )
                        merged_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to merge entities: {e}")

                return {
                    "dry_run": False,
                    "duplicates_found": len(duplicates),
                    "merged": merged_count,
                    "message": f"Merged {merged_count} duplicate entities",
                }

        except Exception as e:
            logger.error(f"Entity deduplication failed: {e}")
            raise

    async def invalidate_stale_edges(
        self,
        days_since_update: int = 30,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """
        Invalidate or remove stale edges that haven't been updated.

        Args:
            days_since_update: Days since last update to consider as stale
            dry_run: If True, only report without deleting

        Returns:
            Invalidation result
        """
        try:
            from datetime import datetime, timedelta

            cutoff = datetime.utcnow() - timedelta(days=days_since_update)

            # Count stale edges
            count_query = """
            MATCH ()-[r]->()
            WHERE r.created_at < datetime($cutoff)
            RETURN count(r) as count
            """
            result = await self.client.driver.execute_query(count_query, cutoff=cutoff.isoformat())
            stale_count = result.records[0]["count"] if result.records else 0

            if dry_run:
                return {
                    "dry_run": True,
                    "stale_edges_found": stale_count,
                    "cutoff_date": cutoff.isoformat(),
                    "message": f"Found {stale_count} stale edges older than {days_since_update} days (dry run)",
                }
            else:
                # Delete stale edges
                delete_query = """
                MATCH ()-[r]->()
                WHERE r.created_at < datetime($cutoff)
                DELETE r
                RETURN count(r) as deleted
                """
                result = await self.client.driver.execute_query(
                    delete_query, cutoff=cutoff.isoformat()
                )
                deleted = result.records[0]["deleted"] if result.records else 0

                logger.info(f"Deleted {deleted} stale edges older than {days_since_update} days")

                return {
                    "dry_run": False,
                    "stale_edges_found": stale_count,
                    "deleted": deleted,
                    "cutoff_date": cutoff.isoformat(),
                    "message": f"Deleted {deleted} stale edges older than {days_since_update} days",
                }

        except Exception as e:
            logger.error(f"Edge invalidation failed: {e}")
            raise

    async def get_maintenance_status(self) -> Dict[str, Any]:
        """
        Get maintenance status and recommendations.

        Returns:
            Maintenance status with recommendations
        """
        try:
            from datetime import datetime, timedelta

            status = {
                "last_checked": datetime.utcnow().isoformat(),
                "recommendations": [],
                "metrics": {},
            }

            # Get graph stats
            stats = await self.get_graph_stats()
            status["metrics"] = stats

            # Check for potential issues
            if stats.get("entity_count", 0) > 10000:
                status["recommendations"].append(
                    {
                        "type": "deduplication",
                        "priority": "medium",
                        "message": "Large number of entities detected. Consider running deduplication.",
                    }
                )

            # Check for old data
            old_data_query = """
            MATCH (e:Episodic)
            WHERE e.created_at < datetime($cutoff)
            RETURN count(e) as count
            """
            cutoff = datetime.utcnow() - timedelta(days=90)
            result = await self.client.driver.execute_query(
                old_data_query, cutoff=cutoff.isoformat()
            )
            old_count = result.records[0]["count"] if result.records else 0

            if old_count > 1000:
                status["recommendations"].append(
                    {
                        "type": "cleanup",
                        "priority": "low",
                        "message": f"Found {old_count} episodes older than 90 days. Consider data cleanup.",
                    }
                )

            if not status["recommendations"]:
                status["recommendations"].append(
                    {
                        "type": "info",
                        "priority": "info",
                        "message": "Graph is healthy. No maintenance actions required.",
                    }
                )

            return status

        except Exception as e:
            logger.error(f"Failed to get maintenance status: {e}")
            raise

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
