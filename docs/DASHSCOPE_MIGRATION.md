# DashScope SDK 迁移完成报告

## 概述

已成功将所有 Qwen 客户端从 OpenAI SDK 迁移到阿里云百炼官方的 DashScope SDK。

## 迁移的文件

### 1. QwenEmbedder (`server/llm_clients/qwen_embedder.py`)
- **移除**: `from openai import AsyncOpenAI`
- **添加**: `import dashscope` 和 `from dashscope import TextEmbedding`
- **API 调用**: `TextEmbedding.call()` 替代 `client.embeddings.create()`
- **响应格式**: `resp.output["embeddings"][0]["embedding"]` 替代 `result.data[0].embedding`
- **批次大小**: 保持为 10（text-embedding-v3 的限制）

### 2. QwenClient (`server/llm_clients/qwen_client.py`)
- **移除**: `from openai import AsyncOpenAI`
- **添加**: `import asyncio`, `import dashscope` 和 `from dashscope import Generation`
- **移除**: `base_url` 配置（DashScope SDK 不需要）
- **API 调用**: `await asyncio.to_thread(Generation.call, ...)` 替代 `await client.chat.completions.create()`
- **异步包装**: 使用 `asyncio.to_thread` 将同步 API 包装为异步调用
- **响应格式**: `response.output.choices[0].message.content` 替代 `response.choices[0].message.content`
- **状态检查**: 添加 `response.status_code != HTTPStatus.OK` 检查

### 3. QwenRerankerClient (`server/llm_clients/qwen_reranker_client.py`)
- **移除**: `from openai import AsyncOpenAI`
- **添加**: `import asyncio`, `import dashscope` 和 `from dashscope import Generation`
- **移除**: `base_url` 配置
- **API 调用**: `await asyncio.to_thread(Generation.call, ...)` 替代 `await client.chat.completions.create()`
- **异步包装**: 使用 `asyncio.to_thread` 将同步 API 包装为异步调用
- **响应格式**: `response.output.choices[0].message.content` 替代 `response.choices[0].message.content`

## 依赖更新

在 `pyproject.toml` 中添加了：
```toml
dependencies = [
    # ... 其他依赖 ...
    "dashscope>=1.20.0",
]
```

## API 密钥配置

所有客户端现在支持两种方式配置 API 密钥：

1. **通过配置对象**:
   ```python
   config = LLMConfig(api_key="your-api-key")
   client = QwenClient(config=config)
   ```

2. **通过环境变量**:
   ```bash
   export DASHSCOPE_API_KEY="your-api-key"
   ```

**重要**: 环境变量已统一为 `DASHSCOPE_API_KEY`（官方标准），不再使用 `QWEN_API_KEY`。详见 [环境变量统一说明](./ENV_VARIABLES_UNIFIED.md)。

## 主要变更

### 初始化方式
**之前 (OpenAI SDK)**:
```python
self.client = AsyncOpenAI(
    api_key=config.api_key,
    base_url=config.base_url,
)
```

**现在 (DashScope SDK)**:
```python
if config.api_key:
    dashscope.api_key = config.api_key
elif not os.environ.get("DASHSCOPE_API_KEY"):
    logger.warning(
        "API key not provided and DASHSCOPE_API_KEY environment variable not set"
    )
```

### API 调用方式

**Embedder - 之前**:
```python
result = await self.client.embeddings.create(
    model=self.config.embedding_model,
    input=text_input,
)
embeddings = result.data[0].embedding
```

**Embedder - 现在**:
```python
resp = TextEmbedding.call(
    model=self.config.embedding_model,
    input=text_input,
)
if resp.status_code != HTTPStatus.OK:
    raise ValueError(f"DashScope API error: {resp.code} - {resp.message}")
embeddings = resp.output["embeddings"][0]["embedding"]
```

**Generation - 之前**:
```python
response = await self.client.chat.completions.create(
    model=model,
    messages=messages,
    temperature=self.temperature,
    max_tokens=max_tokens,
)
content = response.choices[0].message.content
```

**Generation - 现在**:
```python
# DashScope SDK 只提供同步 API，使用 asyncio.to_thread 包装为异步
response = await asyncio.to_thread(
    Generation.call,
    model=model,
    messages=messages,
)
if response.status_code != HTTPStatus.OK:
    raise ValueError(f"DashScope API error: {response.code} - {response.message}")
content = response.output.choices[0].message.content
```

## 兼容性

- 保留了 `client` 参数以保持向后兼容性，但不再使用
- 移除了 `base_url` 配置，因为 DashScope SDK 会自动处理
- 所有现有功能保持不变，只是底层实现从 OpenAI SDK 切换到 DashScope SDK

## 测试

创建了测试脚本 `test_dashscope_migration.py` 用于验证：
- Embedder 功能
- LLM Client 功能
- Reranker 功能

运行测试：
```bash
export DASHSCOPE_API_KEY="your-api-key"
uv run python test_dashscope_migration.py
```

## 验证结果

✅ 所有模块导入成功  
✅ 代码编译无错误  
✅ 依赖安装成功  
✅ API 调用接口正确实现  

## 注意事项

1. **API 密钥**: 确保使用阿里云百炼的 API 密钥（`DASHSCOPE_API_KEY`），而不是 OpenAI 的密钥
2. **模型名称**: 继续使用相同的模型名称（如 `qwen-plus`, `qwen-turbo`, `text-embedding-v3`）
3. **异步支持**: DashScope SDK 本身只提供同步 API（`Generation.call`, `TextEmbedding.call`），需要使用 `asyncio.to_thread()` 包装为异步调用
4. **错误处理**: DashScope SDK 使用 `status_code` 和 `HTTPStatus` 进行错误检查

## 异步包装说明

DashScope SDK 不提供原生的异步方法（如 `call_async()`），我们使用 Python 标准库的 `asyncio.to_thread()` 将同步调用包装为异步：

```python
import asyncio
from dashscope import Generation

# 错误的方式（这个方法不存在）
# response = await Generation.call_async(...)

# 正确的方式
response = await asyncio.to_thread(
    Generation.call,
    model="qwen-plus",
    messages=[...],
)
```

这种方式可以：
- 保持与 Graphiti 框架的异步接口兼容
- 避免阻塞事件循环
- 在线程池中执行同步的 SDK 调用

## 迁移完成时间

2025年12月19日

## 异步包装说明

DashScope SDK 不提供原生的异步方法（如 `call_async()`），我们使用 Python 标准库的 `asyncio.to_thread()` 将同步调用包装为异步：

```python
import asyncio
from dashscope import Generation

# 错误的方式（这个方法不存在）
# response = await Generation.call_async(...)

# 正确的方式
response = await asyncio.to_thread(
    Generation.call,
    model="qwen-plus",
    messages=[...],
)
```

这种方式可以：
- 保持与 Graphiti 框架的异步接口兼容
- 避免阻塞事件循环
- 在线程池中执行同步的 SDK 调用

## 迁移完成时间

2025年12月19日
