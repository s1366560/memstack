import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    LayoutDashboard,
    Folder,
    Users,
    Settings,
    Plus,
    ArrowLeft,
    Calendar,
    MoreVertical
} from 'lucide-react';
import { AppLayout, NavigationItem } from '../components/AppLayout';
import { useTenantStore } from '../stores/tenant';
import { useProjectStore } from '../stores/project';
import { ProjectCreateModal } from '../components/ProjectCreateModal';
import { Project } from '../types/memory';

export const SpaceDashboard: React.FC = () => {
    const { spaceId } = useParams<{ spaceId: string }>();
    const navigate = useNavigate();
    const { currentTenant, getTenant } = useTenantStore();
    const { projects, listProjects, setCurrentProject } = useProjectStore();
    const [isCreateProjectOpen, setIsCreateProjectOpen] = useState(false);
    const [activeTab, setActiveTab] = useState('projects');

    useEffect(() => {
        if (spaceId) {
            getTenant(spaceId);
            listProjects(spaceId); // Assuming listProjects takes tenantId (spaceId)
        }
    }, [spaceId, getTenant, listProjects]);

    const handleEnterProject = (project: Project) => {
        setCurrentProject(project);
        navigate(`/space/${spaceId}/project/${project.id}`);
    };

    const navItems: NavigationItem[] = [
        { id: 'projects', label: '项目列表', icon: Folder, onClick: () => setActiveTab('projects') },
        { id: 'overview', label: '空间概览', icon: LayoutDashboard, onClick: () => setActiveTab('overview') },
        { id: 'members', label: '成员管理', icon: Users, onClick: () => setActiveTab('members') },
        { id: 'settings', label: '空间设置', icon: Settings, onClick: () => setActiveTab('settings') },
    ];

    const BackButton = (
        <button
            onClick={() => navigate('/spaces')}
            className="p-1 hover:bg-blue-700 rounded transition-colors mr-2"
            title="返回空间列表"
        >
            <ArrowLeft className="h-5 w-5 text-white" />
        </button>
    );

    return (
        <AppLayout
            title={currentTenant?.name || 'Loading...'}
            navigationItems={navItems}
            activeItem={activeTab}
            contextInfo={{ tenantName: currentTenant?.name }}
            backButton={BackButton}
        >
            {activeTab === 'projects' && (
                <div className="max-w-7xl mx-auto">
                    <div className="flex justify-between items-center mb-6">
                        <div>
                            <h2 className="text-xl font-bold text-gray-900">项目列表</h2>
                            <p className="text-sm text-gray-500 mt-1">管理当前空间下的所有项目</p>
                        </div>
                        <button
                            onClick={() => setIsCreateProjectOpen(true)}
                            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
                        >
                            <Plus className="h-4 w-4" />
                            <span>新建项目</span>
                        </button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                        {projects.map((project) => (
                            <div
                                key={project.id}
                                onClick={() => handleEnterProject(project)}
                                className="group bg-white rounded-lg border border-gray-200 hover:shadow-md hover:border-blue-300 transition-all cursor-pointer flex flex-col h-full"
                            >
                                <div className="p-5 flex-1">
                                    <div className="flex justify-between items-start mb-3">
                                        <div className="p-2 bg-green-50 rounded-lg">
                                            <Folder className="h-6 w-6 text-green-600" />
                                        </div>
                                        <button className="p-1 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100" onClick={(e) => e.stopPropagation()}>
                                            <MoreVertical className="h-4 w-4" />
                                        </button>
                                    </div>
                                    <h3 className="text-lg font-bold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors truncate">
                                        {project.name}
                                    </h3>
                                    <p className="text-sm text-gray-500 line-clamp-3 mb-4 h-10">
                                        {project.description || '暂无描述'}
                                    </p>
                                </div>

                                <div className="px-5 py-3 bg-gray-50 border-t border-gray-100 rounded-b-lg flex items-center justify-between text-xs text-gray-500">
                                    <div className="flex items-center space-x-1">
                                        <Calendar className="h-3 w-3" />
                                        <span>{new Date(project.created_at).toLocaleDateString()}</span>
                                    </div>
                                    <div className="flex items-center space-x-1">
                                        <Users className="h-3 w-3" />
                                        <span>1 成员</span>
                                    </div>
                                </div>
                            </div>
                        ))}

                        {/* Empty State */}
                        {projects.length === 0 && (
                            <div className="col-span-full py-12 flex flex-col items-center justify-center text-center bg-white border border-dashed border-gray-300 rounded-lg">
                                <div className="p-3 bg-gray-100 rounded-full mb-3">
                                    <Folder className="h-8 w-8 text-gray-400" />
                                </div>
                                <h3 className="text-lg font-medium text-gray-900">暂无项目</h3>
                                <p className="text-gray-500 max-w-sm mt-1 mb-4">当前空间下还没有项目，创建一个新项目来开始管理记忆。</p>
                                <button
                                    onClick={() => setIsCreateProjectOpen(true)}
                                    className="px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors font-medium"
                                >
                                    立即创建
                                </button>
                            </div>
                        )}
                    </div>

                    <ProjectCreateModal
                        isOpen={isCreateProjectOpen}
                        onClose={() => setIsCreateProjectOpen(false)}
                        onSuccess={() => listProjects(spaceId!)}
                    />
                </div>
            )}

            {activeTab === 'overview' && (
                <div className="text-center py-20 text-gray-500">
                    <LayoutDashboard className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p className="text-lg">空间概览功能开发中...</p>
                </div>
            )}

            {activeTab === 'members' && (
                <div className="text-center py-20 text-gray-500">
                    <Users className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p className="text-lg">成员管理功能开发中...</p>
                </div>
            )}

            {activeTab === 'settings' && (
                <div className="text-center py-20 text-gray-500">
                    <Settings className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p className="text-lg">空间设置功能开发中...</p>
                </div>
            )}
        </AppLayout>
    );
};
