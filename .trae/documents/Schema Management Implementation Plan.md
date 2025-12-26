# Schema Management Implementation Plan

## Backend Implementation

### 1. Database Models (`server/db_models.py`)
Add new tables to store user-defined schema definitions scoped by project.

- **EntityType**: Stores custom entity definitions
  - `id` (PK), `project_id` (FK), `name`, `description`, `schema` (JSON - Pydantic fields definition)
- **EdgeType**: Stores custom edge definitions
  - `id` (PK), `project_id` (FK), `name`, `description`, `schema` (JSON - Pydantic fields definition)
- **EdgeTypeMap**: Stores valid relationships between entities
  - `id` (PK), `project_id` (FK), `source_type`, `target_type`, `edge_type`

### 2. Pydantic Models (`server/models/schema.py`)
Create DTOs for API validation and serialization.
- `EntityTypeCreate`, `EntityTypeUpdate`, `EntityTypeResponse`
- `EdgeTypeCreate`, `EdgeTypeUpdate`, `EdgeTypeResponse`
- `EdgeMapCreate`, `EdgeMapResponse`

### 3. API Endpoints (`server/api/schema.py`)
Implement CRUD operations for schema management.
- `GET /api/v1/projects/{project_id}/schema/entities`
- `POST /api/v1/projects/{project_id}/schema/entities`
- `GET /api/v1/projects/{project_id}/schema/edges`
- `POST /api/v1/projects/{project_id}/schema/edges`
- `GET /api/v1/projects/{project_id}/schema/mappings`
- `POST /api/v1/projects/{project_id}/schema/mappings`

### 4. Graphiti Service Integration (`server/services/graphiti_service.py`)
Update `add_episode` to use dynamic schema loading.
- Implement `get_project_schema(project_id)`: Fetches definitions from DB and converts JSON schemas to dynamic Pydantic models using `pydantic.create_model`.
- Modify `add_episode` to fetch and pass these dynamic types to `graphiti.add_episode`.

## Frontend Implementation

### 1. API Client (`web/src/services/api.ts`)
Add methods for schema management endpoints.

### 2. New Pages (`web/src/pages/project/schema/`)
Implement the UI based on the provided HTML templates.
- **SchemaOverview.tsx**: Dashboard showing summary of types.
- **EntityTypeList.tsx**: List view with Create/Edit modal for Entity Types.
- **EdgeTypeList.tsx**: List view with Create/Edit modal for Edge Types.
- **EdgeMapList.tsx**: Matrix/List view for managing allowed edges between entities.

### 3. Routing (`web/src/App.tsx`)
Add new routes to the Project Workbench section.
- `/project/:projectId/schema` (Redirects to overview)
- `/project/:projectId/schema/overview`
- `/project/:projectId/schema/entities`
- `/project/:projectId/schema/edges`
- `/project/:projectId/schema/mapping`

### 4. Navigation (`web/src/layouts/ProjectLayout.tsx`)
Update the sidebar to include the "Schema" section with links to the new pages.
