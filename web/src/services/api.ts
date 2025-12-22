/// <reference types="vite/client" />
import axios from 'axios';
import {
    ProjectCreate,
    ProjectUpdate,
    MemoryCreate,
    MemoryUpdate,
    MemoryQuery,
    TenantCreate,
    TenantUpdate
} from '../types/memory';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Response interceptor to handle errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Clear token and redirect to login if unauthorized
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            if (window.location.pathname !== '/login') {
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export const authAPI = {
    login: async (email: string, password: string) => {
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);
        const response = await api.post('/auth/token', formData, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        });
        // Assuming backend returns { access_token, token_type, user }
        // If not, we might need to fetch user separately
        const token = response.data.access_token;

        // Fetch user details
        const userResponse = await api.get('/auth/me', {
            headers: { Authorization: `Bearer ${token}` }
        });

        return { token, user: userResponse.data };
    },
    verifyToken: async (_token: string) => {
        const response = await api.get('/auth/me');
        return response.data;
    },
};

export const tenantAPI = {
    list: async (params = {}) => {
        const response = await api.get('/tenants/', { params });
        return response.data;
    },
    create: async (data: TenantCreate) => {
        const response = await api.post('/tenants/', data);
        return response.data;
    },
    update: async (id: string, data: TenantUpdate) => {
        const response = await api.put(`/tenants/${id}`, data);
        return response.data;
    },
    delete: async (id: string) => {
        await api.delete(`/tenants/${id}`);
    },
    addMember: async (tenantId: string, userId: string, role: string) => {
        await api.post(`/tenants/${tenantId}/members`, { user_id: userId, role });
    },
    removeMember: async (tenantId: string, userId: string) => {
        await api.delete(`/tenants/${tenantId}/members/${userId}`);
    },
    listMembers: async (tenantId: string) => {
        const response = await api.get(`/tenants/${tenantId}/members`);
        return response.data;
    },
    get: async (id: string) => {
        const response = await api.get(`/tenants/${id}`);
        return response.data;
    },
};

export const projectAPI = {
    list: async (tenantId: string, params = {}) => {
        const response = await api.get('/projects/', { params: { ...params, tenant_id: tenantId } });
        return response.data;
    },
    create: async (tenantId: string, data: ProjectCreate) => {
        const response = await api.post('/projects/', { ...data, tenant_id: tenantId });
        return response.data;
    },
    update: async (_tenantId: string, projectId: string, data: ProjectUpdate) => {
        const response = await api.put(`/projects/${projectId}`, data);
        return response.data;
    },
    delete: async (_tenantId: string, projectId: string) => {
        await api.delete(`/projects/${projectId}`);
    },
    get: async (_tenantId: string, projectId: string) => {
        const response = await api.get(`/projects/${projectId}`);
        return response.data;
    },
};

export const memoryAPI = {
    list: async (projectId: string, params = {}) => {
        const response = await api.get('/memories/', { params: { ...params, project_id: projectId } });
        return response.data;
    },
    create: async (projectId: string, data: MemoryCreate) => {
        const response = await api.post('/memories/', { ...data, project_id: projectId });
        return response.data;
    },
    update: async (_projectId: string, memoryId: string, data: MemoryUpdate) => {
        const response = await api.put(`/memories/${memoryId}`, data);
        return response.data;
    },
    delete: async (_projectId: string, memoryId: string) => {
        await api.delete(`/memories/${memoryId}`);
    },
    search: async (projectId: string, query: MemoryQuery) => {
        const response = await api.post('/memories/search', { ...query, project_id: projectId });
        return response.data;
    },
    get: async (_projectId: string, memoryId: string) => {
        const response = await api.get(`/memories/${memoryId}`);
        return response.data;
    },
    getGraphData: async (projectId: string, options = {}) => {
        const response = await api.get('/memories/graph', { params: { ...options, project_id: projectId } });
        return response.data;
    },
    extractEntities: async (projectId: string, text: string) => {
        const response = await api.post('/memories/extract-entities', { text, project_id: projectId });
        return response.data;
    },
    extractRelationships: async (projectId: string, text: string) => {
        const response = await api.post('/memories/extract-relationships', { text, project_id: projectId });
        return response.data;
    },
};

export default api;
