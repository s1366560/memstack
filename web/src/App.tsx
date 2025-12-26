import { Routes, Route, Navigate } from 'react-router-dom'
import { Login } from './pages/Login'
import { TenantLayout } from './layouts/TenantLayout'
import { TenantOverview } from './pages/tenant/TenantOverview'
import { ProjectList } from './pages/tenant/ProjectList'
import { UserList } from './pages/tenant/UserList'
import { UserProfile } from './pages/UserProfile'
import { NewProject } from './pages/tenant/NewProject'
import { NewTenant } from './pages/tenant/NewTenant'
import { TenantSettings } from './pages/tenant/TenantSettings'
import { ProjectLayout } from './layouts/ProjectLayout'
import { ProjectOverview } from './pages/project/ProjectOverview'
import { MemoryList } from './pages/project/MemoryList'
import { NewMemory } from './pages/project/NewMemory'
import { MemoryDetail } from './pages/project/MemoryDetail'
import { MemoryGraph } from './pages/project/MemoryGraph'
import { EntitiesList } from './pages/project/EntitiesList'
import { CommunitiesList } from './pages/project/CommunitiesList'
import { EnhancedSearch } from './pages/project/EnhancedSearch'
import { Maintenance } from './pages/project/Maintenance'
import { SchemaLayout } from './layouts/SchemaLayout'
import SchemaOverview from './pages/project/schema/SchemaOverview'
import EntityTypeList from './pages/project/schema/EntityTypeList'
import EdgeTypeList from './pages/project/schema/EdgeTypeList'
import EdgeMapList from './pages/project/schema/EdgeMapList'
import { useAuthStore } from './stores/auth'
import './App.css'

function App() {
    const { isAuthenticated } = useAuthStore()

    return (
        <Routes>
            <Route
                path="/login"
                element={!isAuthenticated ? <Login /> : <Navigate to="/" replace />}
            />

            {/* Protected Routes */}
            {/* Redirect root to tenant overview if authenticated */}
            <Route
                path="/"
                element={isAuthenticated ? <Navigate to="/tenant" replace /> : <Navigate to="/login" replace />}
            />

            <Route path="/tenants/new" element={isAuthenticated ? <NewTenant /> : <Navigate to="/login" replace />} />

            {/* Tenant Console */}
            <Route path="/tenant" element={isAuthenticated ? <TenantLayout /> : <Navigate to="/login" replace />}>
                <Route index element={<TenantOverview />} />

                {/* Generic routes (use currentTenant from store) */}
                <Route path="projects" element={<ProjectList />} />
                <Route path="projects/new" element={<NewProject />} />
                <Route path="users" element={<UserList />} />
                <Route path="profile" element={<UserProfile />} />
                <Route path="analytics" element={<div className="p-8 text-slate-500">Analytics (Coming Soon)</div>} />
                <Route path="billing" element={<div className="p-8 text-slate-500">Billing (Coming Soon)</div>} />
                <Route path="settings" element={<TenantSettings />} />

                {/* Tenant specific routes */}
                <Route path=":tenantId" element={<TenantOverview />} />
                <Route path=":tenantId/projects" element={<ProjectList />} />
                <Route path=":tenantId/projects/new" element={<NewProject />} />
                <Route path=":tenantId/users" element={<UserList />} />
                <Route path=":tenantId/analytics" element={<div className="p-8 text-slate-500">Analytics (Coming Soon)</div>} />
                <Route path=":tenantId/billing" element={<div className="p-8 text-slate-500">Billing (Coming Soon)</div>} />
                <Route path=":tenantId/settings" element={<TenantSettings />} />
            </Route>

            {/* Project Workbench */}
            <Route path="/project/:projectId" element={isAuthenticated ? <ProjectLayout /> : <Navigate to="/login" replace />}>
                <Route index element={<ProjectOverview />} />
                <Route path="memories" element={<MemoryList />} />
                <Route path="memories/new" element={<NewMemory />} />
                <Route path="memory/:memoryId" element={<MemoryDetail />} />
                {/* <Route path="search" element={<SearchPage />} /> */}
                <Route path="graph" element={<MemoryGraph />} />
                <Route path="entities" element={<EntitiesList />} />
                <Route path="communities" element={<CommunitiesList />} />
                <Route path="advanced-search" element={<EnhancedSearch />} />
                <Route path="search" element={<Navigate to="advanced-search" replace />} />
                <Route path="maintenance" element={<Maintenance />} />
                <Route path="schema" element={<SchemaLayout />}>
                    <Route index element={<SchemaOverview />} />
                    <Route path="entities" element={<EntityTypeList />} />
                    <Route path="edges" element={<EdgeTypeList />} />
                    <Route path="mapping" element={<EdgeMapList />} />
                </Route>
                <Route path="team" element={<div className="p-8 text-slate-500">Team Management (Coming Soon)</div>} />
                <Route path="settings" element={<div className="p-8 text-slate-500">Project Settings (Coming Soon)</div>} />
                <Route path="support" element={<div className="p-8 text-slate-500">Support (Coming Soon)</div>} />
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    )
}

export default App
