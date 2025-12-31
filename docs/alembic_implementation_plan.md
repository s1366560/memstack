# Alembic 迁移系统实施计划

## 实施步骤

### 1. 安装和初始化

```bash
# 1. 安装 Alembic
uv add alembic

# 2. 初始化 Alembic
alembic init alembic

# 3. 项目结构
# alembic/
#   ├── env.py           # 迁移环境配置
#   ├── README
#   ├── script.py.mako   # 模板
#   └── versions/
#       ├── 001_initial.py
#       └── 002_add_task_id.py
```

### 2. 配置 alembic.ini

```ini
[alembic]
# 迁移脚本位置
script_location = alembic

# 数据库连接（从环境变量读取）
sqlalchemy.url = postgresql://user:pass@localhost/dbname

[log]
# 日志配置
basicConfig = %(levelname)s %(name)s %(message)s

[post_write_hooks]
# 迁移脚本格式化
hooks = black
black.type = console_scripts
black.entrypoint = black
black.options = -l 79 REVISION_SCRIPT_FILENAME
```

### 3. 配置 alembic/env.py

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.configuration.config import get_settings
from src.infrastructure.adapters.secondary.persistence.models import Base

# 导入所有模型以确保它们被注册
from src.infrastructure.adapters.secondary.persistence.models import (
    User, Tenant, Project, Memory, EntityType, TaskLog
)

# Alembic Config 对象
config = context.config

# 从配置覆盖数据库 URL
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.postgres_url)

# 解释配置文件中的 Python 日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 添加模型的 MetaData 对象
target_metadata = Base.metadata

# ... 其他 Alembic 配置
```

### 4. 创建迁移脚本

#### 自动生成（推荐）

```bash
# 自动检测模型变化并生成迁移
alembic revision --autogenerate -m "Add task_id to memories"
```

生成的文件 `alembic/versions/20241231_1234_add_task_id_to_memories.py`:

```python
"""Add task_id to memories

Revision ID: abc123def456
Revises: def456ghi789
Create Date: 2024-12-31 12:34:56.123456

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'abc123def456'
down_revision = 'def456ghi789'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add task_id column to memories table."""
    op.add_column('memories',
        sa.Column('task_id', sa.String(), nullable=True)
    )


def downgrade() -> None:
    """Remove task_id column from memories table."""
    op.drop_column('memories', 'task_id')
```

#### 手动创建

```bash
# 创建空迁移模板
alembic revision -m "Add progress tracking to task_logs"
```

然后手动编辑 `alembic/versions/20241231_1235_add_progress_tracking.py`:

```python
"""Add progress tracking to task_logs

Revision ID: ghi789jkl012
Revises: abc123def456
Create Date: 2024-12-31 12:35:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'ghi789jkl012'
down_revision = 'abc123def456'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add progress tracking columns."""
    # Add progress column
    op.add_column('task_logs',
        sa.Column('progress', sa.Integer(), nullable=True, server_default='0')
    )

    # Add result column
    op.add_column('task_logs',
        sa.Column('result', sa.JSON(), nullable=True)
    )

    # Add message column
    op.add_column('task_logs',
        sa.Column('message', sa.String(), nullable=True)
    )


def downgrade() -> None:
    """Remove progress tracking columns."""
    op.drop_column('task_logs', 'message')
    op.drop_column('task_logs', 'result')
    op.drop_column('task_logs', 'progress')
```

### 5. 运行迁移

```bash
# 升级到最新版本
alembic upgrade head

# 升级到特定版本
alembic upgrade abc123def456

# 查看当前版本
alembic current

# 查看迁移历史
alembic history

# 回滚一个版本
alembic downgrade -1

# 回滚到特定版本
alembic downgrade def456ghi789

# 查看待执行的迁移（干运行）
alembic upgrade head --sql
```

### 6. 集成到应用

```python
# src/infrastructure/adapters/secondary/persistence/migrations_alembic.py
from alembic.config import Config
from alembic import command
import logging

logger = logging.getLogger(__name__)


