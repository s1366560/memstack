import React, { useState } from 'react'
import { useParams } from 'react-router-dom'
import { graphitiService } from '../../services/graphitiService'

interface SearchResult {
    content: string
    score: number
    metadata: {
        type: string
        name?: string
        uuid?: string
        depth?: number
        [key: string]: any
    }
    source: string
}

export const EnhancedSearch: React.FC = () => {
    const { projectId } = useParams()
    const [searchType, setSearchType] = useState<'semantic' | 'graph' | 'temporal' | 'faceted'>('semantic')
    const [query, setQuery] = useState('')
    const [results, setResults] = useState<SearchResult[]>([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    // Graph traversal specific
    const [startEntityUuid, setStartEntityUuid] = useState('')
    const [maxDepth, setMaxDepth] = useState(2)

    // Temporal search specific
    const [since, setSince] = useState('')
    const [until, setUntil] = useState('')

    // Faceted search specific
    const [entityTypes, setEntityTypes] = useState<string[]>([])
    const [tags, setTags] = useState<string[]>([])

    const handleSearch = async () => {
        if (!query && searchType !== 'graph') return

        setLoading(true)
        setError(null)
        setResults([])

        try {
            let data

            switch (searchType) {
                case 'semantic':
                    // Use the basic memory search
                    data = await graphitiService.getGraphData({
                        project_id: projectId,
                        limit: 100,
                    })
                    // For now, just show empty results - in real implementation would call search API
                    setResults([])
                    break

                case 'graph':
                    if (!startEntityUuid) {
                        setError('Please enter an entity UUID')
                        setLoading(false)
                        return
                    }
                    data = await graphitiService.searchByGraphTraversal({
                        start_entity_uuid: startEntityUuid,
                        max_depth: maxDepth,
                        limit: 50,
                    })
                    setResults(data.results)
                    break

                case 'temporal':
                    data = await graphitiService.searchTemporal({
                        query,
                        since: since || undefined,
                        until: until || undefined,
                        limit: 50,
                    })
                    setResults(data.results)
                    break

                case 'faceted':
                    data = await graphitiService.searchWithFacets({
                        query,
                        entity_types: entityTypes.length > 0 ? entityTypes : undefined,
                        tags: tags.length > 0 ? tags : undefined,
                        since: since || undefined,
                        limit: 50,
                    })
                    setResults(data.results)
                    break
            }
        } catch (err) {
            console.error('Search failed:', err)
            setError('Search failed. Please try again.')
        } finally {
            setLoading(false)
        }
    }

    const getScoreColor = (score: number) => {
        if (score >= 0.8) return 'bg-green-500'
        if (score >= 0.6) return 'bg-yellow-500'
        if (score >= 0.4) return 'bg-orange-500'
        return 'bg-slate-400'
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                    Advanced Search
                </h1>
                <p className="text-slate-600 dark:text-slate-400 mt-1">
                    Use advanced search capabilities to explore the knowledge graph
                </p>
            </div>

            {/* Search Type Selector */}
            <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
                <div className="flex flex-wrap gap-2 mb-4">
                    <button
                        onClick={() => setSearchType('semantic')}
                        className={`px-4 py-2 rounded-md font-medium transition-colors ${
                            searchType === 'semantic'
                                ? 'bg-blue-600 text-white'
                                : 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
                        }`}
                    >
                        Semantic Search
                    </button>
                    <button
                        onClick={() => setSearchType('graph')}
                        className={`px-4 py-2 rounded-md font-medium transition-colors ${
                            searchType === 'graph'
                                ? 'bg-blue-600 text-white'
                                : 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
                        }`}
                    >
                        Graph Traversal
                    </button>
                    <button
                        onClick={() => setSearchType('temporal')}
                        className={`px-4 py-2 rounded-md font-medium transition-colors ${
                            searchType === 'temporal'
                                ? 'bg-blue-600 text-white'
                                : 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
                        }`}
                    >
                        Temporal Search
                    </button>
                    <button
                        onClick={() => setSearchType('faceted')}
                        className={`px-4 py-2 rounded-md font-medium transition-colors ${
                            searchType === 'faceted'
                                ? 'bg-blue-600 text-white'
                                : 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
                        }`}
                    >
                        Faceted Search
                    </button>
                </div>

                {/* Search Input Fields */}
                <div className="space-y-4">
                    {searchType !== 'graph' && (
                        <div>
                            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                                Query
                            </label>
                            <input
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                                placeholder="Enter your search query..."
                                className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-md text-slate-900 dark:text-white placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                        </div>
                    )}

                    {searchType === 'graph' && (
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                                    Start Entity UUID
                                </label>
                                <input
                                    type="text"
                                    value={startEntityUuid}
                                    onChange={(e) => setStartEntityUuid(e.target.value)}
                                    placeholder="entity-uuid-123"
                                    className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-md text-slate-900 dark:text-white placeholder-slate-500 focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                                    Max Depth (1-5)
                                </label>
                                <input
                                    type="number"
                                    min={1}
                                    max={5}
                                    value={maxDepth}
                                    onChange={(e) => setMaxDepth(parseInt(e.target.value) || 2)}
                                    className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-md text-slate-900 dark:text-white"
                                />
                            </div>
                        </div>
                    )}

                    {searchType === 'temporal' && (
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                                    Since (optional)
                                </label>
                                <input
                                    type="datetime-local"
                                    value={since}
                                    onChange={(e) => setSince(e.target.value)}
                                    className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-md text-slate-900 dark:text-white"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                                    Until (optional)
                                </label>
                                <input
                                    type="datetime-local"
                                    value={until}
                                    onChange={(e) => setUntil(e.target.value)}
                                    className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-md text-slate-900 dark:text-white"
                                />
                            </div>
                        </div>
                    )}

                    {searchType === 'faceted' && (
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                                    Entity Types (comma separated)
                                </label>
                                <input
                                    type="text"
                                    value={entityTypes.join(',')}
                                    onChange={(e) => setEntityTypes(e.target.value.split(',').filter(Boolean))}
                                    placeholder="Person, Organization"
                                    className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-md text-slate-900 dark:text-white"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                                    Tags (comma separated)
                                </label>
                                <input
                                    type="text"
                                    value={tags.join(',')}
                                    onChange={(e) => setTags(e.target.value.split(',').filter(Boolean))}
                                    placeholder="important, archived"
                                    className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-md text-slate-900 dark:text-white"
                                />
                            </div>
                        </div>
                    )}

                    <button
                        onClick={handleSearch}
                        disabled={loading}
                        className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-medium px-6 py-2.5 rounded-md transition-colors disabled:opacity-50"
                    >
                        <span className="material-symbols-outlined">
                            {loading ? 'progress_activity' : 'search'}
                        </span>
                        {loading ? 'Searching...' : 'Search'}
                    </button>
                </div>
            </div>

            {/* Results */}
            {error && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                    <div className="flex gap-2">
                        <span className="material-symbols-outlined text-red-600">error</span>
                        <p className="text-red-800 dark:text-red-400">{error}</p>
                    </div>
                </div>
            )}

            {!loading && results.length > 0 && (
                <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                    <div className="p-4 border-b border-slate-200 dark:border-slate-700">
                        <h2 className="font-semibold text-slate-900 dark:text-white">
                            Search Results ({results.length})
                        </h2>
                    </div>
                    <div className="divide-y divide-slate-200 dark:divide-slate-700">
                        {results.map((result, index) => (
                            <div key={index} className="p-4 hover:bg-slate-50 dark:hover:bg-slate-900 transition-colors">
                                <div className="flex items-start gap-3">
                                    <div className={`w-2 h-2 rounded-full mt-2 ${getScoreColor(result.score)}`} />
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                                                result.metadata.type === 'entity'
                                                    ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
                                                    : result.metadata.type === 'episode'
                                                    ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400'
                                                    : 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400'
                                            }`}>
                                                {result.source}
                                            </span>
                                            {result.score > 0 && (
                                                <span className="text-xs text-slate-500">
                                                    Score: {result.score.toFixed(2)}
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-slate-900 dark:text-white">{result.content}</p>
                                        {result.metadata.name && (
                                            <div className="text-xs text-slate-500 mt-1">
                                                {result.metadata.name}
                                            </div>
                                        )}
                                        {result.metadata.depth !== undefined && (
                                            <div className="text-xs text-slate-500">
                                                Distance: {result.metadata.depth} hops
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {!loading && results.length === 0 && !error && (
                <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-12 text-center">
                    <span className="material-symbols-outlined text-4xl text-slate-400">search_off</span>
                    <p className="text-slate-500 mt-2">
                        {query || startEntityUuid ? 'No results found' : 'Enter a search query to get started'}
                    </p>
                </div>
            )}

            {/* Search Type Info */}
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <div className="flex gap-3">
                    <span className="material-symbols-outlined text-blue-600 dark:text-blue-400 text-2xl">tips_and_updates</span>
                    <div>
                        <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-300">
                            Search Tips
                        </h3>
                        <ul className="text-sm text-blue-800 dark:text-blue-400 mt-2 space-y-1">
                            <li>• <strong>Semantic Search</strong>: Find content by meaning and concepts</li>
                            <li>• <strong>Graph Traversal</strong>: Explore related entities starting from a specific entity</li>
                            <li>• <strong>Temporal Search</strong>: Find memories from a specific time period</li>
                            <li>• <strong>Faceted Search</strong>: Filter results by entity type and tags</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    )
}
