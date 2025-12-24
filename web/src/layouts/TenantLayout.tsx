import React, { useEffect, useState } from 'react'
import { Link, Outlet, useLocation, useParams } from 'react-router-dom'
import { WorkspaceSwitcher } from '../components/WorkspaceSwitcher'
import { useTenantStore } from '../stores/tenant'

export const TenantLayout: React.FC = () => {
    const location = useLocation()
    const { tenantId } = useParams()
    const { currentTenant, setCurrentTenant, getTenant } = useTenantStore()
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)

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
                    }
                })
            }
        }
    }, [tenantId, currentTenant, getTenant, setCurrentTenant])

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
                </nav>

                <div className="p-4 border-t border-slate-100 dark:border-slate-800">
                    <div className={`flex items-center gap-3 p-2 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-100 dark:border-slate-700/50 ${isSidebarCollapsed ? 'justify-center' : ''}`}>
                        <div className="size-8 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-xs font-bold text-slate-600 dark:text-slate-300 shrink-0">
                            TA
                        </div>
                        {!isSidebarCollapsed && (
                            <div className="flex flex-col overflow-hidden">
                                <p className="text-sm font-medium text-slate-900 dark:text-white truncate">Tenant Admin</p>
                                <p className="text-xs text-slate-500 truncate">admin@tenant.co</p>
                            </div>
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
                            <Link to={getLink('')} className="hover:text-primary transition-colors">Home</Link>
                            <span className="mx-2 text-slate-300">/</span>
                            <span className="font-medium text-slate-900 dark:text-white">
                                {location.pathname === getLink('') ? 'Overview' :
                                    location.pathname.split('/').pop()?.charAt(0).toUpperCase()! + location.pathname.split('/').pop()?.slice(1)!}
                            </span>
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
                        <button className="relative p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 transition-colors">
                            <span className="material-symbols-outlined text-[22px]">notifications</span>
                            <span className="absolute top-2 right-2 size-2 bg-red-500 rounded-full border-2 border-white dark:border-slate-900"></span>
                        </button>
                        <div className="h-8 w-[1px] bg-slate-200 dark:bg-slate-700"></div>
                        <button className="flex items-center gap-2">
                            <div className="size-8 rounded-full bg-cover bg-center border border-slate-200 dark:border-slate-700 bg-slate-200"></div>
                        </button>
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
