I will refactor the frontend to match the provided static designs and enhance the backend to support the new dashboard requirements.

### Phase 1: Backend Enhancements (Python/FastAPI)
The existing backend already supports most requirements. I will add a missing endpoint for project-specific statistics.

1.  **Create Project Stats Endpoint**
    *   **File**: `server/api/projects.py`
    *   **Action**: Add `GET /api/v1/projects/{project_id}/stats`.
    *   **Logic**: Return aggregated data for the Project Workbench dashboard:
        *   `memory_count`: Total memories in the project.
        *   `storage_used`: Calculated or mocked storage usage.
        *   `collaborators`: Count of members.
        *   `active_nodes`: (Mocked) Number of active graph nodes.
        *   `recent_activity`: (Mocked) List of recent actions.

### Phase 2: Frontend Foundation (React/Vite/Tailwind)
I will configure the frontend to match the visual style of the static files.

1.  **Dependencies & Assets**
    *   **File**: `web/index.html`
    *   **Action**: Add Google Fonts (Inter, Noto Sans SC) and Material Symbols CDN links.
    *   **File**: `web/src/index.css` / `web/tailwind.config.js` (if exists)
    *   **Action**: Configure Tailwind theme colors (`primary`, `background-light`, `surface-dark`, etc.) and fonts to match `docs/statics`.

2.  **Layout Architecture**
    *   **Create**: `web/src/layouts/TenantLayout.tsx`
        *   Sidebar with Tenant navigation (Overview, Projects, Users, Billing).
        *   Header with Breadcrumbs and User Profile.
    *   **Create**: `web/src/layouts/ProjectLayout.tsx`
        *   Sidebar with Project navigation (Overview, Memories, Team, Settings).
        *   Header with Project context.

### Phase 3: Frontend Page Implementation
I will rebuild the core pages using the new layouts and components.

1.  **Tenant Console Pages**
    *   **Create**: `web/src/pages/tenant/TenantOverview.tsx`
        *   Matches `docs/statics/home/code.html`.
        *   Fetches data from `/api/v1/tenants/{id}/stats`.
    *   **Create**: `web/src/pages/tenant/ProjectList.tsx`
        *   Matches `docs/statics/tenant console/project management/code.html`.
        *   Fetches projects from `/api/v1/projects`.

2.  **Project Workbench Pages**
    *   **Create**: `web/src/pages/project/ProjectOverview.tsx`
        *   Matches `docs/statics/project workbench/code.html`.
        *   Fetches data from the new `/api/v1/projects/{id}/stats`.
    *   **Update**: `web/src/pages/project/MemoryList.tsx` (Refactor existing `SpaceDashboard` or create new)
        *   Implement the "Active Memories" table design.

3.  **Routing & App Entry**
    *   **File**: `web/src/App.tsx`
    *   **Action**: Define routes:
        *   `/tenant` -> `TenantLayout` -> `TenantOverview`
        *   `/tenant/projects` -> `TenantLayout` -> `ProjectList`
        *   `/project/:projectId` -> `ProjectLayout` -> `ProjectOverview`
        *   `/project/:projectId/memories` -> `ProjectLayout` -> `MemoryList`

### Phase 4: Integration & Verification
1.  **API Integration**: Ensure `web/src/services/api.ts` has methods for the new stats endpoints.
2.  **Verification**: Launch the dev server and verify the new UI against the static designs and ensure data loads correctly from the backend.
