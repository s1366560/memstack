import React, { useEffect, useState } from 'react'
import { Link, Outlet, useLocation, useNavigate, useParams } from 'react-router-dom'
import { WorkspaceSwitcher } from '../components/WorkspaceSwitcher'
import { ThemeToggle } from '../components/ThemeToggle'
import { useTenantStore } from '../stores/tenant'
import { useAuthStore } from '../stores/auth'
import { useProjectStore } from '../stores/project'
import { LogOut } from 'lucide-react'

export const TenantLayout: React.FC = () => {
    const location = useLocation()
    const navigate = useNavigate()
    const { tenantId, projectId } = useParams()
    const { currentTenant, setCurrentTenant, getTenant } = useTenantStore()
    const { currentProject } = useProjectStore()
    const { logout, user } = useAuthStore()
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
    const [noTenants, setNoTenants] = useState(false)

    const handleLogout = () => {
        logout()
        navigate('/login')
    }

    // Sync tenant ID from URL with store
    useEffect(() => {
        if (tenantId && (!currentTenant || currentTenant.id !== tenantId)) {
            getTenant(tenantId)
        } else if (!tenantId && !currentTenant) {
            // Check if we have tenants in store, if so, use the first one
            // If not, we rely on WorkspaceSwitcher or TenantOverview to fetch them.
            // But WorkspaceSwitcher is inside the layout, so it might render later or in parallel.
            // We should probably try to fetch tenants here if we don't have any.
            const tenants = useTenantStore.getState().tenants
            if (tenants.length > 0) {
                setCurrentTenant(tenants[0])
            } else {
                useTenantStore.getState().listTenants().then(() => {
                    const tenants = useTenantStore.getState().tenants
                    if (tenants.length > 0) {
                        setCurrentTenant(tenants[0])
                    } else {
                        // Auto create default tenant
                        const defaultName = user?.name ? `${user.name}'s Workspace` : 'My Workspace'
                        useTenantStore.getState().createTenant({
                            name: defaultName,
                            description: 'Automatically created default workspace'
                        }).then(() => {
                            const newTenants = useTenantStore.getState().tenants
                            if (newTenants.length > 0) {
                                setCurrentTenant(newTenants[newTenants.length - 1])
                            } else {
                                setNoTenants(true)
                            }
                        }).catch((err) => {
                            console.error("Failed to auto-create tenant:", err)
                            setNoTenants(true)
                        })
                    }
                }).catch(() => {
                    // Ignore error
                })
            }
        }
    }, [tenantId, currentTenant, getTenant, setCurrentTenant, user])

    // Sync project ID from URL with store
    useEffect(() => {
        if (projectId && currentTenant && (!currentProject || currentProject.id !== projectId)) {
            const { projects, setCurrentProject, getProject } = useProjectStore.getState()
            // Try to find in existing list first
            const project = projects.find(p => p.id === projectId)
            if (project) {
                setCurrentProject(project)
            } else {
                // Fetch specific project
                getProject(currentTenant.id, projectId).then(p => {
                    setCurrentProject(p)
                }).catch(console.error)
            }
        } else if (!projectId && currentProject) {
            // Clear current project if not in project route
            useProjectStore.getState().setCurrentProject(null)
        }
    }, [projectId, currentTenant, currentProject])

    if (noTenants) {
        return (
            <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 dark:bg-slate-900">
                <div className="mx-auto flex w-full max-w-md flex-col items-center space-y-6 p-6 text-center">
                    <div className="flex items-center gap-3">
                        <div className="bg-primary/10 p-2 rounded-lg">
                            <span className="material-symbols-outlined text-primary text-4xl">memory</span>
                        </div>
                        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                            MemStack<span className="text-primary">.ai</span>
                        </h1>
                    </div>

                    <div className="space-y-2">
                        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">欢迎来到 MemStack</h2>
                        <p className="text-slate-500 dark:text-slate-400">
                            您还没有加入任何租户空间。请联系管理员邀请您加入，或者创建一个新的租户空间。
                        </p>
                    </div>

                    <div className="flex flex-col gap-4 w-full">
                        <button
                            onClick={() => {
                                // TODO: Implement create tenant modal or page
                                // For now we can maybe redirect to a create tenant page if it exists
                                // or show a modal. Since we don't have a route, let's just show a message or 
                                // navigate to a hypothetical create page.
                                // Actually, WorkspaceSwitcher usually has a create button. 
                                // Let's just guide them to logout for now or retry.
                                window.location.reload()
                            }}
                            className="inline-flex w-full items-center justify-center rounded-lg bg-primary px-5 py-2.5 text-center text-sm font-medium text-white hover:bg-primary/90 focus:outline-none focus:ring-4 focus:ring-primary/30 transition-all"
                        >
                            刷新页面
                        </button>
                        <button
                            onClick={handleLogout}
                            className="inline-flex w-full items-center justify-center rounded-lg border border-slate-200 bg-white px-5 py-2.5 text-center text-sm font-medium text-slate-900 hover:bg-slate-50 hover:text-primary focus:outline-none focus:ring-4 focus:ring-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-white dark:hover:bg-slate-700 transition-all"
                        >
                            退出登录
                        </button>
                    </div>
                </div>
            </div>
        )
    }

    const getBreadcrumbs = () => {
        const paths = location.pathname.split('/').filter(Boolean)
        // paths: ['tenant', 't1', 'project', 'p1', ...] or ['tenant', 't1', 'projects']

        // Always start with Home (Overview)
        const breadcrumbs = [
            { label: 'Home', path: getLink('') }
        ]

        // If we are deeper than tenant root
        if (paths.length > 2) {
            const section = paths[2] // 'projects', 'users', etc.

            if (section === 'project' && projectId && currentProject) {
                // Project context: Home / Projects / Project Name
                breadcrumbs.push({ label: 'Projects', path: getLink('/projects') })
                breadcrumbs.push({ label: currentProject.name, path: getLink(`/project/${projectId}`) })

                // Add sub-section if any (e.g. memories)
                if (paths.length > 4) {
                    const subSection = paths[4]
                    breadcrumbs.push({
                        label: subSection.charAt(0).toUpperCase() + subSection.slice(1),
                        path: getLink(`/project/${projectId}/${subSection}`)
                    })
                }
            } else {
                // Standard section: Home / Section Name
                breadcrumbs.push({
                    label: section.charAt(0).toUpperCase() + section.slice(1),
                    path: getLink(`/${section}`)
                })
            }
        } else if (paths.length === 2) {
            // Root tenant path, just show Overview (which is Home)
            // breadcrumbs already has Home
            breadcrumbs[0].label = 'Overview'
        }

        return breadcrumbs
    }

    const isActive = (path: string) => {
        // Handle exact match or nested paths
        const currentPath = location.pathname
        const targetPath = tenantId ? `/tenant/${tenantId}${path}` : `/tenant${path}`

        // Special case for root/overview
        if (path === '') {
            return currentPath === (tenantId ? `/tenant/${tenantId}` : '/tenant')
        }

        return currentPath === targetPath || currentPath.startsWith(`${targetPath}/`)
    }

    const getLink = (path: string) => {
        return tenantId ? `/tenant/${tenantId}${path}` : `/tenant${path}`
    }

    return (
        <div className="flex h-screen w-full overflow-hidden">
            {/* Side Navigation */}
            <aside
                className={`flex flex-col bg-surface-light dark:bg-surface-dark border-r border-slate-200 dark:border-slate-800 flex-none z-20 transition-all duration-300 ease-in-out ${isSidebarCollapsed ? 'w-20' : 'w-64'
                    }`}
            >
                <div className="px-4 py-4 border-b border-slate-100 dark:border-slate-800/50 flex items-center justify-between h-16">
                    {!isSidebarCollapsed && (
                        <div className="flex items-center gap-3 px-2">
                            <div className="bg-primary/10 p-2 rounded-lg">
                                <span className="material-symbols-outlined text-primary">memory</span>
                            </div>
                            <h1 className="text-slate-900 dark:text-white text-lg font-bold leading-none tracking-tight">
                                MemStack<span className="text-primary">.ai</span>
                            </h1>
                        </div>
                    )}
                    {isSidebarCollapsed && (
                        <div className="w-full flex justify-center">
                            <div className="bg-primary/10 p-2 rounded-lg shrink-0">
                                <span className="material-symbols-outlined text-primary">memory</span>
                            </div>
                        </div>
                    )}
                </div>

                <nav className="flex flex-col gap-1 px-4 py-6 overflow-y-auto flex-1">
                    {!isSidebarCollapsed && (
                        <p className="px-2 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 transition-opacity duration-300">Platform</p>
                    )}

                    <Link
                        to={getLink('')}
                        className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors group ${isActive('')
                            ? 'bg-primary/10 text-primary'
                            : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white'
                            } ${isSidebarCollapsed ? 'justify-center' : ''}`}
                        title={isSidebarCollapsed ? "Overview" : ""}
                    >
                        <span className={`material-symbols-outlined text-[20px] ${isActive('') ? 'icon-filled' : ''}`}>dashboard</span>
                        {!isSidebarCollapsed && <span className="text-sm font-medium whitespace-nowrap">Overview</span>}
                    </Link>

                    <Link
                        to={getLink('/projects')}
                        className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors group ${isActive('/projects')
                            ? 'bg-primary/10 text-primary'
                            : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white'
                            } ${isSidebarCollapsed ? 'justify-center' : ''}`}
                        title={isSidebarCollapsed ? "Projects" : ""}
                    >
                        <span className={`material-symbols-outlined text-[20px] ${isActive('/projects') ? 'icon-filled' : ''}`}>folder</span>
                        {!isSidebarCollapsed && <span className="text-sm font-medium whitespace-nowrap">Projects</span>}
                    </Link>

                    <Link
                        to={getLink('/users')}
                        className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors group ${isActive('/users')
                            ? 'bg-primary/10 text-primary'
                            : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white'
                            } ${isSidebarCollapsed ? 'justify-center' : ''}`}
                        title={isSidebarCollapsed ? "Users" : ""}
                    >
                        <span className={`material-symbols-outlined text-[20px] ${isActive('/users') ? 'icon-filled' : ''}`}>group</span>
                        {!isSidebarCollapsed && <span className="text-sm font-medium whitespace-nowrap">Users</span>}
                    </Link>

                    <Link
                        to={getLink('/analytics')}
                        className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors group ${isActive('/analytics')
                            ? 'bg-primary/10 text-primary'
                            : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white'
                            } ${isSidebarCollapsed ? 'justify-center' : ''}`}
                        title={isSidebarCollapsed ? "Analytics" : ""}
                    >
                        <span className={`material-symbols-outlined text-[20px] ${isActive('/analytics') ? 'icon-filled' : ''}`}>monitoring</span>
                        {!isSidebarCollapsed && <span className="text-sm font-medium whitespace-nowrap">Analytics</span>}
                    </Link>

                    <Link
                        to={getLink('/tasks')}
                        className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors group ${isActive('/tasks')
                            ? 'bg-primary/10 text-primary'
                            : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white'
                            } ${isSidebarCollapsed ? 'justify-center' : ''}`}
                        title={isSidebarCollapsed ? "Tasks" : ""}
                    >
                        <span className={`material-symbols-outlined text-[20px] ${isActive('/tasks') ? 'icon-filled' : ''}`}>task</span>
                        {!isSidebarCollapsed && <span className="text-sm font-medium whitespace-nowrap">Tasks</span>}
                    </Link>

                    {!isSidebarCollapsed && (
                        <p className="px-2 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 mt-6 transition-opacity duration-300">Administration</p>
                    )}
                    {isSidebarCollapsed && <div className="my-2 border-t border-slate-100 dark:border-slate-800"></div>}

                    <Link
                        to={getLink('/billing')}
                        className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white transition-colors group ${isSidebarCollapsed ? 'justify-center' : ''}`}
                        title={isSidebarCollapsed ? "Billing" : ""}
                    >
                        <span className="material-symbols-outlined text-[20px]">credit_card</span>
                        {!isSidebarCollapsed && <span className="text-sm font-medium whitespace-nowrap">Billing</span>}
                    </Link>

                    <Link
                        to={getLink('/settings')}
                        className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white transition-colors group ${isSidebarCollapsed ? 'justify-center' : ''}`}
                        title={isSidebarCollapsed ? "Settings" : ""}
                    >
                        <span className="material-symbols-outlined text-[20px]">settings</span>
                        {!isSidebarCollapsed && <span className="text-sm font-medium whitespace-nowrap">Settings</span>}
                    </Link>

                    <Link
                        to={getLink('/profile')}
                        className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white transition-colors group ${isActive('/profile')
                            ? 'bg-primary/10 text-primary'
                            : ''
                            } ${isSidebarCollapsed ? 'justify-center' : ''}`}
                        title={isSidebarCollapsed ? "Profile" : ""}
                    >
                        <span className={`material-symbols-outlined text-[20px] ${isActive('/profile') ? 'icon-filled' : ''}`}>person</span>
                        {!isSidebarCollapsed && <span className="text-sm font-medium whitespace-nowrap">Profile</span>}
                    </Link>
                </nav>

                <div className="p-4 border-t border-slate-100 dark:border-slate-800">
                    <div className="flex justify-center mb-4">
                        <ThemeToggle />
                    </div>
                    <div className={`flex items-center justify-between p-2 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-100 dark:border-slate-700/50 ${isSidebarCollapsed ? 'justify-center' : ''} group`}>
                        <div className="flex items-center gap-3 min-w-0">
                            <div className="size-8 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-xs font-bold text-slate-600 dark:text-slate-300 shrink-0">
                                {user?.name?.[0]?.toUpperCase() || 'TA'}
                            </div>
                            {!isSidebarCollapsed && (
                                <div className="flex flex-col overflow-hidden">
                                    <p className="text-sm font-medium text-slate-900 dark:text-white truncate">{user?.name || 'Tenant Admin'}</p>
                                    <p className="text-xs text-slate-500 truncate">{user?.email || 'admin@tenant.co'}</p>
                                </div>
                            )}
                        </div>
                        {!isSidebarCollapsed && (
                            <button
                                onClick={handleLogout}
                                className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md transition-colors"
                                title="Sign out"
                            >
                                <LogOut className="size-4" />
                            </button>
                        )}
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex flex-col flex-1 h-full overflow-hidden relative bg-background-light dark:bg-background-dark">
                {/* Top Header */}
                <header className="flex items-center justify-between px-8 py-4 bg-surface-light dark:bg-surface-dark border-b border-slate-200 dark:border-slate-800 flex-none">
                    <div className="flex items-center gap-4 text-sm text-slate-500">
                        <button
                            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
                            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
                        >
                            <span className="material-symbols-outlined">menu</span>
                        </button>
                        <div className="flex items-center">
                            {getBreadcrumbs().map((crumb, index, array) => (
                                <React.Fragment key={crumb.path}>
                                    {index > 0 && <span className="mx-2 text-slate-300">/</span>}
                                    {index === array.length - 1 ? (
                                        <span className="font-medium text-slate-900 dark:text-white">
                                            {crumb.label}
                                        </span>
                                    ) : (
                                        <Link to={crumb.path} className="hover:text-primary transition-colors">
                                            {crumb.label}
                                        </Link>
                                    )}
                                </React.Fragment>
                            ))}
                        </div>
                    </div>

                    <div className="flex items-center gap-6">
                        <div className="relative group">
                            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-primary text-[20px]">search</span>
                            <input
                                type="text"
                                placeholder="Search resources..."
                                className="pl-10 pr-4 py-2 w-64 bg-slate-100 dark:bg-slate-800 border-none rounded-full text-sm focus:ring-2 focus:ring-primary/50 text-slate-900 dark:text-white placeholder-slate-500 transition-all outline-none"
                            />
                        </div>
                        <ThemeToggle />
                        <button className="relative p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 transition-colors">
                            <span className="material-symbols-outlined text-[22px]">notifications</span>
                            <span className="absolute top-2 right-2 size-2 bg-red-500 rounded-full border-2 border-white dark:border-slate-900"></span>
                        </button>
                        <div className="h-8 w-[1px] bg-slate-200 dark:bg-slate-700"></div>
                        <Link to={getLink('/profile')} className="flex items-center gap-2">
                            <div className="size-8 rounded-full bg-cover bg-center border border-slate-200 dark:border-slate-700 bg-slate-200 flex items-center justify-center text-xs font-bold text-slate-600 dark:text-slate-300">
                                {user?.name?.[0]?.toUpperCase() || 'U'}
                            </div>
                        </Link>
                        <div className="w-64">
                            <WorkspaceSwitcher mode="tenant" />
                        </div>
                    </div>
                </header>

                {/* Page Content */}
                <div className="flex-1 overflow-y-auto p-8">
                    <Outlet />
                </div>
            </main>
        </div>
    )
}
