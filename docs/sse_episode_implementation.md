# SSE Implementation for Episode/Memory Creation

## Summary

Implemented real-time progress tracking for episode/memory creation using Server-Sent Events (SSE), following the same pattern used for community rebuild.

## Changes Made

### Backend Changes

#### 1. Queue Service - Return task_id
**File**: `src/infrastructure/adapters/secondary/queue/redis_queue.py:352-400`

- Changed `add_episode()` return type from `int` (queue length) to `str` (task_id)
- Now returns the task_id which can be used for SSE streaming

```python
async def add_episode(...) -> str:
    """Add an episode processing task to the queue. Returns task_id."""
    # ... create task log ...
    return task_id  # Instead of: return await self._redis.llen(queue_key)
```

#### 2. Memories Router - Return task_id in response
**File**: `src/infrastructure/adapters/primary/web/routers/memories.py:60-81, 190-213`

- Added `task_id` field to `MemoryResponse` schema
- Modified `create_memory` endpoint to capture and return task_id

```python
class MemoryResponse(BaseModel):
    # ... existing fields ...
    task_id: Optional[str] = None  # Task ID for SSE streaming

# In create_memory endpoint:
task_id = await queue_service.add_episode(...)
memory.task_id = task_id  # Store for response
return MemoryResponse.from_orm(memory)
```

#### 3. Memory Model - Add task_id column
**File**: `src/infrastructure/adapters/secondary/persistence/models.py:256`

- Added `task_id` column to Memory model for tracking

```python
task_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
```

#### 4. Episode Task Handler - Add Progress Reporting
**File**: `src/application/tasks/episode.py:19-150`

- Added progress tracking at 5 key stages:
  - 10%: Starting episode ingestion
  - 20%: Loading schema (if applicable)
  - 30%: Extracting entities and relationships
  - 50%: Syncing schema
  - 75%: Updating communities
  - 100%: Episode ingestion completed

```python
async def process(self, payload: Dict[str, Any], context: Any) -> None:
    task_id = payload.get("task_id")

    async def update_progress(progress: int, message: str = None):
        if task_id:
            await queue_service._update_task_log(
                task_id, "PROCESSING",
                progress=progress,
                message=message
            )

    await update_progress(10, "Starting episode ingestion...")
    # ... processing steps ...
    await update_progress(100, "Episode ingestion completed")
```

### Frontend Changes

#### 5. NewMemory Page - SSE Integration
**File**: `web/src/pages/project/NewMemory.tsx:1-103, 149-184, 223-284`

- Added `TaskStatus` interface for type safety
- Implemented `streamTaskStatus()` function with EventSource
- Added progress UI with real-time updates
- Added error handling with user-friendly messages

**Key Features:**
- Real-time progress bar (0-100%)
- Status messages for each processing stage
- Automatic navigation on completion
- Error display with retry capability
- Console logging for debugging

```typescript
interface TaskStatus {
    task_id: string
    status: string
    progress: number
    message: string
    result?: any
}

const streamTaskStatus = useCallback((taskId: string) => {
    const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
    const streamUrl = `${apiBaseUrl}/tasks/${taskId}/stream`
    const eventSource = new EventSource(streamUrl)

    eventSource.addEventListener('progress', (e: MessageEvent) => {
        const data = JSON.parse(e.data)
        setCurrentTask({
            task_id: data.id,
            status: statusMap[data.status?.toLowerCase()],
            progress: data.progress || 0,
            message: data.message || 'Processing...',
        })
    })

    eventSource.addEventListener('completed', (e: MessageEvent) => {
        // Navigate to memories list after 1.5s
        setTimeout(() => {
            eventSource.close()
            navigate(`/project/${projectId}/memories`)
        }, 1500)
    })
}, [navigate, projectId])
```

## SSE Endpoint

The existing SSE endpoint is reused for episode tasks:
- **URL**: `/api/v1/tasks/{task_id}/stream`
- **Method**: GET
- **Event Types**:
  - `progress`: Task progress update (0-100%)
  - `completed`: Task completed successfully
  - `failed`: Task failed with error

## User Experience

### Before
- User clicks "Save Memory"
- Button shows loading spinner
- After ~10-60 seconds, navigates to memories list
- No feedback during processing
- User doesn't know if it's working or stuck

