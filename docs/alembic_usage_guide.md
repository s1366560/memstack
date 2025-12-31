# Alembic Migration System - User Guide

## 概述

MemStack 现在使用 Alembic 进行数据库迁移管理。这是一个生产级的迁移系统，提供版本控制、回滚支持和自动迁移功能。

## 快速开始

### 1. 检查迁移状态

```bash
# 方法 1: 通过应用启动日志（推荐）
# 启动应用，查看日志中的迁移信息
uv run python -m src.infrastructure.adapters.primary.web.main

# 日志会显示:
# INFO: Applying database migrations with Alembic...
# INFO: Current database version: 001
# INFO: Latest migration version: 001
# INFO: ✅ Database is already at latest version
```

### 2. 应用自动运行

应用启动时会自动运行迁移：

```python
# main.py 中的 lifespan 函数
async def lifespan(app: FastAPI):
    logger.info("Applying database migrations with Alembic...")
    await run_alembic_migrations()
    logger.info("Database migrations completed")
```

### 3. 手动运行迁移（高级）

```bash
# 使用 Python 直接运行
PYTHONPATH=. uv run python -c "
from src.infrastructure.adapters.secondary.persistence.alembic_migrations import run_alembic_migrations
import asyncio
asyncio.run(run_alembic_migrations())
"
```

## 开发工作流

### 添加新字段到现有表

**步骤 1: 修改模型**

```python
# src/infrastructure/adapters/secondary/persistence/models.py

class Memory(Base):
    __tablename__ = "memories"

    # ... 现有字段 ...

    # 新字段
    new_field: Mapped[Optional[str]] = mapped_column(String, nullable=True)
```

**步骤 2: 创建迁移**

```bash
# 创建新的迁移文件
# 这会在 alembic/versions/ 目录创建新文件

# 方法 1: 手动创建（推荐，更可控）
# 创建文件: alembic/versions/20250101_1200-002_add_new_field.py
```

```python
"""Add new_field to memories table

Revision ID: 002
Revises: 001
Create Date: 2025-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add new_field column."""
    op.add_column('memories',
        sa.Column('new_field', sa.String(), nullable=True)
    )


def downgrade() -> None:
    """Remove new_field column."""
    op.drop_column('memories', 'new_field')
```

**步骤 3: 应用迁移**

```bash
# 重启应用，迁移会自动应用
uv run python -m src.infrastructure.adapters.primary.web.main
```

### 创建新表

**步骤 1: 定义模型**

```python
# models.py

class NewTable(Base):
    __tablename__ = "new_tables"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

**步骤 2: 创建迁移**

```python
# alembic/versions/20250101_1300-003_create_new_table.py

def upgrade() -> None:
    """Create new_tables table."""
    op.execute("""
        CREATE TABLE new_tables (
            id VARCHAR PRIMARY KEY,
            name VARCHAR(500) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """)

def downgrade() -> None:
    """Drop new_tables table."""
    op.execute("DROP TABLE new_tables CASCADE;")
```

**步骤 3: 应用迁移**

重启应用即可。

### 数据迁移

如果需要在迁移时迁移数据：

```python
def upgrade() -> None:
    """Add full_name column and migrate data."""
    # 1. Add new column (nullable)
    op.add_column('users', sa.Column('full_name', sa.String(), nullable=True))

    # 2. Migrate data
    from sqlalchemy.sql import table, column
    users = table('users',
        column('id', sa.String),
        column('first_name', sa.String),
        column('last_name', sa.String),
        column('full_name', sa.String)
    )

    op.execute(
        users.update()
        .where(users.c.full_name.is_(None))
        .values(full_name=users.c.first_name + " " + users.c.last_name)
    )

    # 3. Make column non-nullable if needed
    # op.alter_column('users', 'full_name', nullable=False)

def downgrade() -> None:
    """Remove full_name column."""
    op.drop_column('users', 'full_name')
```

## 迁移文件命名规范

使用日期时间前缀 + 修订号 + 描述：

```
20241231_1700-001_initial_schema_with_sse.py
20250101_1200-002_add_new_field.py
20250102_1400-003_create_new_table.py
```

- `YYYYMMDD_HHMM`: 创建时间
- `###`: 递增的修订号（001, 002, 003...）
- `description`: 简短描述

## 版本控制

### Revision ID 系统

每个迁移都有唯一的 `revision` ID：

```python
revision = '002'           # 当前迁移的 ID
down_revision = '001'      # 父迁移的 ID
```

### 迁移链

```
001 (初始) → 002 (添加字段) → 003 (创建表) → 004 (添加索引) ...
```

### 查看当前版本

数据库版本存储在 `alembic_version` 表中：

```sql
SELECT version_num FROM alembic_version;
```

## 回滚支持

每个迁移都有 `upgrade()` 和 `downgrade()` 函数：

```python
def upgrade() -> None:
    """应用迁移"""
    op.add_column('memories', sa.Column('new_field', sa.String()))

def downgrade() -> None:
    """回滚迁移"""
    op.drop_column('memories', 'new_field')
```

### 手动回滚

