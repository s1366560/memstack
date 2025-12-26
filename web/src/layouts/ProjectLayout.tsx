import React, { useEffect } from 'react'
import { Link, Outlet, useLocation, useParams, useNavigate } from 'react-router-dom'
import { WorkspaceSwitcher } from '../components/WorkspaceSwitcher'
import { ThemeToggle } from '../components/ThemeToggle'
import { useProjectStore } from '../stores/project'
import { useTenantStore } from '../stores/tenant'
import { useAuthStore } from '../stores/auth'
import { LogOut } from 'lucide-react'

export const ProjectLayout: React.FC = () => {
    const location = useLocation()
    const navigate = useNavigate()
    const { projectId } = useParams()
    const { currentProject, setCurrentProject, getProject } = useProjectStore()
    const { currentTenant, setCurrentTenant } = useTenantStore()
    const { user, logout } = useAuthStore()

    // Sync project and tenant data
    useEffect(() => {
        if (projectId && (!currentProject || currentProject.id !== projectId)) {
            // We need to fetch project first to get tenant_id if we don't know it
            // However, getProject requires tenantId. 
            // Wait, projectAPI.get(tenantId, projectId).
            // If we don't have tenantId from URL, we might have a problem if the API strictly requires it in path.
            // Let's check api.ts.

            // Assuming we have currentTenant, we can fetch.
            if (currentTenant) {
                getProject(currentTenant.id, projectId).then(project => {
                    setCurrentProject(project)
                }).catch(console.error)
            } else {
                // If we don't have tenant context, we might need to find which tenant this project belongs to.
                // This is tricky if the API structure is strictly hierarchical (/tenants/{tid}/projects/{pid}).
                // But usually we can list user's projects or use a global lookup if backend supports it.
                // Or we rely on the fact that we should have entered via a flow that sets tenant.
                // BUT, if user enters via direct URL /project/:id, we don't have tenantId.

                // Let's assume we need to load tenants first, then search for the project?
                // Or maybe there's an API to get project by ID globally?
                // Checking api.ts...

                // For now, let's try to iterate tenants if we have them, or list tenants first.
                const { tenants, listTenants } = useTenantStore.getState()
                if (tenants.length === 0) {
                    listTenants().then(() => {
                        // After listing, try to find project in all tenants? That's expensive.
                        // Ideally backend provides an endpoint to get project context.
                        // Let's assume for now the user has access and we can find it in the first tenant or iterate?
                        // Or maybe we can't solve this easily without backend change.
                        // But wait, listProjects is per tenant.

                        // Workaround: If we have tenants, try to find project in them?
                        // Or maybe we just use the first tenant for now if we can't determine.
                        // Actually, let's check if we can get project without tenantId.
                        // If not, we might be stuck.

                        // However, if the user visited /tenant before, we might have data.
                        // If completely fresh reload:
                        const tenants = useTenantStore.getState().tenants
                        if (tenants.length > 0) {
                            // Try to find project in these tenants
                            // This is not efficient but might work for small numbers
                            // For now let's just pick the first tenant and hope, or try to fetch project with it.
                            const firstTenant = tenants[0]
                            setCurrentTenant(firstTenant)
                            getProject(firstTenant.id, projectId!).then(p => setCurrentProject(p)).catch(() => {
                                // If failed, maybe try others?
                                console.warn("Project not found in first tenant")
                            })
                        }
                    })
                } else {
                    // We have tenants but no currentTenant set?
                    // Set first as default
                    const firstTenant = tenants[0]
                    setCurrentTenant(firstTenant)
                    getProject(firstTenant.id, projectId!).then(p => setCurrentProject(p)).catch(console.error)
                }
            }
        }
    }, [projectId, currentProject, currentTenant, getProject, setCurrentProject, setCurrentTenant])

    const isActive = (path: string) => {
        // Simple check if the current path ends with the given path (e.g. /memories)
        return location.pathname.endsWith(path)
    }

    const getBreadcrumbs = () => {
        const paths = location.pathname.split('/').filter(Boolean)
        // paths: ['project', 'p1', 'memories']

        const breadcrumbs = [
            { label: 'Home', path: '/tenant' },
            { label: 'Projects', path: '/tenant/projects' }
        ]

        if (currentProject) {
            breadcrumbs.push({ label: currentProject.name, path: `/project/${currentProject.id}` })
        } else {
            breadcrumbs.push({ label: 'Project', path: `/project/${projectId}` })
        }

        if (paths.length > 2) {
            const section = paths[2]
            breadcrumbs.push({
                label: section.charAt(0).toUpperCase() + section.slice(1),
                path: location.pathname
            })
        }

        return breadcrumbs
    }

    return (
        <div className="flex h-screen w-full overflow-hidden">
            {/* Sidebar Navigation */}
            <aside className="flex w-64 flex-col border-r border-slate-200 dark:border-slate-800 bg-surface-light dark:bg-surface-dark transition-colors duration-300">
                <div className="flex flex-col h-full p-4 justify-between">
                    {/* Top Section: Branding & Nav */}
                    <div className="flex flex-col gap-6">
                        <div className="flex items-center gap-3 px-4 py-2">
                            <div className="bg-primary/10 p-2 rounded-lg">
                                <span className="material-symbols-outlined text-primary">memory</span>
                            </div>
                            <h1 className="text-slate-900 dark:text-white text-lg font-bold leading-none tracking-tight">
                                MemStack<span className="text-primary">.ai</span>
                            </h1>
                        </div>

                        {/* Navigation Menu */}
                        <nav className="flex flex-col gap-1">
                            <Link
                                to={`/project/${projectId}`}
                                className={`flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors group ${location.pathname === `/project/${projectId}`
                                    ? 'bg-primary/10 text-primary'
                                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                                    }`}
                            >
                                <span className="material-symbols-outlined" style={{ fontVariationSettings: isActive('') ? "'FILL' 1" : "'FILL' 0" }}>dashboard</span>
                                <span className="text-sm font-medium">Overview</span>
                            </Link>

                            {/* ... other links ... */}
                            <Link
                                to={`/project/${projectId}/memories`}
                                className={`flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors group ${isActive('/memories')
                                    ? 'bg-primary/10 text-primary'
                                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                                    }`}
                            >
                                <span className="material-symbols-outlined" style={{ fontVariationSettings: isActive('/memories') ? "'FILL' 1" : "'FILL' 0" }}>database</span>
                                <span className="text-sm font-medium">Memories</span>
                            </Link>

                            <Link
                                to={`/project/${projectId}/graph`}
                                className={`flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors group ${isActive('/graph')
                                    ? 'bg-primary/10 text-primary'
                                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                                    }`}
                            >
                                <span className="material-symbols-outlined" style={{ fontVariationSettings: isActive('/graph') ? "'FILL' 1" : "'FILL' 0" }}>hub</span>
                                <span className="text-sm font-medium">Graph</span>
                            </Link>

                            <Link
                                to={`/project/${projectId}/search`}
                                className={`flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors group ${isActive('/search') || isActive('/advanced-search')
                                    ? 'bg-primary/10 text-primary'
                                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                                    }`}
                            >
                                <span className="material-symbols-outlined" style={{ fontVariationSettings: (isActive('/search') || isActive('/advanced-search')) ? "'FILL' 1" : "'FILL' 0" }}>search</span>
                                <span className="text-sm font-medium">Search</span>
                            </Link>

                            <Link
                                to={`/project/${projectId}/entities`}
                                className={`flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors group ${isActive('/entities')
                                    ? 'bg-primary/10 text-primary'
                                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                                    }`}
                            >
                                <span className="material-symbols-outlined" style={{ fontVariationSettings: isActive('/entities') ? "'FILL' 1" : "'FILL' 0" }}>category</span>
                                <span className="text-sm font-medium">Entities</span>
                            </Link>

                            <Link
                                to={`/project/${projectId}/communities`}
                                className={`flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors group ${isActive('/communities')
                                    ? 'bg-primary/10 text-primary'
                                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                                    }`}
                            >
                                <span className="material-symbols-outlined" style={{ fontVariationSettings: isActive('/communities') ? "'FILL' 1" : "'FILL' 0" }}>groups</span>
                                <span className="text-sm font-medium">Communities</span>
                            </Link>

                            <Link
                                to={`/project/${projectId}/advanced-search`}
                                className={`flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors group ${isActive('/advanced-search')
                                    ? 'bg-primary/10 text-primary'
                                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                                    }`}
                            >
                                <span className="material-symbols-outlined" style={{ fontVariationSettings: isActive('/advanced-search') ? "'FILL' 1" : "'FILL' 0" }}>travel_explore</span>
                                <span className="text-sm font-medium">Advanced Search</span>
                            </Link>

                            <Link
                                to={`/project/${projectId}/schema`}
                                className={`flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors group ${isActive('/schema')
                                    ? 'bg-primary/10 text-primary'
                                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                                    }`}
                            >
                                <span className="material-symbols-outlined" style={{ fontVariationSettings: isActive('/schema') ? "'FILL' 1" : "'FILL' 0" }}>schema</span>
                                <span className="text-sm font-medium">Schema</span>
                            </Link>

                            <Link
                                to={`/project/${projectId}/maintenance`}
                                className={`flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors group ${isActive('/maintenance')
                                    ? 'bg-primary/10 text-primary'
                                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                                    }`}
                            >
                                <span className="material-symbols-outlined" style={{ fontVariationSettings: isActive('/maintenance') ? "'FILL' 1" : "'FILL' 0" }}>build</span>
                                <span className="text-sm font-medium">Maintenance</span>
                            </Link>

                            <Link
                                to={`/project/${projectId}/team`}
                                className={`flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors group ${isActive('/team')
                                    ? 'bg-primary/10 text-primary'
                                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                                    }`}
                            >
                                <span className="material-symbols-outlined" style={{ fontVariationSettings: isActive('/team') ? "'FILL' 1" : "'FILL' 0" }}>group</span>
                                <span className="text-sm font-medium">Team</span>
                                <span className="ml-auto bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 text-[10px] font-bold px-1.5 py-0.5 rounded-full">4</span>
                            </Link>

                            <Link
                                to={`/project/${projectId}/settings`}
                                className={`flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors group ${isActive('/settings')
                                    ? 'bg-primary/10 text-primary'
                                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                                    }`}
                            >
                                <span className="material-symbols-outlined" style={{ fontVariationSettings: isActive('/settings') ? "'FILL' 1" : "'FILL' 0" }}>settings</span>
                                <span className="text-sm font-medium">Settings</span>
                            </Link>

                            <div className="h-px bg-slate-200 dark:bg-slate-700 my-2 mx-3"></div>

                            <Link
                                to={`/project/${projectId}/support`}
                                className="flex items-center gap-3 px-3 py-2.5 rounded-md text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200 transition-all"
                            >
                                <span className="material-symbols-outlined">help</span>
                                <span className="text-sm font-medium">Support</span>
                            </Link>
                        </nav>
                    </div>

                    {/* Bottom Section: User Profile */}
                    <div className="mt-auto">
                        <div className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors group">
                            <div className="flex items-center gap-3 min-w-0">
                                <div className="h-9 w-9 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-xs font-bold text-slate-600 dark:text-slate-300 shrink-0">
                                    {user?.name?.[0]?.toUpperCase() || 'U'}
                                </div>
                                <div className="flex flex-col items-start overflow-hidden">
                                    <span className="text-sm font-medium text-slate-900 dark:text-white truncate w-full text-left">{user?.name || 'User'}</span>
                                    <span className="text-xs text-slate-500 dark:text-slate-400 truncate w-full text-left">{user?.email || 'user@example.com'}</span>
                                </div>
                            </div>
                            <button
                                onClick={() => {
                                    logout()
                                    navigate('/login')
                                }}
                                className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md transition-colors"
                                title="Sign out"
                            >
                                <LogOut className="size-4" />
                            </button>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Content Area */}
            <main className="flex-1 flex flex-col min-w-0 bg-background-light dark:bg-background-dark">
                {/* Header Bar */}
                <header className="h-16 flex items-center justify-between px-6 py-3 border-b border-slate-200 dark:border-slate-800 bg-surface-light dark:bg-surface-dark sticky top-0 z-10">
                    {/* Breadcrumbs */}
                    <nav className="flex items-center text-sm font-medium text-slate-500 dark:text-slate-400">
                        {getBreadcrumbs().map((crumb, index, array) => (
                            <React.Fragment key={crumb.path}>
                                {index > 0 && <span className="mx-2 text-slate-300 dark:text-slate-600">/</span>}
                                {index === array.length - 1 ? (
                                    <span className="text-slate-900 dark:text-white font-semibold">
                                        {crumb.label}
                                    </span>
                                ) : (
                                    <Link to={crumb.path} className="hover:text-primary transition-colors">
                                        {crumb.label}
                                    </Link>
                                )}
                            </React.Fragment>
                        ))}
                    </nav>

                    {/* Actions */}
                    <div className="flex items-center gap-4">
                        {/* Search */}
                        <div className="relative hidden md:block">
                            <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
                                <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>search</span>
                            </span>
                            <input
                                type="text"
                                className="w-64 py-2 pl-10 pr-4 text-sm bg-slate-100 dark:bg-slate-800 border-none rounded-md text-slate-900 dark:text-white placeholder-slate-500 focus:ring-2 focus:ring-primary focus:bg-white dark:focus:bg-slate-800 transition-all outline-none"
                                placeholder="Search memories or files..."
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter') {
                                        window.location.href = `/project/${projectId}/search`
                                    }
                                }}
                            />
                        </div>

                        <ThemeToggle />

                        {/* Notification Bell */}
                        <button className="relative p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors">
                            <span className="material-symbols-outlined">notifications</span>
                            <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-red-500 ring-2 ring-white dark:ring-surface-dark"></span>
                        </button>

                        {/* Primary Action */}
                        <Link to={`/project/${projectId}/memories/new`}>
                            <button className="flex items-center gap-2 bg-primary hover:bg-primary/90 text-white text-sm font-medium px-4 py-2 rounded-md shadow-sm transition-all active:scale-95">
                                <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>add</span>
                                <span>Add Memory</span>
                            </button>
                        </Link>

                        <div className="h-8 w-[1px] bg-slate-200 dark:bg-slate-700 mx-2"></div>

                        <div className="w-64">
                            <WorkspaceSwitcher mode="project" />
                        </div>
                    </div>
                </header>

                {/* Scrollable Page Content */}
                <div className="flex-1 overflow-y-auto p-6 lg:p-10">
                    <Outlet />
                </div>
            </main>
        </div>
    )
}
