"""
OpenAI LLM Client for Graphiti
"""

import json
import logging
import os
import typing

from graphiti_core.llm_client.client import LLMClient
from graphiti_core.llm_client.config import DEFAULT_MAX_TOKENS, LLMConfig, ModelSize
from graphiti_core.llm_client.errors import RateLimitError
from graphiti_core.prompts.models import Message
from openai import AsyncOpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4o"
DEFAULT_SMALL_MODEL = "gpt-4o-mini"


class OpenAIClient(LLMClient):
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

        super().__init__(config, cache)

        # Configure OpenAI client
        api_key = config.api_key or os.environ.get("OPENAI_API_KEY")
        base_url = config.base_url or os.environ.get("OPENAI_BASE_URL")

        if not api_key:
            logger.warning("API key not provided and OPENAI_API_KEY environment variable not set")

        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

        if not config.model:
            config.model = DEFAULT_MODEL
        if not config.small_model:
            config.small_model = DEFAULT_SMALL_MODEL

        self.model = config.model
        self.small_model = config.small_model

    def _get_model_for_size(self, model_size: ModelSize) -> str:
        """Get appropriate model based on requested size"""
        if model_size == ModelSize.small:
            return self.small_model or DEFAULT_SMALL_MODEL
        else:
            return self.model or DEFAULT_MODEL

    async def _generate_response(
        self,
        messages: list[Message],
        response_model: type[BaseModel] | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        model_size: ModelSize = ModelSize.medium,
    ) -> dict[str, typing.Any]:
        """Generate response from OpenAI"""
        try:
            openai_messages = [{"role": m.role, "content": m.content} for m in messages]
            model = self._get_model_for_size(model_size)

            kwargs = {
                "model": model,
                "messages": openai_messages,
                "max_tokens": max_tokens,
                "temperature": self.config.temperature or 0.7,
            }

            if response_model:
                kwargs["response_format"] = {"type": "json_object"}
                # Ensure system prompt mentions JSON output if not already present
                # But typically Graphiti prompts already ask for JSON

            response = await self.client.chat.completions.create(**kwargs)

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")

            logger.debug(f"OpenAI raw output: {content}")

            if response_model:
                try:
                    # Clean up markdown code blocks if present
                    json_str = content.strip()
                    if json_str.startswith("```json"):
                        json_str = json_str[7:]
                    elif json_str.startswith("```"):
                        json_str = json_str[3:]
                    if json_str.endswith("```"):
                        json_str = json_str[:-3]
                    json_str = json_str.strip()

                    parsed_json = json.loads(json_str)

                    # Basic cleaning similar to Qwen client
                    cleaned_json = self._clean_json(parsed_json)

                    validated = response_model.model_validate(cleaned_json)
                    return validated.model_dump()
                except Exception as e:
                    logger.error(f"Failed to parse/validate JSON: {e}")
                    logger.error(f"Raw output: {content}")
                    raise

            return {"content": content}

        except Exception as e:
            if "rate_limit" in str(e).lower() or "429" in str(e):
                raise RateLimitError from e
            logger.error(f"Error generating response from OpenAI: {e}")
            raise e

    def _clean_json(self, data: typing.Any) -> typing.Any:
        """Recursively clean JSON data (handle nulls etc)"""
        if isinstance(data, dict):
            return {k: self._clean_json(v) for k, v in data.items() if v is not None}
        elif isinstance(data, list):
            return [self._clean_json(item) for item in data if item is not None]
        return data

    def _get_provider_type(self) -> str:
        return "openai"
