I will implement a robust, persistent task queue using Redis and add comprehensive task execution logging to the database.

### 1. Database Model Updates (`server/db_models.py`)
*   **Add `TaskLog` Model**: Create a new SQLAlchemy model to track the lifecycle of each task.
    *   Fields: `id` (UUID), `group_id`, `task_type` (e.g., 'add_episode'), `status` (PENDING, PROCESSING, COMPLETED, FAILED), `created_at`, `started_at`, `completed_at`, `error_message`, `worker_id`, `retry_count`, and `payload` (JSON).
    *   This table will be automatically created on startup via `Base.metadata.create_all`.

### 2. Refactor `QueueService` (`server/services/queue_service.py`)
*   **Replace In-Memory Queue**: Switch from `asyncio.Queue` to `redis.asyncio.Redis` for persistence.
*   **Reliable Queue Pattern**:
    *   Use `LMOVE` (or `RPOPLPUSH`) to atomically move tasks from `pending` to `processing` queues to prevent data loss during crashes.
*   **Integrated Logging**:
    *   **Enqueue**: Create a `TaskLog` entry with status `PENDING` when a task is added.
    *   **Processing**: Update `TaskLog` to `PROCESSING`, recording `started_at` and `worker_id`.
    *   **Completion**: Update `TaskLog` to `COMPLETED` on success.
    *   **Failure**: Update `TaskLog` to `FAILED` with the error message on failure.
*   **Worker Logic**:
    *   Implement a worker loop that pulls tasks from Redis, deserializes the payload, and executes the core episode processing logic (which will be moved from `GraphitiService`'s closure to `QueueService`).
    *   Support dynamic schema fetching via a callback (`schema_loader`).
*   **Recovery Mechanism**:
    *   Implement a background `_recovery_loop` to scan for stalled tasks (e.g., stuck in `PROCESSING` for >10 mins).
    *   Recovered tasks will have their `retry_count` incremented in `TaskLog` and be re-queued.

### 3. Update `GraphitiService` (`server/services/graphiti_service.py`)
*   **Initialization**: Pass `self.get_project_schema` as the `schema_loader` callback to `QueueService`.
*   **Add Episode**: Refactor `add_episode` to serializing the task data and submitting it to `QueueService`, removing the complex internal closure.

This plan ensures **exactly-once execution** (via idempotency checks), **persistence** (Redis), **scalability** (multiple workers/instances), and **complete observability** (TaskLog database records).
