I have successfully implemented the data processing status tracking and updated the frontend and tests.

### Backend Changes
1.  **Enums**: Created `server/models/enums.py` with `ProcessingStatus` (PENDING, PROCESSING, COMPLETED, FAILED) and `DataStatus` (ENABLED, DISABLED).
2.  **Database**: Updated `server/db_models.py` to add `status` and `processing_status` columns to `Memory` table.
3.  **API Models**: Updated `server/models/memory_app.py` to include these fields in `MemoryItem` and `MemoryResponse`.
4.  **Queue Service**: Updated `server/services/queue_service.py` to update the `processing_status` in the database during processing (Start -> Processing, Success -> Completed, Failure -> Failed).

### Frontend Changes
1.  **Types**: Updated `web/src/types/memory.ts` to include `status` and `processing_status`.
2.  **Project Overview**: Updated `web/src/pages/project/ProjectOverview.tsx` to display Data Availability Status (Available/Unavailable) based on `status`.
3.  **Memory List**: Updated `web/src/pages/project/MemoryList.tsx` to:
    -   Use `memoryAPI.list` to fetch SQL-backed data (including statuses).
    -   Display both "Data Status" and "Processing Status" columns.
    -   Update filtering and display logic to use correct fields (`title`, `content_type`).
4.  **Memory Detail**: Updated `web/src/pages/project/MemoryDetail.tsx` to:
    -   Use `memoryAPI.get` to fetch SQL-backed data.
    -   Display Processing Status in the header badge.
    -   Display Data Status (Availability) via the online indicator dot.

### Test Updates
1.  **Integration Tests**: Updated `tests/test_integration_memories.py` to verify that created memories have the correct default statuses (`ENABLED`, `PENDING`).
2.  **Queue Service Tests**: Updated `server/tests/test_queue_service.py` to verify that status update methods are called during processing.
3.  **Frontend Tests**: Updated `web/src/test/components/MemoryManager.test.tsx` to include new status fields in mock data.
