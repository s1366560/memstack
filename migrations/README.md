# Database Migrations

This directory contains database migration scripts for updating the PostgreSQL schema.

## Recent Migrations

### 2025-01-01: Add Task Progress Tracking

**File**: `add_task_progress_fields.sql`
**Script**: `scripts/migrate_add_task_progress.py`

Added the following columns to the `task_logs` table to support real-time progress tracking:

- `progress` (INTEGER, DEFAULT 0): Task progress percentage (0-100)
- `result` (JSONB): Task result data (e.g., communities_count, edges_count)
- `message` (VARCHAR): Task status message for user feedback

**Impact**:
- Enables real-time task progress tracking in the UI
- Supports detailed result reporting
- Improves user experience with status messages

**Running the migration**:

```bash
# Option 1: Run the Python script (recommended)
PYTHONPATH=/Users/tiejunsun/github/mem/memstack uv run python scripts/migrate_add_task_progress.py

# Option 2: Run SQL manually
psql -U your_user -d your_database -f migrations/add_task_progress_fields.sql
```

## Migration Template

When adding new fields to models:

1. Update the model in `src/infrastructure/adapters/secondary/persistence/models.py`
2. Create a migration script in `scripts/` directory
3. Run the migration to update the database
4. Update any related query/update methods to use the new fields
5. Update the API response schemas if needed

## Rolling Back

To roll back this migration:

```sql
ALTER TABLE task_logs DROP COLUMN IF EXISTS progress;
ALTER TABLE task_logs DROP COLUMN IF EXISTS result;
ALTER TABLE task_logs DROP COLUMN IF EXISTS message;
DROP INDEX IF EXISTS idx_task_logs_progress;
```

Or create a rollback script in the `scripts/` directory.
