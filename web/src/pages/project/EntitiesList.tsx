import React, { useState, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { graphitiService } from '../../services/graphitiService'

interface Entity {
    uuid: string
    name: string
    entity_type: string
    summary: string
    created_at?: string
}

interface Relationship {
    uuid: string
    source_uuid: string
    target_uuid: string
    relation_type: string
    fact: string
    score: number
}

export const EntitiesList: React.FC = () => {
    const { projectId } = useParams()
    const [entities, setEntities] = useState<Entity[]>([])
    const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null)
    const [relationships, setRelationships] = useState<Relationship[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [page, setPage] = useState(0)
    const [totalCount, setTotalCount] = useState(0)
    const limit = 20
    const [entityTypeFilter, setEntityTypeFilter] = useState<string>('')

    const entityTypeColors: Record<string, string> = {
        'Person': 'bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-400',
        'Organization': 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900/30 dark:text-cyan-400',
        'Product': 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
        'Location': 'bg-lime-100 text-lime-800 dark:bg-lime-900/30 dark:text-lime-400',
        'Event': 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
        'Entity': 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
    }

    const loadEntities = useCallback(async () => {
        setLoading(true)
        setError(null)
        try {
            const result = await graphitiService.listEntities({
                tenant_id: undefined, // Will use current tenant
                project_id: projectId,
                entity_type: entityTypeFilter || undefined,
                limit,
                offset: page * limit,
            })
            setEntities(result.items)
            setTotalCount(result.total)
        } catch (err) {
            console.error('Failed to load entities:', err)
            setError('Failed to load entities')
        } finally {
            setLoading(false)
        }
    }, [projectId, entityTypeFilter, page])

    const loadRelationships = async (entityUuid: string) => {
        try {
            const result = await graphitiService.getEntityRelationships(entityUuid, { limit: 50 })
            setRelationships(result.relationships)
        } catch (err) {
            console.error('Failed to load relationships:', err)
        }
    }

    useEffect(() => {
        loadEntities()
    }, [loadEntities])

    const handleEntityClick = (entity: Entity) => {
        setSelectedEntity(entity)
        loadRelationships(entity.uuid)
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-start">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                        Entities
                    </h1>
                    <p className="text-slate-600 dark:text-slate-400 mt-1">
                        Browse and manage extracted entities from the knowledge graph
                    </p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={loadEntities}
                        className="flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-md hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                    >
                        <span className="material-symbols-outlined">refresh</span>
                        Refresh
                    </button>
                </div>
            </div>

            {/* Filters */}
            <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
                <div className="flex items-center gap-4">
                    <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                        Entity Type:
                    </label>
                    <select
                        value={entityTypeFilter}
                        onChange={(e) => {
                            setEntityTypeFilter(e.target.value)
                            setPage(0)
                        }}
                        className="px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-md text-sm text-slate-900 dark:text-white"
                    >
                        <option value="">All Types</option>
                        <option value="Person">Person</option>
                        <option value="Organization">Organization</option>
                        <option value="Product">Product</option>
                        <option value="Location">Location</option>
                        <option value="Event">Event</option>
                    </select>
                    <div className="ml-auto text-sm text-slate-500">
                        {totalCount.toLocaleString()} entities total
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Entity List */}
                <div className="lg:col-span-2 space-y-4">
                    {loading ? (
                        <div className="text-center py-12">
                            <span className="material-symbols-outlined text-4xl text-slate-400 animate-spin">
                                progress_activity
                            </span>
                            <p className="text-slate-500 mt-2">Loading entities...</p>
                        </div>
                    ) : error ? (
                        <div className="text-center py-12">
                            <span className="material-symbols-outlined text-4xl text-red-500">error</span>
                            <p className="text-slate-500 mt-2">{error}</p>
                            <button
                                onClick={loadEntities}
                                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-500"
                            >
                                Retry
                            </button>
                        </div>
                    ) : entities.length === 0 ? (
                        <div className="text-center py-12 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                            <span className="material-symbols-outlined text-4xl text-slate-400">
                                category
                            </span>
                            <p className="text-slate-500 mt-2">No entities found</p>
                        </div>
                    ) : (
                        <>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {entities.map((entity) => (
                                    <div
                                        key={entity.uuid}
                                        onClick={() => handleEntityClick(entity)}
                                        className={`bg-white dark:bg-slate-800 rounded-lg border p-4 cursor-pointer transition-all hover:shadow-md ${selectedEntity?.uuid === entity.uuid
                                                ? 'border-blue-500 shadow-md'
                                                : 'border-slate-200 dark:border-slate-700'
                                            }`}
                                    >
                                        <div className="flex items-start justify-between mb-2">
                                            <h3 className="font-semibold text-slate-900 dark:text-white">
                                                {entity.name}
                                            </h3>
                                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${entityTypeColors[entity.entity_type] || entityTypeColors['Entity']
                                                }`}>
                                                {entity.entity_type || 'Entity'}
                                            </span>
                                        </div>
                                        {entity.summary && (
                                            <p className="text-sm text-slate-600 dark:text-slate-400 line-clamp-2">
                                                {entity.summary}
                                            </p>
                                        )}
                                        <div className="mt-2 text-xs text-slate-500">
                                            Created: {entity.created_at ? new Date(entity.created_at).toLocaleDateString() : 'Unknown'}
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* Pagination */}
                            {totalCount > limit && (
                                <div className="flex items-center justify-between bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
                                    <button
                                        onClick={() => setPage(p => Math.max(0, p - 1))}
                                        disabled={page === 0}
                                        className="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-md hover:bg-slate-200 dark:hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        Previous
                                    </button>
                                    <span className="text-sm text-slate-600 dark:text-slate-400">
                                        Page {page + 1} of {Math.ceil(totalCount / limit)}
                                    </span>
                                    <button
                                        onClick={() => setPage(p => p + 1)}
                                        disabled={(page + 1) * limit >= totalCount}
                                        className="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-md hover:bg-slate-200 dark:hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        Next
                                    </button>
                                </div>
                            )}
                        </>
                    )}
                </div>

                {/* Entity Detail Panel */}
                <div className="lg:col-span-1">
                    {selectedEntity ? (
                        <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6 sticky top-6">
                            <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
                                Entity Details
                            </h2>
                            <div className="space-y-4">
                                <div>
                                    <label className="text-xs font-semibold text-slate-500 uppercase">Name</label>
                                    <p className="text-slate-900 dark:text-white font-medium">{selectedEntity.name}</p>
                                </div>
                                <div>
                                    <label className="text-xs font-semibold text-slate-500 uppercase">Type</label>
                                    <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium mt-1 ${entityTypeColors[selectedEntity.entity_type] || entityTypeColors['Entity']
                                        }`}>
                                        {selectedEntity.entity_type || 'Entity'}
                                    </span>
                                </div>
                                {selectedEntity.summary && (
                                    <div>
                                        <label className="text-xs font-semibold text-slate-500 uppercase">Summary</label>
                                        <p className="text-sm text-slate-600 dark:text-slate-400">{selectedEntity.summary}</p>
                                    </div>
                                )}
                                <div>
                                    <label className="text-xs font-semibold text-slate-500 uppercase">Created</label>
                                    <p className="text-sm text-slate-600 dark:text-slate-400">
                                        {selectedEntity.created_at ? new Date(selectedEntity.created_at).toLocaleString() : 'Unknown'}
                                    </p>
                                </div>

                                {/* Relationships */}
                                <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
                                    <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-3">
                                        Relationships ({relationships.length})
                                    </h3>
                                    {relationships.length > 0 ? (
                                        <div className="space-y-2 max-h-64 overflow-y-auto">
                                            {relationships.map((rel) => (
                                                <div
                                                    key={rel.uuid}
                                                    className="p-2 bg-slate-50 dark:bg-slate-900 rounded-md text-xs"
                                                >
                                                    <div className="font-medium text-blue-600 dark:text-blue-400">
                                                        {rel.relation_type}
                                                    </div>
                                                    <div className="text-slate-600 dark:text-slate-400 mt-1">
                                                        {rel.fact}
                                                    </div>
                                                    {rel.score > 0 && (
                                                        <div className="text-slate-500 mt-1">
                                                            Score: {rel.score.toFixed(2)}
                                                        </div>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <p className="text-sm text-slate-500">No relationships found</p>
                                    )}
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-12 text-center sticky top-6">
                            <span className="material-symbols-outlined text-4xl text-slate-400">
                                touch_app
                            </span>
                            <p className="text-slate-500 mt-2">Select an entity to view details</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
