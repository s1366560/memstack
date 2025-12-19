# VIP Memory 快速启动指南

欢迎使用 VIP Memory！这份指南将帮助您在 5 分钟内启动并运行应用。

## 📋 启动前准备

### 1. 检查系统要求

```bash
# Python 版本（需要 3.12+）
python --version

# 或使用虚拟环境中的 Python
.venv/bin/python --version
```

### 2. 启动依赖服务

VIP Memory 需要 Neo4j 数据库：

```bash
# 使用 Docker Compose 启动 Neo4j
docker-compose up -d neo4j

# 检查服务状态
docker-compose ps neo4j

# 访问 Neo4j Web UI 验证
# http://localhost:7474
# 用户名: neo4j
# 密码: 参见 .env 文件中的 NEO4J_PASSWORD
```

### 3. 运行配置检查

```bash
# 运行自动配置检查
.venv/bin/python scripts/check_config.py
```

预期输出：
```
🎉 所有检查通过！应用可以启动。
```

## 🚀 启动应用

### 方式 1：直接运行（推荐）

```bash
.venv/bin/python -m server.main
```

### 方式 2：使用 Uvicorn

```bash
.venv/bin/uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

### 方式 3：VSCode 调试

1. 在 VSCode 中打开项目
2. 按 `F5` 键
3. 选择 "Python: FastAPI Server"
4. 应用将在调试模式下启动

## ✅ 验证启动

启动成功后，您应该看到类似的日志输出：

```json
{"time":"2025-12-19 11:30:00","level":"INFO","name":"server.main","message":"Starting VIP Memory application..."}
{"time":"2025-12-19 11:30:01","level":"INFO","name":"server.services.graphiti_service","message":"Graphiti client initialized successfully"}
{"time":"2025-12-19 11:30:01","level":"INFO","name":"server.main","message":"Graphiti service initialized"}
{"time":"2025-12-19 11:30:01","level":"INFO","name":"uvicorn.error","message":"Application startup complete."}
{"time":"2025-12-19 11:30:01","level":"INFO","name":"uvicorn.error","message":"Uvicorn running on http://0.0.0.0:8000"}
```

### 访问 API

打开浏览器访问以下地址：

1. **API 文档（交互式）**
   - URL: http://localhost:8000/docs
   - 可以直接在浏览器中测试 API

2. **健康检查**
   - URL: http://localhost:8000/health
   - 预期响应：
     ```json
     {
       "status": "healthy",
       "service": "vip-memory"
     }
     ```

3. **根端点**
   - URL: http://localhost:8000/
   - 预期响应：
     ```json
     {
       "name": "VIP Memory API",
       "version": "0.1.0",
       "description": "Enterprise-grade AI Memory Cloud Platform",
       "docs": "/docs"
     }
     ```

## 🧪 测试 API

### 1. 创建一个 Episode

使用 curl：

```bash
curl -X POST "http://localhost:8000/api/v1/episodes/" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "用户 John 喜欢深色模式界面",
    "source_type": "text",
    "tenant_id": "test-tenant"
  }'
```

或在 API 文档页面 (http://localhost:8000/docs) 中直接测试。

预期响应：

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Episode queued for ingestion",
  "created_at": "2025-12-19T11:30:00.000000"
}
```

### 2. 搜索记忆

```bash
curl -X POST "http://localhost:8000/api/v1/memory/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "用户偏好",
    "limit": 10,
    "tenant_id": "test-tenant"
  }'
```

## 🔧 遇到问题？

### 问题 1：导入错误

**错误**：`module 'server.services.graphiti_service' has no attribute 'initialize'`

**✅ 已修复**：这个问题已在最新版本中修复。如果仍然遇到，请：

```bash
# 拉取最新代码
git pull

# 重新检查配置
.venv/bin/python scripts/check_config.py
```

### 问题 2：Neo4j 连接失败

**错误**：`Failed to initialize Graphiti client: Could not connect to Neo4j`

**解决方案**：

```bash
# 1. 确认 Neo4j 正在运行
docker-compose ps neo4j

# 2. 如果没有运行，启动它
docker-compose up -d neo4j

# 3. 查看日志
docker-compose logs -f neo4j

# 4. 检查 .env 配置
cat .env | grep NEO4J
```

### 问题 3：端口被占用

**错误**：`Error: [Errno 48] Address already in use`

**解决方案**：

```bash
# 查找占用端口的进程
lsof -ti:8000

# 停止该进程
kill -9 $(lsof -ti:8000)

# 或更改端口（编辑 .env 文件）
# API_PORT=8001
```

### 更多帮助

查看详细的故障排查指南：

- **[启动故障排查](docs/startup-troubleshooting.md)** - 完整的问题诊断手册
- **[修复说明](docs/FIX-STARTUP-ISSUE.md)** - 最近修复的问题详情
- **[调试指南](docs/debugging.md)** - VSCode 调试配置

## 📚 下一步

恭喜！您的 VIP Memory 已经成功运行。接下来可以：

### 1. 查看示例代码

```bash
# 运行基础使用示例
.venv/bin/python examples/basic_usage.py
```

### 2. 阅读文档

- [API 文档](docs/api.md) - 详细的 API 参考
- [设计文档](.qoder/quests/cloud-product-creation.md) - 完整的产品设计
- [实施报告](IMPLEMENTATION_REPORT.md) - 项目当前状态

### 3. 探索功能

在 API 文档页面 (http://localhost:8000/docs) 中尝试：

- 创建不同类型的 Episodes
- 搜索和检索记忆
- 查看健康检查状态

### 4. 开发集成

查看 Python SDK 使用示例：

```python
from server.services.graphiti_service import graphiti_service

# 初始化服务
await graphiti_service.initialize()

# 添加记忆
episode = await graphiti_service.add_episode(
    episode_data={
        "content": "用户偏好设置",
        "source_type": "text"
    }
)

# 搜索记忆
results = await graphiti_service.search(
    query="用户偏好",
    limit=10
)
```

## 🛑 停止应用

### 停止 API 服务

在运行应用的终端中按 `Ctrl+C`

### 停止所有服务

```bash
# 停止所有 Docker 服务
docker-compose down

# 或只停止特定服务
docker-compose stop neo4j
```

## 💡 小贴士

1. **开发模式**：使用 `--reload` 选项自动重载代码变更
   ```bash
   uvicorn server.main:app --reload
   ```

2. **调试模式**：设置环境变量启用详细日志
   ```bash
   export LOG_LEVEL=DEBUG
   python -m server.main
   ```

3. **性能监控**：访问 Neo4j Web UI 查看图谱统计
   - http://localhost:7474

4. **测试 API**：使用 API 文档的 "Try it out" 功能
   - http://localhost:8000/docs

## 🎯 常用命令速查

```bash
# 配置检查
.venv/bin/python scripts/check_config.py

# 启动测试
.venv/bin/python scripts/test_startup.py

# 启动应用
.venv/bin/python -m server.main

# 启动 Neo4j
docker-compose up -d neo4j

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 🆘 获取帮助

遇到问题？

1. 查看 [启动故障排查指南](docs/startup-troubleshooting.md)
2. 运行配置检查：`python scripts/check_config.py`
3. 查看应用日志
4. 检查 Neo4j 状态

---

**祝您使用愉快！** 🚀
