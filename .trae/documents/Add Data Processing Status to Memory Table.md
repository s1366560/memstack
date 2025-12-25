I will implement data processing status tracking, update the frontend, and ensure comprehensive test coverage.

### 1. Backend Implementation
-   **Enums**: Create `server/models/enums.py` with `ProcessingStatus` and `DataStatus`.
-   **Database**: Add `status` and `processing_status` columns to `Memory` table in `server/db_models.py`.
-   **API Models**: Update `server/models/memory_app.py` to include new fields.
-   **Service Logic**: Update `server/services/queue_service.py` to handle database status updates during processing.

### 2. Frontend Implementation
-   **Types**: Update `web/src/types/memory.ts`.
-   **UI Components**:
    -   `ProjectOverview.tsx`: Display Data Availability Status.
    -   `MemoryList.tsx`: Add columns/indicators for both Data and Processing statuses.
    -   `MemoryDetail.tsx`: Display both statuses in the header.

### 3. Test Updates & Coverage
-   **Backend Unit Tests**: Update `server/tests/test_api_memories.py` to verify default status values on creation.
-   **Queue Service Tests**: Update `server/tests/test_queue_service.py` to verify status transitions (PENDING -> PROCESSING -> COMPLETED/FAILED).
-   **Integration Tests**: Update `tests/test_integration_memories.py` to validate the full lifecycle of a memory status.
-   **Frontend Tests**: Update `web/src/test/components/MemoryManager.test.tsx` and `MemoryDetailModal.test.tsx` to accommodate the new type definitions and UI elements.
