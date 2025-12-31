I will refactor the new project code in `src/` to remove all direct imports from the legacy `server/` directory, ensuring strict architectural separation.

### Refactoring Plan

1.  **Refactor `SqlAlchemyMemoryRepository` (`src/infrastructure/adapters/secondary/sql_memory_repository.py`)**:
    *   **Problem**: It currently imports `MemoryModel` from `server.db_models`.
    *   **Solution**:
        *   Define the `MemoryModel` (and necessary base classes) locally within `src/infrastructure/adapters/secondary/persistence/models.py`.
        *   Alternatively, if the goal is to share the *same* database schema during migration, we should move the core DB models to a shared location within `src/`. For this task, I will move the `MemoryModel` definition into `src/infrastructure/adapters/secondary/persistence/models.py` (copying from `server/db_models.py` for now to decouple).
        *   Update the repository to use this new local model definition.

2.  **Refactor `RedisQueueAdapter` (`src/infrastructure/adapters/secondary/queue_adapter.py`)**:
    *   **Problem**: It imports `QueueService` from `server.services.queue_service`.
    *   **Solution**:
        *   The adapter currently *wraps* the old service. To fully decouple, we must port the necessary logic from `QueueService` directly into `RedisQueueAdapter` or a new `RedisQueueService` within `src/infrastructure/`.
        *   I will implement the `add_episode` logic directly using `redis` (aio-redis) in `RedisQueueAdapter`, replicating the payload structure required by the existing workers (to maintain compatibility with running workers).
        *   This avoids importing the old `QueueService` class.

3.  **Refactor `DIContainer` (`src/configuration/container.py`)**:
    *   **Problem**: It imports `QueueService` from `server.services.queue_service` and `get_settings` from `server.config`.
    *   **Solution**:
        *   Remove `QueueService` dependency. The container will configure `RedisQueueAdapter` directly with a Redis URL/Client.
        *   Create a local configuration adapter or move `get_settings` logic to `src/configuration/config.py` to avoid importing from `server/`.

4.  **Create Missing Infrastructure Components**:
    *   `src/infrastructure/config.py`: Port the settings/config logic needed.
    *   `src/infrastructure/adapters/secondary/persistence/database.py`: Port the SQLAlchemy base/setup logic if needed for the models.

5.  **Verify**:
    *   Run tests to ensure the refactored adapters still work correctly.

This plan effectively "cuts the cord" between `src/` and `server/`, making `src/` a self-contained module.
