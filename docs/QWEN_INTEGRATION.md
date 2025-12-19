# Qwen (通义千问) 集成指南

VIP Memory 现已支持阿里云通义千问 (Qwen) 作为 LLM 提供商，可以在 Google Gemini 和 Qwen 之间灵活切换。

## 功能特性

- ✅ **LLM 支持**: 使用 Qwen 大模型 (`qwen-plus`) 和小模型 (`qwen-turbo`)
- ✅ **Embedding 支持**: 使用 `text-embedding-v3` 模型生成向量嵌入
- ✅ **结构化输出**: 支持 JSON mode 的结构化响应
- ✅ **批处理**: Embedder 支持批量向量生成 (batch_size=16)
- ✅ **OpenAI 兼容**: 使用 OpenAI 兼容的 API 接口
- ✅ **动态切换**: 通过环境变量轻松切换 LLM 提供商

## 快速开始

### 1. 获取 Qwen API Key

访问 [阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/) 获取 API Key。

### 2. 配置环境变量

在 `.env` 文件中配置 Qwen 相关参数：

```bash
# LLM Provider Selection
LLM_PROVIDER=qwen

# Qwen (通义千问) 配置
DASHSCOPE_API_KEY=sk-your-qwen-api-key-here
QWEN_MODEL=qwen-plus
QWEN_SMALL_MODEL=qwen-turbo
QWEN_EMBEDDING_MODEL=text-embedding-v3
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 3. 运行测试

```bash
# 运行 Qwen 集成测试
python examples/test_qwen_integration.py
```

## 配置说明

### LLM 提供商选择

通过 `LLM_PROVIDER` 环境变量切换提供商：

- `gemini`: 使用 Google Gemini (默认)
- `qwen`: 使用阿里云通义千问

### Qwen 配置参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `DASHSCOPE_API_KEY` | Qwen API 密钥（阿里云百炼 DashScope API Key） | 必填 |
| `QWEN_MODEL` | 大模型名称 | `qwen-plus` |
| `QWEN_SMALL_MODEL` | 小模型名称 | `qwen-turbo` |
| `QWEN_EMBEDDING_MODEL` | Embedding 模型 | `text-embedding-v3` |
| `QWEN_BASE_URL` | API 基础 URL | `https://dashscope.aliyuncs.com/compatible-mode/v1` |

### 可用模型

#### LLM 模型
- `qwen-plus`: 通义千问增强版，适合复杂任务
- `qwen-turbo`: 通义千问高速版，适合简单任务
- `qwen-max`: 通义千问旗舰版，性能最强（需要额外权限）

#### Embedding 模型
- `text-embedding-v3`: 通义千问 Embedding 模型，支持多语言
- `text-embedding-v2`: 旧版 Embedding 模型

## 架构设计

### 客户端实现

```
server/llm_clients/
├── __init__.py              # 模块导出
├── qwen_client.py           # Qwen LLM 客户端
└── qwen_embedder.py         # Qwen Embedder 客户端
```

### QwenClient

继承自 `graphiti_core.llm_client.LLMClient`，实现：

- 使用 `AsyncOpenAI` 客户端访问 Qwen 兼容接口
- 支持结构化输出 (JSON mode)
- 支持动态模型选择 (small/medium)
- 错误处理和速率限制检测

### QwenEmbedder

继承自 `graphiti_core.embedder.EmbedderClient`，实现：

- 单个文本向量生成 (`create()`)
- 批量向量生成 (`create_batch()`)
- 批处理失败时自动回退到逐个处理
- 向量维度截断支持

### GraphitiService 集成

`server/services/graphiti_service.py` 中的 `initialize()` 方法支持动态选择提供商：

