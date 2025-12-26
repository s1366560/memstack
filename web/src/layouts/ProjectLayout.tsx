import React, { useEffect, useState } from 'react'
import { Link, Outlet, useLocation, useParams, useNavigate } from 'react-router-dom'
import { WorkspaceSwitcher } from '../components/WorkspaceSwitcher'
import { ThemeToggle } from '../components/ThemeToggle'
import { useProjectStore } from '../stores/project'
import { useTenantStore } from '../stores/tenant'
import { useAuthStore } from '../stores/auth'
import {
    LogOut,
    LayoutDashboard,
    Database,
    Network,
    Search,
    Box,
    Users,
    Telescope,
    FileJson,
    Wrench,
    UserCog,
    Settings,
    HelpCircle,
    Menu,
    Bell,
    Plus,
    ChevronDown,
    ChevronRight,
    BrainCircuit
} from 'lucide-react'

export const ProjectLayout: React.FC = () => {
    const location = useLocation()
    const navigate = useNavigate()
    const { projectId } = useParams()
    const { currentProject, setCurrentProject, getProject } = useProjectStore()
    const { currentTenant, setCurrentTenant } = useTenantStore()
    const { user, logout } = useAuthStore()
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)

    // State for collapsible groups
    const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({
        'knowledge': true,
        'discovery': true,
        'config': true
    })

    const toggleGroup = (group: string) => {
        setOpenGroups(prev => ({ ...prev, [group]: !prev[group] }))
    }

    // Sync project and tenant data
    useEffect(() => {
        if (projectId && (!currentProject || currentProject.id !== projectId)) {
            if (currentTenant) {
                getProject(currentTenant.id, projectId).then(project => {
                    setCurrentProject(project)
                }).catch(console.error)
            } else {
                const { tenants, listTenants } = useTenantStore.getState()
                if (tenants.length === 0) {
                    listTenants().then(() => {
                        const tenants = useTenantStore.getState().tenants
                        if (tenants.length > 0) {
                            const firstTenant = tenants[0]
                            setCurrentTenant(firstTenant)
                            getProject(firstTenant.id, projectId!).then(p => setCurrentProject(p)).catch(() => {
                                console.warn("Project not found in first tenant")
                            })
                        }
                    })
                } else {
                    const firstTenant = tenants[0]
                    setCurrentTenant(firstTenant)
                    getProject(firstTenant.id, projectId!).then(p => setCurrentProject(p)).catch(console.error)
                }
            }
        }
    }, [projectId, currentProject, currentTenant, getProject, setCurrentProject, setCurrentTenant])

    const isActive = (path: string) => {
        if (path === '') return location.pathname === `/project/${projectId}` || location.pathname === `/project/${projectId}/`
        return location.pathname.includes(`/project/${projectId}${path}`)
    }

    const getBreadcrumbs = () => {
        const paths = location.pathname.split('/').filter(Boolean)
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

    const NavItem = ({ to, icon: Icon, label, exact = false }: { to: string, icon: any, label: string, exact?: boolean }) => {
        const active = exact ? isActive('') : isActive(to.replace(`/project/${projectId}`, ''))

        return (
            <Link
                to={to}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200 group relative ${active
                    ? 'bg-[#193db3]/10 text-[#193db3] font-medium'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white'
                    } ${isSidebarCollapsed ? 'justify-center' : ''}`}
                title={isSidebarCollapsed ? label : ""}
            >
                <Icon className={`w-5 h-5 transition-colors ${active ? 'text-[#193db3]' : 'text-slate-500 dark:text-slate-400 group-hover:text-slate-900 dark:group-hover:text-white'}`} />
                {!isSidebarCollapsed && <span>{label}</span>}
                {active && !isSidebarCollapsed && (
                    <div className="absolute right-2 w-1.5 h-1.5 rounded-full bg-[#193db3]"></div>
                )}
            </Link>
        )
    }

    return (
        <div className="flex h-screen w-full overflow-hidden bg-slate-50 dark:bg-[#111521]">
            {/* Sidebar Navigation */}
            <aside className={`flex flex-col border-r border-slate-200 dark:border-[#2a324a] bg-white dark:bg-[#121521] transition-all duration-300 ${isSidebarCollapsed ? 'w-20' : 'w-64'}`}>
                <div className="flex flex-col h-full">
                    {/* Top Section: Branding */}
                    <div className="h-16 flex items-center px-4 border-b border-slate-200 dark:border-[#2a324a]">
                        {!isSidebarCollapsed ? (
                            <div className="flex items-center gap-3">
                                <div className="bg-blue-600/10 dark:bg-[#193db3]/20 p-2 rounded-lg border border-blue-600/20 dark:border-[#193db3]/30">
                                    <BrainCircuit className="text-blue-600 dark:text-[#193db3] w-5 h-5" />
                                </div>
                                <h1 className="text-slate-900 dark:text-white text-lg font-bold leading-none tracking-tight">
                                    MemStack<span className="text-blue-600 dark:text-[#193db3]">.ai</span>
                                </h1>
                            </div>
                        ) : (
                            <div className="w-full flex justify-center">
                                <div className="bg-blue-600/10 dark:bg-[#193db3]/20 p-2 rounded-lg border border-blue-600/20 dark:border-[#193db3]/30">
                                    <BrainCircuit className="text-blue-600 dark:text-[#193db3] w-5 h-5" />
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Navigation Menu */}
                    <nav className="flex-1 overflow-y-auto py-4 px-3 flex flex-col gap-1 custom-scrollbar">
                        <NavItem to={`/project/${projectId}`} icon={LayoutDashboard} label="Overview" exact />

                        {!isSidebarCollapsed && <div className="h-px bg-slate-200 dark:bg-[#2a324a] my-2 mx-2 opacity-50"></div>}

                        {/* Knowledge Base Group */}
                        <div className="flex flex-col gap-1">
                            {!isSidebarCollapsed && (
                                <button
                                    onClick={() => toggleGroup('knowledge')}
                                    className="flex items-center justify-between px-3 py-1.5 text-xs font-semibold text-slate-500 uppercase tracking-wider hover:text-slate-700 dark:hover:text-slate-300 transition-colors mt-2"
                                >
                                    <span>Knowledge Base</span>
                                    {openGroups['knowledge'] ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                                </button>
                            )}
                            {(isSidebarCollapsed || openGroups['knowledge']) && (
                                <>
                                    <NavItem to={`/project/${projectId}/memories`} icon={Database} label="Memories" />
                                    <NavItem to={`/project/${projectId}/entities`} icon={Box} label="Entities" />
                                    <NavItem to={`/project/${projectId}/communities`} icon={Users} label="Communities" />
                                    <NavItem to={`/project/${projectId}/graph`} icon={Network} label="Knowledge Graph" />
                                </>
                            )}
                        </div>

                        {/* Discovery Group */}
                        <div className="flex flex-col gap-1">
                            {!isSidebarCollapsed && (
                                <button
                                    onClick={() => toggleGroup('discovery')}
                                    className="flex items-center justify-between px-3 py-1.5 text-xs font-semibold text-slate-500 uppercase tracking-wider hover:text-slate-700 dark:hover:text-slate-300 transition-colors mt-2"
                                >
                                    <span>Discovery</span>
                                    {openGroups['discovery'] ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                                </button>
                            )}
                            {(isSidebarCollapsed || openGroups['discovery']) && (
                                <>
                                    <NavItem to={`/project/${projectId}/search`} icon={Search} label="Search" />
                                    <NavItem to={`/project/${projectId}/advanced-search`} icon={Telescope} label="Deep Search" />
                                </>
                            )}
                        </div>

                        {/* Configuration Group */}
                        <div className="flex flex-col gap-1">
                            {!isSidebarCollapsed && (
                                <button
                                    onClick={() => toggleGroup('config')}
                                    className="flex items-center justify-between px-3 py-1.5 text-xs font-semibold text-slate-500 uppercase tracking-wider hover:text-slate-700 dark:hover:text-slate-300 transition-colors mt-2"
                                >
                                    <span>Configuration</span>
                                    {openGroups['config'] ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                                </button>
                            )}
                            {(isSidebarCollapsed || openGroups['config']) && (
                                <>
                                    <NavItem to={`/project/${projectId}/schema`} icon={FileJson} label="Schema" />
                                    <NavItem to={`/project/${projectId}/maintenance`} icon={Wrench} label="Maintenance" />
                                    <NavItem to={`/project/${projectId}/team`} icon={UserCog} label="Team" />
                                    <NavItem to={`/project/${projectId}/settings`} icon={Settings} label="Settings" />
                                </>
                            )}
                        </div>
                    </nav>

                    {/* Bottom Section */}
                    <div className="p-3 border-t border-slate-200 dark:border-[#2a324a] bg-slate-50 dark:bg-[#121521]">
                        <NavItem to={`/project/${projectId}/support`} icon={HelpCircle} label="Support" />
                        <div className="mt-2 pt-2 border-t border-slate-200 dark:border-[#2a324a]/50">
                            <div className={`flex items-center gap-3 p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-[#252d46] transition-colors cursor-pointer group ${isSidebarCollapsed ? 'justify-center' : ''}`}>
                                <div className="size-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-xs font-bold text-white shadow-lg shadow-blue-900/20 shrink-0">
                                    {user?.name?.[0]?.toUpperCase() || 'U'}
                                </div>
                                {!isSidebarCollapsed && (
                                    <div className="flex flex-col overflow-hidden min-w-0">
                                        <span className="text-sm font-medium text-slate-700 dark:text-white truncate">{user?.name || 'User'}</span>
                                        <span className="text-xs text-slate-500 truncate">{user?.email || 'user@example.com'}</span>
                                    </div>
                                )}
                                {!isSidebarCollapsed && (
                                    <button
                                        onClick={() => {
                                            logout()
                                            navigate('/login')
                                        }}
                                        className="ml-auto p-1.5 text-slate-500 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-md transition-colors opacity-0 group-hover:opacity-100"
                                        title="Sign out"
                                    >
                                        <LogOut className="w-4 h-4" />
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Content Area */}
            <main className="flex-1 flex flex-col min-w-0 bg-slate-50 dark:bg-[#111521]">
                {/* Header Bar */}
                <header className="h-16 flex items-center justify-between px-6 border-b border-slate-200 dark:border-[#2a324a] bg-white dark:bg-[#121521] sticky top-0 z-10">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
                            className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-[#252d46] transition-colors"
                        >
                            <Menu className="w-5 h-5" />
                        </button>

                        {/* Breadcrumbs */}
                        <nav className="flex items-center text-sm font-medium text-slate-500">
                            {getBreadcrumbs().map((crumb, index, array) => (
                                <React.Fragment key={crumb.path}>
                                    {index > 0 && <ChevronRight className="w-4 h-4 mx-1 text-slate-400 dark:text-slate-600" />}
                                    {index === array.length - 1 ? (
                                        <span className="text-slate-900 dark:text-white font-semibold">
                                            {crumb.label}
                                        </span>
                                    ) : (
                                        <Link to={crumb.path} className="hover:text-blue-600 dark:hover:text-[#193db3] transition-colors">
                                            {crumb.label}
                                        </Link>
                                    )}
                                </React.Fragment>
                            ))}
                        </nav>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-4">
                        {/* Search */}
                        <div className="relative hidden md:block group">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500 group-focus-within:text-blue-600 dark:group-focus-within:text-[#193db3] w-4 h-4 transition-colors" />
                            <input
                                type="text"
                                className="w-64 h-9 pl-9 pr-4 text-sm bg-slate-100 dark:bg-[#1e2433] border border-slate-200 dark:border-[#2a324a] rounded-lg text-slate-900 dark:text-white placeholder-slate-500 focus:border-blue-600 dark:focus:border-[#193db3] focus:ring-1 focus:ring-blue-600 dark:focus:ring-[#193db3] transition-all outline-none"
                                placeholder="Search memories..."
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter') {
                                        window.location.href = `/project/${projectId}/search`
                                    }
                                }}
                            />
                        </div>

                        <ThemeToggle />

                        {/* Notification Bell */}
                        <button className="relative p-2 text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-[#252d46] rounded-full transition-colors">
                            <Bell className="w-5 h-5" />
                            <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-red-500 ring-2 ring-white dark:ring-[#121521]"></span>
                        </button>

                        <div className="h-6 w-px bg-slate-200 dark:bg-[#2a324a] mx-1"></div>

                        {/* Primary Action */}
                        <Link to={`/project/${projectId}/memories/new`}>
                            <button className="flex items-center gap-2 bg-blue-600 dark:bg-[#193db3] hover:bg-blue-700 dark:hover:bg-[#254bcc] text-white text-sm font-bold px-4 py-2 rounded-lg shadow-lg shadow-blue-600/20 dark:shadow-blue-900/20 transition-all active:scale-95">
                                <Plus className="w-4 h-4" />
                                <span>New Memory</span>
                            </button>
                        </Link>

                        <div className="w-48">
                            <WorkspaceSwitcher mode="project" />
                        </div>
                    </div>
                </header>

                {/* Scrollable Page Content */}
                <div className={`flex-1 relative ${location.pathname.includes('/schema') || location.pathname.includes('/graph') ? 'overflow-hidden' : 'overflow-y-auto p-6 lg:p-10'}`}>
                    <Outlet />
                </div>
            </main>
        </div>
    )
}
