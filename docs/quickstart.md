# MemStack 快速入门指南

本指南将帮助您快速启动和使用 MemStack 平台。

## 前置要求

- Python 3.10 或更高版本
- Docker 和 Docker Compose（推荐）
- OpenAI API 密钥

## 方式一：使用 Docker Compose（推荐）

### 1. 克隆仓库

```bash
git clone https://github.com/s1366560/memstack.git
cd memstack
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置您的 OpenAI API 密钥和其他配置：

```bash
OPENAI_API_KEY=sk-your-key-here
SECRET_KEY=your-secret-key-here
```

### 3. 启动服务

```bash
docker-compose up -d
```

这将启动以下服务：
- Neo4j（端口 7474, 7687）
- PostgreSQL（端口 5432）
- Redis（端口 6379）
- MemStack API（端口 8000）

### 4. 验证服务

访问 http://localhost:8000/docs 查看 API 文档。

## 方式二：本地开发

### 1. 安装依赖

```bash
# 使用 pip
pip install -e .

# 或使用 uv（推荐）
uv sync
```

### 2. 启动 Neo4j（使用 Docker）

```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5.26-community
```

### 3. 配置环境变量

```bash
export OPENAI_API_KEY=sk-your-key-here
export SECRET_KEY=your-secret-key-here
export NEO4J_PASSWORD=password
```

### 4. 启动 API 服务

```bash
python -m server.main
```

## 使用示例

### 1. 创建 Episode

```python
import httpx

# 创建 episode
response = httpx.post(
    "http://localhost:8000/api/v1/episodes/",
    json={
        "content": "John prefers dark mode in the application.",
        "source_type": "text",
        "metadata": {
            "user_id": "user_123"
        }
    }
)

print(response.json())
# 输出: {"id": "...", "status": "processing", ...}
```

### 2. 搜索记忆

```python
import httpx

# 搜索相关记忆
response = httpx.post(
    "http://localhost:8000/api/v1/memory/search",
    json={
        "query": "What does John prefer?",
        "limit": 10
    }
)

print(response.json())
# 输出: {"results": [...], "total": 1, "query": "..."}
```

### 3. 使用 Python SDK

```python
from memstack import MemStackClient

# 初始化客户端
client = MemStackClient(
    api_key="your-api-key",
    base_url="http://localhost:8000"
)

# 添加 episode
episode = client.create_episode(
    name="Test Episode",
    content="Alice is a software engineer at TechCorp.",
    metadata={"department": "Engineering"}
)

# 搜索记忆
results = client.search_memory("Who is Alice?")
for result in results.results:
    print(f"Content: {result.content}")
    print(f"Score: {result.score}")
```

## 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_models.py

# 运行并查看覆盖率
pytest --cov=server tests/
```

## API 端点

### Episode 端点

- `POST /api/v1/episodes/` - 创建新 episode
- `GET /api/v1/episodes/health` - 健康检查

### Memory 端点

- `POST /api/v1/memory/search` - 搜索记忆

### 系统端点

- `GET /` - API 信息
- `GET /health` - 系统健康检查
- `GET /docs` - Swagger UI 文档
- `GET /redoc` - ReDoc 文档

## 下一步

- 查看 [API 文档](api-reference.md)
- 了解 [架构设计](../README.md#架构设计)

## 故障排除

### Neo4j 连接失败

确保 Neo4j 已启动并且凭据正确：

```bash
docker logs memstack-neo4j
```

### OpenAI API 错误

检查您的 API 密钥是否正确设置：

```bash
echo $OPENAI_API_KEY
```

### 端口占用

如果端口被占用，修改 `docker-compose.yml` 中的端口映射。

## 获取帮助

- GitHub Issues: https://github.com/s1366560/memstack/issues
- 文档: https://github.com/s1366560/memstack/docs
