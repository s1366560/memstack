# MemStack API参考文档

## 基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **认证方式**: API Key (Bearer Token)
- **内容类型**: `application/json`
- **字符编码**: UTF-8

## 认证

所有API请求都需要在Header中包含API Key：

```http
Authorization: Bearer ms_sk_your_api_key_here
```

### 获取API Key

开发环境下，服务器启动时会自动生成默认API Key并打印到日志：

```
INFO:     Generated default API key: ms_sk_abc123...
INFO:     Default user created: developer@memstack.local
```

生产环境下，通过用户管理系统创建API Key。

### 认证错误

- **401 Unauthorized**: API Key无效或缺失
- **403 Forbidden**: API Key有效但权限不足

## API端点

### 1. 健康检查

#### GET /health

检查服务状态。

**请求**
```http
GET /health HTTP/1.1
Host: localhost:8000
```

**响应**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2024-12-19T10:00:00Z"
}
```

**状态码**
- `200 OK`: 服务正常
- `503 Service Unavailable`: 服务不可用

---

### 2. 根端点

#### GET /

获取API基本信息。

**请求**
```http
GET / HTTP/1.1
Host: localhost:8000
```

**响应**
```json
{
  "name": "MemStack API",
  "version": "0.1.0",
  "description": "Enterprise AI Memory Platform",
  "docs_url": "/docs"
}
```

---

### 3. 创建Episode

#### POST /api/v1/episodes/

将新的内容片段摄取到知识图谱中。

**认证**: 必需

**请求体**
```json
{
  "name": "用户对话记录",
  "content": "用户表示想要预订明天下午2点的会议室",
  "source_type": "text",
  "source_description": "Slack对话",
  "group_id": "user_12345",
  "metadata": {
    "channel": "support",
    "user_id": "12345"
  }
}
```

**字段说明**
- `name` (required, string): Episode名称
- `content` (required, string): Episode内容，将被用于提取实体和关系
- `source_type` (optional, string): 来源类型，默认"text"
  - 可选值: "text", "message", "document", "audio", "video"
- `source_description` (optional, string): 来源描述
- `group_id` (optional, string): 分组ID，用于多租户或用户隔离
- `metadata` (optional, object): 自定义元数据

**响应**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Episode queued for ingestion",
  "created_at": "2024-12-19T10:00:00Z"
}
```

**状态码**
- `202 Accepted`: Episode已接收，正在处理
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 认证失败
- `422 Unprocessable Entity`: 数据验证失败

**示例**

cURL:
```bash
curl -X POST http://localhost:8000/api/v1/episodes/ \
  -H "Authorization: Bearer ms_sk_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "用户咨询",
    "content": "用户询问产品价格和配送时间"
  }'
```

Python SDK:
```python
from memstack import MemStackClient

client = MemStackClient(api_key="ms_sk_...")
response = client.create_episode(
    name="用户咨询",
    content="用户询问产品价格和配送时间"
)
print(f"Episode ID: {response.id}")
```

---

### 4. 搜索记忆

#### POST /api/v1/memory/search

在知识图谱中搜索相关记忆。

**认证**: 必需

**请求体**
```json
{
  "query": "会议室预订",
  "limit": 10,
  "tenant_id": "tenant_123",
  "filters": {
    "entity_type": "Person",
    "date_from": "2024-12-01",
    "date_to": "2024-12-31"
  }
}
```

**字段说明**
- `query` (required, string): 搜索查询文本
- `limit` (optional, integer): 返回结果数量，默认10，最大100
- `tenant_id` (optional, string): 租户ID，用于隔离搜索结果
- `filters` (optional, object): 额外过滤条件
  - `entity_type`: 实体类型过滤
  - `date_from/date_to`: 时间范围过滤

**响应**
```json
{
  "results": [
    {
      "content": "用户想要预订明天下午2点的会议室",
      "score": 0.95,
      "metadata": {
        "episode_id": "550e8400-...",
        "entity_names": ["用户", "会议室"],
        "created_at": "2024-12-19T10:00:00Z"
      },
      "source": "episode"
    },
    {
      "content": "会议室A在3楼，容纳10人",
      "score": 0.87,
      "metadata": {
        "entity_id": "entity_123",
        "entity_type": "Location"
      },
      "source": "entity"
    }
  ],
  "total": 2,
  "query": "会议室预订"
}
```

