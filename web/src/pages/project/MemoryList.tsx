import React, { useEffect, useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { memoryAPI } from '../../services/api'
import { Memory } from '../../types/memory'
import { DeleteConfirmationModal } from '../../components/DeleteConfirmationModal'

export const MemoryList: React.FC = () => {
    const { projectId } = useParams()
    const [memories, setMemories] = useState<Memory[]>([])
    const [isLoading, setIsLoading] = useState(false)
    const [search, setSearch] = useState('')
    const [deletingId, setDeletingId] = useState<string | null>(null)
    const [deleteModalOpen, setDeleteModalOpen] = useState(false)
    const [itemToDelete, setItemToDelete] = useState<string | null>(null)

    const fetchMemories = useCallback(async () => {
        if (projectId) {
            setIsLoading(true)
            try {
                const data = await memoryAPI.list(projectId, {
                    page_size: 100
                })
                setMemories(data.memories || [])
            } catch (error) {
                console.error('Failed to list memories:', error)
            } finally {
                setIsLoading(false)
            }
        }
    }, [projectId])

    // Polling for processing status
    useEffect(() => {
        let interval: NodeJS.Timeout

        // Check if any memories are processing or pending
        const hasProcessingMemories = memories.some(m =>
            m.processing_status === 'PROCESSING' || m.processing_status === 'PENDING'
        )

        if (hasProcessingMemories && projectId) {
            interval = setInterval(async () => {
                try {
                    const data = await memoryAPI.list(projectId, {
                        page_size: 100
                    })
                    // Only update if statuses changed to avoid re-renders?
                    // For simplicity, just update the list
                    setMemories(data.memories || [])
                } catch (error) {
                    console.error('Failed to poll memories:', error)
                }
            }, 5000) // Poll every 5 seconds
        }

        return () => {
            if (interval) clearInterval(interval)
        }
    }, [memories, projectId])

    useEffect(() => {
        fetchMemories()
    }, [fetchMemories])

    const confirmDelete = (memoryId: string) => {
        setItemToDelete(memoryId)
        setDeleteModalOpen(true)
    }

    const handleDelete = async () => {
        if (!itemToDelete || !projectId) return

        setDeletingId(itemToDelete)
        try {
            await memoryAPI.delete(projectId, itemToDelete)
            await fetchMemories()
            setDeleteModalOpen(false)
            setItemToDelete(null)
        } catch (error) {
            console.error('Failed to delete memory:', error)
            alert('Failed to delete memory')
        } finally {
            setDeletingId(null)
        }
    }

    if (!projectId) {
        return <div className="p-8 text-center text-slate-500">Project not found</div>
    }

    // Filter memories client-side for search (until backend supports text search on list)
    const filteredMemories = memories.filter(m =>
        m.title?.toLowerCase().includes(search.toLowerCase()) ||
        m.content_type?.toLowerCase().includes(search.toLowerCase())
    )

    return (
        <div className="max-w-7xl mx-auto flex flex-col gap-8">
            <DeleteConfirmationModal
                isOpen={deleteModalOpen}
                onClose={() => {
                    if (!deletingId) {
                        setDeleteModalOpen(false)
                        setItemToDelete(null)
                    }
                }}
                onConfirm={handleDelete}
                title="Delete Memory"
                message={`Are you sure you want to delete this memory? This action cannot be undone and will remove all associated graph data.`}
                isDeleting={!!deletingId}
            />
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
                                    <th className="px-6 py-3 font-semibold text-slate-500 dark:text-slate-400">Data Status</th>
                                    <th className="px-6 py-3 font-semibold text-slate-500 dark:text-slate-400">Processing</th>
                                    <th className="px-6 py-3 font-semibold text-slate-500 dark:text-slate-400 text-right">Created</th>
                                    <th className="px-6 py-3 font-semibold text-slate-500 dark:text-slate-400"></th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                                {filteredMemories.length === 0 ? (
                                    <tr>
                                        <td colSpan={6} className="p-8 text-center text-slate-500">
                                            No memories found. Create one to get started.
                                        </td>
                                    </tr>
                                ) : (
                                    filteredMemories.map((memory) => (
                                        <tr key={memory.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors group">
                                            <td className="px-6 py-3">
                                                <div className="flex items-center gap-3">
                                                    <div className="p-2 rounded bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400">
                                                        <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>description</span>
                                                    </div>
                                                    <div>
                                                        <Link to={`/project/${projectId}/memory/${memory.id}`} className="font-medium text-slate-900 dark:text-white hover:text-primary transition-colors">
                                                            {memory.title || 'Untitled'}
                                                        </Link>
                                                        <div className="text-xs text-slate-500">
                                                            <span className="font-mono opacity-70">{memory.id.substring(0, 8)}...</span>
                                                        </div>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-6 py-3 text-slate-600 dark:text-slate-300 capitalize">
                                                {memory.content_type || 'Unknown'}
                                            </td>
                                            <td className="px-6 py-3">
                                                <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${memory.status === 'DISABLED'
                                                    ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                                                    : 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                                                    }`}>
                                                    <span className={`w-1.5 h-1.5 rounded-full ${memory.status === 'DISABLED' ? 'bg-red-500' : 'bg-green-500'
                                                        }`}></span>
                                                    {memory.status || 'ENABLED'}
                                                </span>
                                            </td>
                                            <td className="px-6 py-3">
                                                <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${memory.processing_status === 'FAILED' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                                                    memory.processing_status === 'COMPLETED' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                                                        'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                                                    }`}>
                                                    <span className={`w-1.5 h-1.5 rounded-full ${memory.processing_status === 'FAILED' ? 'bg-red-500' :
                                                        memory.processing_status === 'COMPLETED' ? 'bg-green-500' :
                                                            'bg-yellow-500'
                                                        }`}></span>
                                                    {memory.processing_status || 'PENDING'}
                                                </span>
                                            </td>
                                            <td className="px-6 py-3 text-slate-600 dark:text-slate-300 text-right">
                                                {memory.created_at ? new Date(memory.created_at).toLocaleDateString() : '-'}
                                            </td>
                                            <td className="px-6 py-3 text-right">
                                                <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                    <button
                                                        onClick={() => confirmDelete(memory.id)}
                                                        disabled={deletingId === memory.id}
                                                        className="text-slate-400 hover:text-red-500 p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                                                        title="Delete"
                                                    >
                                                        {deletingId === memory.id ? (
                                                            <span className="material-symbols-outlined animate-spin" style={{ fontSize: '20px' }}>progress_activity</span>
                                                        ) : (
                                                            <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>delete</span>
                                                        )}
                                                    </button>
                                                </div>
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
