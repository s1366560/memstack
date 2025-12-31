# 开发命令快速参考

## 🚀 启动开发环境

### 完整启动（推荐）
```bash
make dev
```
这将自动：
1. 启动基础设施服务（Neo4j, PostgreSQL, Redis）
2. 创建数据库（如果不存在）
3. 启动 API 服务器（后台运行，日志：`logs/api.log`）
4. 启动 Worker 服务（后台运行，日志：`logs/worker.log`）

### 管理后台服务
```bash
# 查看所有日志
make dev-logs

# 或单独查看
tail -f logs/api.log      # API 日志
tail -f logs/worker.log   # Worker 日志

# 停止所有后台服务
make dev-stop
```

### 单独启动服务
```bash
make dev-infra      # 仅基础设施
make dev-backend    # 仅 API（前台运行）
make dev-worker     # 仅 Worker（前台运行）
make dev-web        # 前端开发服务器
```

## 📋 日志管理

所有日志文件存储在 `logs/` 目录：
- `logs/api.log` - API 服务器日志
- `logs/worker.log` - Worker 日志
- `logs/api.pid` - API 进程 ID
- `logs/worker.pid` - Worker 进程 ID

查看实时日志：
```bash
tail -f logs/api.log
tail -f logs/worker.log
```

## 🛑 停止服务

```bash
# 停止后台服务（API + Worker）
make dev-stop

# 清理日志文件
make clean-logs

# 停止 Docker 服务
make docker-down
```

## 🗄️ 数据库管理

```bash
make db-init      # 初始化数据库（自动创建）
make db-reset     # 重置数据库（删除所有数据）
make db-shell     # 打开 PostgreSQL shell
```

**注意**：
- 数据库会在 `make dev` 时自动初始化
- 表结构会在首次启动时自动创建（SQLAlchemy auto-create）
- 无需手动运行迁移

## 🧪 测试

```bash
make test           # 所有测试
make test-unit      # 单元测试
make test-e2e       # E2E 测试
```

## 🔧 其他常用命令

```bash
make help           # 显示所有可用命令
make clean          # 清理所有生成文件
make format         # 格式化代码
make lint           # 代码检查
make shell          # Python shell
make get-api-key    # 获取 API 密钥信息
```

## ⚠️ 注意事项

1. **数据库自动初始化**：
   - 首次运行 `make dev` 会自动创建 `vip_memory` 数据库
   - 表结构会在 API 启动时自动创建
   - 如需重置数据库：`make db-reset`

2. **Worker 服务的重要性**：
   - Worker 负责处理异步任务（如 PDF 处理、Graphiti 索引等）
   - 如果 Worker 未运行，这些任务将无法完成
   - 使用 `make dev` 会自动启动 Worker

3. **日志监控**：
   - 启动服务后，使用 `make dev-logs` 监控日志
   - 或者使用 `tail -f logs/api.log` 查看特定服务日志

4. **端口占用**：
   - API: http://localhost:8000
   - Web: http://localhost:3000
   - Neo4j: http://localhost:7474
   - PostgreSQL: localhost:5432
   - Redis: localhost:6379

5. **故障排除**：
   - 如果服务无法启动，先检查 `make dev-infra`
   - 查看日志文件了解详细错误信息
   - 使用 `make clean-logs` 清理旧日志
   - 如果数据库错误：`make db-reset`