```bash
# 创建一个临时脚本来回滚
python -c "
from alembic.config import Config
from alembic import command

config = Config('alembic.ini')
config.set_main_option('sqlalchemy.url', 'postgresql://...')

# 回滚一个版本
command.downgrade(config, '-1')

# 或回滚到特定版本
# command.downgrade(config, '001')
"
```

## 最佳实践

### ✅ DO (推荐做法)

1. **保持迁移幂等性**
   ```python
   def upgrade():
       # 检查列是否已存在
       from sqlalchemy import inspect
       inspector = inspect(op.get_bind())
       columns = [c['name'] for c in inspector.get_columns('memories')]

       if 'new_field' not in columns:
           op.add_column('memories', sa.Column('new_field', sa.String()))
   ```

2. **使用事务**
   ```python
   def upgrade():
       # Alembic 默认在事务中运行
       # 如果任何操作失败，整个迁移会回滚
       op.add_column('memories', sa.Column('field1', sa.String()))
       op.add_column('memories', sa.Column('field2', sa.String()))
       # 如果 field2 添加失败，field1 也会回滚
   ```

3. **先在开发环境测试**
   - 在本地数据库测试迁移
   - 验证 upgrade 和 downgrade
   - 检查数据完整性

4. **版本控制迁移文件**
   - 所有迁移都应提交到 Git
   - 不要修改已发布的迁移
   - 如果需要修复，创建新迁移

5. **编写清晰的描述**
   ```python
   """Add task tracking for episode processing

   This migration adds:
   - task_id column to memories table for SSE tracking
   - progress, result, message columns to task_logs table

   Related to: #123
   """
   ```

### ❌ DON'T (避免做法)

1. **不要修改已发布的迁移**
   - 如果已经在生产环境运行，创建新迁移来修复

2. **不要在迁移中删除数据**
   ```python
   # 坏例子
   def upgrade():
       op.execute("DELETE FROM memories WHERE created_at < '2024-01-01'")

   # 好做法：使用专门的清理脚本
   ```

3. **不要在迁移中执行长时间操作**
   ```python
   # 坏例子
   def upgrade():
       # 处理百万行数据
       for row in op.execute("SELECT * FROM large_table"):
           # 复杂处理...

   # 好做法：使用批处理或后台任务
   ```

4. **不要跳过版本号**
   - 保持版本号连续（001, 002, 003...）

## 故障排除

### 问题 1: 迁移在启动时失败

**症状**: 应用无法启动，日志显示迁移错误

**解决**:
1. 检查日志中的具体错误
2. 修复迁移文件
3. 手动修复数据库状态
4. 重启应用

```bash
# 查看当前数据库版本
psql -d memstack -c "SELECT version_num FROM alembic_version;"

# 如果需要，手动更新版本
psql -d memstack -c "UPDATE alembic_version SET version_num = '001';"
```

### 问题 2: 迁移卡住

**症状**: 迁移运行但不完成

**解决**:
1. 检查是否有锁
```sql
SELECT * FROM pg_stat_activity WHERE state = 'active';
```

2. 取消长时间运行的查询
```sql
SELECT pg_cancel_backend(pid);
```

### 问题 3: 需要重新运行迁移

**症状**: 开发环境需要重置数据库

**解决**:
```bash
# ⚠️ 仅用于开发环境！

# 删除所有表和数据
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

# 重置 Alembic 版本
# (应用重启时会重新创建表并运行迁移)
```

## 与旧迁移系统的对比

| 特性 | 旧系统 (migrations.py) | Alembic |
|------|----------------------|---------|
| 版本控制 | ❌ 无 | ✅ 完整 |
| 回滚支持 | ❌ 无 | ✅ 支持 |
| 迁移历史 | ❌ 无 | ✅ 完整历史 |
| 自动生成 | ❌ 手动 | ⚠️ 部分支持 |
| 社区支持 | ⚠️ 内部 | ✅ 庞大 |
| 生产验证 | ❌ 未验证 | ✅ 成熟 |

## 迁移到 Alembic 的步骤

如果你还在使用旧的迁移系统：

1. ✅ Alembic 已安装和配置
2. ✅ 初始迁移已创建 (001)
3. ✅ main.py 已更新使用 Alembic
4. ⏭️  旧迁移系统已弃用（但保留作为参考）

**下一步**:
- 新迁移使用 Alembic
- 旧代码继续工作
- 逐步迁移所有手动 SQL 到 Alembic

## 相关文档

- Alembic 官方文档: https://alembic.sqlalchemy.org/
- 实施计划: `docs/alembic_implementation_plan.md`
- 工具对比: `docs/database_migration_tools_comparison.md`
- 迁移历史: `alembic/versions/`

## 总结

Alembic 提供了：

- ✅ **版本控制**: 每个迁移都有唯一 ID
- ✅ **回滚支持**: 可以安全地回滚迁移
- ✅ **自动应用**: 启动时自动运行
- ✅ **生产就绪**: 经过大量生产验证
- ✅ **团队协作**: 标准化流程

**开始使用**:
1. 修改模型 (`models.py`)
2. 创建迁移 (`alembic/versions/`)
3. 重启应用（自动应用）

就这么简单！🎉
