import axios from 'axios'

// API client configuration
const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
})

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// Types
export interface GraphNode {
    id: string
    label: string
    type: 'Entity' | 'Episodic' | 'Community'
    name: string
    summary?: string
    entity_type?: string
    member_count?: number
    tenant_id?: string
    project_id?: string
    created_at?: string
    [key: string]: any
}

export interface GraphEdge {
    id: string
    source: string
    target: string
    label: string
    weight?: number
    [key: string]: any
}

export interface GraphData {
    elements: {
        nodes: Array<{ data: GraphNode }>
        edges: Array<{ data: GraphEdge }>
    }
}

export interface Entity {
    uuid: string
    name: string
    entity_type: string
    summary: string
    tenant_id?: string
    project_id?: string
    created_at?: string
}

export interface Community {
    uuid: string
    name: string
    summary: string
    member_count: number
    tenant_id?: string
    project_id?: string
    formed_at?: string
    created_at?: string
}

export interface PaginatedResponse<T> {
    items: T[]
    total: number
    limit: number
    offset: number
    has_more: boolean
}

// Graphiti Service
export const graphitiService = {
    // Graph Data
    async getGraphData(params: {
        tenant_id?: string
        project_id?: string
        limit?: number
        since?: string
    }): Promise<GraphData> {
        const queryParams = new URLSearchParams()
        if (params.tenant_id) queryParams.append('tenant_id', params.tenant_id)
        if (params.project_id) queryParams.append('project_id', params.project_id)
        if (params.limit) queryParams.append('limit', params.limit.toString())
        if (params.since) queryParams.append('since', params.since)

        const response = await apiClient.get(`/memory/graph?${queryParams.toString()}`)
        return response.data
    },

    // Entities
    async getEntity(entityId: string): Promise<Entity> {
        const response = await apiClient.get(`/entities/${entityId}`)
        return response.data
    },

    async listEntities(params: {
        tenant_id?: string
        project_id?: string
        entity_type?: string
        limit?: number
        offset?: number
    }): Promise<PaginatedResponse<Entity>> {
        const queryParams = new URLSearchParams()
        if (params.tenant_id) queryParams.append('tenant_id', params.tenant_id)
        if (params.project_id) queryParams.append('project_id', params.project_id)
        if (params.entity_type) queryParams.append('entity_type', params.entity_type)
        if (params.limit) queryParams.append('limit', params.limit.toString())
        if (params.offset) queryParams.append('offset', params.offset.toString())

        const response = await apiClient.get(`/entities/?${queryParams.toString()}`)
        return {
            ...response.data,
            items: response.data.entities || response.data.items || []
        }
    },

    async getEntityRelationships(
        entityId: string,
        params: { relationship_type?: string; limit?: number } = {}
    ): Promise<{ relationships: any[]; total: number }> {
        const queryParams = new URLSearchParams()
        if (params.relationship_type) queryParams.append('relationship_type', params.relationship_type)
        if (params.limit) queryParams.append('limit', params.limit.toString())

        const response = await apiClient.get(`/entities/${entityId}/relationships?${queryParams.toString()}`)
        return response.data
    },

    // Communities
    async getCommunity(communityId: string): Promise<Community> {
        const response = await apiClient.get(`/communities/${communityId}`)
        return response.data
    },

    async listCommunities(params: {
        tenant_id?: string
        project_id?: string
        min_members?: number
        limit?: number
    }): Promise<{ communities: Community[]; total: number }> {
        const queryParams = new URLSearchParams()
        if (params.tenant_id) queryParams.append('tenant_id', params.tenant_id)
        if (params.project_id) queryParams.append('project_id', params.project_id)
        if (params.min_members) queryParams.append('min_members', params.min_members.toString())
        if (params.limit) queryParams.append('limit', params.limit.toString())

        const response = await apiClient.get(`/communities/?${queryParams.toString()}`)
        return response.data
    },

    async getCommunityMembers(communityId: string, limit = 100): Promise<{ members: Entity[]; total: number }> {
        const response = await apiClient.get(`/communities/${communityId}/members?limit=${limit}`)
        return response.data
    },

    async rebuildCommunities(): Promise<{ status: string; message: string }> {
        const response = await apiClient.post('/communities/rebuild')
        return response.data
    },

    // Enhanced Search
    async searchByGraphTraversal(params: {
        start_entity_uuid: string
        max_depth?: number
        relationship_types?: string[]
        limit?: number
        tenant_id?: string
    }): Promise<{ results: any[]; total: number; search_type: string }> {
        const response = await apiClient.post('/search-enhanced/graph-traversal', params)
        return response.data
    },

    async searchByCommunity(params: {
        community_uuid: string
        limit?: number
        include_episodes?: boolean
    }): Promise<{ results: any[]; total: number; search_type: string }> {
        const response = await apiClient.post('/search-enhanced/community', params)
        return response.data
    },

    async searchTemporal(params: {
        query: string
        since?: string
        until?: string
        limit?: number
        tenant_id?: string
    }): Promise<{ results: any[]; total: number; search_type: string; time_range?: any }> {
        const response = await apiClient.post('/search-enhanced/temporal', params)
        return response.data
    },

    async searchWithFacets(params: {
        query: string
        entity_types?: string[]
        tags?: string[]
        since?: string
        limit?: number
        offset?: number
        tenant_id?: string
    }): Promise<{ results: any[]; facets: any; total: number; limit: number; offset: number; search_type: string }> {
        const response = await apiClient.post('/search-enhanced/faceted', params)
        return response.data
    },

    async getSearchCapabilities(): Promise<any> {
        const response = await apiClient.get('/search-enhanced/capabilities')
        return response.data
    },

    // Data Export
    async exportData(params: {
        tenant_id?: string
        include_episodes?: boolean
        include_entities?: boolean
        include_relationships?: boolean
        include_communities?: boolean
    }): Promise<any> {
        const response = await apiClient.post('/data/export', params)
        return response.data
    },

    async getGraphStats(tenant_id?: string): Promise<{
        entity_count: number
        episodic_count: number
        community_count: number
        edge_count: number
    }> {
        const queryParams = tenant_id ? `?tenant_id=${tenant_id}` : ''
        const response = await apiClient.get(`/data/stats${queryParams}`)
        return response.data
    },

    // Episodes (Enhanced)
    async addEpisode(data: {
        content: string
        project_id: string
        source_type?: string
        source_id?: string
        name?: string
        url?: string
        metadata?: any
    }): Promise<any> {
        const response = await apiClient.post('/episodes/', data)
        return response.data
    },

    async getEpisode(episodeName: string): Promise<any> {
        const response = await apiClient.get(`/episodes-enhanced/${encodeURIComponent(episodeName)}`)
        return response.data
    },

    async listEpisodes(params: {
        tenant_id?: string
        project_id?: string
        user_id?: string
        limit?: number
        offset?: number
        sort_by?: string
        sort_desc?: boolean
    }): Promise<PaginatedResponse<any>> {
        const queryParams = new URLSearchParams()
        if (params.tenant_id) queryParams.append('tenant_id', params.tenant_id)
        if (params.project_id) queryParams.append('project_id', params.project_id)
        if (params.user_id) queryParams.append('user_id', params.user_id)
        if (params.limit) queryParams.append('limit', params.limit.toString())
        if (params.offset) queryParams.append('offset', params.offset.toString())
        if (params.sort_by) queryParams.append('sort_by', params.sort_by)
        if (params.sort_desc !== undefined) queryParams.append('sort_desc', params.sort_desc.toString())

        const response = await apiClient.get(`/episodes-enhanced/?${queryParams.toString()}`)
        // Map backend 'episodes' to frontend 'items'
        return {
            ...response.data,
            items: response.data.episodes || response.data.items || []
        }
    },

    async deleteEpisode(episodeName: string): Promise<{ status: string; message: string }> {
        const response = await apiClient.delete(`/episodes-enhanced/${encodeURIComponent(episodeName)}`)
        return response.data
    },

    // AI Tools
    async optimizeContent(data: {
        content: string
        instruction?: string
    }): Promise<{ content: string }> {
        const response = await apiClient.post('/ai/optimize', data)
        return response.data
    },
}


export default graphitiService