```python
async def initialize(self, provider: str = 'gemini'):
    """
    初始化 Graphiti 客户端
    
    Args:
        provider: LLM 提供商，可选 'gemini' 或 'qwen'
    """
    if provider.lower() == 'qwen':
        # 创建 Qwen 客户端
        llm_client = QwenClient(config=llm_config)
        embedder = QwenEmbedder(config=embedder_config)
    else:
        # 创建 Gemini 客户端（默认）
        llm_client = GeminiClient(config=llm_config)
        embedder = GeminiEmbedder(config=embedder_config)
    
    # 初始化 Graphiti
    self._client = Graphiti(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
        llm_client=llm_client,
        embedder=embedder,
    )
```

## 使用示例

### 创建 Episode

```python
from server.services.graphiti_service import GraphitiService
from server.models.episode import EpisodeCreate

# 初始化服务（使用 Qwen）
service = GraphitiService()
await service.initialize(provider='qwen')

# 创建 Episode
episode = EpisodeCreate(
    content="我叫张三，是一名软件工程师，专注于 AI 和机器学习。",
    source_type="conversation",
    metadata={"user_id": "user123"}
)

result = await service.add_episode(episode)
print(f"Episode ID: {result.id}")
```

### 语义搜索

```python
# 搜索相关记忆
results = await service.search(
    query="张三的职业是什么？",
    limit=5
)

for result in results:
    print(f"[{result.source}] {result.content} (score: {result.score})")
```

### 切换提供商

只需修改 `.env` 文件中的 `LLM_PROVIDER`：

```bash
# 使用 Gemini
LLM_PROVIDER=gemini

# 或使用 Qwen
LLM_PROVIDER=qwen
```

重启服务后生效。

## API 兼容性

Qwen 实现完全兼容 Graphiti 的 LLM 客户端接口：

- ✅ `_generate_response()`: 生成 LLM 响应
- ✅ `_get_provider_type()`: 返回提供商类型
- ✅ 结构化输出支持
- ✅ 速率限制错误处理
- ✅ 消息格式转换

## 性能对比

| 特性 | Gemini | Qwen |
|------|--------|------|
| 中文支持 | 良好 | 优秀 |
| 英文支持 | 优秀 | 良好 |
| 速度 | 快 | 快 |
| 成本 | 低 | 低 |
| 免费额度 | 有 | 有 |
| 速率限制 | 严格 | 中等 |

## 故障排除

### 1. API Key 错误

```
Error: Authentication failed
```

**解决方法**: 检查 `DASHSCOPE_API_KEY` 是否正确设置。

### 2. 模型不存在

```
Error: Model not found
```

**解决方法**: 确认使用的模型在您的账户中可用，某些模型需要额外申请权限。

### 3. 速率限制

```
Error: Rate limit exceeded
```

**解决方法**: 
- 减少并发请求
- 增加 Episode 之间的延迟
- 升级到付费 API

### 4. 向量维度不匹配

如果遇到向量维度问题，可以在 `QwenEmbedderConfig` 中设置 `embedding_dim`：

```python
embedder_config = QwenEmbedderConfig(
    api_key=settings.qwen_api_key,
    embedding_model=settings.qwen_embedding_model,
    embedding_dim=1536  # 截断到指定维度
)
```

## 最佳实践

1. **开发环境**: 使用 `qwen-turbo` 小模型节省成本
2. **生产环境**: 使用 `qwen-plus` 或 `qwen-max` 获得更好性能
3. **批处理**: 利用 Embedder 的批处理功能提高效率
4. **错误处理**: 实现重试机制应对临时性错误
5. **监控**: 跟踪 API 使用量和速率限制

## 参考资料

- [阿里云 DashScope 文档](https://help.aliyun.com/zh/dashscope/)
- [Qwen API 参考](https://help.aliyun.com/zh/dashscope/developer-reference/api-details)
- [OpenAI 兼容接口说明](https://help.aliyun.com/zh/dashscope/developer-reference/compatibility-of-openai-with-dashscope/)
- [Graphiti 文档](https://github.com/getzep/graphiti)

## 贡献

如果您在使用过程中遇到问题或有改进建议，欢迎提交 Issue 或 Pull Request。
