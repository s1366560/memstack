"""
OpenAI Reranker Client for Graphiti
"""

import logging
import os
import re
import typing
import asyncio
from openai import AsyncOpenAI
from graphiti_core.cross_encoder.client import CrossEncoderClient
from graphiti_core.helpers import semaphore_gather
from graphiti_core.llm_client import LLMConfig, RateLimitError

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4o-mini"


class OpenAIRerankerClient(CrossEncoderClient):
    """
    OpenAI Reranker Client
    """

    def __init__(
        self,
        config: LLMConfig | None = None,
        client: typing.Any = None,
    ):
        if config is None:
            config = LLMConfig()

        self.config = config

        api_key = config.api_key or os.environ.get("OPENAI_API_KEY")
        base_url = config.base_url or os.environ.get("OPENAI_BASE_URL")

        if not api_key:
            logger.warning(
                "API key not provided and OPENAI_API_KEY environment variable not set"
            )

        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

        if not config.model:
            config.model = DEFAULT_MODEL

    async def rank(self, query: str, passages: list[str]) -> list[tuple[str, float]]:
        """
        Rank passages based on relevance to query using OpenAI.
        """
        if len(passages) <= 1:
            return [(passage, 1.0) for passage in passages]

        async def score_passage(passage: str) -> float:
            prompt = f"""请对这段文本与查询的相关性进行评分，使用 0 到 100 的量表。

查询: {query}

段落: {passage}

只提供一个 0 到 100 之间的数字（不要解释，只要数字）："""

            try:
                response = await self.client.chat.completions.create(
                    model=self.config.model or DEFAULT_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=10,
                )
                
                content = response.choices[0].message.content
                if not content:
                    return 0.0
                    
                score_match = re.search(r"\b(\d{1,3})\b", content)
                if score_match:
                    score = float(score_match.group(1))
                    return max(0.0, min(1.0, score / 100.0))
                return 0.0
            except Exception as e:
                logger.warning(f"Error scoring passage: {e}")
                return 0.0

        try:
            # Concurrent execution
            tasks = [score_passage(p) for p in passages]
            scores = await asyncio.gather(*tasks)
            
            results = list(zip(passages, scores))
            results.sort(reverse=True, key=lambda x: x[1])
            
            return results

        except Exception as e:
            if "rate_limit" in str(e).lower() or "429" in str(e):
                raise RateLimitError from e
            logger.error(f"Error in OpenAI reranker: {e}")
            raise
