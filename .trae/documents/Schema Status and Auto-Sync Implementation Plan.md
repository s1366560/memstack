# Schema Status and Auto-Sync Implementation Plan

## 1. Database Model Updates
Add `status` and `source` fields to Schema-related tables to track their state and origin (user-defined vs. auto-generated).

### server/db_models.py
- Update `EntityType`, `EdgeType`, and `EdgeTypeMap` classes.
- Add `status`: String column, default `DataStatus.ENABLED`.
- Add `source`: String column, default "user" (can be "generated").

### server/models/schema.py
- Update Pydantic models (`EntityTypeBase`, `EdgeTypeBase`, `EdgeTypeMapBase` or their responses) to include `status` and `source`.

## 2. Queue Service Enhancement
Modify `QueueService` to intercept Graphiti results and synchronize the schema.

### server/services/queue_service.py
- Import necessary models: `EntityType`, `EdgeType`, `EdgeTypeMap`, `DataStatus`.
- Implement `_sync_schema_from_graph_result` method:
    1.  Accept `nodes`, `edges`, and `project_id`.
    2.  **Entity Types**: Iterate through `nodes`, extract labels (excluding "Entity"). Check and insert missing `EntityType` records with `source="generated"` and `status="ENABLED"`.
    3.  **Edge Types**: Iterate through `edges`, extract `name`. Check and insert missing `EdgeType` records.
    4.  **Edge Type Maps**: For each edge, resolve source and target node types using a UUID lookup map. Check and insert missing `EdgeTypeMap` records.
- Update `_process_episode_task` to call `_sync_schema_from_graph_result` after successful `add_episode`.

## 3. Verification
- Review code changes for correctness.
- Ensure no circular dependencies.
- Verify that `add_result` from Graphiti provides necessary data (`nodes` and `edges`).
