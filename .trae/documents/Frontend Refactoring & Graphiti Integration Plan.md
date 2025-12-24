Based on the analysis of the documentation and current codebase, here is the plan to refactor the frontend and integrate it with the enhanced Graphiti backend services.

### 1. Enhance Graphiti Service (`web/src/services/graphitiService.ts`)
The `graphitiService` is missing the creation method and has a type mismatch for listing episodes.
- **Add `addEpisode` method**: Implement the call to `POST /api/v1/episodes/` for creating new memories.
- **Fix `listEpisodes` response mapping**: The backend returns `{ episodes: [], total: ... }` but the frontend type expects `{ items: [], total: ... }`. We will update the service to map `episodes` to `items` or update the type definition to match the API response.
- **Verify `deleteEpisode`**: Ensure it correctly calls `DELETE /api/v1/episodes-enhanced/{id}`.

### 2. Refactor Memory List Page (`web/src/pages/project/MemoryList.tsx`)
Currently using the legacy `memoryAPI`.
- **Switch to `graphitiService`**: Replace `memoryAPI.list` with `graphitiService.listEpisodes`.
- **Update Data Handling**: Adapt to the paginated response structure from the enhanced API.
- **Add Delete Functionality**: Implement the delete action using `graphitiService.deleteEpisode` with a confirmation dialog.
- **UI Improvements**: Ensure the list displays the enhanced metadata (tags, entity counts, etc.) if available.

### 3. Refactor New Memory Page (`web/src/pages/project/NewMemory.tsx`)
Currently using the legacy `memoryAPI`.
- **Switch to `graphitiService`**: Replace `memoryAPI.create` with `graphitiService.addEpisode`.
- **Update Payload**: Ensure the payload structure matches what `POST /api/v1/episodes/` expects (likely `EpisodeCreate` schema).

### 4. Refactor Memory Detail Page (`web/src/pages/project/MemoryDetail.tsx`)
- **Switch to `graphitiService`**: Replace legacy calls with `graphitiService.getEpisode`.
- **Enhance Display**: Show more details provided by the enhanced endpoint (e.g., extracted entities, community memberships) if available in the response.

### 5. Verification
- **Build & Run**: Ensure the frontend builds without errors.
- **Manual Testing**:
    - Create a new memory/episode.
    - List memories and verify pagination.
    - View memory details.
    - Delete a memory.
    - Verify that Entities and Communities pages continue to work (as they were already using the correct service).