### After
- User clicks "Save Memory"
- Progress card appears immediately
- Shows real-time progress: 10% → 30% → 50% → 75% → 100%
- Displays current processing stage:
  - "Starting episode ingestion..."
  - "Loading schema..."
  - "Extracting entities and relationships..."
  - "Syncing schema..."
  - "Updating communities..."
  - "Episode ingestion completed"
- Automatically navigates to memories list on completion
- Shows helpful error message if processing fails

## Testing

### Manual Testing Steps

1. **Start Backend and Frontend**
   ```bash
   # Terminal 1: Start backend
   cd /Users/tiejunsun/github/mem/memstack
   uv run python -m src.infrastructure.adapters.primary.web.main

   # Terminal 2: Start frontend
   cd /Users/tiejunsun/github/mem/memstack/web
   npm run dev
   ```

2. **Test Episode Creation**
   - Navigate to http://localhost:3000/project/{project_id}/memories
   - Click "New Memory"
   - Enter title and content
   - Click "Save Memory"
   - Observe progress card with real-time updates
   - Verify automatic navigation on completion

3. **Check Browser Console**
   ```
   📡 Connecting to SSE stream for task: {task_id}
   📡 SSE URL: http://localhost:8000/api/v1/tasks/{task_id}/stream
   ✅ SSE connection opened - waiting for events...
   📊 Progress event: {status: "pending", progress: 0}
   📊 Progress event: {status: "processing", progress: 10, message: "Starting episode ingestion..."}
   📊 Progress event: {status: "processing", progress: 30, message: "Extracting entities and relationships..."}
   📊 Progress event: {status: "processing", progress: 50, message: "Syncing schema..."}
   📊 Progress event: {status: "processing", progress: 75, message: "Updating communities..."}
   ✅ Completed event: {status: "Completed", progress: 100, result: {...}}
   ```

4. **Verify Backend Logs**
   ```
   INFO: Task {task_id} added to queue
   INFO: Task {task_id} is active, sending initial progress event
   INFO: Polling task {task_id}: status=PROCESSING, progress=10
   INFO: Task {task_id} status changed: PENDING→PROCESSING, progress: 0→10
   INFO: Polling task {task_id}: status=PROCESSING, progress=30
   ...
   INFO: Polling task {task_id}: status=COMPLETED, progress=100
   INFO: SSE stream completed for task {task_id}
   ```

### Error Testing

1. **Test Error Handling**
   - Create memory with invalid data (if applicable)
   - Verify error message appears
   - Check console for error logs
   - Verify user can try again

2. **Test Connection Issues**
   - Stop backend while processing
   - Verify error message: "Failed to connect to task updates..."
   - Verify user can dismiss error and try again

## Database Migration

A database migration may be needed to add the `task_id` column to the `memories` table:

```sql
ALTER TABLE memories ADD COLUMN task_id VARCHAR NULL;
```

The column is nullable, so existing memories will not be affected.

## Files Modified

### Backend
1. `src/infrastructure/adapters/secondary/queue/redis_queue.py` - Return task_id from add_episode()
2. `src/infrastructure/adapters/primary/web/routers/memories.py` - Return task_id in response
3. `src/infrastructure/adapters/secondary/persistence/models.py` - Add task_id to Memory model
4. `src/application/tasks/episode.py` - Add progress reporting

### Frontend
1. `web/src/pages/project/NewMemory.tsx` - Add SSE streaming and progress UI

## Related Documentation

- SSE Session Fix: `docs/sse_session_fix.md` - Explains SQLAlchemy session lifecycle fix
- SSE Testing Guide: `docs/sse_testing_guide.md` - How to test SSE endpoints
- Community Rebuild SSE Implementation: Similar pattern in `web/src/pages/project/CommunitiesList.tsx`

## Benefits

✅ **Better User Experience**: Users see real-time progress instead of waiting without feedback
✅ **Reduced Support**: Users know the system is working, fewer "is it stuck?" questions
✅ **Error Visibility**: Clear error messages if processing fails
✅ **Consistency**: Same pattern as community rebuild, easier to maintain
✅ **Debugging**: Console logs help troubleshoot issues
✅ **Non-Breaking**: Fallback to old behavior if task_id not returned

## Future Enhancements

- Add ability to cancel in-progress episode creation
- Show estimated time remaining
- Add progress percentage to memories list page
- Bulk import with progress tracking
- Historical task status in task dashboard
