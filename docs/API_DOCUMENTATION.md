# MemStack API Documentation

**Version**: 0.2.0 (Hexagonal Architecture)
**Base URL**: `http://localhost:8000`
**Documentation**: `http://localhost:8000/docs`

## Overview

MemStack provides a RESTful API for managing AI-powered memory with knowledge graph integration. The API is built using FastAPI and follows hexagonal architecture principles for better maintainability and testability.

## Authentication

Most endpoints require authentication using API keys.

### Header Format
```
Authorization: Bearer ms_sk_<64-char-hex>
```

### Example
```bash
curl -H "Authorization: Bearer ms_sk_abc123..." http://localhost:8000/api/v1/memories/
```

## API Endpoints

### Episodes

#### Create Episode
```http
POST /api/v1/episodes/
Content-Type: application/json

{
  "name": "Episode Name",
  "content": "Episode content...",
  "source_description": "text",
  "episode_type": "text",
  "project_id": "proj_123",
  "tenant_id": "tenant_123",
  "user_id": "user_123"
}
```

**Response**: `202 Accepted`
```json
{
  "id": "ep_uuid",
  "status": "processing",
  "message": "Episode queued for ingestion",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### Get Episode
```http
GET /api/v1/episodes/{episode_name}
```

**Response**: `200 OK`
```json
{
  "uuid": "ep_uuid",
  "name": "Episode Name",
  "content": "Episode content...",
  "created_at": "2024-01-01T00:00:00Z",
  "status": "completed"
}
```

#### List Episodes
```http
GET /api/v1/episodes/?limit=50&offset=0&tenant_id=tenant_123&project_id=proj_123
```

**Response**: `200 OK`
```json
{
  "episodes": [...],
  "total": 100,
  "limit": 50,
  "offset": 0,
  "has_more": true
}
```

#### Delete Episode
```http
DELETE /api/v1/episodes/{episode_name}
```

**Response**: `200 OK`
```json
{
  "status": "success",
  "message": "Episode 'name' deleted successfully"
}
```

---

### Search

#### Advanced Search
```http
POST /api/v1/search-enhanced/advanced
Content-Type: application/json

{
  "query": "search query",
  "strategy": "COMBINED_HYBRID_SEARCH_RRF",
  "focal_node_uuid": "entity_uuid",
  "limit": 50,
  "project_id": "proj_123",
  "since": "2024-01-01T00:00:00Z"
}
```

**Response**: `200 OK`
```json
{
  "results": [...],
  "total": 10,
  "search_type": "advanced",
  "strategy": "COMBINED_HYBRID_SEARCH_RRF"
}
```

#### Graph Traversal Search
```http
POST /api/v1/search-enhanced/graph-traversal
Content-Type: application/json

{
  "start_entity_uuid": "entity_uuid",
  "max_depth": 2,
  "relationship_types": ["MENTIONS", "RELATES_TO"],
  "limit": 50
}
```

#### Community Search
```http
POST /api/v1/search-enhanced/community
Content-Type: application/json

{
  "community_uuid": "community_uuid",
  "limit": 100,
  "include_episodes": true
}
```

#### Temporal Search
```http
POST /api/v1/search-enhanced/temporal
Content-Type: application/json

{
  "query": "search query",
  "since": "2024-01-01T00:00:00Z",
  "until": "2024-12-31T23:59:59Z",
  "limit": 50
}
```

#### Faceted Search
```http
POST /api/v1/search-enhanced/faceted
Content-Type: application/json

{
  "query": "search query",
  "entity_types": ["Person", "Organization"],
  "tags": ["important"],
  "limit": 20,
  "offset": 0
}
```

#### Search Capabilities
```http
GET /api/v1/search-enhanced/capabilities
```

Returns available search types and configuration.

---

### Recall

#### Short-Term Recall
```http
POST /api/v1/recall/short
Content-Type: application/json

{
  "window_minutes": 1440,
  "limit": 100,
  "tenant_id": "tenant_123"
}
```

**Response**: `200 OK`
```json
{
  "results": [...],
  "total": 50,
  "window_minutes": 1440
}
```

---

### Data Export & Management

#### Export Data
```http
POST /api/v1/data/export
Content-Type: application/json

{
  "tenant_id": "tenant_123",
  "include_episodes": true,
  "include_entities": true,
  "include_relationships": true,
  "include_communities": true
}
```

**Response**: `200 OK`
```json
{
  "exported_at": "2024-01-01T00:00:00Z",
  "episodes": [...],
  "entities": [...],
  "relationships": [...],
  "communities": [...]
}
```

#### Get Graph Statistics
```http
GET /api/v1/data/stats?tenant_id=tenant_123
```

**Response**: `200 OK`
```json
{
  "entities": 150,
  "episodes": 80,
  "communities": 10,
  "relationships": 200,
  "total_nodes": 240
}
```

#### Cleanup Old Data
```http
POST /api/v1/data/cleanup?dry_run=true&older_than_days=90&tenant_id=tenant_123
```

**Response**: `200 OK`
```json
{
  "dry_run": true,
  "would_delete": 25,
  "cutoff_date": "2024-01-01T00:00:00Z",
  "message": "Would delete 25 episodes older than 90 days"
}
```

---

### Maintenance

#### Incremental Refresh
```http
POST /api/v1/maintenance/refresh/incremental
Content-Type: application/json

{
  "episode_uuids": ["ep_1", "ep_2"],
  "rebuild_communities": false
}
```

#### Deduplicate Entities
```http
POST /api/v1/maintenance/deduplicate
Content-Type: application/json

