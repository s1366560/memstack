import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { graphitiService } from '../../services/graphitiService'

export const Maintenance: React.FC = () => {
    const { projectId } = useParams()
    const [stats, setStats] = useState<any>(null)
    const [maintenanceStatus, setMaintenanceStatus] = useState<any>(null)
    const [loading, setLoading] = useState(false)
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

    // Operation states
    const [refreshing, setRefreshing] = useState(false)
    const [deduplicating, setDeduplicating] = useState(false)
    const [cleaningEdges, setCleaningEdges] = useState(false)

    const loadStats = async () => {
        setLoading(true)
        try {
            const data = await graphitiService.getGraphStats()
            setStats(data)
        } catch (err) {
            console.error('Failed to load stats:', err)
            setMessage({ type: 'error', text: 'Failed to load graph statistics' })
        } finally {
            setLoading(false)
        }
    }

    const loadMaintenanceStatus = async () => {
        try {
            const status = await fetch('/api/v1/maintenance/status', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('apiKey')}`,
                },
            }).then(res => res.json())
            setMaintenanceStatus(status)
        } catch (err) {
            console.error('Failed to load maintenance status:', err)
        }
    }

    const handleIncrementalRefresh = async () => {
        setRefreshing(true)
        setMessage(null)
        try {
            const result = await fetch('/api/v1/maintenance/refresh/incremental', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('apiKey')}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    rebuild_communities: false,
                }),
            }).then(res => res.json())

            setMessage({ type: 'success', text: `Refreshed ${result.episodes_processed} episodes` })
            await loadStats()
            await loadMaintenanceStatus()
        } catch (err) {
            console.error('Refresh failed:', err)
            setMessage({ type: 'error', text: 'Failed to refresh graph' })
        } finally {
            setRefreshing(false)
        }
    }

    const handleDeduplicate = async (dryRun = false) => {
        setDeduplicating(true)
        setMessage(null)
        try {
            const result = await fetch('/api/v1/maintenance/deduplicate', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('apiKey')}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    similarity_threshold: 0.9,
                    dry_run: dryRun,
                }),
            }).then(res => res.json())

            if (dryRun) {
                setMessage({ type: 'success', text: `Found ${result.duplicates_found} potential duplicates` })
            } else {
                setMessage({ type: 'success', text: `Merged ${result.merged} duplicate entities` })
            }
            await loadStats()
        } catch (err) {
            console.error('Deduplication failed:', err)
            setMessage({ type: 'error', text: 'Failed to deduplicate entities' })
        } finally {
            setDeduplicating(false)
        }
    }

    const handleInvalidateEdges = async (dryRun = false) => {
        setCleaningEdges(true)
        setMessage(null)
        try {
            const result = await fetch('/api/v1/maintenance/invalidate-edges', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('apiKey')}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    days_since_update: 30,
                    dry_run: dryRun,
                }),
            }).then(res => res.json())

            if (dryRun) {
                setMessage({ type: 'success', text: `Found ${result.stale_edges_found} stale edges` })
            } else {
                setMessage({ type: 'success', text: `Deleted ${result.deleted} stale edges` })
            }
            await loadStats()
        } catch (err) {
            console.error('Edge invalidation failed:', err)
            setMessage({ type: 'error', text: 'Failed to invalidate edges' })
        } finally {
            setCleaningEdges(false)
        }
    }

    const handleExportData = async () => {
        setMessage(null)
        try {
            const data = await graphitiService.exportData({
                include_episodes: true,
                include_entities: true,
                include_relationships: true,
                include_communities: true,
            })

            // Create download link
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `graph-export-${new Date().toISOString().split('T')[0]}.json`
            document.body.appendChild(a)
            a.click()
            document.body.removeChild(a)
            URL.revokeObjectURL(url)

            setMessage({ type: 'success', text: 'Data exported successfully' })
        } catch (err) {
            console.error('Export failed:', err)
            setMessage({ type: 'error', text: 'Failed to export data' })
        }
    }

    useEffect(() => {
        loadStats()
        loadMaintenanceStatus()
    }, [projectId])

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                    Graph Maintenance
                </h1>
                <p className="text-slate-600 dark:text-slate-400 mt-1">
                    Monitor, maintain, and optimize the knowledge graph
                </p>
            </div>

            {/* Message Banner */}
            {message && (
                <div className={`rounded-lg p-4 ${
                    message.type === 'success'
                        ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
                        : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
                }`}>
                    <div className="flex gap-2">
                        <span className={`material-symbols-outlined ${
                            message.type === 'success' ? 'text-green-600' : 'text-red-600'
                        }`}>
                            {message.type === 'success' ? 'check_circle' : 'error'}
                        </span>
                        <p className={`text-sm ${message.type === 'success' ? 'text-green-800 dark:text-green-400' : 'text-red-800 dark:text-red-400'}`}>
                            {message.text}
                        </p>
                    </div>
                </div>
            )}

            {/* Statistics */}
            <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                <div className="p-4 border-b border-slate-200 dark:border-slate-700">
                    <h2 className="font-semibold text-slate-900 dark:text-white">Graph Statistics</h2>
                </div>
                {loading ? (
                    <div className="p-8 text-center">
                        <span className="material-symbols-outlined text-4xl text-slate-400 animate-spin">progress_activity</span>
                    </div>
                ) : stats ? (
                    <div className="p-6 grid grid-cols-2 md:grid-cols-4 gap-6">
                        <div className="text-center">
                            <div className="text-3xl font-bold text-blue-600">{stats.entity_count || 0}</div>
                            <div className="text-sm text-slate-600 dark:text-slate-400 mt-1">Entities</div>
                        </div>
                        <div className="text-center">
                            <div className="text-3xl font-bold text-emerald-600">{stats.episodic_count || 0}</div>
                            <div className="text-sm text-slate-600 dark:text-slate-400 mt-1">Episodes</div>
                        </div>
                        <div className="text-center">
                            <div className="text-3xl font-bold text-purple-600">{stats.community_count || 0}</div>
                            <div className="text-sm text-slate-600 dark:text-slate-400 mt-1">Communities</div>
                        </div>
                        <div className="text-center">
                            <div className="text-3xl font-bold text-orange-600">{stats.edge_count || 0}</div>
                            <div className="text-sm text-slate-600 dark:text-slate-400 mt-1">Relationships</div>
                        </div>
                    </div>
                ) : (
                    <div className="p-6 text-center text-slate-500">Failed to load statistics</div>
                )}
            </div>

            {/* Maintenance Operations */}
            <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                <div className="p-4 border-b border-slate-200 dark:border-slate-700">
                    <h2 className="font-semibold text-slate-900 dark:text-white">Maintenance Operations</h2>
                </div>
                <div className="p-6 space-y-6">
                    {/* Incremental Refresh */}
                    <div className="flex items-start justify-between">
                        <div className="flex-1">
                            <h3 className="font-medium text-slate-900 dark:text-white">Incremental Refresh</h3>
                            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                                Reprocess recent episodes and update graph without full rebuild
                            </p>
                        </div>
                        <button
                            onClick={handleIncrementalRefresh}
                            disabled={refreshing}
                            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-md transition-colors disabled:opacity-50"
                        >
                            <span className="material-symbols-outlined">{refreshing ? 'progress_activity' : 'refresh'}</span>
                            {refreshing ? 'Refreshing...' : 'Refresh'}
                        </button>
                    </div>

                    {/* Deduplicate Entities */}
                    <div className="flex items-start justify-between">
                        <div className="flex-1">
                            <h3 className="font-medium text-slate-900 dark:text-white">Deduplicate Entities</h3>
                            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                                Find and merge duplicate entities based on name similarity
                            </p>
                            <div className="flex gap-2 mt-2">
                                <button
                                    onClick={() => handleDeduplicate(true)}
                                    disabled={deduplicating}
                                    className="px-3 py-1.5 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-md text-sm hover:bg-slate-200 dark:hover:bg-slate-600 disabled:opacity-50"
                                >
                                    Check
                                </button>
                                <button
                                    onClick={() => handleDeduplicate(false)}
                                    disabled={deduplicating}
                                    className="px-3 py-1.5 bg-orange-600 hover:bg-orange-500 text-white rounded-md text-sm disabled:opacity-50"
                                >
                                    {deduplicating ? 'Processing...' : 'Merge'}
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Invalidate Stale Edges */}
                    <div className="flex items-start justify-between">
                        <div className="flex-1">
                            <h3 className="font-medium text-slate-900 dark:text-white">Clean Stale Edges</h3>
                            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                                Remove relationships that haven't been updated in 30 days
                            </p>
                            <div className="flex gap-2 mt-2">
                                <button
                                    onClick={() => handleInvalidateEdges(true)}
                                    disabled={cleaningEdges}
                                    className="px-3 py-1.5 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-md text-sm hover:bg-slate-200 dark:hover:bg-slate-600 disabled:opacity-50"
                                >
                                    Check
                                </button>
                                <button
                                    onClick={() => handleInvalidateEdges(false)}
                                    disabled={cleaningEdges}
                                    className="px-3 py-1.5 bg-orange-600 hover:bg-orange-500 text-white rounded-md text-sm disabled:opacity-50"
                                >
                                    {cleaningEdges ? 'Cleaning...' : 'Clean'}
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Export Data */}
                    <div className="flex items-start justify-between">
                        <div className="flex-1">
                            <h3 className="font-medium text-slate-900 dark:text-white">Export Data</h3>
                            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                                Download all graph data as JSON for backup or analysis
                            </p>
                        </div>
                        <button
                            onClick={handleExportData}
                            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-md transition-colors"
                        >
                            <span className="material-symbols-outlined">download</span>
                            Export
                        </button>
                    </div>
                </div>
            </div>

            {/* Maintenance Recommendations */}
            {maintenanceStatus && maintenanceStatus.recommendations && (
                <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                    <div className="p-4 border-b border-slate-200 dark:border-slate-700">
                        <h2 className="font-semibold text-slate-900 dark:text-white">Recommendations</h2>
                    </div>
                    <div className="p-6">
                        {maintenanceStatus.recommendations.length === 0 ? (
                            <p className="text-sm text-slate-500">No recommendations at this time</p>
                        ) : (
                            <div className="space-y-3">
                                {maintenanceStatus.recommendations.map((rec: any, index: number) => (
                                    <div key={index} className="flex items-start gap-3 p-3 bg-slate-50 dark:bg-slate-900 rounded-md">
                                        <span className={`material-symbols-outlined ${
                                            rec.priority === 'high' ? 'text-red-600' :
                                            rec.priority === 'medium' ? 'text-orange-600' :
                                            rec.priority === 'low' ? 'text-yellow-600' :
                                            'text-blue-600'
                                        }`}>
                                            {rec.priority === 'high' ? 'warning' :
                                             rec.priority === 'medium' ? 'info' :
                                             rec.priority === 'low' ? 'lightbulb' : 'check_circle'}
                                        </span>
                                        <div className="flex-1">
                                            <p className="text-sm text-slate-700 dark:text-slate-300">{rec.message}</p>
                                            <p className="text-xs text-slate-500 mt-1">Type: {rec.type}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Warning Info */}
            <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
                <div className="flex gap-3">
                    <span className="material-symbols-outlined text-amber-600 dark:text-amber-400 text-2xl">warning</span>
                    <div>
                        <h3 className="text-sm font-semibold text-amber-900 dark:text-amber-300">
                            Important Notice
                        </h3>
                        <p className="text-sm text-amber-800 dark:text-amber-400 mt-1">
                            Some operations like merging duplicates and cleaning edges cannot be undone.
                            We recommend running "Check" first to see what would be affected before executing.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}
