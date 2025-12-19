# 应用启动问题排查指南

本文档帮助您诊断和解决 VIP Memory 应用的启动问题。

## 🔧 已修复的问题

### 问题：`module 'server.services.graphiti_service' has no attribute 'initialize'`

**原因**：`main.py` 导入了 `graphiti_service` 模块而不是服务实例。

**解决方案**：已修复导入语句，现在正确导入服务实例：
```python
# 修复前
from server.services import graphiti_service

# 修复后
from server.services.graphiti_service import graphiti_service
```

## 📋 启动前检查清单

### 1. 环境配置检查

```bash
# 检查 .env 文件是否存在
ls -la .env

# 如果不存在，从示例文件创建
cp .env.example .env
```

**关键环境变量**：
- `NEO4J_URI`: Neo4j 数据库连接地址（默认：bolt://localhost:7687）
- `NEO4J_USER`: Neo4j 用户名（默认：neo4j）
- `NEO4J_PASSWORD`: Neo4j 密码（需要设置）
- `OPENAI_API_KEY`: OpenAI API 密钥（用于实体提取）

### 2. 依赖服务检查

VIP Memory 依赖以下服务，启动前请确保它们正在运行：

#### Neo4j 数据库

```bash
# 使用 Docker Compose 启动
docker-compose up -d neo4j

# 检查 Neo4j 是否运行
docker-compose ps neo4j

# 查看 Neo4j 日志
docker-compose logs -f neo4j

# 测试 Neo4j 连接
curl http://localhost:7474
```

**Neo4j 访问**：
- Web UI: http://localhost:7474
- Bolt 协议: bolt://localhost:7687

#### Redis 缓存（可选）

```bash
# 启动 Redis
docker-compose up -d redis

# 检查 Redis 状态
docker-compose exec redis redis-cli ping
```

### 3. Python 环境检查

```bash
# 检查 Python 版本（需要 3.12+）
python --version

# 检查虚拟环境
which python

# 同步依赖
uv sync --python 3.12

# 验证关键包
python -c "import graphiti_core; print('Graphiti 已安装')"
python -c "import fastapi; print('FastAPI 已安装')"
```

## 🚀 启动应用的方式

### 方式 1：直接运行（开发模式）

```bash
# 确保在项目根目录
cd /Users/tiejun.sun/Documents/github/vip-memory

# 运行应用
python -m server.main
```

### 方式 2：使用 Uvicorn

```bash
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

### 方式 3：使用 Docker Compose

```bash
# 构建并启动所有服务
docker-compose up --build

# 后台运行
docker-compose up -d

# 查看日志
docker-compose logs -f api
```

### 方式 4：VSCode 调试

1. 在 VSCode 中打开项目
2. 按 `F5` 或点击调试面板的"启动调试"
3. 选择 "Python: FastAPI Server" 配置
4. 应用将在调试模式下启动

## 🧪 测试启动流程

我们提供了一个测试脚本来验证服务初始化：

```bash
# 运行启动测试
python scripts/test_startup.py
```

测试内容：
- ✓ Graphiti 服务初始化
- ✓ 健康检查
- ✓ 服务关闭

## 🔍 常见启动错误及解决方案

### 错误 1：Neo4j 连接失败

```
Failed to initialize Graphiti client: Could not connect to Neo4j
```

**解决方案**：
1. 检查 Neo4j 是否运行：`docker-compose ps neo4j`
2. 检查连接配置：`.env` 中的 `NEO4J_URI`、`NEO4J_USER`、`NEO4J_PASSWORD`
3. 测试连接：访问 http://localhost:7474
4. 重启 Neo4j：`docker-compose restart neo4j`

### 错误 1.1：Graphiti 初始化参数错误

```
TypeError: Graphiti.__init__() got an unexpected keyword argument 'neo4j_uri'
```

**原因**：Graphiti 的正确参数名是 `uri`、`user`、`password`，而不是 `neo4j_uri`、`neo4j_user`、`neo4j_password`。

**解决方案**：
已在最新版本中修复。如果仍然遇到，请：
```bash
# 拉取最新代码
git pull

