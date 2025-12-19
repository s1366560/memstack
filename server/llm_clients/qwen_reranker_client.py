"""
Qwen (通义千问) Reranker Client for Graphiti

基于 Graphiti 的 CrossEncoderClient 接口实现 Qwen 重排序支持
使用 LLM 直接评分的方式对段落进行相关性排序
使用阿里云百炼官方的 DashScope SDK
"""

import asyncio
import logging
import os
import re
import typing
from http import HTTPStatus

import dashscope
from dashscope import Generation
from graphiti_core.cross_encoder.client import CrossEncoderClient
from graphiti_core.helpers import semaphore_gather
from graphiti_core.llm_client import LLMConfig, RateLimitError

logger = logging.getLogger(__name__)

# Qwen 默认重排序模型（使用较小的模型以降低成本和延迟）
DEFAULT_MODEL = "qwen-turbo"


class QwenRerankerClient(CrossEncoderClient):
    """
    Qwen Reranker Client

    使用通义千问 LLM 对段落进行相关性评分和重排序。
    每个段落单独评分（0-100），然后归一化到 [0,1] 范围。
    """

    def __init__(
        self,
        config: LLMConfig | None = None,
        client: typing.Any = None,
    ):
        """
        使用提供的配置和客户端初始化 QwenRerankerClient。

        Args:
            config (LLMConfig | None): LLM 客户端配置，包括 API 密钥、模型等
            client (Any | None): 保留此参数以保持兼容性，但不再使用
        """
        if config is None:
            config = LLMConfig()

        self.config = config

        # 设置 API 密钥
        if config.api_key:
            dashscope.api_key = config.api_key
        elif not os.environ.get("DASHSCOPE_API_KEY"):
            logger.warning(
                "API key not provided and DASHSCOPE_API_KEY environment variable not set"
            )

        # 设置默认值
        if not config.model:
            config.model = DEFAULT_MODEL

    async def rank(self, query: str, passages: list[str]) -> list[tuple[str, float]]:
        """
        基于段落与查询的相关性对段落进行排序。

        使用 LLM 直接评分方式，每个段落单独评分（0-100），然后归一化到 [0,1]。

        Args:
            query (str): 查询字符串
            passages (list[str]): 要排序的段落列表

        Returns:
            list[tuple[str, float]]: 包含段落和分数的元组列表，按相关性降序排序
        """
        if len(passages) <= 1:
            return [(passage, 1.0) for passage in passages]

        # 为每个段落生成评分提示词
        scoring_prompts = []
        for passage in passages:
            prompt = f"""请对这段文本与查询的相关性进行评分，使用 0 到 100 的量表。

查询: {query}

段落: {passage}

只提供一个 0 到 100 之间的数字（不要解释，只要数字）："""

            scoring_prompts.append(
                [
                    {"role": "user", "content": prompt},
                ]
            )

        try:
            # 并发执行所有评分请求 - O(n) API 调用
            # 注意: DashScope SDK 只提供同步 API,使用 asyncio.to_thread 包装为异步
            responses = await semaphore_gather(
                *[
                    asyncio.to_thread(
                        Generation.call,
                        model=self.config.model or DEFAULT_MODEL,
                        messages=prompt_messages,
                    )
                    for prompt_messages in scoring_prompts
                ]
            )

            # 提取分数并创建结果
            results = []
            for passage, response in zip(passages, responses, strict=True):
                try:
                    # 检查响应状态
                    if response.status_code != HTTPStatus.OK:
                        logger.warning(f"DashScope API error: {response.code} - {response.message}")
                        results.append((passage, 0.0))
                        continue

                    if response.output and response.output.choices:
                        content = response.output.choices[0].message.content
                        if content:
                            # 从响应中提取数字分数
                            score_text = content.strip()
                            # 处理模型可能返回非数字文本的情况
                            score_match = re.search(r"\b(\d{1,3})\b", score_text)
                            if score_match:
                                score = float(score_match.group(1))
                                # 归一化到 [0, 1] 范围并限制在有效范围内
                                normalized_score = max(0.0, min(1.0, score / 100.0))
                                results.append((passage, normalized_score))
                            else:
                                logger.warning(
                                    f"Could not extract numeric score from response: {score_text}"
                                )
                                results.append((passage, 0.0))
                        else:
                            logger.warning("Empty content from DashScope for passage scoring")
                            results.append((passage, 0.0))
                    else:
                        logger.warning("Empty response from DashScope for passage scoring")
                        results.append((passage, 0.0))
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Error parsing score from DashScope response: {e}")
                    results.append((passage, 0.0))

            # 按分数降序排序（相关性最高的在前）
            results.sort(reverse=True, key=lambda x: x[1])
            return results

        except Exception as e:
            # 检查是否是速率限制错误
            error_message = str(e).lower()
            if (
                "rate limit" in error_message
                or "quota" in error_message
                or "throttling" in error_message
                or "429" in str(e)
            ):
                raise RateLimitError from e

            logger.error(f"Error in Qwen reranker: {e}")
            raise

            logger.error(f"Error in Qwen reranker: {e}")
            raise
