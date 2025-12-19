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
            )

            # Add episode to Graphiti
            # Note: Graphiti will automatically extract entities and relationships
            await self.client.add_episode(
                name=str(episode.id),
                episode_body=episode.content,
                source_description=episode_data.source_type or "User input",
                source=EpisodeType.text,
                reference_time=episode.valid_at,
            )

            logger.info(f"Episode {episode.id} added successfully")
            return episode

        except Exception as e:
            logger.error(f"Failed to add episode: {e}")
            raise

    async def search(
        self, query: str, limit: int = 10, tenant_id: Optional[str] = None
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

            # Process episodes from search results
            if hasattr(search_results, "episodes") and search_results.episodes:
                for i, episode in enumerate(search_results.episodes):
                    score = (
                        search_results.episode_reranker_scores[i]
                        if i < len(search_results.episode_reranker_scores)
                        else 0.0
                    )
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

    async def get_entities(
        self, limit: int = 100, tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get entities from the knowledge graph.

        Args:
            limit: Maximum number of entities to return
            tenant_id: Optional tenant filter

        Returns:
            List of entities
        """
        try:
            # Get entities from Graphiti
            # This is a placeholder - actual implementation depends on Graphiti's API
            entities = await self.client.get_entities(limit=limit)

            logger.info(f"Retrieved {len(entities)} entities")
            return entities

        except Exception as e:
            logger.error(f"Failed to get entities: {e}")
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
