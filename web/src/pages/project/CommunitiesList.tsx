import React, { useState, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { graphitiService } from '../../services/graphitiService'
import { TaskList } from '../../components/tasks/TaskList'

interface Community {
    uuid: string
    name: string
    summary: string
    member_count: number
    formed_at?: string
    created_at?: string
}

interface Entity {
    uuid: string
    name: string
    entity_type: string
    summary: string
}

export const CommunitiesList: React.FC = () => {
    const { projectId } = useParams()
    const [communities, setCommunities] = useState<Community[]>([])
    const [selectedCommunity, setSelectedCommunity] = useState<Community | null>(null)
    const [members, setMembers] = useState<Entity[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [rebuilding, setRebuilding] = useState(false)

    const loadCommunities = useCallback(async () => {
        setLoading(true)
        setError(null)
        try {
            const result = await graphitiService.listCommunities({
                tenant_id: undefined,
                project_id: projectId,
                min_members: 1,
                limit: 100,
            })
            setCommunities(result.communities)
        } catch (err) {
            console.error('Failed to load communities:', err)
            setError('Failed to load communities')
        } finally {
            setLoading(false)
        }
    }, [projectId])

    const loadMembers = async (communityUuid: string) => {
        try {
            const result = await graphitiService.getCommunityMembers(communityUuid, 100)
            setMembers(result.members)
        } catch (err) {
            console.error('Failed to load members:', err)
        }
    }

    const handleRebuildCommunities = async () => {
        setRebuilding(true)
        try {
            await graphitiService.rebuildCommunities()
            await loadCommunities()
        } catch (err) {
            console.error('Failed to rebuild communities:', err)
            setError('Failed to rebuild communities')
        } finally {
            setRebuilding(false)
        }
    }

    const handleCommunityClick = (community: Community) => {
        setSelectedCommunity(community)
        loadMembers(community.uuid)
    }

    useEffect(() => {
        loadCommunities()
    }, [loadCommunities])

    const getCommunityColor = (index: number) => {
        const colors = [
            'from-blue-500 to-cyan-500',
            'from-purple-500 to-pink-500',
            'from-emerald-500 to-teal-500',
            'from-orange-500 to-amber-500',
            'from-rose-500 to-red-500',
        ]
        return colors[index % colors.length]
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-start">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                        Communities
                    </h1>
                    <p className="text-slate-600 dark:text-slate-400 mt-1">
                        Automatically detected groups of related entities in the knowledge graph
                    </p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={handleRebuildCommunities}
                        disabled={rebuilding}
                        className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-md transition-colors disabled:opacity-50"
                    >
                        <span className="material-symbols-outlined">
                            {rebuilding ? 'progress_activity' : 'refresh'}
                        </span>
                        {rebuilding ? 'Rebuilding...' : 'Rebuild Communities'}
                    </button>
                    <button
                        onClick={loadCommunities}
                        className="flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-md hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                    >
                        <span className="material-symbols-outlined">refresh</span>
                        Refresh
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Communities List */}
                <div className="lg:col-span-2 space-y-4">
                    {loading ? (
                        <div className="text-center py-12">
                            <span className="material-symbols-outlined text-4xl text-slate-400 animate-spin">
                                progress_activity
                            </span>
                            <p className="text-slate-500 mt-2">Loading communities...</p>
                        </div>
                    ) : error ? (
                        <div className="text-center py-12">
                            <span className="material-symbols-outlined text-4xl text-red-500">error</span>
                            <p className="text-slate-500 mt-2">{error}</p>
                        </div>
                    ) : communities.length === 0 ? (
                        <div className="text-center py-12 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                            <span className="material-symbols-outlined text-4xl text-slate-400">groups</span>
                            <p className="text-slate-500 mt-2">No communities found</p>
                            <p className="text-sm text-slate-400 mt-1">
                                Add more episodes to enable community detection
                            </p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {communities.map((community, index) => (
                                <div
                                    key={community.uuid}
                                    onClick={() => handleCommunityClick(community)}
                                    className={`bg-white dark:bg-slate-800 rounded-lg border p-5 cursor-pointer transition-all hover:shadow-md ${selectedCommunity?.uuid === community.uuid
                                        ? 'border-purple-500 shadow-md'
                                        : 'border-slate-200 dark:border-slate-700'
                                        }`}
                                >
                                    <div className="flex items-start justify-between mb-3">
                                        <div className={`p-3 rounded-lg bg-gradient-to-br ${getCommunityColor(index)} text-white`}>
                                            <span className="material-symbols-outlined">groups</span>
                                        </div>
                                        <span className="bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-400 px-2 py-1 rounded-full text-xs font-medium">
                                            {community.member_count} members
                                        </span>
                                    </div>
                                    <h3 className="font-semibold text-slate-900 dark:text-white mb-2">
                                        {community.name || `Community ${index + 1}`}
                                    </h3>
                                    {community.summary && (
                                        <p className="text-sm text-slate-600 dark:text-slate-400 line-clamp-2">
                                            {community.summary}
                                        </p>
                                    )}
                                    {community.formed_at && (
                                        <div className="mt-2 text-xs text-slate-500">
                                            Formed: {new Date(community.formed_at).toLocaleDateString()}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Community Detail Panel */}
                <div className="lg:col-span-1">
                    {selectedCommunity ? (
                        <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6 sticky top-6">
                            <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
                                Community Details
                            </h2>
                            <div className="space-y-4">
                                <div>
                                    <label className="text-xs font-semibold text-slate-500 uppercase">Tasks</label>
                                    <div className="mt-2">
                                        <TaskList entityId={selectedCommunity.uuid} entityType="community" embedded />
                                    </div>
                                </div>
                                <div>
                                    <label className="text-xs font-semibold text-slate-500 uppercase">Name</label>
                                    <p className="text-slate-900 dark:text-white font-medium">
                                        {selectedCommunity.name || 'Unnamed Community'}
                                    </p>
                                </div>
                                <div>
                                    <label className="text-xs font-semibold text-slate-500 uppercase">Members</label>
                                    <p className="text-2xl font-bold text-purple-600">
                                        {selectedCommunity.member_count}
                                    </p>
                                </div>
                                {selectedCommunity.summary && (
                                    <div>
                                        <label className="text-xs font-semibold text-slate-500 uppercase">Summary</label>
                                        <p className="text-sm text-slate-600 dark:text-slate-400">
                                            {selectedCommunity.summary}
                                        </p>
                                    </div>
                                )}
                                {selectedCommunity.formed_at && (
                                    <div>
                                        <label className="text-xs font-semibold text-slate-500 uppercase">Formed</label>
                                        <p className="text-sm text-slate-600 dark:text-slate-400">
                                            {new Date(selectedCommunity.formed_at).toLocaleString()}
                                        </p>
                                    </div>
                                )}

                                {/* Members List */}
                                <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
                                    <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-3">
                                        Community Members ({members.length})
                                    </h3>
                                    {members.length > 0 ? (
                                        <div className="space-y-2 max-h-64 overflow-y-auto">
                                            {members.slice(0, 20).map((member) => (
                                                <div
                                                    key={member.uuid}
                                                    className="p-2 bg-slate-50 dark:bg-slate-900 rounded-md text-sm hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                                                >
                                                    <div className="font-medium text-slate-900 dark:text-white">
                                                        {member.name}
                                                    </div>
                                                    <div className="text-xs text-slate-500">
                                                        {member.entity_type}
                                                    </div>
                                                    {member.summary && (
                                                        <div className="text-xs text-slate-600 dark:text-slate-400 mt-1 line-clamp-1">
                                                            {member.summary}
                                                        </div>
                                                    )}
                                                </div>
                                            ))}
                                            {members.length > 20 && (
                                                <div className="text-center text-sm text-slate-500 pt-2">
                                                    ...and {members.length - 20} more
                                                </div>
                                            )}
                                        </div>
                                    ) : (
                                        <p className="text-sm text-slate-500">No members loaded</p>
                                    )}
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-12 text-center sticky top-6">
                            <span className="material-symbols-outlined text-4xl text-slate-400">groups</span>
                            <p className="text-slate-500 mt-2">Select a community to view details</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Info Card */}
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <div className="flex gap-3">
                    <span className="material-symbols-outlined text-blue-600 dark:text-blue-400 text-2xl">info</span>
                    <div>
                        <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-300">
                            About Communities
                        </h3>
                        <p className="text-sm text-blue-800 dark:text-blue-400 mt-1">
                            Communities are automatically detected groups of related entities using the Louvain algorithm.
                            They help organize knowledge and reveal patterns in your data. Click "Rebuild Communities" to
                            re-run the detection algorithm after adding new episodes.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}
