"""
OpenAI LLM Client for Graphiti
"""

import logging
import os

from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.llm_client.openai_client import OpenAIClient as GraphitiOpenAIClient

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4o"
DEFAULT_SMALL_MODEL = "gpt-4o-mini"


class OpenAIClient(GraphitiOpenAIClient):
    """
    OpenAI Client for Graphiti
    """

    def __init__(
        self,
        config: LLMConfig | None = None,
        cache: bool = False,
    ):
        if config is None:
            config = LLMConfig()

        # Configure OpenAI client settings from env if not provided
        if not config.api_key:
            config.api_key = os.environ.get("OPENAI_API_KEY")

        if not config.base_url:
            config.base_url = os.environ.get("OPENAI_BASE_URL")

        if not config.api_key:
            logger.warning("API key not provided and OPENAI_API_KEY environment variable not set")

        if not config.model:
            config.model = os.environ.get("OPENAI_MODEL", DEFAULT_MODEL)

        super().__init__(config=config, cache=cache)
