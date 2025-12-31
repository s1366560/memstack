# Alembic 迁移系统 - 快速开始

## 🎉 好消息！

MemStack 现在使用 **Alembic** 进行数据库迁移管理。这是一个生产级的迁移系统，提供完整的版本控制和回滚支持。

## 最重要的变化

### 之前（旧系统）
```python
# 简单的迁移定义
MIGRATIONS = [
    {"table": "memories", "column": "task_id", "type": "VARCHAR"},
]
```

### 现在（Alembic）
```python
# 独立的迁移文件，包含升级和降级
revision = '002'
down_revision = '001'

def upgrade():
    op.add_column('memories', sa.Column('new_field', sa.String()))

def downgrade():
    op.drop_column('memories', 'new_field')
```

## 如何添加新迁移？

### 1. 修改模型
```python
# src/infrastructure/adapters/secondary/persistence/models.py
class Memory(Base):
    new_field: Mapped[Optional[str]] = mapped_column(String, nullable=True)
```

### 2. 创建迁移文件
```bash
# 在 alembic/versions/ 创建新文件
# 例如: 20250101_1200-002_add_new_field.py
```

```python
"""Add new_field to memories

Revision ID: 002
Revises: 001
Create Date: 2025-01-01

"""
from alembic import op
import sqlalchemy as sa

revision = '002'
down_revision = '001'

def upgrade() -> None:
    op.add_column('memories', sa.Column('new_field', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('memories', 'new_field')
```

### 3. 重启应用
```bash
make dev
# 迁移会自动应用！
```

## 查看迁移状态

```bash
# 查看当前状态
make db-status

# 查看迁移历史
make db-history

# 手动运行迁移
make db-migrate
```

## 应用启动日志

启动时会看到：
```
INFO: Applying database migrations with Alembic...
INFO: Current database version: 001
INFO: Latest migration version: 001
INFO: ✅ Database is already at latest version
INFO: Database migrations completed
```

## 为什么更好？

| 特性 | 旧系统 | Alembic |
|------|--------|---------|
| 版本控制 | ❌ | ✅ |
| 回滚支持 | ❌ | ✅ |
| 迁移历史 | ❌ | ✅ |
| 生产验证 | ❌ | ✅ |
| 社区支持 | 内部 | 庞大 |

## 完整文档

- **用户指南**: `docs/alembic_usage_guide.md`
- **完成总结**: `docs/alembic_migration_complete.md`
- **实施计划**: `docs/alembic_implementation_plan.md`

## 快速参考

```bash
# 查看状态
make db-status

# 运行迁移
make db-migrate

# 查看历史
make db-history

# 添加新迁移:
# 1. 修改 models.py
# 2. 创建 alembic/versions/XXX_new_migration.py
# 3. 重启应用
```

## 需要帮助？

查看详细文档：`docs/alembic_usage_guide.md`

---

**就这些！** 🚀

系统会自动处理迁移，你只需要：
1. 修改模型
2. 创建迁移文件
3. 重启应用