async def run_alembic_migrations():
    """
    Run Alembic migrations at startup.

    This will apply any pending migrations automatically.
    """
    alembic_cfg = Config("alembic.ini")

    try:
        logger.info("Running Alembic migrations...")

        # Get current revision
        with engine.begin() as conn:
            current = command.current(alembic_cfg)

        logger.info(f"Current database revision: {current}")

        # Upgrade to head
        command.upgrade(alembic_cfg, "head")

        logger.info("✅ Migrations applied successfully")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise
```

在 `main.py` 中：

```python
from src.infrastructure.adapters.secondary.persistence.migrations_alembic import run_alembic_migrations

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting MemStack application...")

    # Run Alembic migrations
    await run_alembic_migrations()

    # ... other startup tasks
```

### 7. 开发工作流

#### 添加新字段

1. 修改模型：
   ```python
   # models.py
   class Memory(Base):
       new_field = mapped_column(String, nullable=True)
   ```

2. 生成迁移：
   ```bash
   alembic revision --autogenerate -m "Add new_field to memories"
   ```

3. 审查生成的迁移：
   ```python
   # alembic/versions/xxx_add_new_field.py
   def upgrade():
       op.add_column('memories', sa.Column('new_field', sa.String(), nullable=True))

   def downgrade():
       op.drop_column('memories', 'new_field')
   ```

4. 应用迁移：
   ```bash
   alembic upgrade head
   ```

#### 修改表结构

```bash
# 创建迁移
alembic revision -m "Modify memories table"

# 编辑迁移文件
def upgrade():
    # 重命名列
    op.alter_column('memories', 'old_name', new_column_name='new_name')

    # 修改列类型
    op.alter_column('memories', 'title',
                    type_=sa.String(1000),
                    existing_type=sa.String(500))

    # 添加索引
    op.create_index('ix_memories_project_id', 'memories', ['project_id'])

def downgrade():
    op.drop_index('ix_memories_project_id', table_name='memories')
    op.alter_column('memories', 'title',
                    type_=sa.String(500),
                    existing_type=sa.String(1000))
    op.alter_column('memories', 'new_name', new_column_name='old_name')
```

### 8. 高级功能

#### 数据迁移

```python
def upgrade():
    # Add new column
    op.add_column('users', sa.Column('full_name', sa.String(), nullable=True))

    # Migrate data from first_name + last_name to full_name
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

def downgrade():
    op.drop_column('users', 'full_name')
```

#### 条件迁移

```python
def upgrade():
    # Only add column if it doesn't exist
    from sqlalchemy import inspect
    inspector = inspect(op.get_bind())
    columns = [c['name'] for c in inspector.get_columns('memories')]

    if 'task_id' not in columns:
        op.add_column('memories', sa.Column('task_id', sa.String(), nullable=True))
```

#### 批量操作

```python
def upgrade():
    with op.batch_alter_table('memories') as batch_op:
        batch_op.add_column(sa.Column('new_field', sa.String(), nullable=True))
        batch_op.create_index('idx_new_field', ['new_field'])
```

### 9. CLI 工具增强

```python
# scripts/alembic_cli.py
import click
from alembic.config import Config
from alembic import command

@click.group()
def cli():
    """Alembic migration CLI."""
    pass

@cli.command()
@click.option('--revision', '-r', default='head', help='Revision to upgrade to')
def upgrade(revision):
    """Upgrade database to a later version."""
    cfg = Config("alembic.ini")
    command.upgrade(cfg, revision)
    click.echo(f"✅ Upgraded to {revision}")

@cli.command()
@click.option('--revision', '-r', default='-1', help='Revision to downgrade to')
def downgrade(revision):
    """Downgrade database to an earlier version."""
    cfg = Config("alembic.ini")
    command.downgrade(cfg, revision)
    click.echo(f"✅ Downgraded to {revision}")

@cli.command()
def current():
    """Show current revision."""
    cfg = Config("alembic.ini")
    rev = command.current(cfg)
    click.echo(f"Current revision: {rev}")

@cli.command()
def history():
    """Show migration history."""
    cfg = Config("alembic.ini")
    command.history(cfg)

