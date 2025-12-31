# Database Migration System

## Overview

The MemStack application now uses an incremental database migration system that automatically applies schema changes at startup. This ensures the database schema stays in sync with the application models without manual intervention.

## How It Works

### Startup Process

When the application starts, it automatically:

1. **Creates Missing Tables**: Uses SQLAlchemy's `create_all()` to create any tables that don't exist
2. **Applies Incremental Migrations**: Adds missing columns to existing tables as defined in the migration registry

This two-step process ensures:
- ✅ New deployments get all tables created automatically
- ✅ Existing deployments get new columns added without data loss
- ✅ No manual SQL scripts needed for common schema changes

### Migration Registry

Migrations are defined in `src/infrastructure/adapters secondary/persistence/migrations.py`:

```python
MIGRATIONS = [
    {
        "table": "memories",
        "column": "task_id",
        "type": "VARCHAR",
        "nullable": True,
        "description": "Task ID for SSE streaming"
    },
    {
        "table": "task_logs",
        "column": "progress",
        "type": "INTEGER",
        "nullable": True,
        "default": 0,
        "description": "Task progress percentage (0-100)"
    },
    # ... more migrations
]
```

Each migration specifies:
- `table`: The table to modify
- `column`: The column to add
- `type`: SQL data type (VARCHAR, INTEGER, JSONB, etc.)
- `nullable`: Whether NULL values are allowed
- `default`: Optional default value
- `description`: Human-readable description

## Usage

### Automatic Migration at Startup

By default, migrations run automatically when the application starts:

```python
# In main.py lifespan function
await apply_migrations()
```

Logs look like:
```
INFO: Applying database migrations...
INFO: Ensuring all tables exist...
INFO: ✅ Tables verified
INFO: Applying incremental migrations...
INFO: ✅ Migrations applied
```

### Manual Migration Management

Use the CLI tool to manage migrations manually:

```bash
# Show migration status
PYTHONPATH=/path/to/memstack uv run python scripts/manage_migrations.py status

# Apply pending migrations
PYTHONPATH=/path/to/memstack uv run python scripts/manage_migrations.py apply

# Check schema compatibility
PYTHONPATH=/path/to/memstack uv run python scripts/manage_migrations.py check
```

## Adding New Migrations

When you need to add a new column to an existing table:

1. **Update the Model**: Add the field to the SQLAlchemy model

```python
# In src/infrastructure/adapters/secondary/persistence/models.py
class Memory(Base):
    # ... existing fields ...
    new_field: Mapped[Optional[str]] = mapped_column(String, nullable=True)
```

2. **Add Migration**: Register the column in the migration list

```python
# In src/infrastructure/adapters/secondary/persistence/migrations.py
MIGRATIONS = [
    # ... existing migrations ...
    {
        "table": "memories",
        "column": "new_field",
        "type": "VARCHAR",
        "nullable": True,
        "description": "Your description here"
    },
]
```

3. **Test**: Apply the migration locally

```bash
PYTHONPATH=. uv run python scripts/manage_migrations.py status
PYTHONPATH=. uv run python scripts/manage_migrations.py apply
```

4. **Deploy**: When you deploy, the migration runs automatically at startup

## Migration Best Practices

### DO:
- ✅ Use `nullable=True` for new columns on existing tables
- ✅ Provide sensible default values when adding non-nullable columns
- ✅ Write clear descriptions for each migration
- ✅ Test migrations on a copy of production data
- ✅ Add migrations before deploying code that uses new columns

### DON'T:
- ❌ Don't remove migrations from the registry (they'll be re-applied)
- ❌ Don't add non-nullable columns without defaults to existing tables
- ❌ Don't change migration definitions after they've been applied
- ❌ Don't use migrations for complex schema changes (use manual SQL)

## Advanced Scenarios

### Complex Schema Changes

For complex changes beyond simple column additions:

1. Write a manual SQL script in `scripts/migrations/`
2. Document the change in the migration history
3. Run the script manually during maintenance window

### Rollbacks

The system doesn't support automatic rollbacks. If you need to revert:

1. Manually drop the added column:
   ```sql
   ALTER TABLE table_name DROP COLUMN column_name;
   ```
2. Remove the migration from the registry
3. Update the model

### Data Migrations

If you need to migrate data:

```python
# In a one-off script
async def migrate_data():
    async with async_session_factory() as session:
        # Migrate existing data
        await session.execute(
            text("UPDATE memories SET new_field = old_field WHERE new_field IS NULL")
        )
        await session.commit()
```

## Migration Status Example

```
================================================================================
DATABASE MIGRATION STATUS
================================================================================

Total migrations defined: 4
Applied migrations: 4
Pending migrations: 0

✅ Applied migrations:
   ✓ memories.task_id
     Task ID for SSE streaming during episode ingestion
   ✓ task_logs.progress
     Task progress percentage (0-100)
   ✓ task_logs.result
     Task result data
   ✓ task_logs.message
     Task status message

================================================================================
```

## Troubleshooting

### Migration Fails at Startup

**Problem**: Application won't start due to migration error

**Solution**:
1. Check backend logs for specific error
2. Run manual status check:
   ```bash
   python scripts/manage_migrations.py status
   ```
3. Apply migrations manually:
   ```bash
   python scripts/manage_migrations.py apply
   ```
4. Verify schema compatibility:
   ```bash
   python scripts/manage_migrations.py check
   ```

### Column Already Exists Error

**Problem**: Migration says column already exists

**Solution**: This is expected! The system checks before adding. If you see this in logs:
```
DEBUG: Column memories.task_id already exists in table memories - skipping
```
It means the migration was already applied, which is fine.

### Permission Denied

**Problem**: Can't add columns due to permissions

**Solution**: Ensure the database user has ALTER TABLE permissions:
```sql
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_user;
```

## Files Modified

### Core Migration System
- `src/infrastructure/adapters/secondary/persistence/database.py` - Migration orchestration
- `src/infrastructure/adapters/secondary/persistence/migrations.py` - Migration registry and logic

### Application Integration
- `src/infrastructure/adapters/primary/web/main.py` - Calls `apply_migrations()` at startup

### Management Tools
- `scripts/manage_migrations.py` - CLI tool for manual migration management
- `scripts/add_task_id_column.py` - One-off migration script (kept for reference)

## Related Documentation

- SQLAlchemy Migrations: https://docs.sqlalchemy.org/en/20/core/metadata.html
- PostgreSQL ALTER TABLE: https://www.postgresql.org/docs/current/sql-altertable.html
- Database Schema Design: docs/database_schema.md (if it exists)

## Future Improvements

Potential enhancements to the migration system:

1. **Version Tracking**: Track which migrations have been applied in a versions table
2. **Rollback Support**: Add ability to rollback migrations
3. **Dependency Tracking**: Ensure migrations run in correct order
4. **Dry Run Mode**: Preview what migrations would do without applying them
5. **Migration History**: Keep a log of all applied migrations with timestamps
6. **Automated Testing**: Test migrations against a copy of production data

## Summary

The migration system provides:
- ✅ Automatic schema updates at startup
- ✅ Zero-downtime deployments for column additions
- ✅ No manual SQL for common changes
- ✅ Clear visibility into migration status
- ✅ Manual control when needed

This allows the team to iterate on the database schema confidently while maintaining production stability.
