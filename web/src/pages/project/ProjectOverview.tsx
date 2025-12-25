import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { projectAPI, memoryAPI } from '../../services/api'
import { Project, Memory } from '../../types/memory'

export const ProjectOverview: React.FC = () => {
    const { projectId } = useParams()
    const [stats, setStats] = useState<any>(null)
    const [project, setProject] = useState<Project | null>(null)
    const [memories, setMemories] = useState<Memory[]>([])
    const [isLoading, setIsLoading] = useState(false)

    useEffect(() => {
        const fetchData = async () => {
            if (projectId) {
                setIsLoading(true)
                try {
                    // Pass projectId as tenantId since it's ignored by the API wrapper currently, 
                    // or we could get the tenantId from context/url if available.
                    const [statsData, projectData, memoriesData] = await Promise.all([
                        projectAPI.getStats(projectId),
                        projectAPI.get(projectId, projectId),
                        memoryAPI.list(projectId, { page: 1, page_size: 5 })
                    ])
                    setStats(statsData)
                    setProject(projectData)
                    setMemories(memoriesData.memories)
                } catch (error) {
                    console.error('Failed to fetch project data:', error)
                } finally {
                    setIsLoading(false)
                }
            }
        }
        fetchData()
    }, [projectId])

    if (!projectId) {
        return <div className="p-8 text-center text-slate-500">Project not found</div>
    }

    if (isLoading || !stats) {
        return <div className="p-8 text-center text-slate-500">Loading project dashboard...</div>
    }

    const formatStorage = (bytes: number) => {
        const gb = bytes / (1024 * 1024 * 1024)
        if (gb >= 1) return `${gb.toFixed(1)} GB`
        const mb = bytes / (1024 * 1024)
        if (mb >= 1) return `${mb.toFixed(1)} MB`
        const kb = bytes / 1024
        return `${kb.toFixed(1)} KB`
    }

    const formatDate = (dateString: string) => {
        const date = new Date(dateString)
        const now = new Date()
        const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)

        if (diffInSeconds < 60) return 'Just now'
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`
        return date.toLocaleDateString()
    }

    return (
        <div className="max-w-7xl mx-auto space-y-8">
            {/* Page Title & Greeting */}
            <div className="flex flex-col gap-1">
                <h2 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">Overview</h2>
                <p className="text-slate-500 dark:text-slate-400">Welcome back. Here's what's happening with {project?.name || 'Project'}.</p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Stat Card 1 */}
                <div className="bg-surface-light dark:bg-surface-dark p-5 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between h-32 hover:border-primary/50 transition-colors group">
                    <div className="flex justify-between items-start">
                        <div className="flex flex-col">
                            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Total Memories</span>
                            <span className="text-2xl font-bold text-slate-900 dark:text-white mt-1">{stats.memory_count}</span>
                        </div>
                        <div className="p-2 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-md group-hover:bg-blue-100 dark:group-hover:bg-blue-900/30 transition-colors">
                            <span className="material-symbols-outlined">memory</span>
                        </div>
                    </div>
                    <div className="flex items-center gap-1 text-xs text-slate-500 font-medium">
                        <span>Stored in database</span>
                    </div>
                </div>

                {/* Stat Card 2 */}
                <div className="bg-surface-light dark:bg-surface-dark p-5 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between h-32 hover:border-primary/50 transition-colors group">
                    <div className="flex justify-between items-start">
                        <div className="flex flex-col">
                            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Storage Used</span>
                            <span className="text-2xl font-bold text-slate-900 dark:text-white mt-1">{formatStorage(stats.storage_used)}</span>
                        </div>
                        <div className="p-2 bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400 rounded-md group-hover:bg-purple-100 dark:group-hover:bg-purple-900/30 transition-colors">
                            <span className="material-symbols-outlined">cloud</span>
                        </div>
                    </div>
                    <div className="w-full bg-slate-100 dark:bg-slate-700 h-1.5 rounded-full mt-2 overflow-hidden">
                        <div className="bg-purple-500 h-full rounded-full" style={{ width: `${(stats.storage_used / stats.storage_limit) * 100}%` }}></div>
                    </div>
                    <span className="text-xs text-slate-500 mt-1">{Math.round((stats.storage_used / stats.storage_limit) * 100)}% of quota</span>
                </div>

                {/* Stat Card 3 */}
                <div className="bg-surface-light dark:bg-surface-dark p-5 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between h-32 hover:border-primary/50 transition-colors group">
                    <div className="flex justify-between items-start">
                        <div className="flex flex-col">
                            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Active Nodes</span>
                            <span className="text-2xl font-bold text-slate-900 dark:text-white mt-1">{stats.active_nodes}</span>
                        </div>
                        <div className="p-2 bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 rounded-md group-hover:bg-amber-100 dark:group-hover:bg-amber-900/30 transition-colors">
                            <span className="material-symbols-outlined">hub</span>
                        </div>
                    </div>
                    <div className="flex items-center gap-1 text-xs text-slate-500 font-medium">
                        <span className="material-symbols-outlined text-green-500" style={{ fontSize: '16px' }}>check_circle</span>
                        <span>All systems operational</span>
                    </div>
                </div>

                {/* Stat Card 4 */}
                <div className="bg-surface-light dark:bg-surface-dark p-5 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between h-32 hover:border-primary/50 transition-colors group">
                    <div className="flex justify-between items-start">
                        <div className="flex flex-col">
                            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Collaborators</span>
                            <span className="text-2xl font-bold text-slate-900 dark:text-white mt-1">{stats.collaborators}</span>
                        </div>
                        <div className="p-2 bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400 rounded-md group-hover:bg-indigo-100 dark:group-hover:bg-indigo-900/30 transition-colors">
                            <span className="material-symbols-outlined">diversity_3</span>
                        </div>
                    </div>
                    <div className="flex items-center gap-1 text-xs text-slate-500 font-medium">
                        <span>Project members</span>
                    </div>
                </div>
            </div>

            {/* Main Content Split */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left Column: Active Memories Table (2/3 width) */}
                <div className="lg:col-span-2 flex flex-col gap-4">
                    <div className="flex items-center justify-between">
                        <h3 className="text-lg font-bold text-slate-900 dark:text-white">Active Memories</h3>
                        <Link to={`/project/${projectId}/memories`} className="text-sm text-primary font-medium hover:text-primary/80">View All</Link>
                    </div>
                    <div className="bg-surface-light dark:bg-surface-dark border border-slate-200 dark:border-slate-800 rounded-lg shadow-sm overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-sm">
                                <thead className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-800">
                                    <tr>
                                        <th className="px-6 py-3 font-semibold text-slate-500 dark:text-slate-400">Name</th>
                                        <th className="px-6 py-3 font-semibold text-slate-500 dark:text-slate-400">Type</th>
                                        <th className="px-6 py-3 font-semibold text-slate-500 dark:text-slate-400">Status</th>
                                        <th className="px-6 py-3 font-semibold text-slate-500 dark:text-slate-400 text-right">Size</th>
                                        <th className="px-6 py-3 font-semibold text-slate-500 dark:text-slate-400"></th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                                    {memories.length === 0 ? (
                                        <tr>
                                            <td colSpan={5} className="px-6 py-8 text-center text-slate-500">
                                                No memories found. Start by creating one!
                                            </td>
                                        </tr>
                                    ) : (
                                        memories.map((memory) => (
                                            <tr key={memory.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors group">
                                                <td className="px-6 py-3">
                                                    <div className="flex items-center gap-3">
                                                        <div className="p-2 rounded bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400">
                                                            <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>
                                                                {memory.content_type === 'image' ? 'image' :
                                                                    memory.content_type === 'video' ? 'movie' : 'description'}
                                                            </span>
                                                        </div>
                                                        <div>
                                                            <div className="font-medium text-slate-900 dark:text-white">{memory.title}</div>
                                                            <div className="text-xs text-slate-500">
                                                                Updated {formatDate(memory.updated_at || memory.created_at)}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-3 text-slate-600 dark:text-slate-300 capitalize">{memory.content_type}</td>
                                                <td className="px-6 py-3">
                                                    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                                                        <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                                                        Synced
                                                    </span>
                                                </td>
                                                <td className="px-6 py-3 text-slate-600 dark:text-slate-300 text-right font-mono">
                                                    {formatStorage(memory.content?.length || 0)}
                                                </td>
                                                <td className="px-6 py-3 text-right">
                                                    <button className="text-slate-400 hover:text-primary p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-700">
                                                        <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>more_vert</span>
                                                    </button>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                        <div className="px-6 py-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-surface-dark flex justify-center">
                            <button className="text-xs font-medium text-slate-500 hover:text-primary flex items-center gap-1">
                                Show More <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>expand_more</span>
                            </button>
                        </div>
                    </div>
                </div>

                {/* Right Column: Team & Activity (1/3 width) */}
                <div className="flex flex-col gap-6">
                    {/* Team Card */}
                    <div className="bg-surface-light dark:bg-surface-dark border border-slate-200 dark:border-slate-800 rounded-lg shadow-sm p-5">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wide">Project Team</h3>
                            <button className="p-1 text-slate-400 hover:text-primary rounded hover:bg-slate-100 dark:hover:bg-slate-800">
                                <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>group</span>
                            </button>
                        </div>
                        <div className="flex flex-col gap-3">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400 rounded-full">
                                    <span className="material-symbols-outlined">diversity_3</span>
                                </div>
                                <div>
                                    <p className="text-sm font-medium text-slate-900 dark:text-white">{stats?.collaborators || 0} Members</p>
                                    <p className="text-xs text-slate-500">Collaborating on this project</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Quick Actions / Activity */}
                    <div className="bg-primary text-white rounded-lg shadow-lg p-5 relative overflow-hidden group">
                        <div className="absolute -right-6 -top-6 w-32 h-32 bg-white/10 rounded-full blur-2xl group-hover:bg-white/20 transition-all"></div>
                        <div className="relative z-10">
                            <h3 className="text-sm font-bold uppercase tracking-wide mb-3">System Status</h3>
                            <div className="flex items-start gap-3 mb-4">
                                <div className="p-1.5 bg-white/20 rounded">
                                    <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>smart_toy</span>
                                </div>
                                <div>
                                    <p className="text-sm font-medium">Auto-Indexing Active</p>
                                    <p className="text-xs text-blue-100 mt-1">System is ready to process new memories.</p>
                                </div>
                            </div>
                            <div className="w-full bg-blue-900/50 h-1.5 rounded-full overflow-hidden">
                                <div className="bg-white h-full rounded-full w-full"></div>
                            </div>
                            <div className="flex justify-between text-[10px] mt-1 text-blue-200">
                                <span>Status</span>
                                <span>Operational</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