**字段说明**
- `results`: 搜索结果数组
  - `content`: 记忆内容
  - `score`: 相关性分数 (0-1)
  - `metadata`: 元数据信息
  - `source`: 来源类型 (episode/entity/relation)
- `total`: 结果总数
- `query`: 原始查询

**状态码**
- `200 OK`: 搜索成功
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 认证失败
- `422 Unprocessable Entity`: 数据验证失败

**示例**

cURL:
```bash
curl -X POST http://localhost:8000/api/v1/memory/search \
  -H "Authorization: Bearer ms_sk_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "会议室预订",
    "limit": 5
  }'
```

Python SDK:
```python
client = MemStackClient(api_key="ms_sk_...")
results = client.search_memory(
    query="会议室预订",
    limit=5
)

for result in results.results:
    print(f"- {result.content} (score: {result.score})")
```

---

## 错误响应

所有错误响应遵循统一格式：

```json
{
  "detail": "错误描述信息",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-12-19T10:00:00Z"
}
```

### 常见错误码

| HTTP状态码 | 错误描述 | 解决方案 |
|-----------|---------|---------|
| 400 | Bad Request | 检查请求参数格式 |
| 401 | Unauthorized | 提供有效的API Key |
| 403 | Forbidden | 检查API Key权限 |
| 404 | Not Found | 检查URL路径 |
| 422 | Unprocessable Entity | 检查数据验证规则 |
| 429 | Too Many Requests | 降低请求频率 |
| 500 | Internal Server Error | 联系技术支持 |
| 503 | Service Unavailable | 稍后重试 |

---

## Rate Limiting (待实现)

当前版本暂未实施Rate Limiting。

未来版本计划：
- 每个API Key: 100 请求/分钟
- 突发流量: 200 请求/分钟
- 超出限制返回: `429 Too Many Requests`

Response Header将包含：
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1703001600
```

---

## Webhooks (待实现)

未来版本将支持Webhook通知：

### Episode处理完成
```json
{
  "event": "episode.completed",
  "data": {
    "episode_id": "550e8400-...",
    "entities_extracted": 5,
    "relationships_found": 8,
    "completed_at": "2024-12-19T10:05:00Z"
  }
}
```

---

## 最佳实践

### 1. 错误处理
```python
from memstack import MemStackClient
from memstack.exceptions import AuthenticationError, APIError

client = MemStackClient(api_key="ms_sk_...")

try:
    response = client.create_episode(name="Test", content="...")
except AuthenticationError:
    print("API Key无效")
except APIError as e:
    print(f"API错误: {e.message}")
```

### 2. 重试策略
SDK自动实现指数退避重试：
- 最大重试次数: 3
- 退避间隔: 1s, 2s, 4s
- 仅对5xx错误和网络错误重试

### 3. 超时设置
```python
client = MemStackClient(
    api_key="ms_sk_...",
    timeout=60  # 60秒超时
)
```

### 4. 批量处理
```python
episodes = [...]
for episode in episodes:
    try:
        response = client.create_episode(**episode)
        print(f"Created: {response.id}")
    except Exception as e:
        print(f"Failed: {e}")
        continue
```

### 5. 异步调用
```python
from memstack import MemStackAsyncClient
import asyncio

async def main():
    async with MemStackAsyncClient(api_key="ms_sk_...") as client:
        tasks = [
            client.create_episode(name=f"Episode {i}", content="...")
            for i in range(10)
        ]
        results = await asyncio.gather(*tasks)
        print(f"Created {len(results)} episodes")

asyncio.run(main())
```

---

## 变更日志

### v0.1.0 (2024-12-19)
- ✅ Episode创建API
- ✅ 记忆搜索API
- ✅ API Key认证
- ✅ 基本错误处理

### 未来版本
- [ ] Episode列表和详情查询
- [ ] API Key管理API
- [ ] Webhook支持
- [ ] Rate Limiting
- [ ] 批量操作API

---

## 技术支持

- **文档**: https://memstack.readthedocs.io
- **GitHub**: https://github.com/s1366560/memstack
- **Issues**: https://github.com/s1366560/memstack/issues

---

**更新时间**: 2024-12-19
**API版本**: v1
**文档版本**: 1.0
