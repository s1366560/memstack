import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { memoryAPI } from '../../services/api'
import { MemoryItem } from '../../types/memory'

export const SearchPage: React.FC = () => {
    const { projectId } = useParams()
    const [query, setQuery] = useState('')
    const [results, setResults] = useState<MemoryItem[]>([])
    const [isLoading, setIsLoading] = useState(false)
    const [similarity, setSimilarity] = useState(0.7)
    const [filters, setFilters] = useState({
        timeRange: 'all',
        contentTypes: {
            document: true,
            text: true,
            image: false
        }
    })

    const handleSearch = async () => {
        if (!projectId || !query.trim()) return

        setIsLoading(true)
        try {
            const response = await memoryAPI.search(projectId, {
                query,
                limit: 20,
                // In a real app, we would pass similarity and filters here
            })
            setResults(response.results)
        } catch (error) {
            console.error('Search failed:', error)
        } finally {
            setIsLoading(false)
        }
    }

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            handleSearch()
        }
    }

    // Mock initial search for demo
    useEffect(() => {
        if (projectId) {
            setQuery('Project Alpha architecture decisions')
        }
    }, [projectId])

    return (
        <div className="flex flex-col h-full overflow-hidden bg-background-light dark:bg-background-dark">
            {/* Header Section */}
            <header className="flex flex-col gap-4 px-6 pt-6 pb-2 shrink-0">
                {/* Search Bar Cluster */}
                <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
                    <div className="flex-1 w-full flex gap-3">
                        {/* Search Input */}
                        <label className="flex-1 relative group">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <span className="material-symbols-outlined text-slate-400 group-focus-within:text-primary transition-colors">search</span>
                            </div>
                            <input 
                                className="block w-full pl-10 pr-12 py-3 bg-white dark:bg-surface-dark border border-transparent focus:border-primary/50 ring-0 focus:ring-4 focus:ring-primary/10 rounded-xl text-sm placeholder-slate-400 text-slate-900 dark:text-white shadow-sm transition-all" 
                                placeholder="Search memories by keyword, concept, or ask a question..." 
                                type="text" 
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                onKeyDown={handleKeyDown}
                            />
                            <div className="absolute inset-y-0 right-0 pr-2 flex items-center">
                                <button className="p-1.5 rounded-lg text-slate-400 hover:text-primary hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors" title="Voice Search">
                                    <span className="material-symbols-outlined text-xl">mic</span>
                                </button>
                            </div>
                        </label>
                        {/* Search Mode Toggle */}
                        <div className="hidden lg:flex bg-slate-200 dark:bg-slate-800 p-1 rounded-lg h-[46px] items-center shrink-0">
                            <button className="px-3 py-1.5 h-full rounded-md bg-white dark:bg-surface-dark shadow-sm text-slate-900 dark:text-white text-xs font-semibold transition-all">Smart Search</button>
                            <button className="px-3 py-1.5 h-full rounded-md text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 text-xs font-medium transition-all">Literal</button>
                        </div>
                        {/* Retrieve Button */}
                        <button 
                            onClick={handleSearch}
                            disabled={isLoading}
                            className="h-[46px] px-6 bg-primary hover:bg-primary/90 text-white text-sm font-semibold rounded-lg shadow-md shadow-primary/20 flex items-center gap-2 transition-all active:scale-95 shrink-0 disabled:opacity-70 disabled:cursor-not-allowed"
                        >
                            {isLoading ? (
                                <span className="material-symbols-outlined animate-spin text-lg">progress_activity</span>
                            ) : (
                                <>
                                    <span>Retrieve</span>
                                    <span className="material-symbols-outlined text-lg">arrow_forward</span>
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </header>

            {/* Content Grid */}
            <div className="flex-1 flex overflow-hidden p-6 gap-6 pt-4">
                {/* Left Panel: Filters */}
                <aside className="w-64 flex flex-col gap-6 shrink-0 overflow-y-auto pr-1 pb-4">
                    {/* Time Range */}
                    <div className="flex flex-col gap-3">
                        <div className="flex items-center justify-between">
                            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Time Range</h3>
                            <button className="text-xs text-primary hover:underline">Reset</button>
                        </div>
                        <div className="flex flex-col gap-2">
                            <label className="flex items-center gap-2 p-2 rounded hover:bg-slate-100 dark:hover:bg-slate-800/50 cursor-pointer group transition-colors">
                                <input 
                                    className="text-primary focus:ring-primary bg-transparent border-slate-300 dark:border-slate-600" 
                                    name="time" 
                                    type="radio"
                                    checked={filters.timeRange === 'all'}
                                    onChange={() => setFilters({...filters, timeRange: 'all'})}
                                />
                                <span className="text-sm text-slate-700 dark:text-slate-300 group-hover:text-slate-900 dark:group-hover:text-white">All Time</span>
                            </label>
                            <label className="flex items-center gap-2 p-2 rounded bg-white dark:bg-surface-dark shadow-sm border border-slate-200 dark:border-slate-800 cursor-pointer group">
                                <input 
                                    className="text-primary focus:ring-primary bg-transparent border-slate-300 dark:border-slate-600" 
                                    name="time" 
                                    type="radio"
                                    checked={filters.timeRange === '30days'}
                                    onChange={() => setFilters({...filters, timeRange: '30days'})}
                                />
                                <span className="text-sm font-medium text-slate-900 dark:text-white">Last 30 Days</span>
                            </label>
                        </div>
                    </div>
                    
                    <hr className="border-slate-200 dark:border-slate-800"/>
                    
                    {/* Similarity Slider */}
                    <div className="flex flex-col gap-3">
                        <div className="flex items-center justify-between">
                            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Similarity</h3>
                            <span className="text-xs font-medium text-slate-600 dark:text-slate-300">{Math.round(similarity * 100)}%</span>
                        </div>
                        <div className="px-1">
                            <input 
                                className="w-full h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-primary" 
                                max="1" 
                                min="0" 
                                step="0.1"
                                type="range" 
                                value={similarity}
                                onChange={(e) => setSimilarity(parseFloat(e.target.value))}
                            />
                            <div className="flex justify-between mt-2 text-[10px] text-slate-400">
                                <span>Broad</span>
                                <span>Exact</span>
                            </div>
                        </div>
                    </div>

                    <hr className="border-slate-200 dark:border-slate-800"/>

                    {/* Entity Types */}
                    <div className="flex flex-col gap-3">
                        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Entity Type</h3>
                        <div className="flex flex-col gap-1">
                            <label className="flex items-center gap-2 py-1 cursor-pointer">
                                <input 
                                    checked={filters.contentTypes.document}
                                    onChange={(e) => setFilters({...filters, contentTypes: {...filters.contentTypes, document: e.target.checked}})}
                                    className="rounded border-slate-300 text-primary focus:ring-primary bg-transparent" 
                                    type="checkbox"
                                />
                                <span className="text-sm text-slate-700 dark:text-slate-300">Documents</span>
                            </label>
                            <label className="flex items-center gap-2 py-1 cursor-pointer">
                                <input 
                                    checked={filters.contentTypes.text}
                                    onChange={(e) => setFilters({...filters, contentTypes: {...filters.contentTypes, text: e.target.checked}})}
                                    className="rounded border-slate-300 text-primary focus:ring-primary bg-transparent" 
                                    type="checkbox"
                                />
                                <span className="text-sm text-slate-700 dark:text-slate-300">Text</span>
                            </label>
                        </div>
                    </div>
                </aside>

                {/* Center Stage: Knowledge Graph Placeholder */}
                <section className="flex-1 bg-white dark:bg-surface-dark rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 relative overflow-hidden group flex items-center justify-center">
                    <div className="text-center">
                        <div className="w-20 h-20 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mx-auto mb-4">
                            <span className="material-symbols-outlined text-4xl text-slate-300 dark:text-slate-600">hub</span>
                        </div>
                        <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-2">Knowledge Graph Visualization</h3>
                        <p className="text-sm text-slate-500 max-w-xs mx-auto">
                            Interactive graph visualization of search results and their relationships will appear here.
                        </p>
                    </div>
                    {/* Simulated Nodes for Visual Appeal */}
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full pointer-events-none opacity-20">
                         {/* Abstract background pattern could go here */}
                    </div>
                </section>

                {/* Right Panel: Results List */}
                <aside className="w-80 flex flex-col gap-4 shrink-0 overflow-hidden bg-transparent">
                    {/* Header */}
                    <div className="flex items-center justify-between shrink-0">
                        <h2 className="text-sm font-bold text-slate-900 dark:text-white">Results <span className="text-slate-400 font-normal">({results.length})</span></h2>
                        <div className="flex items-center gap-1 text-slate-500 cursor-pointer hover:text-primary transition-colors">
                            <span className="material-symbols-outlined text-lg">sort</span>
                            <span className="text-xs font-medium">Relevance</span>
                        </div>
                    </div>
                    
                    {/* Cards Container */}
                    <div className="flex flex-col gap-3 overflow-y-auto pb-4 -mr-2 pr-2">
                        {results.length > 0 ? (
                            results.map((result) => (
                                <Link key={result.id} to={`/project/${projectId}/memory/${result.id}`}>
                                    <div className="p-4 bg-white dark:bg-surface-dark rounded-xl shadow-sm border border-transparent hover:border-primary/30 cursor-pointer transition-all group">
                                        <div className="flex items-start justify-between mb-2">
                                            <div className="flex items-center gap-2">
                                                <span className="material-symbols-outlined text-emerald-500 text-lg">description</span>
                                                <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-500/10 px-1.5 py-0.5 rounded capitalize">{result.content_type || 'Text'}</span>
                                            </div>
                                            <span className="text-xs font-bold text-primary">{Math.round((result.score || 0.85) * 100)}% Match</span>
                                        </div>
                                        <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-1 group-hover:text-primary transition-colors line-clamp-1">{result.title}</h3>
                                        <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed mb-3 line-clamp-2">
                                            {result.content}
                                        </p>
                                        <div className="flex items-center justify-between mt-auto">
                                            <div className="flex gap-2">
                                                {result.tags?.slice(0, 2).map(tag => (
                                                    <span key={tag} className="text-[10px] text-slate-400 font-medium">#{tag}</span>
                                                ))}
                                            </div>
                                            <span className="text-[10px] text-slate-400">{new Date(result.created_at).toLocaleDateString()}</span>
                                        </div>
                                    </div>
                                </Link>
                            ))
                        ) : (
                             !isLoading && (
                                <div className="text-center py-10 text-slate-500 text-sm">
                                    No results found. Try adjusting your query or filters.
                                </div>
                             )
                        )}
                        
                        {/* Mock Result Card for Demo if no real results */}
                        {results.length === 0 && !isLoading && (
                             <div className="opacity-50 pointer-events-none">
                                <div className="p-4 bg-white dark:bg-surface-dark rounded-xl shadow-sm border border-transparent mb-3">
                                    <div className="flex items-start justify-between mb-2">
                                        <div className="flex items-center gap-2">
                                            <span className="material-symbols-outlined text-slate-400 text-lg">description</span>
                                            <span className="text-xs font-bold text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">Example</span>
                                        </div>
                                    </div>
                                    <h3 className="text-sm font-semibold text-slate-700 mb-1">Example Result</h3>
                                    <p className="text-xs text-slate-400 mb-3">Search results will appear here...</p>
                                </div>
                             </div>
                        )}
                    </div>
                </aside>
            </div>
        </div>
    )
}
