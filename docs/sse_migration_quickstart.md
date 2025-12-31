# Quick Start: SSE & Migration System

## 快速验证

### 1. 检查迁移状态
```bash
cd /Users/tiejunsun/github/mem/memstack
PYTHONPATH=. uv run python scripts/manage_migrations.py status
```

预期输出：
```
================================================================================
DATABASE MIGRATION STATUS
================================================================================

Total migrations defined: 4
Applied migrations: 4
Pending migrations: 0

✅ Applied migrations:
   ✓ memories.task_id
   ✓ task_logs.progress
   ✓ task_logs.result
   ✓ task_logs.message

================================================================================
```

### 2. 启动应用
```bash
# 后端会自动运行迁移
uv run python -m src.infrastructure.adapters.primary.web.main
```

查看日志中的迁移信息：
```
INFO: Applying database migrations...
INFO: Ensuring all tables exist...
INFO: ✅ Tables verified
INFO: Applying incremental migrations...
INFO: ✅ Migrations applied
```

### 3. 测试 SSE 功能
1. 打开浏览器: http://localhost:3000/project/{project_id}/memories
2. 点击 "New Memory"
3. 输入标题和内容
4. 点击 "Save Memory"
5. 观察实时进度更新

## 常用命令

```bash
# 查看迁移状态
python scripts/manage_migrations.py status

# 手动应用迁移
python scripts/manage_migrations.py apply

# 检查 schema 兼容性
python scripts/manage_migrations.py check

# 创建所有表（仅用于新部署）
python scripts/manage_migrations.py create
```

## 添加新迁移

1. 更新模型 (`models.py`):
```python
class Memory(Base):
    new_field: Mapped[Optional[str]] = mapped_column(String, nullable=True)
```

2. 注册迁移 (`migrations.py`):
```python
MIGRATIONS = [
    # ... existing ...
    {
        "table": "memories",
        "column": "new_field",
        "type": "VARCHAR",
        "nullable": True,
        "description": "New field for feature X"
    },
]
```

3. 测试:
```bash
python scripts/manage_migrations.py status
python scripts/manage_migrations.py apply
```

4. 部署（自动运行）:
重启应用，迁移会自动应用

## 故障排除

### 问题: 迁移失败
```bash
# 查看详细状态
python scripts/manage_migrations.py status

# 手动应用
python scripts/manage_migrations.py apply

# 检查兼容性
python scripts/manage_migrations.py check
```

### 问题: SSE 不工作
1. 检查浏览器控制台是否有错误
2. 验证 task_id 是否返回
3. 确认 SSE 端点可访问: `/api/v1/tasks/{task_id}/stream`

## 相关文档

- 完整文档: `docs/sse_and_migrations_summary.md`
- SSE 实现: `docs/sse_episode_implementation.md`
- 迁移系统: `docs/database_migrations.md`
- SSE 测试: `docs/sse_testing_guide.md`