# 检查 server/services/graphiti_service.py 中的初始化代码
# 应该是：
Graphiti(
    uri=settings.neo4j_uri,
    user=settings.neo4j_user,
    password=settings.neo4j_password,
)
```

### 错误 2：端口已被占用

```
Error: [Errno 48] Address already in use
```

**解决方案**：
1. 查找占用端口的进程：
   ```bash
   lsof -ti:8000
   ```
2. 停止该进程或更改端口：
   ```bash
   # 停止进程
   kill -9 $(lsof -ti:8000)
   
   # 或更改端口（在 .env 中设置 API_PORT=8001）
   ```

### 错误 3：缺少环境变量

```
KeyError: 'OPENAI_API_KEY'
```

**解决方案**：
1. 检查 `.env` 文件是否存在
2. 确保 `.env` 中设置了所有必需的环境变量
3. 重新加载环境：
   ```bash
   source .env  # 仅在 shell 中有效
   # 或重启应用
   ```

### 错误 4：模块导入错误

```
ModuleNotFoundError: No module named 'graphiti_core'
```

**解决方案**：
1. 确认虚拟环境已激活
2. 重新安装依赖：
   ```bash
   uv sync --python 3.12
   ```
3. 验证安装：
   ```bash
   python -c "import graphiti_core"
   ```

### 错误 5：数据库未初始化

```
Neo4j.ClientError.Schema.ConstraintValidationFailed
```

**解决方案**：
1. 首次使用需要初始化数据库架构
2. Graphiti 会自动创建索引和约束
3. 如果问题持续，清空数据库：
   ```bash
   # 进入 Neo4j
   docker-compose exec neo4j cypher-shell -u neo4j -p your_password
   
   # 清空所有数据（警告：会删除所有数据！）
   MATCH (n) DETACH DELETE n;
   ```

## 📊 启动日志解读

### 正常启动日志

```json
{"time":"2025-12-19 11:15:38","level":"INFO","name":"server.main","message":"Starting VIP Memory application..."}
{"time":"2025-12-19 11:15:39","level":"INFO","name":"server.services.graphiti_service","message":"Graphiti client initialized successfully"}
{"time":"2025-12-19 11:15:39","level":"INFO","name":"server.main","message":"Graphiti service initialized"}
{"time":"2025-12-19 11:15:39","level":"INFO","name":"uvicorn.error","message":"Application startup complete."}
{"time":"2025-12-19 11:15:39","level":"INFO","name":"uvicorn.error","message":"Uvicorn running on http://0.0.0.0:8000"}
```

### 异常启动日志

```json
{"time":"2025-12-19 11:15:38","level":"INFO","name":"server.main","message":"Starting VIP Memory application..."}
{"time":"2025-12-19 11:15:38","level":"ERROR","name":"server.main","message":"Failed to initialize services: ..."}
{"time":"2025-12-19 11:15:38","level":"ERROR","name":"uvicorn.error","message":"Application startup failed. Exiting."}
```

## 🛠️ 调试技巧

### 1. 启用详细日志

在 `.env` 中设置：
```bash
LOG_LEVEL=DEBUG
```

这将输出更详细的日志，包括：
- 函数调用时间
- 参数值
- SQL 查询
- 网络请求

### 2. 使用调试器

在 VSCode 中：
1. 在 `server/main.py` 的 `lifespan` 函数中设置断点
2. 按 `F5` 启动调试
3. 逐步执行代码，查看变量值

### 3. 使用调试装饰器

在需要调试的函数上添加装饰器：

```python
from server.debug_utils import debug_timer, debug_log_args

@debug_timer
@debug_log_args
async def my_function(arg1, arg2):
    # 函数逻辑
    pass
```

### 4. 手动测试服务

```python
# 在 Python REPL 中测试
import asyncio
from server.services.graphiti_service import graphiti_service

async def test():
    await graphiti_service.initialize()
    print("初始化成功！")
    await graphiti_service.close()

asyncio.run(test())
```

## 📞 获取帮助

如果问题仍然存在：

1. **检查日志**：`docker-compose logs -f`
2. **查看完整错误**：包括堆栈跟踪
3. **记录环境信息**：
   ```bash
   python --version
   uv --version
   docker --version
   docker-compose --version
   ```
4. **提供复现步骤**

## ✅ 验证启动成功

启动成功后，访问以下端点验证：

1. **API 文档**：http://localhost:8000/docs
2. **健康检查**：http://localhost:8000/health
3. **根端点**：http://localhost:8000/

预期响应：
```json
{
  "name": "VIP Memory API",
  "version": "0.1.0",
  "description": "Enterprise-grade AI Memory Cloud Platform",
  "docs": "/docs"
}
```

## 🎯 下一步

启动成功后，您可以：

1. 查看 API 文档：http://localhost:8000/docs
2. 阅读快速入门：[docs/quickstart.md](../docs/quickstart.md)
3. 运行示例代码：[examples/basic_usage.py](../examples/basic_usage.py)
4. 查看调试指南：[docs/debugging.md](../docs/debugging.md)
