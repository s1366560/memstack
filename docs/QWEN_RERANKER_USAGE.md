# Qwen Reranker 使用指南

## 概述

Qwen Reranker 是为 Graphiti 知识图谱引擎实现的基于通义千问 LLM 的重排序器。它可以对检索结果进行相关性重新排序，提高搜索质量。

## 功能特性

- ✅ 基于 LLM 的智能相关性评分（0-100 分制）
- ✅ 并发处理多个段落，提高效率
- ✅ 自动归一化分数到 [0,1] 范围
- ✅ 支持速率限制检测和错误处理
- ✅ 使用 `qwen-turbo` 小模型，降低成本和延迟

## 快速开始

### 1. 基本使用

```python
from graphiti_core import Graphiti
from graphiti_core.llm_client import LLMConfig
from server.llm_clients.qwen_client import QwenClient
from server.llm_clients.qwen_embedder import QwenEmbedder, QwenEmbedderConfig
from server.llm_clients.qwen_reranker_client import QwenRerankerClient

# 初始化 Graphiti（包含 Reranker）
graphiti = Graphiti(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password",
    llm_client=QwenClient(
        config=LLMConfig(
            api_key="your-qwen-api-key",
            model="qwen-plus",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
    ),
    embedder=QwenEmbedder(
        config=QwenEmbedderConfig(
            api_key="your-qwen-api-key",
            embedding_model="text-embedding-v3",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
    ),
    cross_encoder=QwenRerankerClient(
        config=LLMConfig(
            api_key="your-qwen-api-key",
            model="qwen-turbo",  # 使用 turbo 模型以降低成本
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
    ),
)
```

### 2. 在 GraphitiService 中使用

GraphitiService 已经集成了 Qwen Reranker，使用 `qwen` 提供商时会自动启用：

```python
from server.services.graphiti_service import graphiti_service

# 初始化服务（自动包含 Reranker）
await graphiti_service.initialize(provider='qwen')

# 执行搜索（自动使用 Reranker 重排序）
results = await graphiti_service.search(query="用户的兴趣爱好是什么？", limit=10)
```

### 3. 直接使用 Reranker

也可以单独使用 Reranker 对文本段落进行排序：

```python
from graphiti_core.llm_client import LLMConfig
from server.llm_clients.qwen_reranker_client import QwenRerankerClient

# 创建 Reranker 实例
reranker = QwenRerankerClient(
    config=LLMConfig(
        api_key="your-qwen-api-key",
        model="qwen-turbo",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
)

# 对段落进行排序
query = "机器学习工程师的工作内容"
passages = [
    "负责推荐系统的研发",
    "喜欢打篮球和健身",
    "会弹吉他和钢琴",
    "有3年机器学习经验",
]

ranked_results = await reranker.rank(query, passages)

# 结果格式: [(passage, score), ...]
for passage, score in ranked_results:
    print(f"[{score:.3f}] {passage}")
```

## 配置选项

### LLMConfig 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `api_key` | 通义千问 API 密钥 | 必需 |
| `model` | 使用的模型名称 | `qwen-turbo` |
| `base_url` | API 基础 URL | `https://dashscope.aliyuncs.com/compatible-mode/v1` |

### 推荐模型选择

- **qwen-turbo**（推荐）：性价比最高，速度快，成本低
- **qwen-plus**：准确性更高，但成本稍高
- **qwen-max**：最高准确性，但成本最高，不推荐用于 reranking

## 工作原理

1. **评分阶段**：对每个段落，Reranker 会向 LLM 发送评分请求，要求给出 0-100 的相关性分数
2. **并发处理**：使用 `semaphore_gather` 并发执行所有评分请求，提高效率
3. **分数提取**：使用正则表达式从 LLM 响应中提取数字分数
4. **归一化**：将 0-100 分数归一化到 [0,1] 范围
5. **排序**：按分数降序排序，返回排序后的段落列表

## 性能考虑

### 成本优化

- 使用 `qwen-turbo` 模型，每次评分成本约为 ¥0.0003（按 API 调用计费）
- 对于 10 个段落的重排序，总成本约为 ¥0.003
- 相比 `qwen-plus` 和 `qwen-max`，成本降低 50-75%

### 延迟优化

- 并发处理所有段落，延迟约等于单次 LLM 调用（约 100-300ms）
- 使用 `max_tokens=3` 限制响应长度，减少延迟
- `temperature=0.0` 确保输出稳定性

### 质量保证

- 从 LLM 响应中智能提取分数，容错性强
- 处理异常情况（空响应、解析错误等），给予默认分数 0.0
- 检测速率限制错误，抛出 `RateLimitError` 供上层处理

## 测试

运行测试脚本验证 Reranker 功能：

```bash
cd /path/to/vip-memory
export DASHSCOPE_API_KEY="your-api-key"
uv run python examples/test_qwen_reranker.py
```

测试脚本会：
1. 初始化带有 Reranker 的 Graphiti
2. 添加测试数据
3. 执行语义搜索
4. 直接测试 Reranker 排序功能
5. 验证排序质量

## 错误处理

Reranker 会自动处理以下错误：

- **速率限制错误**：抛出 `RateLimitError`，可由调用方重试
- **网络错误**：向上传播，建议实现重试逻辑
- **解析错误**：给予默认分数 0.0，记录警告日志
- **空响应**：给予默认分数 0.0，记录警告日志

## 最佳实践

1. **合理设置段落数量**：建议每次重排序不超过 20 个段落，以控制成本和延迟
2. **使用合适的模型**：对于大多数场景，`qwen-turbo` 已经足够
3. **监控 API 配额**：设置 API 配额告警，避免超限
4. **实现降级策略**：当 Reranker 失败时，可以退回到基于向量相似度的排序
5. **缓存结果**：对于相同查询和段落组合，可以缓存重排序结果

## 相关资源

- [Graphiti 文档](https://github.com/getzep/graphiti)
- [通义千问 API 文档](https://help.aliyun.com/zh/dashscope/)
- [CrossEncoderClient 接口](https://github.com/getzep/graphiti/blob/main/graphiti_core/cross_encoder/client.py)

## 常见问题

### Q: Reranker 会增加多少延迟？

A: 由于并发处理，延迟约等于单次 LLM 调用（100-300ms），不会随段落数量线性增长。

### Q: 如何选择合适的模型？

A: 对于大多数场景，`qwen-turbo` 已经足够。如果需要更高准确性，可以尝试 `qwen-plus`。

### Q: Reranker 失败了怎么办？

A: Graphiti 会自动退回到基于向量相似度的排序。你也可以捕获 `RateLimitError` 并实现自定义降级逻辑。

### Q: 可以自定义评分提示词吗？

A: 可以。修改 `QwenRerankerClient.rank()` 方法中的提示词模板即可。

## 更新日志

### 2024-12-19

- ✅ 初始版本发布
- ✅ 实现基于 LLM 的评分机制
- ✅ 添加并发处理支持
- ✅ 集成到 GraphitiService
- ✅ 完成测试验证
