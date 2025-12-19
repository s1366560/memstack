# 环境变量统一说明

## 概述

本文档说明了 VIP Memory 项目中环境变量的统一命名规范，特别是 Qwen（通义千问）相关的环境变量。

## Qwen 环境变量统一

### 变更说明

为了与阿里云百炼官方 DashScope SDK 保持一致，我们已将所有 Qwen 相关的环境变量统一使用官方标准：

**之前（已废弃）**:
```bash
QWEN_API_KEY=sk-xxx
```

**现在（官方标准）**:
```bash
DASHSCOPE_API_KEY=sk-xxx
```

### 原因

1. **官方标准**: `DASHSCOPE_API_KEY` 是阿里云百炼 DashScope SDK 的官方环境变量名
2. **SDK 自动识别**: DashScope SDK 会自动从环境变量 `DASHSCOPE_API_KEY` 读取 API 密钥
3. **避免混淆**: 统一使用官方命名，避免维护多个不同的环境变量名

### 影响的文件

已更新以下文件中的环境变量引用：

1. **配置文件**:
   - `server/config.py`: 将 alias 从 `QWEN_API_KEY` 改为 `DASHSCOPE_API_KEY`
   - `.env.example`: 添加 `DASHSCOPE_API_KEY` 配置示例

2. **示例代码**:
   - `examples/test_qwen_integration.py`
   - `examples/test_qwen_reranker.py`

3. **文档**:
   - `docs/CHANGELOG_QWEN.md`
   - `docs/QWEN_IMPLEMENTATION_SUMMARY.md`
   - `docs/QWEN_INTEGRATION.md`
   - `docs/QWEN_RERANKER_USAGE.md`

4. **SDK 客户端**:
   - `server/llm_clients/qwen_client.py`
   - `server/llm_clients/qwen_embedder.py`
   - `server/llm_clients/qwen_reranker_client.py`

## 完整的 Qwen 环境变量列表

```bash
# API 密钥（必填）
DASHSCOPE_API_KEY=sk-your-dashscope-api-key-here

# 模型配置（可选，有默认值）
QWEN_MODEL=qwen-plus              # 默认主模型
QWEN_SMALL_MODEL=qwen-turbo       # 默认小模型
QWEN_EMBEDDING_MODEL=text-embedding-v3  # 默认嵌入模型
```

## 配置方式

### 方式 1: 使用 .env 文件

```bash
# 编辑 .env 文件
DASHSCOPE_API_KEY=sk-your-dashscope-api-key-here
QWEN_MODEL=qwen-plus
QWEN_SMALL_MODEL=qwen-turbo
QWEN_EMBEDDING_MODEL=text-embedding-v3
```

### 方式 2: 使用环境变量

```bash
export DASHSCOPE_API_KEY="sk-your-dashscope-api-key-here"
export QWEN_MODEL="qwen-plus"
export QWEN_SMALL_MODEL="qwen-turbo"
export QWEN_EMBEDDING_MODEL="text-embedding-v3"
```

### 方式 3: 在代码中配置

```python
from graphiti_core.llm_client.config import LLMConfig
from server.llm_clients.qwen_client import QwenClient

config = LLMConfig(
    api_key="sk-your-dashscope-api-key-here",
    model="qwen-plus",
    small_model="qwen-turbo",
)

client = QwenClient(config=config)
```

## 迁移指南

如果您之前使用 `QWEN_API_KEY`，请按照以下步骤迁移：

### 步骤 1: 更新 .env 文件

```bash
# 将
QWEN_API_KEY=sk-xxx

# 改为
DASHSCOPE_API_KEY=sk-xxx
```

### 步骤 2: 更新环境变量

```bash
# 删除旧的环境变量
unset QWEN_API_KEY

# 设置新的环境变量
export DASHSCOPE_API_KEY="sk-xxx"
```

### 步骤 3: 验证配置

```bash
# 运行测试确认配置正确
uv run python examples/test_qwen_integration.py
```

## 其他 LLM 提供商的环境变量

为了保持一致性，不同 LLM 提供商使用各自的官方标准环境变量：

| 提供商 | API 密钥环境变量 | 说明 |
|--------|----------------|------|
| OpenAI | `OPENAI_API_KEY` | OpenAI 官方标准 |
| Google Gemini | `GOOGLE_API_KEY` | Google 官方标准 |
| Qwen (DashScope) | `DASHSCOPE_API_KEY` | 阿里云百炼官方标准 |

## 常见问题

### Q: 为什么不继续支持 QWEN_API_KEY？

A: 为了与官方 SDK 保持一致，避免维护多个环境变量名。DashScope SDK 原生支持 `DASHSCOPE_API_KEY`，使用官方标准可以减少配置混淆。

### Q: 旧代码会受到影响吗？

A: 不会。我们已经更新了所有代码和文档。只要按照迁移指南更新环境变量即可。

### Q: 可以同时使用两个环境变量名吗？

A: 不建议。请统一使用 `DASHSCOPE_API_KEY`。

## 参考资料

- [阿里云百炼 DashScope SDK 文档](https://help.aliyun.com/zh/model-studio/dashscope-api-reference)
- [DashScope Python SDK](https://github.com/aliyun/alibabacloud-python-sdk-v2)
- [VIP Memory 配置文档](./QWEN_INTEGRATION.md)

## 更新日期

2025年12月19日
