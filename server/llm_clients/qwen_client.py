"""
Qwen (通义千问) LLM Client for Graphiti

基于 Graphiti 的 LLM 客户端接口实现 Qwen API 支持
使用阿里云百炼官方的 DashScope SDK
"""

import asyncio
import json
import logging
import os
import typing
from http import HTTPStatus

import dashscope
from dashscope import Generation
from graphiti_core.llm_client.client import LLMClient
from graphiti_core.llm_client.config import DEFAULT_MAX_TOKENS, LLMConfig, ModelSize
from graphiti_core.llm_client.errors import RateLimitError
from graphiti_core.prompts.models import Message
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Qwen 默认模型
DEFAULT_MODEL = "qwen-plus"
DEFAULT_SMALL_MODEL = "qwen-turbo"


class QwenClient(LLMClient):
    """
    QwenClient 是用于与阿里云通义千问 (Qwen) 模型交互的客户端类。

    使用阿里云百炼官方的 DashScope SDK。

    Attributes:
        model (str): 用于生成响应的模型名称
        small_model (str): 用于小型任务的模型名称
        temperature (float): 生成响应时使用的温度参数
        max_tokens (int): 响应中生成的最大 token 数
    """

    def __init__(
        self,
        config: LLMConfig | None = None,
        cache: bool = False,
        client: typing.Any = None,
    ):
        """
        使用提供的配置、缓存设置和客户端初始化 QwenClient。

        Args:
            config (LLMConfig | None): LLM 客户端的配置，包括 API 密钥、模型、温度和最大 token 数
            cache (bool): 是否对响应使用缓存。默认为 False
            client (Any | None): 保留此参数以保持兼容性，但不再使用
        """
        if config is None:
            config = LLMConfig()

        super().__init__(config, cache)

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
        if not config.small_model:
            config.small_model = DEFAULT_SMALL_MODEL

        self.model = config.model
        self.small_model = config.small_model

    def _get_model_for_size(self, model_size: ModelSize) -> str:
        """根据请求的大小获取适当的模型名称"""
        if model_size == ModelSize.small:
            return self.small_model or DEFAULT_SMALL_MODEL
        else:
            return self.model or DEFAULT_MODEL

    def _clean_parsed_json(
        self, data: dict[str, typing.Any], response_model: type[BaseModel] | None
    ) -> dict[str, typing.Any]:
        """
        清理解析后的 JSON 数据，处理 null 值和无效数据。

        Args:
            data: 解析后的 JSON 数据
            response_model: Pydantic 响应模型

        Returns:
            清理后的数据
        """
        if not isinstance(data, dict):
            return data

        cleaned_data = {}

        for key, value in data.items():
            if value is None:
                # 对于 null 值，根据字段名提供默认值
                if "id" in key.lower():
                    # ID 字段默认为 0
                    cleaned_data[key] = 0
                elif "facts" in key.lower() or "edges" in key.lower():
                    # 列表字段默认为空列表
                    cleaned_data[key] = []
                else:
                    # 其他字段保持 None，让 Pydantic 验证器处理
                    cleaned_data[key] = value
            elif isinstance(value, list):
                # 递归清理列表中的元素
                cleaned_list = []
                for item in value:
                    if isinstance(item, dict):
                        # 清理字典中的 null 值
                        cleaned_item = {}
                        for item_key, item_value in item.items():
                            if item_value is None and "id" in item_key.lower():
                                cleaned_item[item_key] = 0
                            else:
                                cleaned_item[item_key] = item_value
                        # 只添加有效的项（例如，如果所有 ID 都是 0，跳过该项）
                        if self._is_valid_item(cleaned_item):
                            cleaned_list.append(cleaned_item)
                    else:
                        cleaned_list.append(item)
                cleaned_data[key] = cleaned_list
            elif isinstance(value, dict):
                # 递归清理嵌套字典
                cleaned_data[key] = self._clean_parsed_json(value, None)
            else:
                cleaned_data[key] = value

        return cleaned_data

    def _is_valid_item(self, item: dict[str, typing.Any]) -> bool:
        """
        检查一个项是否有效。

        如果项中的所有 ID 字段都是 0 或 None，则认为无效。
        """
        has_id_field = False
        has_valid_id = False

        for key, value in item.items():
            if "id" in key.lower():
                has_id_field = True
                if value is not None and value != 0:
                    has_valid_id = True
                    break

        # 如果没有 ID 字段，认为有效
        # 如果有 ID 字段，则必须至少有一个有效的 ID
        return not has_id_field or has_valid_id

    async def _generate_response(
        self,
        messages: list[Message],
        response_model: type[BaseModel] | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        model_size: ModelSize = ModelSize.medium,
    ) -> dict[str, typing.Any]:
        """
        从 Qwen 语言模型生成响应。

        Args:
            messages (list[Message]): 要发送到语言模型的消息列表
            response_model (type[BaseModel] | None): 可选的 Pydantic 模型，用于解析响应
            max_tokens (int): 响应中生成的最大 token 数
            model_size (ModelSize): 要使用的模型大小（small 或 medium）

        Returns:
            dict[str, typing.Any]: 来自语言模型的响应

        Raises:
            RateLimitError: 如果超出 API 速率限制
            Exception: 如果生成响应时出错
        """
        try:
            # 转换消息格式为 DashScope 格式
            dashscope_messages = []
            for m in messages:
                dashscope_messages.append({"role": m.role, "content": self._clean_input(m.content)})

            # 获取适当大小的模型
            model = self._get_model_for_size(model_size)

            # 准备请求参数
            request_params = {
                "model": model,
                "messages": dashscope_messages,
            }

            # 如果需要结构化输出，设置 result_format 为 message
            if response_model is not None:
                request_params["result_format"] = "message"

            # 调用 DashScope Generation API（使用 asyncio.to_thread 包装同步调用）
            response = await asyncio.to_thread(
                Generation.call,
                **request_params
            )

            # 检查响应状态
            if response.status_code != HTTPStatus.OK:
                raise ValueError(f"DashScope API error: {response.code} - {response.message}")

            # 提取响应内容
            if not response.output or not response.output.choices:
                raise ValueError("No response choices returned from DashScope API")

            raw_output = response.output.choices[0].message.content

            if not raw_output:
                raise ValueError("Empty response content from DashScope API")

            # 如果是结构化输出请求，解析并验证响应
            if response_model is not None:
                try:
                    # 解析 JSON
                    parsed_json = json.loads(raw_output)

                    # Qwen 可能返回 JSON Schema 而不是实际数据
                    # 检查是否是 Schema 格式（包含 'properties' 和 'type'）
                    if (
                        isinstance(parsed_json, dict)
                        and "properties" in parsed_json
                        and "type" in parsed_json
                    ):
                        logger.warning(
                            "Qwen returned JSON Schema instead of data, extracting from description"
                        )
                        # 尝试从 Schema 的 properties 字段提取实际值
                        extracted_data = {}
                        properties = parsed_json.get("properties", {})

                        for field_name, field_value in properties.items():
                            # 如果值是字典且包含 'type' 键，说明这是 Schema 定义
                            if isinstance(field_value, dict) and "type" in field_value:
                                # 尝试从各种字段提取值
                                if "description" in field_value:
                                    # description 字段可能包含实际值（对于字符串类型）
                                    extracted_data[field_name] = field_value["description"]
                                elif "default" in field_value:
                                    extracted_data[field_name] = field_value["default"]
                                elif "enum" in field_value and field_value["enum"]:
                                    extracted_data[field_name] = field_value["enum"][0]
                                else:
                                    # 根据类型提供默认值
                                    field_type = field_value.get("type", "string")
                                    if field_type == "array":
                                        extracted_data[field_name] = []
                                    elif field_type == "object":
                                        extracted_data[field_name] = {}
                                    elif field_type == "boolean":
                                        extracted_data[field_name] = False
                                    elif field_type == "number" or field_type == "integer":
                                        extracted_data[field_name] = 0
                                    else:
                                        extracted_data[field_name] = ""
                            else:
                                # 直接使用值（这是 Qwen 有时的返回格式）
                                extracted_data[field_name] = field_value

                        if extracted_data:
                            logger.info(f"Extracted data from Schema: {extracted_data}")
                            parsed_json = extracted_data
                        else:
                            logger.error(
                                "Could not extract data from Schema, using original response"
                            )

                    # 清理数据：处理 null 值和无效数据
                    parsed_json = self._clean_parsed_json(parsed_json, response_model)

                    # 使用 Pydantic 模型验证
                    validated_model = response_model.model_validate(parsed_json)

                    # 返回为字典以保持 API 一致性
                    return validated_model.model_dump()
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.error(f"Raw output: {raw_output}")
                    raise Exception(f"Failed to parse JSON response: {e}") from e
                except Exception as e:
                    logger.error(f"Failed to validate response with model: {e}")
                    logger.error(f"Raw output: {raw_output}")
                    raise Exception(f"Failed to validate structured response: {e}") from e

            # 否则，返回响应文本作为字典
            return {"content": raw_output}

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

            logger.error(f"Error in generating LLM response: {e}")
            raise

    def _get_provider_type(self) -> str:
        """获取提供商类型"""
        return "qwen"

    def _get_provider_type(self) -> str:
        """获取提供商类型"""
        return "qwen"
