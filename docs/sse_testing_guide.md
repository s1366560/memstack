# SSE Testing Guide

## Quick Test

### 1. Test SSE Endpoint Directly

```bash
# Test with an already completed task
PYTHONPATH=/Users/tiejunsun/github/mem/memstack uv run python scripts/test_eventsource.py ca855bc7-2754-4ec2-8854-f188298f5d79
```

Expected output:
```
📡 Connecting to SSE: http://localhost:8000/api/v1/tasks/.../stream
======================================================================
✅ Connected (HTTP 200)
   Content-Type: text/event-stream; charset=utf-8
======================================================================

📨 Event: completed
📦 Data: {...}
   ✓ Status: Completed
   ✓ Progress: 100%
   ✓ Message: Community rebuild completed successfully
```

### 2. Test in Browser

1. Open http://localhost:3000/project/{project_id}/communities
2. Open Browser Developer Tools (F12)
3. Go to Console tab
4. Click "Rebuild Communities" button
5. Watch console for:

**Expected Console Output:**
```
📡 Connecting to SSE stream for task: {task_id}
📡 SSE URL: http://localhost:8000/api/v1/tasks/{task_id}/stream
✅ SSE connection opened - waiting for events...
📊 Progress event: {id: "...", status: "processing", progress: 10, message: "Removing existing communities..."}
📊 Progress event: {id: "...", status: "processing", progress: 30, message: "Detecting communities..."}
...
✅ Completed event: {id: "...", status: "Completed", progress: 100, result: {...}}
✅ Communities reloaded: X communities, Y edges
```

**Troubleshooting Console Output:**

If you see:
```
❌ SSE connection error: Event
   ReadyState: 2
   Connection CLOSED - check for CORS errors
```

This means EventSource failed to connect. Check:
1. Backend is running on port 8000
2. No CORS errors in browser console
3. Network tab shows the SSE request

## Debugging Steps

### Step 1: Verify Backend is Running
```bash
curl http://localhost:8000/health
```

Should return: `{"status":"ok","version":"0.2.0"}`

### Step 2: Verify Task Exists
```bash
PYTHONPATH=/Users/tiejunsun/github/mem/memstack uv run python scripts/check_task.py {task_id}
```

### Step 3: Test SSE Endpoint with curl
```bash
curl -N -H "Accept: text/event-stream" \
  'http://localhost:8000/api/v1/tasks/{task_id}/stream' \
  --max-time 5
```

Should show:
```
event: completed
data: {"status":"Completed",...}
```

### Step 4: Check Browser Network Tab
1. Open DevTools → Network tab
2. Filter by "EventStream"
3. Look for request to `/tasks/{task_id}/stream`
4. Check:
   - Status: 200
   - Type: `eventsource`
   - Response headers include `Content-Type: text/event-stream`

### Step 5: Check Browser Console for Errors
Look for:
- CORS errors
- Mixed content errors (https vs http)
- Network errors
- JSON parse errors

## Common Issues & Solutions

### Issue 1: "Rebuild Scheduled" Stuck

**Symptom:** UI shows "Rebuild Scheduled" with "Cancel" button

**Cause:** EventSource not receiving events

**Solutions:**
1. Check browser console for errors
2. Verify SSE endpoint works with curl
3. Check ReadyState in console logs
4. Look for CORS errors

### Issue 2: CORS Error

**Symptom:**
```
Access to resource at 'http://localhost:8000/...' from origin 'http://localhost:3000' has been blocked by CORS policy
```

**Solution:** Backend CORS is configured with `allow_origins=["*"]`, so this shouldn't happen. If it does, check:
```bash
# Check CORS settings
grep -r "api_allowed_origins" src/configuration/config.py
```

### Issue 3: EventSource ReadyState = 2 (CLOSED)

**Symptom:** Connection closes immediately

**Possible Causes:**
1. Backend not running
2. Wrong URL (port mismatch)
3. Authentication required (EventSource doesn't support custom headers)

**Solution:** SSE endpoint should NOT require authentication. Verify:
```python
# In tasks.py, the endpoint should NOT have:
# Depends(get_current_user)
```

### Issue 4: No Events Received

**Symptom:** Connection opens but no events

**Possible Causes:**
1. Task not found in database
2. Backend logs show errors
3. Database connection issue

**Solution:**
```bash
# Check backend logs
tail -f /tmp/backend.log

# Look for:
# "SSE stream requested for task ..."
# "Event generator started for task ..."
# "Task ... found with status: ..."
```

## Verify Fix Works

After making changes, verify the complete flow:

1. **Trigger Rebuild:**
   ```bash
   # In browser, click "Rebuild Communities"
   # Note the task_id from console
   ```

2. **Monitor Progress:**
   ```bash
   # Watch console for progress events:
   📊 Progress event: {progress: 10, message: "Removing existing communities..."}
   📊 Progress event: {progress: 30, message: "Detecting communities..."}
   📊 Progress event: {progress: 50, message: "Found X communities..."}
   📊 Progress event: {progress: 75, message: "Saving community relationships..."}
   📊 Progress event: {progress: 90, message: "Calculating member counts..."}
   ```

3. **Verify Completion:**
   ```bash
   # Console should show:
   ✅ Completed event: {status: "Completed", progress: 100, result: {...}}
   ✅ Communities reloaded: X communities, Y edges
   ```

4. **Verify UI Updates:**
   - Task status card shows "Rebuild Completed Successfully"
   - Progress bar at 100%
   - Result statistics shown (communities count, edges count)
   - Communities list refreshes automatically
   - Status card disappears after 5 seconds

## Code Locations

- **Backend SSE Endpoint:** `src/infrastructure/adapters/primary/web/routers/tasks.py:378-560`
- **Frontend EventSource:** `web/src/pages/project/CommunitiesList.tsx:94-244`
- **Service Method:** `web/src/services/graphitiService.ts:189-199`

## Summary

The SSE implementation should provide:
- ✅ Real-time progress updates (every 1 second)
- ✅ Instant completion notifications
- ✅ Automatic UI refresh on completion
- ✅ Graceful error handling with fallback
- ✅ Proper cleanup of EventSource connections

If issues persist, check:
1. Backend logs for errors
2. Browser console for errors
3. Network tab for failed requests
4. Task status in database
