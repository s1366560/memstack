import React from 'react'
import { Link, Outlet, useLocation, useParams } from 'react-router-dom'
import { WorkspaceSwitcher } from '../components/WorkspaceSwitcher'

export const ProjectLayout: React.FC = () => {
    const location = useLocation()
    const { projectId } = useParams()

    const isActive = (path: string) => {
        // Simple check if the current path ends with the given path (e.g. /memories)
        return location.pathname.endsWith(path)
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
                                className={`flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors group ${isActive('/search')
                                    ? 'bg-primary/10 text-primary'
                                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                                    }`}
                            >
                                <span className="material-symbols-outlined" style={{ fontVariationSettings: isActive('/search') ? "'FILL' 1" : "'FILL' 0" }}>search</span>
                                <span className="text-sm font-medium">Search</span>
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
                        <button className="flex items-center gap-3 px-3 py-2 w-full rounded-md hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
                            <div className="h-9 w-9 rounded-full bg-cover bg-center border border-slate-200 dark:border-slate-700 bg-slate-200"></div>
                            <div className="flex flex-col items-start overflow-hidden">
                                <span className="text-sm font-medium text-slate-900 dark:text-white truncate w-full text-left">Admin User</span>
                                <span className="text-xs text-slate-500 dark:text-slate-400 truncate w-full text-left">admin@corpone.com</span>
                            </div>
                            <span className="material-symbols-outlined text-slate-400 ml-auto" style={{ fontSize: '20px' }}>logout</span>
                        </button>
                    </div>
                </div>
            </aside>

            {/* Main Content Area */}
            <main className="flex-1 flex flex-col min-w-0 bg-background-light dark:bg-background-dark">
                {/* Header Bar */}
                <header className="h-16 flex items-center justify-between px-6 py-3 border-b border-slate-200 dark:border-slate-800 bg-surface-light dark:bg-surface-dark sticky top-0 z-10">
                    {/* Breadcrumbs */}
                    <nav className="flex items-center text-sm font-medium text-slate-500 dark:text-slate-400">
                        <Link to="/tenant" className="hover:text-primary transition-colors">Home</Link>
                        <span className="mx-2 text-slate-300 dark:text-slate-600">/</span>
                        <Link to="/tenant/projects" className="hover:text-primary transition-colors">Projects</Link>
                        <span className="mx-2 text-slate-300 dark:text-slate-600">/</span>
                        <span className="text-slate-900 dark:text-white font-semibold">Project Alpha</span>
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
