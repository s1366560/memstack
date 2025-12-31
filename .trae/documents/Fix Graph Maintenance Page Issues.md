I will fix the issues in the Graph Maintenance page by refactoring both the frontend and backend, and updating the tests.

### Frontend (`web/src/pages/project/Maintenance.tsx` & `web/src/services/graphitiService.ts`)
1.  **Update `graphitiService.ts`**: Add methods for maintenance operations to centralize API calls.
    *   `getMaintenanceStatus()`
    *   `incrementalRefresh()`
    *   `deduplicateEntities()`
    *   `invalidateStaleEdges()`
    *   `optimizeGraph()`
2.  **Refactor `Maintenance.tsx`**:
    *   Replace direct `fetch` calls with `graphitiService` methods.
    *   Remove manual header management (handled by service interceptors).
    *   Add proper type definitions for state variables.

### Backend (`src/infrastructure/adapters/primary/web/routers/maintenance.py`)
1.  **Fix `optimize_graph`**:
    *   Implement missing `rebuild_communities` logic by calling `queue_service.rebuild_communities`.
    *   Ensure proper dependency injection when calling other maintenance functions.
2.  **Enhance `deduplicate_entities`**:
    *   Ensure consistency between dry-run (Cypher query) and actual execution (Queue task).

### Tests (`tests/test_api_maintenance.py`)
1.  **Rewrite Tests**:
    *   Update imports to match the current project structure (`src.infrastructure...`).
    *   Use `AsyncClient` with the FastAPI app.
    *   Mock `graphiti_client` and `queue_service` dependencies correctly.
    *   Add test cases for `optimize_graph` ensuring all operations are triggered correctly.

### Verification
*   Run the updated `tests/test_api_maintenance.py` to verify backend fixes.
*   (Manual) Verify frontend compiles and calls the correct endpoints.
