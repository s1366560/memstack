I will add unit tests for the new hexagonal architecture implementation to ensure it matches the original business logic.

### Test Plan

1.  **Create Test Structure**:
    *   `src/tests/unit/`: For Use Case logic tests.
    *   `src/tests/integration/`: For Repository/Adapter tests.

2.  **Implement Unit Tests (`src/tests/unit/`)**:
    *   `test_create_memory_use_case.py`: Verify `CreateMemoryUseCase` correctly:
        *   Creates a `Memory` entity with expected defaults (Status: ENABLED, Processing: PENDING).
        *   Calls `MemoryRepository.save`.
        *   Calls `GraphServicePort.add_episode` when content is text.
        *   Handles graph service failures gracefully (logging error but succeeding).
    *   `test_search_memory_use_case.py`: Verify `SearchMemoryUseCase` delegates to `GraphServicePort`.

3.  **Implement Integration Tests (`src/tests/integration/`)**:
    *   `test_sql_memory_repository.py`: Verify `SqlAlchemyMemoryRepository` can save and retrieve memories using an in-memory SQLite database. This ensures the DB mapping is correct.

4.  **Verification**:
    *   Run the new tests using `pytest`.

This approach ensures that the new "Hexagonal" implementation strictly follows the business rules defined in the original project, satisfying the "consistency" requirement.