@cli.command()
@click.option('--message', '-m', required=True, help='Migration message')
@click.option('--autogenerate/--empty', default=False, help='Autogenerate from models')
def revision(message, autogenerate):
    """Create a new migration."""
    cfg = Config("alembic.ini")
    if autogenerate:
        command.revision(cfg, message=message, autogenerate=True)
    else:
        command.revision(cfg, message=message)
    click.echo(f"✅ Created migration: {message}")

if __name__ == '__main__':
    cli()
```

使用：
```bash
python scripts/alembic_cli.py upgrade
python scripts/alembic_cli.py downgrade -r abc123
python scripts/alembic_cli.py current
python scripts/alembic_cli.py revision -m "Add new feature" --autogenerate
```

### 10. 最佳实践

1. **总是审查自动生成的迁移**
   - `--autogenerate` 很强大但不是完美的
   - 检查生成的 SQL 是否符合预期

2. **保持迁移幂等性**
   ```python
   def upgrade():
       # 检查列是否已存在
       from sqlalchemy import inspect
       inspector = inspect(op.get_bind())
       if 'task_id' not in [c['name'] for c in inspector.get_columns('memories')]:
           op.add_column('memories', sa.Column('task_id', sa.String()))
   ```

3. **使用事务**
   ```python
   from alembic import op

   def upgrade():
       # 默认在事务中执行
       with op.get_bind().begin():
           op.add_column('memories', sa.Column('task_id', sa.String()))
           # 其他操作...
           # 如果任何操作失败，整个迁移会回滚
   ```

4. **测试迁移**
   ```python
   # tests/test_migrations.py
   from alembic import command
   from alembic.config import Config

   def test_migration():
       # 升级到最新
       cfg = Config("alembic.ini")
       command.upgrade(cfg, "head")

       # 验证 schema
       inspector = inspect(engine)
       columns = [c['name'] for c in inspector.get_columns('memories')]
       assert 'task_id' in columns

       # 回滚
       command.downgrade(cfg, "base")
   ```

5. **版本控制迁移脚本**
   - 所有迁移脚本都应提交到 Git
   - 团队成员应该拉取最新的迁移
   - 不要修改已发布的迁移

## 迁移现有实现到 Alembic

### 步骤 1：初始化 Alembic

```bash
# 1. 安装 Alembic
uv add alembic

# 2. 初始化
alembic init alembic

# 3. 配置（见上面的配置步骤）
```

### 步骤 2：创建初始迁移

```bash
# 基于当前模型创建初始迁移
alembic revision --autogenerate -m "Initial migration with existing schema"
```

这会创建一个包含所有当前表结构的迁移。

### 步骤 3：标记已应用的迁移

```bash
# 标记当前数据库状态为最新版本（不实际运行迁移）
alembic stamp head
```

这会告诉 Alembic 当前数据库已经是最新状态，跳过已有的表。

### 步骤 4：保留旧系统作为备份

```python
# 保留 migrations.py 但标记为 deprecated
"""
DEPRECATED: This module is replaced by Alembic.

Old migrations are kept for reference only.
Use Alembic for all new migrations:
  alembic revision --autogenerate -m "description"
  alembic upgrade head
"""
```

### 步骤 5：更新 main.py

```python
# 替换旧的迁移系统
# from src.infrastructure.adapters.secondary.persistence.database import apply_migrations
from src.infrastructure.adapters.secondary.persistence.migrations_alembic import run_alembic_migrations

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting MemStack application...")

    # 使用 Alembic
    await run_alembic_migrations()

    # ... rest of startup
```

### 步骤 6：验证

```bash
# 1. 检查当前版本
alembic current

# 2. 查看历史
alembic history

# 3. 创建测试迁移
alembic revision -m "Test migration"

# 4. 升级
alembic upgrade head

# 5. 验证
alembic current
```

## 总结

迁移到 Alembic 的优势：

✅ **版本控制**：每个迁移都有唯一 ID
✅ **回滚支持**：可以安全地回滚迁移
✅ **自动生成**：从模型自动检测变化
✅ **团队协作**：标准化的迁移流程
✅ **生产就绪**：经过大量生产验证

成本：
- 学习时间：2-3 天
- 迁移时间：1-2 天
- 维护成本：更低（长期）

**建议：立即开始迁移到 Alembic，为新项目提供更好的基础。**
