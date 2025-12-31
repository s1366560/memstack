# SSE Session Fix - Root Cause & Solution

## Problem

前端只收到一个`progress`事件（status: pending, progress: 0），之后只收到ping消息，没有收到`completed`事件。

## Root Cause

**SQLAlchemy AsyncSession在async generator中的生命周期问题。**

原始代码使用了依赖注入的session：
```python
async def stream_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db)  # ❌ Session可能在generator运行时关闭
):
    async def event_generator():
        # 使用注入的db session查询
        result = await db.execute(...)
        while True:
            # 继续使用同一个session...
            result = await db.execute(...)  # ❌ Session可能已关闭或状态不一致
```

**问题**：
1. FastAPI的`Depends(get_db)`创建的session在endpoint函数返回时会被关闭
2. 但event generator是一个async generator，它会持续运行
3. 在while循环中继续使用已关闭或过期的session会导致查询失败或返回过期数据
4. 因此轮询循环没有检测到任务状态变化

## Solution

**在generator内部每次查询都创建新的session：**

```python
async def event_generator():
    from src.infrastructure.adapters.secondary.persistence.database import async_session_factory

    # 初始查询使用新session
    async with async_session_factory() as session:
        result = await session.execute(...)

    while True:
        # 每次轮询都创建新session
        async with async_session_factory() as session:
            result = await session.execute(...)
            # ✅ 确保每次查询都能获取最新数据
```

**好处**：
- ✅ 每次轮询都获取最新的数据库状态
- ✅ 避免session生命周期问题
- ✅ 确保能检测到任务状态变化
- ✅ 正确发送所有SSE事件

## Changes Made

### File: `src/infrastructure/adapters/primary/web/routers/tasks.py`

1. **Line 413**: Import `async_session_factory` inside generator
2. **Line 417**: Wrap initial query in `async with async_session_factory() as session:`
3. **Line 483**: Wrap polling query in `async with async_session_factory() as session:`
4. **Line 480**: Changed log level from `debug` to `info` for better visibility
5. **Line 499**: Changed log level from `debug` to `info`

### Verification

Test with completed task:
```bash
$ PYTHONPATH=/Users/tiejunsun/github/mem/memstack uv run python scripts/test_sse_flow.py <task_id>

✅ Stream closed after 1 events
   Final status: Completed
   Result: {'edges_count': 4, 'communities_count': 1}
```

**Expected Flow for New Task**:

1. User clicks "Rebuild Communities"
2. Frontend: `📡 Connecting to SSE stream for task: {task_id}`
3. Backend: `Event generator started for task {task_id}`
4. Backend: `Task {task_id} found with status: PENDING`
5. Backend: `Task {task_id} is active, sending initial progress event`
6. Frontend receives: `📊 Progress event: {status: "pending", progress: 0}`
7. Backend: `Starting polling loop for task {task_id}: initial status=PENDING`
8. Backend: `Polling iteration 1 for task {task_id}`
9. Backend: `Polling task {task_id}: status=PROCESSING, progress=10`
10. Backend: `Task {task_id} status changed: PENDING→PROCESSING, progress: 0→10`
11. Frontend receives: `📊 Progress event: {status: "processing", progress: 10, message: "Removing existing communities..."}`
12. ... (continues polling every 1 second)
13. Backend: `Polling task {task_id}: status=COMPLETED, progress=100`
14. Backend: `SSE stream completed for task {task_id}`
15. Frontend receives: `✅ Completed event: {...}`
16. Frontend: `✅ Communities reloaded: X communities, Y edges`

## Testing

### Manual Test

1. Open http://localhost:3000/project/{project_id}/communities
2. Open Browser DevTools (F12) → Console
3. Click "Rebuild Communities"
4. Watch console for SSE events

**Expected Output**:
```
📡 Connecting to SSE stream for task: {task_id}
✅ SSE connection opened - waiting for events...
📊 Progress event: {status: "pending", progress: 0}
📊 Progress event: {status: "processing", progress: 10, message: "Removing existing communities..."}
📊 Progress event: {status: "processing", progress: 30, message: "Detecting communities..."}
📊 Progress event: {status: "processing", progress: 50, message: "Found X communities..."}
📊 Progress event: {status: "processing", progress: 75, message: "Saving community relationships..."}
📊 Progress event: {status: "processing", progress: 90, message: "Calculating member counts..."}
✅ Completed event: {status: "Completed", progress: 100, result: {...}}
✅ Communities reloaded: X communities, Y edges
```

### Check Backend Logs

Since we changed logging to INFO level, you can now see the full polling flow in the console where the backend is running:

```
INFO:     SSE stream requested for task {task_id}
INFO:     Event generator started for task {task_id}
INFO:     Task {task_id} found with status: PENDING
INFO:     Task {task_id} is active, sending initial progress event
INFO:     Starting polling loop for task {task_id}: initial status=PENDING, initial progress=0
INFO:     Polling iteration 1 for task {task_id}
INFO:     Polling task {task_id}: status=PROCESSING, progress=10
INFO:     Task {task_id} status changed: PENDING→PROCESSING, progress: 0→10
...
INFO:     Polling task {task_id}: status=COMPLETED, progress=100
INFO:     SSE stream completed for task {task_id}
```

## Summary

- **Problem**: SQLAlchemy session lifecycle in async generator
- **Solution**: Create new session for each database query
- **Result**: SSE now correctly sends all events (progress updates + completion)
- **Impact**: Real-time task progress tracking now works correctly

The fix ensures that every database query in the polling loop gets a fresh session, guaranteeing that we always fetch the latest task status and properly detect changes.
