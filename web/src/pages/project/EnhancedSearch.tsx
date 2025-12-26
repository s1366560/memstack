import React, { useState, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import { graphitiService } from '../../services/graphitiService'
import { CytoscapeGraph } from '../../components/CytoscapeGraph'
import { useProjectStore } from '../../stores/project'
import {
    Search,
    Mic,
    ArrowRight,
    Sliders,
    Info,
    HelpCircle,
    Network,
    Plus,
    Minus,
    Target,
    Maximize,
    Grid,
    List,
    ArrowUpDown,
    FileText,
    MessageSquare,
    Image as ImageIcon,
    Link as LinkIcon,
    ChevronDown,
    AlertCircle,
    Folder,
    X,
    Filter,
    PanelRightClose,
    PanelRightOpen,
    Copy,
    Check
} from 'lucide-react'

interface SearchResult {
    content: string
    score: number
    metadata: {
        type: string
        name?: string
        uuid?: string
        depth?: number
        created_at?: string
        [key: string]: any
    }
    source: string
}

export const EnhancedSearch: React.FC = () => {
    const { projectId } = useParams()
    const { currentProject } = useProjectStore()

    // State
    const [query, setQuery] = useState('')
    const [results, setResults] = useState<SearchResult[]>([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [isSearchFocused, setIsSearchFocused] = useState(false)

    // Configuration State
    const [retrievalMode, setRetrievalMode] = useState<'hybrid' | 'nodeDistance'>('hybrid')
    const [strategy, setStrategy] = useState('COMBINED_HYBRID_SEARCH_RRF')
    const [focalNode, setFocalNode] = useState('')
    const [crossEncoder, setCrossEncoder] = useState('bge')
    const [timeRange, setTimeRange] = useState('last30')
    const [configTab, setConfigTab] = useState<'params' | 'filters'>('params')
    const [showMobileConfig, setShowMobileConfig] = useState(false)
    const [isConfigOpen, setIsConfigOpen] = useState(true)
    const [isResultsCollapsed, setIsResultsCollapsed] = useState(false)
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
    const [copiedId, setCopiedId] = useState<string | null>(null)
    const [isSubgraphMode, setIsSubgraphMode] = useState(false)

    const handleCopyId = (id: string, e: React.MouseEvent) => {
        e.stopPropagation()
        navigator.clipboard.writeText(id)
        setCopiedId(id)
        setTimeout(() => setCopiedId(null), 2000)
    }

    const handleSearch = async () => {
        if (!query) return

        setLoading(true)
        setError(null)

        try {
            let since = undefined
            if (timeRange === 'last30') {
                const date = new Date()
                date.setDate(date.getDate() - 30)
                since = date.toISOString()
            }

            const data = await graphitiService.advancedSearch({
                query,
                strategy,
                project_id: projectId,
                focal_node_uuid: retrievalMode === 'nodeDistance' ? focalNode : undefined,
                reranker: crossEncoder,
                since,
            })

            // Map the raw results to our display format
            const mappedResults = (data.results || []).map((item: any) => ({
                content: item.content || item.text || 'No content',
                score: item.score || 0,
                metadata: item.metadata || {},
                source: item.source || 'unknown'
            }))

            setResults(mappedResults)
            // Expand results by default when search is done
            if (mappedResults.length > 0) {
                setIsResultsCollapsed(false)
                setIsSubgraphMode(true)
            }
        } catch (err) {
            console.error('Search failed:', err)
            setError('Search failed. Please try again.')
        } finally {
            setLoading(false)
        }
    }

    // Extract node IDs for graph highlighting
    const highlightNodeIds = useMemo(() => {
        const ids = new Set<string>()
        results.forEach(result => {
            if (result.metadata.uuid) {
                ids.add(result.metadata.uuid)
            }
        })
        return Array.from(ids)
    }, [results])

    // Reset subgraph mode when no results
    React.useEffect(() => {
        if (highlightNodeIds.length === 0) {
            setIsSubgraphMode(false)
        }
    }, [highlightNodeIds])

    const getScoreColor = (score: number) => {
        if (score >= 0.8) return 'text-emerald-500'
        if (score >= 0.6) return 'text-violet-500'
        if (score >= 0.4) return 'text-amber-500'
        return 'text-slate-400'
    }

    const getIconForType = (type: string) => {
        switch (type?.toLowerCase()) {
            case 'document':
            case 'pdf':
                return <FileText className="w-5 h-5" />
            case 'thread':
            case 'slack':
                return <MessageSquare className="w-5 h-5" />
            case 'asset':
            case 'img':
            case 'image':
                return <ImageIcon className="w-5 h-5" />
            case 'reference':
            case 'web':
            case 'jira':
                return <LinkIcon className="w-5 h-5" />
            default:
                return <FileText className="w-5 h-5" />
        }
    }

    return (
        <div className="bg-slate-50 dark:bg-[#121520] text-slate-900 dark:text-white font-sans h-full flex overflow-hidden">
            {/* Sidebar would go here if not provided by layout */}

            <main className="flex-1 flex flex-col min-w-0 bg-slate-50 dark:bg-[#121520]">
                {/* Header */}
                <header className="flex flex-col gap-4 px-6 pt-6 pb-2 shrink-0">
                    <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
                        <div className="flex-1 w-full flex gap-3">
                            <button
                                onClick={() => setShowMobileConfig(true)}
                                className="lg:hidden p-3 bg-white dark:bg-[#1e212b] border border-slate-200 dark:border-slate-800 rounded-xl text-slate-500 hover:text-blue-600 transition-colors shadow-sm"
                            >
                                <Sliders className="w-5 h-5" />
                            </button>
                            <label className="flex-1 relative group">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Search className="w-5 h-5 text-slate-400 group-focus-within:text-blue-600 transition-colors" />
                                </div>
                                <input
                                    className="block w-full pl-10 pr-12 py-3 bg-white dark:bg-[#1e212b] border border-transparent focus:border-blue-600/50 ring-0 focus:ring-4 focus:ring-blue-600/10 rounded-xl text-sm placeholder-slate-400 text-slate-900 dark:text-white shadow-sm transition-all"
                                    placeholder={isSearchFocused ? '' : "Search memories by keyword, concept, or ask a question..."}
                                    type="text"
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    onFocus={() => setIsSearchFocused(true)}
                                    onBlur={() => setIsSearchFocused(false)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                                />
                                <div className="absolute inset-y-0 right-0 pr-2 flex items-center">
                                    <button className="p-1.5 rounded-lg text-slate-400 hover:text-blue-600 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors" title="Voice Search">
                                        <Mic className="w-5 h-5" />
                                    </button>
                                </div>
                            </label>
                            <button
                                onClick={handleSearch}
                                disabled={loading}
                                className="h-[46px] px-6 bg-blue-600 hover:bg-blue-600/90 text-white text-sm font-semibold rounded-lg shadow-md shadow-blue-600/20 flex items-center gap-2 transition-all active:scale-95 shrink-0 disabled:opacity-50"
                            >
                                <span>{loading ? 'Searching...' : 'Retrieve'}</span>
                                <ArrowRight className="w-5 h-5" />
                            </button>
                            <div className="hidden lg:flex items-center">
                                <button
                                    onClick={() => setIsConfigOpen(!isConfigOpen)}
                                    className={`p-3 h-[46px] rounded-lg transition-colors border ${isConfigOpen
                                        ? 'border-transparent text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
                                        : 'border-blue-200 dark:border-blue-900 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                                        }`}
                                    title={isConfigOpen ? "Collapse Config" : "Expand Config"}
                                >
                                    {isConfigOpen ? <PanelRightClose className="w-5 h-5" /> : <PanelRightOpen className="w-5 h-5" />}
                                </button>
                            </div>
                        </div>
                    </div>
                </header>

                <div className="flex-1 flex overflow-hidden p-6 gap-6 pt-2">
                    {/* Config Sidebar */}
                    {/* Config Sidebar */}
                    {/* Mobile Backdrop */}
                    {showMobileConfig && (
                        <div
                            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
                            onClick={() => setShowMobileConfig(false)}
                        />
                    )}

                    <aside className={`
                        fixed inset-y-0 right-0 z-50 w-80 bg-slate-50 dark:bg-[#121520] lg:bg-transparent transition-all duration-300 ease-in-out lg:relative lg:transform-none lg:z-0 flex flex-col gap-6 shrink-0 h-full
                        ${showMobileConfig ? 'translate-x-0' : 'translate-x-full lg:translate-x-0'}
                        ${!isConfigOpen && 'lg:w-0 lg:overflow-hidden lg:opacity-0 lg:p-0'}
                    `}>
                        <div className="flex-1 flex flex-col gap-5 p-5 bg-white dark:bg-[#1e212b] rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-y-auto custom-scrollbar h-full">
                            <div className="flex items-center justify-between pb-2 border-b border-slate-200 dark:border-slate-800 shrink-0">
                                <h2 className="text-sm font-bold text-slate-800 dark:text-white flex items-center gap-2">
                                    <Sliders className="w-5 h-5 text-blue-600" />
                                    Config
                                </h2>
                                <div className="flex items-center gap-2">
                                    <span className="text-[10px] px-1.5 py-0.5 bg-blue-600/10 text-blue-600 rounded font-medium">Advanced</span>
                                    <button
                                        onClick={() => setShowMobileConfig(false)}
                                        className="lg:hidden p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-500 transition-colors"
                                    >
                                        <X className="w-5 h-5" />
                                    </button>
                                </div>
                            </div>

                            {/* Internal Tabs */}
                            <div className="flex p-1 bg-slate-100 dark:bg-slate-800 rounded-lg shrink-0">
                                <button
                                    onClick={() => setConfigTab('params')}
                                    className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-all flex items-center justify-center gap-1.5 ${configTab === 'params' ? 'bg-white dark:bg-[#1e212b] text-blue-600 dark:text-white shadow-sm' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'}`}
                                >
                                    <Sliders className="w-3.5 h-3.5" />
                                    Parameters
                                </button>
                                <button
                                    onClick={() => setConfigTab('filters')}
                                    className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-all flex items-center justify-center gap-1.5 ${configTab === 'filters' ? 'bg-white dark:bg-[#1e212b] text-blue-600 dark:text-white shadow-sm' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'}`}
                                >
                                    <Filter className="w-3.5 h-3.5" />
                                    Filters
                                </button>
                            </div>

                            {/* Tab Content */}
                            <div className="flex-1 flex flex-col gap-6 overflow-y-auto custom-scrollbar pr-1">
                                {configTab === 'params' ? (
                                    <>
                                        {/* Retrieval Mode */}
                                        <div className="flex flex-col gap-2">
                                            <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Retrieval Mode</label>
                                            <div className="bg-slate-100 dark:bg-slate-800 p-1 rounded-lg flex">
                                                <button
                                                    onClick={() => setRetrievalMode('hybrid')}
                                                    className={`flex-1 py-2 px-2 rounded-md shadow-sm text-xs font-semibold transition-all ${retrievalMode === 'hybrid' ? 'bg-white dark:bg-[#1e212b] text-blue-600 dark:text-white ring-1 ring-black/5 dark:ring-white/10' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'}`}
                                                >
                                                    Hybrid
                                                </button>
                                                <button
                                                    onClick={() => setRetrievalMode('nodeDistance')}
                                                    className={`flex-1 py-2 px-2 rounded-md text-xs font-medium transition-all ${retrievalMode === 'nodeDistance' ? 'bg-white dark:bg-[#1e212b] text-blue-600 dark:text-white ring-1 ring-black/5 dark:ring-white/10' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'}`}
                                                >
                                                    Node Distance
                                                </button>
                                            </div>
                                        </div>

                                        {/* Strategy Recipe */}
                                        <div className="flex flex-col gap-2">
                                            <div className="flex items-center justify-between">
                                                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Strategy Recipe</label>
                                                <Info className="w-4 h-4 text-slate-400 cursor-help" />
                                            </div>
                                            <div className="relative">
                                                <select
                                                    value={strategy}
                                                    onChange={(e) => setStrategy(e.target.value)}
                                                    className="w-full text-xs py-2.5 pl-3 pr-8 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-1 focus:ring-blue-600 focus:border-blue-600 text-slate-700 dark:text-slate-200 appearance-none shadow-sm cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-700/50 transition-colors"
                                                >
                                                    <option value="COMBINED_HYBRID_SEARCH_RRF">Combined Hybrid (RRF)</option>
                                                    <option value="EDGE_HYBRID_SEARCH_CROSS_ENCODER">Edge Hybrid (Cross-Encoder)</option>
                                                    <option value="HYBRID_MMR">Hybrid Search (MMR)</option>
                                                    <option value="STANDARD_DENSE">Standard Dense Only</option>
                                                </select>
                                                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-500">
                                                    <ChevronDown className="w-4 h-4" />
                                                </div>
                                            </div>
                                        </div>

                                        {/* Focal Node UUID */}
                                        <div className="flex flex-col gap-2">
                                            <div className="flex items-center justify-between">
                                                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Focal Node UUID</label>
                                                <HelpCircle className="w-4 h-4 text-slate-400 cursor-help" />
                                            </div>
                                            <div className="relative group">
                                                <input
                                                    className="w-full text-xs py-2.5 pl-9 pr-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-1 focus:ring-blue-600 focus:border-blue-600 text-slate-700 dark:text-slate-200 placeholder-slate-400 transition-shadow"
                                                    placeholder="e.g. node-1234-uuid..."
                                                    type="text"
                                                    value={focalNode}
                                                    onChange={(e) => setFocalNode(e.target.value)}
                                                    disabled={retrievalMode !== 'nodeDistance'}
                                                />
                                                <Network className="absolute left-2.5 top-2.5 w-4 h-4 text-slate-400 group-focus-within:text-blue-600 transition-colors" />
                                            </div>
                                        </div>

                                        {/* Cross-Encoder Client */}
                                        <div className="flex flex-col gap-2">
                                            <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Cross-Encoder Client</label>
                                            <div className="relative">
                                                <select
                                                    value={crossEncoder}
                                                    onChange={(e) => setCrossEncoder(e.target.value)}
                                                    className="w-full text-xs py-2.5 pl-3 pr-8 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-1 focus:ring-blue-600 focus:border-blue-600 text-slate-700 dark:text-slate-200 appearance-none shadow-sm cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-700/50 transition-colors"
                                                >
                                                    <option value="openai">OpenAI (text-embedding-3)</option>
                                                    <option value="gemini">Google Gemini 1.5</option>
                                                    <option value="bge">BGE-M3 (Local Optimized)</option>
                                                </select>
                                                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-500">
                                                    <ChevronDown className="w-4 h-4" />
                                                </div>
                                            </div>
                                        </div>
                                    </>
                                ) : (
                                    <>
                                        {/* Time Range */}
                                        <div className="flex flex-col gap-3">
                                            <div className="flex items-center justify-between">
                                                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Time Range</h3>
                                                <button onClick={() => setTimeRange('last30')} className="text-xs text-blue-600 hover:underline font-medium">Reset</button>
                                            </div>
                                            <div className="flex flex-col gap-1.5">
                                                <label className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer group transition-colors">
                                                    <input
                                                        className="text-blue-600 focus:ring-blue-600 bg-white dark:bg-[#1e212b] border-slate-300 dark:border-slate-600 w-3.5 h-3.5"
                                                        name="time"
                                                        type="radio"
                                                        checked={timeRange === 'all'}
                                                        onChange={() => setTimeRange('all')}
                                                    />
                                                    <span className="text-xs text-slate-700 dark:text-slate-300">All Time</span>
                                                </label>
                                                <label className={`flex items-center gap-2 px-2 py-1.5 rounded cursor-pointer group ${timeRange === 'last30' ? 'bg-blue-600/5 border border-blue-600/10' : 'hover:bg-slate-50 dark:hover:bg-slate-800'}`}>
                                                    <input
                                                        className="text-blue-600 focus:ring-blue-600 bg-white dark:bg-[#1e212b] border-slate-300 dark:border-slate-600 w-3.5 h-3.5"
                                                        name="time"
                                                        type="radio"
                                                        checked={timeRange === 'last30'}
                                                        onChange={() => setTimeRange('last30')}
                                                    />
                                                    <span className={`text-xs font-medium ${timeRange === 'last30' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-700 dark:text-slate-300'}`}>Last 30 Days</span>
                                                </label>
                                                <label className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer group transition-colors">
                                                    <input
                                                        className="text-blue-600 focus:ring-blue-600 bg-white dark:bg-[#1e212b] border-slate-300 dark:border-slate-600 w-3.5 h-3.5"
                                                        name="time"
                                                        type="radio"
                                                        checked={timeRange === 'custom'}
                                                        onChange={() => setTimeRange('custom')}
                                                    />
                                                    <span className="text-xs text-slate-700 dark:text-slate-300">Custom Range</span>
                                                </label>
                                            </div>
                                        </div>

                                        <div className="h-px bg-slate-100 dark:bg-slate-700 my-1"></div>

                                        {/* Tags */}
                                        <div className="flex flex-col gap-3">
                                            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Tags</h3>
                                            <div className="flex flex-wrap gap-1.5">
                                                <button className="px-2 py-1 rounded-md bg-blue-600/10 text-blue-600 border border-blue-600/10 text-[10px] font-semibold transition-colors">#architecture</button>
                                                <button className="px-2 py-1 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700 border border-transparent text-[10px] font-medium transition-colors">#meeting</button>
                                                <button className="px-2 py-1 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700 border border-transparent text-[10px] font-medium transition-colors">#decisions</button>
                                                <button className="px-2 py-1 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700 border border-transparent text-[10px] font-medium transition-colors">#Q3</button>
                                                <button className="px-2 py-1 rounded-md bg-white dark:bg-slate-800 text-slate-400 dark:text-slate-500 border border-dashed border-slate-300 dark:border-slate-600 hover:border-blue-600/50 hover:text-blue-600 text-[10px] font-medium transition-colors flex items-center gap-1">
                                                    <Plus className="w-3 h-3" /> Add
                                                </button>
                                            </div>
                                        </div>
                                    </>
                                )}
                            </div>
                        </div>
                    </aside>

                    <div className="flex-1 flex flex-col gap-4 min-w-0 overflow-hidden">
                        {/* Error Message */}
                        {error && (
                            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 flex items-center gap-2">
                                <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
                                <span className="text-sm text-red-800 dark:text-red-400">{error}</span>
                            </div>
                        )}

                        {/* Graph View */}
                        <section className={`
                            bg-white dark:bg-[#1e212b] rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 relative overflow-hidden group transition-all duration-300 ease-in-out
                            ${isResultsCollapsed ? 'flex-1' : 'h-[55%]'}
                        `}>
                            <div className="absolute top-4 left-4 z-10 flex gap-2">
                                <div className="bg-white/90 dark:bg-slate-800/90 backdrop-blur border border-slate-200 dark:border-slate-700 rounded-lg shadow-sm p-1 flex gap-1">
                                    <button
                                        onClick={() => setIsResultsCollapsed(!isResultsCollapsed)}
                                        className={`p-1.5 hover:bg-slate-100 dark:hover:bg-slate-700 rounded text-slate-600 dark:text-slate-400 transition-colors ${isResultsCollapsed ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20' : ''}`}
                                        title={isResultsCollapsed ? "Show Results" : "Expand Graph"}
                                    >
                                        <Maximize className="w-4 h-4" />
                                    </button>
                                    {highlightNodeIds.length > 0 && (
                                        <button
                                            onClick={() => setIsSubgraphMode(!isSubgraphMode)}
                                            className={`p-1.5 hover:bg-slate-100 dark:hover:bg-slate-700 rounded text-slate-600 dark:text-slate-400 transition-colors ${isSubgraphMode ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20' : ''}`}
                                            title={isSubgraphMode ? "Show Full Graph" : "Show Result Subgraph"}
                                        >
                                            <Network className="w-4 h-4" />
                                        </button>
                                    )}
                                </div>
                            </div>

                            {/* Real Graph Visualization */}
                            <div className="w-full h-full relative">
                                <CytoscapeGraph
                                    projectId={projectId}
                                    tenantId={currentProject?.tenant_id}
                                    highlightNodeIds={highlightNodeIds}
                                    subgraphNodeIds={isSubgraphMode ? highlightNodeIds : undefined}
                                    includeCommunities={true}
                                    onNodeClick={(node) => {
                                        if (node?.uuid) {
                                            setFocalNode(node.uuid)
                                            setRetrievalMode('nodeDistance')
                                        }
                                    }}
                                />
                            </div>
                        </section>

                        {/* Results List */}
                        <section className={`
                            flex flex-col gap-3 min-h-0 transition-all duration-300 ease-in-out
                            ${isResultsCollapsed ? 'h-10 overflow-hidden' : 'flex-1'}
                        `}>
                            <div
                                className="flex items-center justify-between shrink-0 px-1 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50 rounded-lg p-1 transition-colors select-none"
                                onClick={() => setIsResultsCollapsed(!isResultsCollapsed)}
                            >
                                <div className="flex items-center gap-3">
                                    <div className={`transition-transform duration-300 ${isResultsCollapsed ? '-rotate-90' : 'rotate-0'}`}>
                                        <ChevronDown className="w-4 h-4 text-slate-400" />
                                    </div>
                                    <h2 className="text-base font-bold text-slate-900 dark:text-white">Retrieval Results</h2>
                                    <span className="px-2 py-0.5 rounded-full bg-slate-200 dark:bg-slate-700 text-xs font-semibold text-slate-600 dark:text-slate-300">{results.length} items</span>
                                </div>
                                <div className="flex items-center gap-3" onClick={e => e.stopPropagation()}>
                                    <div className="flex items-center bg-white dark:bg-[#1e212b] border border-slate-200 dark:border-slate-800 rounded-lg p-0.5">
                                        <button
                                            onClick={() => setViewMode('grid')}
                                            className={`p-1.5 rounded shadow-sm transition-colors ${viewMode === 'grid' ? 'bg-slate-100 dark:bg-slate-700 text-slate-900 dark:text-white' : 'hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-500 dark:text-slate-400'}`}
                                        >
                                            <Grid className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => setViewMode('list')}
                                            className={`p-1.5 rounded shadow-sm transition-colors ${viewMode === 'list' ? 'bg-slate-100 dark:bg-slate-700 text-slate-900 dark:text-white' : 'hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-500 dark:text-slate-400'}`}
                                        >
                                            <List className="w-4 h-4" />
                                        </button>
                                    </div>
                                    <div className="h-4 w-px bg-slate-300 dark:bg-slate-700"></div>
                                    <div className="flex items-center gap-1 text-slate-500 cursor-pointer hover:text-blue-600 transition-colors group">
                                        <ArrowUpDown className="w-4 h-4 text-slate-400 group-hover:text-blue-600" />
                                        <span className="text-xs font-medium">Relevance</span>
                                    </div>
                                </div>
                            </div>

                            <div className={`overflow-y-auto custom-scrollbar pr-2 flex-1 -mr-2 ${isResultsCollapsed ? 'opacity-0' : 'opacity-100'} transition-opacity duration-200`}>
                                <div className={`gap-4 pb-4 ${viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3' : 'flex flex-col'}`}>
                                    {/* Mock Result 1 (Static Example if no results) */}
                                    {results.length === 0 && !loading && (
                                        <>
                                            <div className={`
                                                bg-white dark:bg-[#1e212b] rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 hover:border-blue-600/40 dark:hover:border-blue-600/40 cursor-pointer transition-all group hover:shadow-md hover:shadow-blue-600/5
                                                ${viewMode === 'grid' ? 'p-4 flex flex-col h-full' : 'p-3 flex items-start gap-4'}
                                            `}>
                                                <div className={`flex ${viewMode === 'grid' ? 'items-start justify-between mb-3' : 'shrink-0'}`}>
                                                    <div className="flex items-center gap-2">
                                                        <div className="p-2 rounded-lg bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                                                            <FileText className="w-5 h-5" />
                                                        </div>
                                                        {viewMode === 'grid' && (
                                                            <div className="flex flex-col">
                                                                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Document</span>
                                                                <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400">PDF</span>
                                                            </div>
                                                        )}
                                                    </div>
                                                    {viewMode === 'grid' && (
                                                        <div className="flex flex-col items-end">
                                                            <span className="text-sm font-bold text-blue-600">98%</span>
                                                            <span className="text-[10px] text-slate-400">Relevance</span>
                                                        </div>
                                                    )}
                                                </div>

                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center justify-between gap-2 mb-1">
                                                        <h3 className="text-sm font-semibold text-slate-900 dark:text-white group-hover:text-blue-600 transition-colors line-clamp-1">Architecture Specs v2.pdf</h3>
                                                        {viewMode === 'list' && (
                                                            <div className="flex items-center gap-3 shrink-0">
                                                                <div
                                                                    className="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded text-[10px] text-slate-500 font-mono cursor-pointer hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                                                                    onClick={(e) => handleCopyId('node-1234-5678', e)}
                                                                    title="Copy Node ID"
                                                                >
                                                                    <span>node-123...</span>
                                                                    {copiedId === 'node-1234-5678' ? (
                                                                        <Check className="w-3 h-3 text-emerald-500" />
                                                                    ) : (
                                                                        <Copy className="w-3 h-3 hover:text-blue-600" />
                                                                    )}
                                                                </div>
                                                                <div className="flex flex-col items-end">
                                                                    <span className="text-sm font-bold text-blue-600 leading-none">98%</span>
                                                                </div>
                                                            </div>
                                                        )}
                                                    </div>

                                                    {/* Node ID for Grid View */}
                                                    {viewMode === 'grid' && (
                                                        <div className="flex items-center gap-1.5 mb-2">
                                                            <span
                                                                className="text-[10px] text-slate-400 font-mono bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded flex items-center gap-1.5 group/id cursor-pointer hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                                                                onClick={(e) => handleCopyId('node-8f7a-2b3c', e)}
                                                                title="Copy Node ID"
                                                            >
                                                                node-8f7a-2b3c
                                                                {copiedId === 'node-8f7a-2b3c' ? (
                                                                    <Check className="w-3 h-3 text-emerald-500" />
                                                                ) : (
                                                                    <Copy className="w-3 h-3 hover:text-blue-600 opacity-0 group-hover/id:opacity-100 transition-opacity" />
                                                                )}
                                                            </span>
                                                        </div>
                                                    )}

                                                    <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed mb-3 line-clamp-2">
                                                        ...final decision regarding the <mark className="bg-yellow-100 dark:bg-yellow-900/30 text-slate-900 dark:text-white px-0.5 rounded">architecture</mark> of Project Alpha was to utilize microservices for better scalability...
                                                    </p>

                                                    <div className={`flex items-center justify-between ${viewMode === 'grid' ? 'mt-auto pt-3 border-t border-slate-50 dark:border-slate-800' : ''}`}>
                                                        <div className="flex gap-2">
                                                            <span className="text-[10px] text-slate-400 font-medium bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">#specs</span>
                                                            <span className="text-[10px] px-1.5 py-0.5 bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-300 rounded-full font-medium">Top-1</span>
                                                        </div>
                                                        <span className="text-[10px] text-slate-400 font-medium">Oct 12, 2023</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </>
                                    )}

                                    {/* Dynamic Results */}
                                    {results.map((result, index) => (
                                        <div key={index} className={`
                                            bg-white dark:bg-[#1e212b] rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 hover:border-blue-600/40 dark:hover:border-blue-600/40 cursor-pointer transition-all group hover:shadow-md hover:shadow-blue-600/5
                                            ${viewMode === 'grid' ? 'p-4 flex flex-col h-full' : 'p-3 flex items-start gap-4'}
                                        `}>
                                            <div className={`flex ${viewMode === 'grid' ? 'items-start justify-between mb-3' : 'shrink-0'}`}>
                                                <div className="flex items-center gap-2">
                                                    <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                                                        {getIconForType(result.metadata.type || 'document')}
                                                    </div>
                                                    {viewMode === 'grid' && (
                                                        <div className="flex flex-col">
                                                            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">{result.metadata.type || 'Result'}</span>
                                                            <span className="text-xs font-bold text-slate-600 dark:text-slate-400">{result.source}</span>
                                                        </div>
                                                    )}
                                                </div>
                                                {viewMode === 'grid' && (
                                                    <div className="flex flex-col items-end">
                                                        <span className={`text-sm font-bold ${getScoreColor(result.score)}`}>{Math.round(result.score * 100)}%</span>
                                                        <span className="text-[10px] text-slate-400">Relevance</span>
                                                    </div>
                                                )}
                                            </div>

                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center justify-between gap-2 mb-1">
                                                    <h3 className="text-sm font-semibold text-slate-900 dark:text-white group-hover:text-blue-600 transition-colors line-clamp-1">{result.metadata.name || 'Untitled Result'}</h3>
                                                    {viewMode === 'list' && (
                                                        <div className="flex items-center gap-3 shrink-0">
                                                            {result.metadata.uuid && (
                                                                <div
                                                                    className="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded text-[10px] text-slate-500 font-mono hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors group/id"
                                                                    onClick={(e) => handleCopyId(result.metadata.uuid!, e)}
                                                                    title="Copy Node ID"
                                                                >
                                                                    <span>{result.metadata.uuid.slice(0, 8)}...</span>
                                                                    {copiedId === result.metadata.uuid ? (
                                                                        <Check className="w-3 h-3 text-emerald-500" />
                                                                    ) : (
                                                                        <Copy className="w-3 h-3 hover:text-blue-600" />
                                                                    )}
                                                                </div>
                                                            )}
                                                            <div className="flex flex-col items-end">
                                                                <span className={`text-sm font-bold ${getScoreColor(result.score)} leading-none`}>{Math.round(result.score * 100)}%</span>
                                                            </div>
                                                        </div>
                                                    )}
                                                </div>

                                                {/* Node ID for Grid View */}
                                                {viewMode === 'grid' && result.metadata.uuid && (
                                                    <div className="flex items-center gap-1.5 mb-2">
                                                        <span
                                                            className="text-[10px] text-slate-400 font-mono bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded flex items-center gap-1.5 group/id hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                                                            onClick={(e) => handleCopyId(result.metadata.uuid!, e)}
                                                            title="Copy Node ID"
                                                        >
                                                            {result.metadata.uuid.slice(0, 8)}...
                                                            {copiedId === result.metadata.uuid ? (
                                                                <Check className="w-3 h-3 text-emerald-500" />
                                                            ) : (
                                                                <Copy className="w-3 h-3 hover:text-blue-600 opacity-0 group-hover/id:opacity-100 transition-opacity" />
                                                            )}
                                                        </span>
                                                    </div>
                                                )}

                                                <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed mb-3 line-clamp-2">
                                                    {result.content}
                                                </p>

                                                <div className={`flex items-center justify-between ${viewMode === 'grid' ? 'mt-auto pt-3 border-t border-slate-50 dark:border-slate-800' : ''}`}>
                                                    <div className="flex gap-2">
                                                        {result.metadata.tags && Array.isArray(result.metadata.tags) && result.metadata.tags.map((tag: string, i: number) => (
                                                            <span key={i} className="text-[10px] text-slate-400 font-medium bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">#{tag}</span>
                                                        ))}
                                                    </div>
                                                    <span className="text-[10px] text-slate-400 font-medium">{result.metadata.created_at || 'Unknown Date'}</span>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </section>
                    </div>
                </div>
            </main>
        </div>
    )
}
