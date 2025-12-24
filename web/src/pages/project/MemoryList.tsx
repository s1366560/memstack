import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { memoryAPI } from '../../services/api'

export const MemoryList: React.FC = () => {
    const { projectId } = useParams()
    const [memories, setMemories] = useState<any[]>([])
    const [isLoading, setIsLoading] = useState(false)
    const [search, setSearch] = useState('')

    useEffect(() => {
        const fetchMemories = async () => {
            if (projectId) {
                setIsLoading(true)
                try {
                    const data = await memoryAPI.list(projectId, { search })
                    setMemories(data.memories || [])
                } catch (error) {
                    console.error('Failed to list memories:', error)
                } finally {
                    setIsLoading(false)
                }
            }
        }
        fetchMemories()
    }, [projectId, search])

    if (!projectId) {
        return <div className="p-8 text-center text-slate-500">Project not found</div>
    }

    return (
        <div className="max-w-7xl mx-auto flex flex-col gap-8">
            {/* Header Area */}
            <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex flex-col gap-1">
                    <h1 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">Memories</h1>
                    <p className="text-sm text-slate-500">Manage and organize your project's knowledge base.</p>
                </div>
                <Link to={`/project/${projectId}/memories/new`}>
                    <button className="flex items-center gap-2 bg-primary hover:bg-primary/90 text-white px-5 py-2.5 rounded-lg text-sm font-medium shadow-lg shadow-primary/20 flex items-center gap-2 transition-all active:scale-95">
                        <span className="material-symbols-outlined text-lg">add</span>
                        Add Memory
                    </button>
                </Link>
            </div>

            {/* Toolbar */}
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
                        placeholder="Search memories..."
                    />
                </div>
                {/* Filters */}
                <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto pb-2 md:pb-0 px-2 md:px-0">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider mr-1">Filter:</span>
                    <button className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-primary/10 text-primary border border-primary/20 text-sm font-medium whitespace-nowrap transition-colors">
                        All Types
                        <span className="material-symbols-outlined text-lg">arrow_drop_down</span>
                    </button>
                    <button className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 text-sm font-medium whitespace-nowrap transition-colors">
                        Status
                        <span className="material-symbols-outlined text-lg">arrow_drop_down</span>
                    </button>
                </div>
            </div>

            {/* Memories List */}
            <div className="bg-surface-light dark:bg-surface-dark border border-slate-200 dark:border-slate-800 rounded-lg shadow-sm overflow-hidden">
                {isLoading ? (
                    <div className="p-10 text-center text-slate-500">Loading memories...</div>
                ) : (
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
                                        <td colSpan={5} className="p-8 text-center text-slate-500">
                                            No memories found. Create one to get started.
                                        </td>
                                    </tr>
                                ) : (
                                    memories.map((memory) => (
                                        <tr key={memory.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors group">
                                            <td className="px-6 py-3">
                                                <div className="flex items-center gap-3">
                                                    <div className="p-2 rounded bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400">
                                                        <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>description</span>
                                                    </div>
                                                    <div>
                                                        <Link to={`/project/${projectId}/memory/${memory.id}`} className="font-medium text-slate-900 dark:text-white hover:text-primary transition-colors">
                                                            {memory.title}
                                                        </Link>
                                                        <div className="text-xs text-slate-500">Updated {new Date(memory.updated_at || memory.created_at).toLocaleDateString()}</div>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-6 py-3 text-slate-600 dark:text-slate-300 capitalize">{memory.content_type || 'Text'}</td>
                                            <td className="px-6 py-3">
                                                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                                                    <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                                                    Synced
                                                </span>
                                            </td>
                                            <td className="px-6 py-3 text-slate-600 dark:text-slate-300 text-right font-mono">
                                                {memory.content ? Math.round(memory.content.length / 1024) : 0} KB
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
                )}
            </div>
        </div>
    )
}
