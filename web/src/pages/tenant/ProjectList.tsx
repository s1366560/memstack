import React, { useEffect, useState } from 'react'
import { useTenantStore } from '../../stores/tenant'
import { useProjectStore } from '../../stores/project'
import { Link } from 'react-router-dom'

export const ProjectList: React.FC = () => {
    const { currentTenant } = useTenantStore()
    const { listProjects, deleteProject, projects, isLoading } = useProjectStore()
    const [search, setSearch] = useState('')
    const [activeMenu, setActiveMenu] = useState<string | null>(null)

    useEffect(() => {
        if (currentTenant) {
            listProjects(currentTenant.id, { search })
        }
    }, [currentTenant, search, listProjects])

    const handleDelete = async (projectId: string) => {
        if (!currentTenant) return
        if (window.confirm('Are you sure you want to delete this project?')) {
            try {
                await deleteProject(currentTenant.id, projectId)
                setActiveMenu(null)
            } catch (error) {
                console.error('Failed to delete project:', error)
            }
        }
    }

    if (!currentTenant) {
        return <div className="p-8 text-center text-slate-500">Loading tenant...</div>
    }

    return (
        <div className="max-w-[1400px] mx-auto w-full flex flex-col gap-8">
            {/* Header Area */}
            <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex flex-col gap-1">
                    <h1 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">Project Management</h1>
                    <p className="text-sm text-slate-500">Manage memory resources, permissions, and environments for your tenant workspace.</p>
                </div>
                <Link to={`/tenant/${currentTenant.id}/projects/new`}>
                    <button className="bg-primary hover:bg-primary-dark text-white px-5 py-2.5 rounded-lg text-sm font-medium shadow-lg shadow-primary/20 flex items-center gap-2 transition-all active:scale-95">
                        <span className="material-symbols-outlined text-lg">add</span>
                        Create New Project
                    </button>
                </Link>
            </div>

            {/* Toolbar: Search & Filters */}
            <div className="flex flex-col md:flex-row gap-4 justify-between items-center bg-white dark:bg-surface-dark p-2 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
                {/* Search */}
                <div className="relative w-full md:max-w-md">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <span className="material-symbols-outlined text-slate-400">search</span>
                    </div>
                    <input
                        type="text"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="block w-full pl-10 pr-3 py-2.5 border-none rounded-lg bg-slate-50 dark:bg-slate-800 text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-primary/20 focus:bg-white dark:focus:bg-slate-700 transition-all outline-none"
                        placeholder="Search by project name, ID, or owner..."
                    />
                </div>
                {/* Filters */}
                <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto pb-2 md:pb-0 px-2 md:px-0">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider mr-1">Filter:</span>
                    <button className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-primary/10 text-primary border border-primary/20 text-sm font-medium whitespace-nowrap transition-colors">
                        All Status
                        <span className="material-symbols-outlined text-lg">arrow_drop_down</span>
                    </button>
                    <button className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 text-sm font-medium whitespace-nowrap transition-colors">
                        Owner
                        <span className="material-symbols-outlined text-lg">arrow_drop_down</span>
                    </button>
                    <div className="w-px h-6 bg-slate-200 dark:bg-slate-700 mx-1"></div>
                    <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-lg">
                        <button className="p-1.5 rounded bg-white dark:bg-slate-700 text-primary shadow-sm">
                            <span className="material-symbols-outlined text-lg block">grid_view</span>
                        </button>
                        <button className="p-1.5 rounded text-slate-400 hover:text-slate-900 dark:hover:text-white">
                            <span className="material-symbols-outlined text-lg block">view_list</span>
                        </button>
                    </div>
                </div>
            </div>

            {/* Projects Grid */}
            {isLoading ? (
                <div className="text-center py-10 text-slate-500">Loading projects...</div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {projects.map((project) => (
                        <div key={project.id} className="bg-white dark:bg-surface-dark rounded-xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm hover:shadow-md hover:border-primary/50 transition-all group flex flex-col gap-4">
                            <div className="flex justify-between items-start">
                                <div className="flex gap-3">
                                    <div className="h-10 w-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-primary">
                                        <span className="material-symbols-outlined">psychology</span>
                                    </div>
                                    <div>
                                        <Link to={`/project/${project.id}`} className="text-base font-bold text-slate-900 dark:text-white group-hover:text-primary transition-colors hover:underline">
                                            {project.name}
                                        </Link>
                                        <p className="text-xs text-slate-500 font-mono mt-0.5">ID: {project.id.slice(0, 8)}</p>
                                    </div>
                                </div>
                                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                                    Active
                                </span>
                            </div>
                            <div className="space-y-3">
                                <div className="flex justify-between items-end text-sm">
                                    <span className="text-slate-500">Memory Usage</span>
                                    {/* Mock Usage Data */}
                                    <span className="font-bold text-slate-900 dark:text-white">25% <span className="text-slate-500 font-normal text-xs ml-1">(32GB / 128GB)</span></span>
                                </div>
                                <div className="w-full bg-slate-100 dark:bg-slate-700 rounded-full h-2 overflow-hidden">
                                    <div className="bg-primary h-2 rounded-full" style={{ width: '25%' }}></div>
                                </div>
                                <div className="flex gap-4 pt-1">
                                    <div className="flex items-center gap-1.5 text-xs text-slate-500">
                                        <span className="material-symbols-outlined text-base">database</span>
                                        1.2 TB Storage
                                    </div>
                                    <div className="flex items-center gap-1.5 text-xs text-slate-500">
                                        <span className="material-symbols-outlined text-base">dns</span>
                                        4 Nodes
                                    </div>
                                </div>
                            </div>
                            <div className="border-t border-slate-100 dark:border-slate-800 pt-4 mt-auto flex items-center justify-between">
                                <div className="flex -space-x-2">
                                    <div className="w-8 h-8 rounded-full border-2 border-white dark:border-surface-dark bg-slate-200 bg-cover bg-center"></div>
                                    <div className="w-8 h-8 rounded-full border-2 border-white dark:border-surface-dark bg-slate-300 bg-cover bg-center"></div>
                                    <div className="w-8 h-8 rounded-full border-2 border-white dark:border-surface-dark bg-slate-100 dark:bg-slate-700 flex items-center justify-center text-xs font-medium text-slate-500">+2</div>
                                </div>
                                <div className="flex items-center gap-2 relative">
                                    <span className="text-xs text-slate-500">2h ago</span>
                                    <button
                                        onClick={(e) => {
                                            e.preventDefault()
                                            setActiveMenu(activeMenu === project.id ? null : project.id)
                                        }}
                                        className="p-1 rounded-md hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 hover:text-slate-900 dark:hover:text-white transition-colors"
                                    >
                                        <span className="material-symbols-outlined text-lg">more_vert</span>
                                    </button>

                                    {activeMenu === project.id && (
                                        <div className="absolute right-0 bottom-full mb-2 w-48 bg-white dark:bg-slate-800 rounded-lg shadow-xl border border-slate-200 dark:border-slate-700 py-1 z-10">
                                            <button
                                                onClick={(e) => {
                                                    e.preventDefault()
                                                    handleDelete(project.id)
                                                }}
                                                className="w-full text-left px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-2"
                                            >
                                                <span className="material-symbols-outlined text-lg">delete</span>
                                                Delete Project
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}

                    {/* New Project Placeholder */}
                    <Link to={`/tenant/${currentTenant.id}/projects/new`} className="bg-slate-50 dark:bg-slate-800/50 rounded-xl border-2 border-dashed border-slate-300 dark:border-slate-700 p-5 flex flex-col items-center justify-center gap-4 hover:border-primary hover:bg-primary/5 transition-all group min-h-[200px]">
                        <div className="h-12 w-12 rounded-full bg-white dark:bg-slate-700 shadow-sm flex items-center justify-center text-slate-400 group-hover:text-primary group-hover:scale-110 transition-all">
                            <span className="material-symbols-outlined text-2xl">add</span>
                        </div>
                        <div className="text-center">
                            <h3 className="text-sm font-bold text-slate-900 dark:text-white group-hover:text-primary">Create New Project</h3>
                            <p className="text-xs text-slate-500 mt-1">Setup a new memory environment</p>
                        </div>
                    </Link>
                </div>
            )}
        </div>
    )
}
