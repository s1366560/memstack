import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Brain,
    Network,
    Settings,
    ArrowLeft,
    Search
} from 'lucide-react';
import { AppLayout, NavigationItem } from '../components/AppLayout';
import { useTenantStore } from '../stores/tenant';
import { useProjectStore } from '../stores/project';
import { MemoryManager } from '../components/MemoryManager';
import { GraphVisualization } from '../components/GraphVisualization';

export const ProjectDashboard: React.FC = () => {
    const { spaceId, projectId } = useParams<{ spaceId: string; projectId: string }>();
    const navigate = useNavigate();
    const { currentTenant, getTenant } = useTenantStore();
    const { currentProject, getProject } = useProjectStore();

    // Local state for active tab (sub-route simulation)
    // Ideally this should be handled by nested routes like /.../memories
    const [activeTab, setActiveTab] = useState('memories');

    useEffect(() => {
        if (spaceId && !currentTenant) {
            getTenant(spaceId);
        }
        if (spaceId && projectId) {
            getProject(spaceId, projectId);
        }
    }, [spaceId, projectId, currentTenant, getTenant, getProject]);

    const navItems: NavigationItem[] = [
        // { id: 'overview', label: '项目概览', icon: LayoutDashboard, onClick: () => setActiveTab('overview') },
        { id: 'memories', label: '记忆管理', icon: Brain, onClick: () => setActiveTab('memories') },
        { id: 'graph', label: '知识图谱', icon: Network, onClick: () => setActiveTab('graph') },
        { id: 'search', label: '全文搜索', icon: Search, onClick: () => setActiveTab('search') },
        { id: 'settings', label: '项目设置', icon: Settings, onClick: () => setActiveTab('settings') },
    ];

    const BackButton = (
        <button
            onClick={() => navigate(`/space/${spaceId}`)}
            className="p-1 hover:bg-blue-700 rounded transition-colors mr-2"
            title="返回项目列表"
        >
            <ArrowLeft className="h-5 w-5 text-white" />
        </button>
    );

    return (
        <AppLayout
            title={currentProject?.name || 'Loading...'}
            navigationItems={navItems}
            activeItem={activeTab}
            contextInfo={{
                tenantName: currentTenant?.name,
                projectName: currentProject?.name
            }}
            backButton={BackButton}
        >
            {activeTab === 'memories' && (
                <div className="space-y-6">
                    <div className="flex items-center justify-between">
                        <h2 className="text-2xl font-bold text-gray-900">记忆管理</h2>
                    </div>
                    <MemoryManager />
                </div>
            )}

            {activeTab === 'graph' && (
                <div className="space-y-6 h-full flex flex-col">
                    <div className="flex items-center justify-between">
                        <h2 className="text-2xl font-bold text-gray-900">知识图谱</h2>
                    </div>
                    <div className="flex-1 bg-white rounded-lg shadow-sm border border-gray-200 min-h-[600px]">
                        <GraphVisualization />
                    </div>
                </div>
            )}

            {activeTab === 'search' && (
                <div className="text-center py-20 text-gray-500">
                    <Search className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p className="text-lg">高级搜索功能即将上线...</p>
                </div>
            )}

            {activeTab === 'settings' && (
                <div className="text-center py-20 text-gray-500">
                    <Settings className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p className="text-lg">项目设置功能开发中...</p>
                </div>
            )}
        </AppLayout>
    );
};
