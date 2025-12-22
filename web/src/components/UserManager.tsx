import React, { useState, useEffect, useCallback } from 'react';
import { Users, UserPlus, Shield, Trash2, Edit3, Search, Mail, Calendar } from 'lucide-react';
import { useTenantStore } from '../stores/tenant';
import { useProjectStore } from '../stores/project';

interface User {
    id: string;
    email: string;
    name: string;
    role: 'owner' | 'admin' | 'member' | 'viewer';
    created_at: string;
    last_login?: string;
    is_active: boolean;
}

interface UserManagerProps {
    context: 'tenant' | 'project';
}

export const UserManager: React.FC<UserManagerProps> = ({ context }) => {
    const { currentTenant } = useTenantStore();
    const { currentProject } = useProjectStore();

    const [users, setUsers] = useState<User[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterRole, setFilterRole] = useState<string>('all');
    const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);
    const [_selectedUser, setSelectedUser] = useState<User | null>(null);

    const loadTenantUsers = useCallback(async () => {
        if (!currentTenant) return;

        setIsLoading(true);
        try {
            // TODO: Implement API call to get tenant users
            // const response = await tenantAPI.listMembers(currentTenant.id);
            // setUsers(response.users);

            // Mock data for now
            setUsers([
                {
                    id: '1',
                    email: 'admin@example.com',
                    name: '管理员',
                    role: 'owner',
                    created_at: '2024-01-01T00:00:00Z',
                    last_login: '2024-12-22T10:30:00Z',
                    is_active: true
                },
                {
                    id: '2',
                    email: 'user@example.com',
                    name: '普通用户',
                    role: 'member',
                    created_at: '2024-01-15T00:00:00Z',
                    last_login: '2024-12-21T15:45:00Z',
                    is_active: true
                }
            ]);
        } catch (error) {
            console.error('Failed to load users:', error);
        } finally {
            setIsLoading(false);
        }
    }, [currentTenant]);

    const loadProjectUsers = useCallback(async () => {
        if (!currentProject) return;

        setIsLoading(true);
        try {
            // TODO: Implement API call to get project users
            // const response = await projectAPI.listMembers(currentProject.id);
            // setUsers(response.users);

            // Mock data for now
            setUsers([
                {
                    id: '1',
                    email: 'admin@example.com',
                    name: '项目管理员',
                    role: 'admin',
                    created_at: '2024-01-01T00:00:00Z',
                    last_login: '2024-12-22T10:30:00Z',
                    is_active: true
                },
                {
                    id: '3',
                    email: 'viewer@example.com',
                    name: '查看者',
                    role: 'viewer',
                    created_at: '2024-02-01T00:00:00Z',
                    last_login: '2024-12-20T09:15:00Z',
                    is_active: true
                }
            ]);
        } catch (error) {
            console.error('Failed to load users:', error);
        } finally {
            setIsLoading(false);
        }
    }, [currentProject]);

    useEffect(() => {
        if (context === 'tenant' && currentTenant) {
            loadTenantUsers();
        } else if (context === 'project' && currentProject) {
            loadProjectUsers();
        }
    }, [context, currentTenant, currentProject, loadTenantUsers, loadProjectUsers]);

    const getRoleColor = (role: string) => {
        switch (role) {
            case 'owner': return 'bg-red-100 text-red-800';
            case 'admin': return 'bg-orange-100 text-orange-800';
            case 'member': return 'bg-blue-100 text-blue-800';
            case 'viewer': return 'bg-gray-100 text-gray-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    const filteredUsers = users.filter(user => {
        const matchesSearch = user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            user.email.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesRole = filterRole === 'all' || user.role === filterRole;
        return matchesSearch && matchesRole;
    });

    const handleInviteUser = () => {
        setIsInviteModalOpen(true);
    };

    const handleEditUser = (user: User) => {
        setSelectedUser(user);
        // TODO: Implement edit user modal
    };

    const handleRemoveUser = async (_userId: string) => {
        if (window.confirm('确定要移除这个用户吗？')) {
            try {
                if (context === 'tenant' && currentTenant) {
                    // await tenantAPI.removeMember(currentTenant.id, userId);
                } else if (context === 'project' && currentProject) {
                    // await projectAPI.removeMember(currentProject.id, userId);
                }

                // Reload users
                if (context === 'tenant') {
                    loadTenantUsers();
                } else {
                    loadProjectUsers();
                }
            } catch (error) {
                console.error('Failed to remove user:', error);
            }
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('zh-CN');
    };

    if (!currentTenant && context === 'tenant') {
        return (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
                <div className="text-center">
                    <Users className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">请先选择工作空间</h3>
                    <p className="text-gray-600">选择一个工作空间来管理用户</p>
                </div>
            </div>
        );
    }

    if (!currentProject && context === 'project') {
        return (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
                <div className="text-center">
                    <Users className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">请先选择项目</h3>
                    <p className="text-gray-600">选择一个项目来管理用户</p>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-2">
                        <Users className="h-5 w-5 text-gray-600" />
                        <h3 className="text-lg font-semibold text-gray-900">
                            {context === 'tenant' ? '工作空间用户' : '项目用户'}
                        </h3>
                        <span className="text-sm text-gray-500">({filteredUsers.length} 人)</span>
                    </div>
                    <button
                        onClick={handleInviteUser}
                        className="flex items-center space-x-1 px-3 py-1.5 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm"
                    >
                        <UserPlus className="h-4 w-4" />
                        <span>邀请用户</span>
                    </button>
                </div>

                <div className="flex space-x-4">
                    <div className="flex-1 relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                        <input
                            type="text"
                            placeholder="搜索用户..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>
                    <div>
                        <select
                            value={filterRole}
                            onChange={(e) => setFilterRole(e.target.value)}
                            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                            <option value="all">所有角色</option>
                            <option value="owner">所有者</option>
                            <option value="admin">管理员</option>
                            <option value="member">成员</option>
                            <option value="viewer">查看者</option>
                        </select>
                    </div>
                </div>
            </div>

            <div className="p-6">
                {isLoading ? (
                    <div className="flex items-center justify-center py-8">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    </div>
                ) : filteredUsers.length === 0 ? (
                    <div className="text-center py-8">
                        <Users className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                        <h4 className="text-lg font-medium text-gray-900 mb-2">暂无用户</h4>
                        <p className="text-gray-600 mb-4">
                            {searchTerm || filterRole !== 'all'
                                ? '没有找到匹配的用户'
                                : '开始邀请用户加入'
                            }
                        </p>
                        {!searchTerm && filterRole === 'all' && (
                            <button
                                onClick={handleInviteUser}
                                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                            >
                                邀请用户
                            </button>
                        )}
                    </div>
                ) : (
                    <div className="space-y-4">
                        {filteredUsers.map((user) => (
                            <div
                                key={user.id}
                                className="flex items-center justify-between p-4 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors"
                            >
                                <div className="flex items-center space-x-4 flex-1">
                                    <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                                        <span className="text-white font-medium text-sm">
                                            {user.name.charAt(0).toUpperCase()}
                                        </span>
                                    </div>

                                    <div className="flex-1">
                                        <div className="flex items-center space-x-2 mb-1">
                                            <h4 className="font-medium text-gray-900">{user.name}</h4>
                                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRoleColor(user.role)}`}>
                                                {user.role}
                                            </span>
                                            {user.role === 'owner' && (
                                                <Shield className="h-4 w-4 text-red-600" />
                                            )}
                                        </div>
                                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                                            <div className="flex items-center space-x-1">
                                                <Mail className="h-3 w-3" />
                                                <span>{user.email}</span>
                                            </div>
                                            <div className="flex items-center space-x-1">
                                                <Calendar className="h-3 w-3" />
                                                <span>加入于 {formatDate(user.created_at)}</span>
                                            </div>
                                            {user.last_login && (
                                                <div className="flex items-center space-x-1">
                                                    <span>最后登录: {formatDate(user.last_login)}</span>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                <div className="flex items-center space-x-2">
                                    <button
                                        onClick={() => handleEditUser(user)}
                                        className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                                        title="编辑用户"
                                    >
                                        <Edit3 className="h-4 w-4" />
                                    </button>
                                    {user.role !== 'owner' && (
                                        <button
                                            onClick={() => handleRemoveUser(user.id)}
                                            className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                                            title="移除用户"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Invite User Modal */}
            {isInviteModalOpen && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
                        <div className="flex items-center justify-between p-6 border-b border-gray-200">
                            <div className="flex items-center space-x-2">
                                <UserPlus className="h-5 w-5 text-blue-600" />
                                <h2 className="text-lg font-semibold text-gray-900">
                                    邀请用户
                                </h2>
                            </div>
                            <button
                                onClick={() => setIsInviteModalOpen(false)}
                                className="p-1 text-gray-400 hover:text-gray-600 rounded-md transition-colors"
                            >
                                <span className="text-xl">×</span>
                            </button>
                        </div>

                        <form className="p-6 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    邮箱地址 *
                                </label>
                                <input
                                    type="email"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    placeholder="输入用户邮箱地址"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    角色 *
                                </label>
                                <select className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                                    <option value="member">成员</option>
                                    <option value="admin">管理员</option>
                                    <option value="viewer">查看者</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    消息（可选）
                                </label>
                                <textarea
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                                    placeholder="添加邀请消息..."
                                    rows={3}
                                />
                            </div>

                            <div className="flex space-x-3 pt-4">
                                <button
                                    type="button"
                                    onClick={() => setIsInviteModalOpen(false)}
                                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
                                >
                                    取消
                                </button>
                                <button
                                    type="submit"
                                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                                >
                                    发送邀请
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};