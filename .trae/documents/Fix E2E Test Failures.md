I have identified several discrepancies between the frontend requirements and backend implementation, as well as missing functionality in the backend.

### Plan

1.  **Frontend Refactoring**:
    *   Update `web/src/services/graphitiService.ts` to use correct API paths (change `/episodes-enhanced` to `/episodes`).
    *   Refactor `web/src/pages/project/MemoryList.tsx` to use `graphitiService` instead of legacy `memoryAPI`.
    *   Refactor `web/src/pages/project/NewMemory.tsx` and `web/src/pages/project/MemoryDetail.tsx` to use `graphitiService`.

2.  **Backend Refactoring (`src/infrastructure/adapters/primary/web/routers/`)**:
    *   **`tenants.py`**: Replace mock data in `get_tenant_stats` with real queries:
        *   Calculate real storage usage from `Memory` table.
        *   Get real active projects status.
        *   Get real member counts.
    *   **`projects.py`**: Implement real logic for `get_project_stats`:
        *   Fetch actual node counts from Graphiti/Neo4j.
        *   Calculate real storage usage.

3.  **Verification**:
    *   Run frontend E2E tests to verify the UI changes.
    *   Manually verify dashboard stats reflect database state.

I will start by updating the frontend service and components, then move to the backend stats implementation.
