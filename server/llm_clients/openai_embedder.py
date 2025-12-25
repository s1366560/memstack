"""
OpenAI Embedder for Graphiti
"""

import logging
import os
from collections.abc import Iterable
from typing import List, Union

from graphiti_core.embedder.client import EmbedderClient, EmbedderConfig
from openai import AsyncOpenAI
from pydantic import Field

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_BATCH_SIZE = 100


class OpenAIEmbedderConfig(EmbedderConfig):
    """OpenAI Embedder Configuration"""

    embedding_model: str = Field(default=DEFAULT_EMBEDDING_MODEL)
    api_key: str | None = None
    base_url: str | None = None


class OpenAIEmbedder(EmbedderClient):
    """
    OpenAI Embedder Client
    """

    def __init__(
        self,
        config: OpenAIEmbedderConfig | None = None,
        batch_size: int | None = None,
    ):
        if config is None:
            config = OpenAIEmbedderConfig()

        self.config = config

        api_key = config.api_key or os.environ.get("OPENAI_API_KEY")
        base_url = config.base_url or os.environ.get("OPENAI_BASE_URL")

        if not api_key:
            logger.warning("API key not provided and OPENAI_API_KEY environment variable not set")

        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.batch_size = batch_size or DEFAULT_BATCH_SIZE

    async def create(
        self, input_data: Union[str, List[str], Iterable[int], Iterable[Iterable[int]]]
    ) -> List[float]:
        """Create embeddings for input data"""
        # Ensure input is string
        if isinstance(input_data, str):
            text_input = input_data
        elif (
            isinstance(input_data, list) and len(input_data) > 0 and isinstance(input_data[0], str)
        ):
            text_input = input_data[0]
        else:
            text_input = str(input_data)

        try:
            resp = await self.client.embeddings.create(
                model=self.config.embedding_model or DEFAULT_EMBEDDING_MODEL,
                input=text_input,
            )

            if not resp.data:
                raise ValueError("No embeddings returned from OpenAI")

            embedding_values = resp.data[0].embedding

            if self.config.embedding_dim and len(embedding_values) > self.config.embedding_dim:
                return embedding_values[: self.config.embedding_dim]

            return embedding_values

        except Exception as e:
            logger.error(f"Error calling OpenAI Embeddings API: {e}")
            raise

    async def create_batch(self, input_data_list: List[str]) -> List[List[float]]:
        """Create embeddings for a batch of inputs"""
        if not input_data_list:
            return []

        batch_size = self.batch_size
        all_embeddings = []

        for i in range(0, len(input_data_list), batch_size):
            batch = input_data_list[i : i + batch_size]

            try:
                resp = await self.client.embeddings.create(
                    model=self.config.embedding_model or DEFAULT_EMBEDDING_MODEL,
                    input=batch,
                )

                # Sort by index to ensure order matches input
                sorted_data = sorted(resp.data, key=lambda x: x.index)

                for item in sorted_data:
                    embedding_values = item.embedding
                    if (
                        self.config.embedding_dim
                        and len(embedding_values) > self.config.embedding_dim
                    ):
                        embedding_values = embedding_values[: self.config.embedding_dim]
                    all_embeddings.append(embedding_values)

            except Exception as e:
                logger.error(f"Batch embedding failed for batch {i}: {e}")
                # Fallback to individual processing
                for item in batch:
                    try:
                        emb = await self.create(item)
                        all_embeddings.append(emb)
                    except Exception as inner_e:
                        logger.error(f"Individual embedding failed: {inner_e}")
                        raise inner_e

        return all_embeddings
