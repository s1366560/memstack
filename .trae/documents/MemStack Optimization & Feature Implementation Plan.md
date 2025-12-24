# MemStack Optimization & Async Queue Plan

## 1. Async Queue Implementation (Graphiti Style)
Reference: `vendor/graphiti/mcp_server/src/services/queue_service.py`

### Backend Changes
1.  **Create Queue Service**:
    - Create `server/services/queue_service.py` adapted from the MCP server implementation.
    - It will manage per-group (project) `asyncio.Queue`s to process episodes sequentially.
2.  **Integrate with GraphitiService**:
    - Update `server/services/graphiti_service.py`:
        - Initialize `QueueService` in `__init__` and `initialize`.
        - Modify `add_episode` to:
            - Create the `Episode` object with a UUID immediately.
            - Submit the ingestion task to `QueueService` using `project_id` as the `group_id`.
            - Return the `Episode` object immediately (simulating "Accepted" state).
3.  **Update API**:
    - `server/api/episodes.py` will remain mostly the same but will now benefit from the non-blocking `graphiti.add_episode`.

## 2. New Memory Page & AI Features
### Backend: AI Tools
1.  **New API Router**: Create `server/api/ai_tools.py` with:
    - `POST /api/v1/ai/optimize`: Takes content + instruction, returns optimized content using LLM.
    - `POST /api/v1/ai/generate-title`: Takes content, returns a generated title.
2.  **LLM Integration**: Use the existing `LLMClient` (Gemini/Qwen/OpenAI) configured in `GraphitiService` (or access via settings) to perform these tasks.

### Frontend: NewMemory.tsx
1.  **Title Optimization**:
    - Remove "Save" button disable state when title is empty.
    - In `handleSave`, if title is empty, call `generate-title` endpoint (or let backend handle it if we move logic there, but frontend call gives better visibility). *Decision*: I'll let the backend `add_episode` handle empty title generation to ensure robustness, but for the UI "AI Assist", I'll add the button.
2.  **Rich Text Editor**:
    - **Toolbar**: Implement `insertMarkdown` logic for Bold, Italic, List, Link, Code buttons.
    - **AI Assist**: Connect the button to `POST /api/v1/ai/optimize`.
        - Show a loading indicator while optimizing.
        - Replace/Append content with the result.

## 3. Execution Order
1.  **Backend**: Implement `QueueService` and integrate into `GraphitiService`.
2.  **Backend**: Implement `ai_tools` endpoints.
3.  **Frontend**: Update `NewMemory.tsx`.
