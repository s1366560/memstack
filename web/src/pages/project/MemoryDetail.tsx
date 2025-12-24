import React, { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { graphitiService } from '../../services/graphitiService'
import { DeleteConfirmationModal } from '../../components/DeleteConfirmationModal'

export const MemoryDetail: React.FC = () => {
    const { projectId, memoryId } = useParams()
    const navigate = useNavigate()
    const [memory, setMemory] = useState<any>(null)
    const [isLoading, setIsLoading] = useState(false)
    const [activeTab, setActiveTab] = useState<'content' | 'metadata' | 'history' | 'raw'>('content')
    const [deleteModalOpen, setDeleteModalOpen] = useState(false)
    const [isDeleting, setIsDeleting] = useState(false)

    useEffect(() => {
        const fetchMemory = async () => {
            if (projectId && memoryId) {
                setIsLoading(true)
                try {
                    const data = await graphitiService.getEpisode(decodeURIComponent(memoryId))
                    setMemory(data)
                } catch (error) {
                    console.error('Failed to fetch memory:', error)
                } finally {
                    setIsLoading(false)
                }
            }
        }
        fetchMemory()
    }, [projectId, memoryId])

    if (!projectId || !memoryId) {
        return <div className="p-8 text-center text-slate-500">Invalid URL parameters</div>
    }

    if (isLoading) {
        return <div className="p-8 text-center text-slate-500">Loading memory details...</div>
    }

    if (!memory) {
        return <div className="p-8 text-center text-slate-500">Memory not found</div>
    }

    const handleDelete = async () => {
        if (!projectId || !memoryId) return
        
        setIsDeleting(true)
        try {
            await graphitiService.deleteEpisode(decodeURIComponent(memoryId))
            navigate(`/project/${projectId}/memories`)
        } catch (error) {
            console.error('Failed to delete memory:', error)
            alert('Failed to delete memory')
            setIsDeleting(false)
            setDeleteModalOpen(false)
        }
    }

    return (
        <div className="flex h-full overflow-hidden">
            <DeleteConfirmationModal
                isOpen={deleteModalOpen}
                onClose={() => setDeleteModalOpen(false)}
                onConfirm={handleDelete}
                title="Delete Memory"
                message="Are you sure you want to delete this memory? This action cannot be undone and will remove all associated graph data."
                isDeleting={isDeleting}
            />
            {/* Main Content Area */}
            <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
                {/* Top Navigation Bar (Breadcrumbs + Toolbar) */}
                <header className="h-16 border-b border-slate-200 dark:border-slate-800 bg-surface-light/80 dark:bg-surface-dark/80 backdrop-blur-md flex items-center justify-between px-6 z-10 sticky top-0">
                    {/* Breadcrumbs */}
                    <div className="flex items-center gap-2 overflow-hidden whitespace-nowrap">
                        <Link to={`/project/${projectId}`} className="text-slate-500 hover:text-primary text-sm font-medium transition-colors">Project</Link>
                        <span className="text-slate-400 text-sm">/</span>
                        <Link to={`/project/${projectId}/memories`} className="text-slate-500 hover:text-primary text-sm font-medium transition-colors">Memories</Link>
                        <span className="text-slate-400 text-sm">/</span>
                        <div className="flex items-center gap-2">
                            <span className="text-slate-900 dark:text-white text-sm font-medium truncate max-w-[200px]">{memory.name || 'Untitled'}</span>
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                                Synced
                            </span>
                        </div>
                    </div>
                    {/* Toolbar Actions */}
                    <div className="flex items-center gap-1">
                        <button className="p-2 text-slate-500 hover:text-primary hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800 rounded-lg transition-all" title="Edit">
                            <span className="material-symbols-outlined text-[20px]">edit</span>
                        </button>
                        <button onClick={() => setDeleteModalOpen(true)} className="p-2 text-slate-500 hover:text-red-600 hover:bg-red-50 dark:text-slate-400 dark:hover:bg-red-900/20 dark:hover:text-red-400 rounded-lg transition-all" title="Delete">
                            <span className="material-symbols-outlined text-[20px]">delete</span>
                        </button>
                        <div className="w-px h-6 bg-slate-200 dark:bg-slate-700 mx-1"></div>
                        <button className="p-2 text-slate-500 hover:text-primary hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800 rounded-lg transition-all" title="Share">
                            <span className="material-symbols-outlined text-[20px]">share</span>
                        </button>
                        <button className="p-2 text-slate-500 hover:text-primary hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800 rounded-lg transition-all" title="Export">
                            <span className="material-symbols-outlined text-[20px]">download</span>
                        </button>
                    </div>
                </header>

                {/* Scrollable Content */}
                <div className="flex-1 overflow-y-auto bg-background-light dark:bg-background-dark">
                    <div className="max-w-5xl mx-auto p-6 md:p-8 flex flex-col gap-6">
                        {/* Memory Card */}
                        <div className="bg-white dark:bg-surface-dark rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden">
                            {/* Profile Header Section */}
                            <div className="p-6 md:p-8 pb-0">
                                <div className="flex flex-col md:flex-row gap-6 items-start md:items-center justify-between">
                                    <div className="flex gap-5 items-center">
                                        <div className="relative">
                                            <div className="bg-center bg-no-repeat bg-cover rounded-full h-16 w-16 md:h-20 md:w-20 ring-4 ring-slate-50 dark:ring-slate-800 shadow-sm bg-slate-200 flex items-center justify-center text-slate-400">
                                                <span className="material-symbols-outlined text-3xl">description</span>
                                            </div>
                                            <div className="absolute -bottom-1 -right-1 bg-white dark:bg-slate-900 rounded-full p-1 shadow-sm border border-slate-100 dark:border-slate-700">
                                                <div className="bg-blue-500 rounded-full h-3 w-3" title="Online"></div>
                                            </div>
                                        </div>
                                        <div className="flex flex-col justify-center gap-1">
                                            <h1 className="text-slate-900 dark:text-white text-2xl md:text-3xl font-bold leading-tight tracking-tight">{memory.name || 'Untitled'}</h1>
                                            <p className="text-slate-500 dark:text-slate-400 text-sm md:text-base font-normal flex items-center gap-2 flex-wrap">
                                                <span>Type: <span className="text-slate-900 dark:text-slate-200 font-medium capitalize">{memory.source_type || 'Unknown'}</span></span>
                                                <span className="w-1 h-1 bg-slate-300 rounded-full"></span>
                                                <span>{new Date(memory.created_at).toLocaleDateString()}</span>
                                            </p>
                                        </div>
                                    </div>
                                    <button className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg font-medium text-sm flex items-center gap-2 transition-colors shadow-sm shadow-primary/20">
                                        <span className="material-symbols-outlined text-[18px]">edit_note</span>
                                        Edit Memory
                                    </button>
                                </div>
                            </div>
                            {/* Tabs */}
                            <div className="mt-8 px-6 md:px-8 border-b border-slate-200 dark:border-slate-800">
                                <div className="flex gap-8 overflow-x-auto">
                                    <button
                                        onClick={() => setActiveTab('content')}
                                        className={`relative flex items-center justify-center pb-4 font-semibold text-sm tracking-wide transition-colors ${activeTab === 'content'
                                            ? 'text-primary border-b-2 border-primary'
                                            : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
                                            }`}
                                    >
                                        Content
                                    </button>
                                    <button
                                        onClick={() => setActiveTab('metadata')}
                                        className={`relative flex items-center justify-center pb-4 font-semibold text-sm tracking-wide transition-colors ${activeTab === 'metadata'
                                            ? 'text-primary border-b-2 border-primary'
                                            : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
                                            }`}
                                    >
                                        Metadata
                                    </button>
                                    <button
                                        onClick={() => setActiveTab('raw')}
                                        className={`relative flex items-center justify-center pb-4 font-semibold text-sm tracking-wide transition-colors ${activeTab === 'raw'
                                            ? 'text-primary border-b-2 border-primary'
                                            : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
                                            }`}
                                    >
                                        Raw Data
                                    </button>
                                </div>
                            </div>
                            {/* Content Body */}
                            <div className="p-6 md:p-8 text-slate-800 dark:text-slate-200 leading-relaxed text-base md:text-lg min-h-[300px]">
                                {activeTab === 'content' && (
                                    <div className="prose dark:prose-invert max-w-none whitespace-pre-wrap">
                                        {memory.content || 'No content available.'}
                                    </div>
                                )}
                                {activeTab === 'metadata' && (
                                    <div className="grid grid-cols-2 gap-4 text-sm">
                                        <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                                            <span className="block text-xs font-bold text-slate-500 uppercase mb-1">ID (UUID)</span>
                                            <span className="font-mono break-all">{memory.uuid}</span>
                                        </div>
                                        <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                                            <span className="block text-xs font-bold text-slate-500 uppercase mb-1">Type</span>
                                            <span className="capitalize">{memory.source_type}</span>
                                        </div>
                                        <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg col-span-2">
                                            <span className="block text-xs font-bold text-slate-500 uppercase mb-1">Custom Metadata</span>
                                            <pre className="text-xs font-mono overflow-auto">{JSON.stringify(memory.metadata || {}, null, 2)}</pre>
                                        </div>
                                    </div>
                                )}
                                {activeTab === 'raw' && (
                                    <div className="bg-slate-900 text-slate-200 p-4 rounded-lg font-mono text-xs overflow-auto">
                                        <pre>{JSON.stringify(memory, null, 2)}</pre>
                                    </div>
                                )}
                            </div>
                            {/* Footer / Activity Snippet */}
                            <div className="bg-slate-50 dark:bg-slate-800/50 px-6 py-4 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                                <div className="flex items-center gap-2">
                                    <span className="material-symbols-outlined text-[16px]">history</span>
                                    Created {new Date(memory.created_at).toLocaleString()}
                                </div>
                                <div>
                                    ID: {memory.uuid ? memory.uuid.slice(0, 12) : 'N/A'}...
                                </div>
                            </div>
                        </div>
                        {/* Spacer for bottom scroll */}
                        <div className="h-10"></div>
                    </div>
                </div>
            </main>

            {/* Right Sidebar: Context */}
            <aside className="w-80 bg-surface-light dark:bg-surface-dark border-l border-slate-200 dark:border-slate-800 hidden xl:flex flex-col flex-shrink-0 z-10">
                <div className="p-5 border-b border-slate-200 dark:border-slate-800">
                    <h2 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
                        <span className="material-symbols-outlined text-primary text-[18px]">hub</span>
                        Knowledge Context
                    </h2>
                </div>
                <div className="overflow-y-auto flex-1 p-5 flex flex-col gap-6">
                    {/* Tags */}
                    <div className="flex flex-col gap-3">
                        <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200">Tags</h3>
                        <div className="flex flex-wrap gap-2">
                            {memory.metadata?.tags?.map((tag: string) => (
                                <span key={tag} className="px-2.5 py-1 rounded-md text-xs font-medium bg-slate-100 text-slate-600 hover:bg-slate-200 cursor-pointer transition-colors dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700">#{tag}</span>
                            )) || <span className="text-xs text-slate-500">No tags</span>}
                        </div>
                    </div>
                </div>
            </aside>
        </div>
    )
}
