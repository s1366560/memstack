"""
Qwen (通义千问) LLM Client for Graphiti

基于 Graphiti 的 LLM 客户端接口实现 Qwen API 支持
使用 OpenAI SDK 连接到阿里云 DashScope 兼容端点
"""

import asyncio
import json
import logging
import os
import typing

from openai import AsyncOpenAI, APIError, RateLimitError as OpenAIRateLimitError
from graphiti_core.llm_client.client import LLMClient
from graphiti_core.llm_client.config import DEFAULT_MAX_TOKENS, LLMConfig, ModelSize
from graphiti_core.llm_client.errors import RateLimitError
from graphiti_core.prompts.models import Message
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Qwen 默认模型
DEFAULT_MODEL = "qwen-plus"
DEFAULT_SMALL_MODEL = "qwen-turbo"

# DashScope Base URL (Beijing Region)
DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


class QwenClient(LLMClient):
    """
    QwenClient 是用于与阿里云通义千问 (Qwen) 模型交互的客户端类。

    使用 OpenAI SDK 连接到阿里云 DashScope 兼容端点。

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
        api_key = config.api_key or os.environ.get("DASHSCOPE_API_KEY")
        if not api_key:
            logger.warning(
                "API key not provided and DASHSCOPE_API_KEY environment variable not set"
            )
        
        base_url = os.environ.get("DASHSCOPE_BASE_URL", DEFAULT_BASE_URL)

        # 初始化 OpenAI Client
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
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
                if key.lower() == "id" or key.lower().endswith("_id") or key == "duplicate_idx":
                    # ID 字段默认为 "0" (字符串以兼容 Graphiti)
                    cleaned_data[key] = "0"
                elif "facts" in key.lower() or "edges" in key.lower() or key == "duplicates":
                    # 列表字段默认为空列表
                    cleaned_data[key] = []
                else:
                    # 其他字段保持 None，让 Pydantic 验证器处理
                    cleaned_data[key] = value
            elif isinstance(value, list):
                # Special handling for duplicates list to ensure strings
                if key == "duplicates":
                    cleaned_list = [str(item) if isinstance(item, (int, float)) else item for item in value]
                    cleaned_data[key] = cleaned_list
                else:
                    # 递归清理列表中的元素
                    cleaned_list = []
                    for item in value:
                        if isinstance(item, dict):
                            # Use recursive cleaning for dict items
                            cleaned_item = self._clean_parsed_json(item, None)
                            # 只添加有效的项（例如，如果所有 ID 都是 0，跳过该项）
                            if self._is_valid_item(cleaned_item):
                                cleaned_list.append(cleaned_item)
                        else:
                            cleaned_list.append(item)
                    cleaned_data[key] = cleaned_list
            elif isinstance(value, dict):
                # Check if it looks like a schema definition (Qwen artifact)
                # Qwen sometimes returns {"description": "actual text", "type": "string"} for string fields
                if (
                    "description" in value
                    and isinstance(value.get("description"), str)
                    and ("type" in value or "title" in value or len(value) == 1)
                ):
                    cleaned_data[key] = value["description"]
                else:
                    # 递归清理嵌套字典
                    cleaned_data[key] = self._clean_parsed_json(value, None)
            else:
                # Handle timestamp fields that are 0 (Qwen sometimes returns 0 for null timestamps)
                if (
                    isinstance(value, (int, float))
                    and value == 0
                    and ("_at" in key.lower() or "time" in key.lower())
                ):
                    cleaned_data[key] = None
                # Ensure ID fields are strings for Graphiti compatibility
                elif (key.lower() == "id" or key.lower().endswith("_id") or key == "duplicate_idx") and isinstance(value, (int, float)):
                    cleaned_data[key] = str(int(value))
                else:
                    cleaned_data[key] = value

        # Map entity_type_id to entity_type if needed
        if "entity_type_id" in cleaned_data and (
            "entity_type" not in cleaned_data or not cleaned_data["entity_type"]
        ):
            type_id = cleaned_data["entity_type_id"]
            # Default mapping based on graphiti_service.py
            mapping = [
                "Entity",
                "Person",
                "Organization",
                "Location",
                "Concept",
                "Event",
                "Artifact",
            ]
            if isinstance(type_id, int) and 0 <= type_id < len(mapping):
                cleaned_data["entity_type"] = mapping[type_id]
            else:
                cleaned_data["entity_type"] = "Entity"

        # Heuristic fix for Qwen's duplicate_idx behavior
        # If duplicate_idx points to self (id), but duplicates list has other IDs,
        # pick the first other ID as the duplicate target.
        current_id = cleaned_data.get("id")
        dup_idx = cleaned_data.get("duplicate_idx")
        duplicates = cleaned_data.get("duplicates", [])
        
        if current_id is not None and dup_idx is not None and duplicates:
            # Ensure types match for comparison (they should be strings now due to cleaning above)
            if str(dup_idx) == str(current_id):
                other_dups = [d for d in duplicates if str(d) != str(current_id)]
                if other_dups:
                    cleaned_data["duplicate_idx"] = str(other_dups[0])
                    logger.info(f"Fixed duplicate_idx from {dup_idx} to {other_dups[0]} based on duplicates list {duplicates}")

        return cleaned_data

    def _is_valid_item(self, item: dict[str, typing.Any]) -> bool:
        """
        检查一个项是否有效。
        """
        # 如果有名称、内容或事实，无论 ID 如何都认为是有效的
        if item.get("name") or item.get("content") or item.get("fact"):
            return True

        # 如果是去重结果，包含 duplicates 字段，认为是有效的
        if "duplicates" in item or "duplicate_idx" in item:
            return True

        # 如果有非空的 id 字段，也认为是有效的（即使是 0 或 "0"）
        # 只有当 ID 为 None 且没有其他内容时才无效
        for key, value in item.items():
            if key.lower() == "id" or key.lower().endswith("_id"):
                if value is not None:
                    return True

        # 如果没有 ID 字段，认为有效
        return True

    async def _generate_response(
        self,
        messages: list[Message],
        response_model: type[BaseModel] | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        model_size: ModelSize = ModelSize.medium,
        retry_count: int = 0,
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
        # 准备 OpenAI 格式的消息
        openai_messages = []
        
        # 如果需要结构化输出，确保 System Prompt 包含 JSON 指令
        # Qwen 的 JSON Mode 要求 System/User Prompt 中必须包含 "json"
        has_system = any(m.role == "system" for m in messages)
        json_instruction = "You must output valid JSON only."
        
        if not has_system and response_model:
            openai_messages.append({"role": "system", "content": json_instruction})
            
        for m in messages:
            content = self._clean_input(m.content)
            if response_model and m.role == "system":
                content += f" {json_instruction}"
            
            # OpenAI Mode 下，我们可以简化 Prompt，因为 json_object mode 很强
            openai_messages.append({"role": m.role, "content": content})

        model = self._get_model_for_size(model_size)
        
        try:
            kwargs = {
                "model": model,
                "messages": openai_messages,
                "max_tokens": max_tokens,
            }
            
            # 启用 JSON Mode
            if response_model:
                kwargs["response_format"] = {"type": "json_object"}
            
            response = await self.client.chat.completions.create(**kwargs)
            
            if not response.choices:
                raise ValueError("No choices in response")
                
            raw_output = response.choices[0].message.content
            
            if not raw_output:
                raise ValueError("Empty response content")

            logger.info(f"Qwen raw output: {raw_output}")
            
            if response_model:
                try:
                    # 尝试解析 JSON
                    try:
                        parsed_json = json.loads(raw_output)
                    except json.JSONDecodeError:
                        # 尝试清理 markdown
                        clean_output = raw_output.strip()
                        if clean_output.startswith("```json"):
                            clean_output = clean_output[7:]
                        elif clean_output.startswith("```"):
                            clean_output = clean_output[3:]
                        if clean_output.endswith("```"):
                            clean_output = clean_output[:-3]
                        parsed_json = json.loads(clean_output.strip())
                    
                    # Check if returned JSON is a Schema (properties, type, etc.)
                    # and try to extract data from description or default fields
                    if isinstance(parsed_json, dict) and "properties" in parsed_json:
                        logger.warning("Qwen returned JSON Schema instead of data. Attempting heuristic extraction...")
                        
                        extracted = {}
                        properties = parsed_json.get("properties", {})
                        for k, v in properties.items():
                            if isinstance(v, dict):
                                # If description is long enough, it might be the content
                                desc = v.get("description", "")
                                # Heuristic: if description looks like content (not just "The summary of...")
                                # But for 'summary' field, description often IS the summary if model is confused
                                if desc and len(str(desc)) > 10:
                                     extracted[k] = desc
                                # Check default
                                if "default" in v:
                                    extracted[k] = v["default"]
                        
                        if extracted:
                            logger.info(f"Heuristically extracted data: {extracted}")
                            # Merge with parsed_json to keep other fields if any
                            # But usually schema only has properties
                            parsed_json = extracted
                        else:
                            logger.warning("Failed to extract data from Schema.")
                            # Trigger retry logic below by raising error
                            raise ValueError("LLM returned JSON Schema instead of data")

                    # 清理数据
                    parsed_json = self._clean_parsed_json(parsed_json, response_model)
                    
                    # 验证
                    validated = response_model.model_validate(parsed_json)
                    return validated.model_dump()
                except Exception as e:
                    logger.error(f"Failed to parse/validate JSON: {e}")
                    logger.error(f"Raw output: {raw_output}")
                    
                    # Retry logic
                    if retry_count < 2:
                         logger.info(f"Retrying generation (attempt {retry_count + 1})...")
                         
                         # Add error feedback to messages
                         # We need to construct new messages list carefully
                         # messages is list[Message]
                         new_messages = list(messages)
                         
                         # Add assistant output (what it generated)
                         new_messages.append(Message(role="assistant", content=raw_output))
                         
                         # Add user correction
                         correction = "You returned the JSON Schema definition instead of the actual data. Please output the JSON object containing the actual extracted data."
                         new_messages.append(Message(role="user", content=correction))
                         
                         return await self._generate_response(
                             messages=new_messages,
                             response_model=response_model,
                             max_tokens=max_tokens,
                             model_size=model_size,
                             retry_count=retry_count + 1
                         )
                    raise

            return {"content": raw_output}

        except OpenAIRateLimitError as e:
            raise RateLimitError from e
        except Exception as e:
            logger.error(f"Error in generating LLM response: {e}")
            raise

    def _get_provider_type(self) -> str:
        """获取提供商类型"""
        return "qwen"