{
  "similarity_threshold": 0.9,
  "dry_run": true
}
```

#### Invalidate Stale Edges
```http
POST /api/v1/maintenance/invalidate-edges
Content-Type: application/json

{
  "days_since_update": 30,
  "dry_run": true
}
```

#### Get Maintenance Status
```http
GET /api/v1/maintenance/status
```

#### Optimize Graph
```http
POST /api/v1/maintenance/optimize
Content-Type: application/json

{
  "operations": ["incremental_refresh", "deduplicate"],
  "dry_run": true
}
```

---

### Tasks

#### Get Task Statistics
```http
GET /api/v1/tasks/stats
```

**Response**: `200 OK`
```json
{
  "total": 1000,
  "pending": 50,
  "processing": 10,
  "completed": 900,
  "failed": 40,
  "throughput_per_minute": 15.5,
  "error_rate": 4.0
}
```

#### Get Queue Depth
```http
GET /api/v1/tasks/queue-depth
```

**Response**: `200 OK`
```json
[
  {
    "timestamp": "00:00",
    "depth": 50
  },
  {
    "timestamp": "03:00",
    "depth": 45
  }
]
```

#### Get Recent Tasks
```http
GET /api/v1/tasks/recent?status=AllStatuses&limit=50&offset=0
```

#### Get Status Breakdown
```http
GET /api/v1/tasks/status-breakdown
```

#### Retry Task
```http
POST /api/v1/tasks/{task_id}/retry
```

#### Stop Task
```http
POST /api/v1/tasks/{task_id}/stop
```

---

### Memos

#### Create Memo
```http
POST /memos
Content-Type: application/json

{
  "content": "Memo content...",
  "visibility": "PRIVATE",
  "tags": ["important", "work"]
}
```

**Response**: `201 Created`
```json
{
  "id": "memo_uuid",
  "content": "Memo content...",
  "visibility": "PRIVATE",
  "tags": ["important", "work"],
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### List Memos
```http
GET /memos?limit=20&offset=0
```

#### Get Memo
```http
GET /memos/{memo_id}
```

#### Update Memo
```http
PATCH /memos/{memo_id}
Content-Type: application/json

{
  "content": "Updated content",
  "visibility": "PUBLIC",
  "tags": ["updated"]
}
```

#### Delete Memo
```http
DELETE /memos/{memo_id}
```

---

### AI Tools

#### Optimize Content
```http
POST /api/v1/ai/optimize
Content-Type: application/json

{
  "content": "Original content...",
  "instruction": "Improve clarity and fix grammar"
}
```

**Response**: `200 OK`
```json
{
  "content": "Optimized content..."
}
```

#### Generate Title
```http
POST /api/v1/ai/generate-title
Content-Type: application/json

{
  "content": "Long content that needs a title..."
}
```

**Response**: `200 OK`
```json
{
  "title": "Generated Title"
}
```

---

## Data Models

### Episode
```typescript
{
  uuid: string;
  name: string;
  content: string;
  source_description: string;
  created_at: string;
  valid_at: string;
  tenant_id: string;
  project_id: string;
  user_id: string;
  status: "processing" | "completed" | "failed";
}
```

### Entity
```typescript
{
  uuid: string;
  name: string;
  entity_type: string;
  summary: string;
  tenant_id: string;
  project_id: string;
  created_at: string;
}
```

### Community
```typescript
{
  uuid: string;
  name: string;
  summary: string;
  member_count: number;
  tenant_id: string;
  project_id: string;
  formed_at: string;
  created_at: string;
}
```

### Memory
```typescript
{
  id: string;
  project_id: string;
  title: string;
  content: string;
  content_type: string;
  tags: string[];
  entities: object[];
  relationships: object[];
  author_id: string;
  collaborators: string[];
  is_public: boolean;
  status: "ENABLED" | "DISABLED";
  processing_status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
  created_at: string;
  updated_at: string;
}
```

### TaskLog
```typescript
{
  id: string;
  group_id: string;
  task_type: string;
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
  created_at: string;
  started_at: string;
  completed_at: string;
  error_message: string;
  worker_id: string;
  retry_count: number;
  entity_id: string;
  entity_type: string;
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid request data"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid authentication credentials"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

API rate limits are configured per API key:
- Free tier: 100 requests/minute
- Pro tier: 1000 requests/minute
- Enterprise tier: Custom limits

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1609459200
```

---

## WebSocket API

For real-time updates, MemStack provides WebSocket connections:

### Connect to Task Updates
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/tasks');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Task update:', update);
};
```

---

## SDKs

Official SDKs are available:
- **Python**: `pip install memstack`
- **JavaScript**: `npm install @memstack/sdk`

See SDK documentation for more details.

---

## Testing

### Using cURL
```bash
# Create episode
curl -X POST http://localhost:8000/api/v1/episodes/ \
  -H "Authorization: Bearer ms_sk_abc123..." \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "content": "Test content"}'

# Search
curl -X POST http://localhost:8000/api/v1/search-enhanced/advanced \
  -H "Authorization: Bearer ms_sk_abc123..." \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "limit": 10}'
```

### Using Python
```python
import requests

headers = {
    "Authorization": "Bearer ms_sk_abc123...",
    "Content-Type": "application/json"
}

# Create episode
response = requests.post(
    "http://localhost:8000/api/v1/episodes/",
    headers=headers,
    json={"name": "Test", "content": "Test content"}
)

print(response.json())
```

---

## Changelog

### Version 0.2.0 (Current)
- Migrated to hexagonal architecture
- Added enhanced search capabilities
- Improved error handling
- Added comprehensive API documentation

### Version 0.1.0
- Initial release
- Basic CRUD operations
- Graphiti integration
