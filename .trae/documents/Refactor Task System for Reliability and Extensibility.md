I will proceed with a comprehensive refactor to solve the task failure issues and support the new requirements.

### 1. Backend: Database Schema Update
*   **Modify `TaskLog` Model**:
    *   Add `entity_id` (String, Index) and `entity_type` (String) to link tasks to Memories or Communities.
    *   Add `parent_task_id` for potential sub-task tracking.
    *   Add `stopped_at` timestamp.

### 2. Backend: Queue Service Refactoring (Strategy Pattern)
*   **Create `server/services/tasks/` module**:
    *   **`TaskHandler` Interface**: Define standard methods (`process`, `timeout_seconds`).
    *   **`EpisodeHandler`**: Encapsulate logic for `add_episode`.
    *   **`RebuildCommunityHandler`**: Encapsulate logic for `rebuild_communities`.
        *   **Fix**: Set a custom timeout (e.g., 1 hour) for this handler to prevent the recovery loop from incorrectly restarting it.
    *   **`TaskRegistry`**: Centralized registration of handlers.
*   **Update `QueueService`**:
    *   Replace the `if/else` block in the worker loop with dynamic handler lookup.
    *   Update `_recovery_loop` to use dynamic timeouts from handlers.
    *   Implement `stop_task(task_id)` method (mark as STOPPED in DB to prevent retries).

### 3. Backend: API Enhancements
*   **Update `server/api/tasks.py`**:
    *   Update `get_recent_tasks` to support filtering by `entity_id`.
    *   Add `POST /tasks/{id}/stop` endpoint.
    *   Ensure `retry_task` supports the new handler structure.

### 4. Frontend: UI Updates
*   **Enhance `TaskDashboard.tsx`**:
    *   Add "Stop" action to the task menu.
    *   Display `entity_id` (or link to the entity) if available.
*   **Integration**:
    *   Ensure the "Rebuild Community" button triggers the task correctly with the new structure.

### Execution Order
1.  **Database Models**: Update `server/db_models.py`.
2.  **Task Logic**: Create the new `server/services/tasks/` package and migrate logic.
3.  **Queue Service**: Switch `server/services/queue_service.py` to use the new handlers.
4.  **API**: Update endpoints in `server/api/tasks.py`.
5.  **Frontend**: Update `web/src/pages/tenant/TaskDashboard.tsx`.
