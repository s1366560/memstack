import React, { useState } from 'react';
import {
    Menu,
    X,
    Bell,
    LogOut,
    Brain
} from 'lucide-react';
import { useAuthStore } from '../stores/auth';
import { useNavigate } from 'react-router-dom';

export interface NavigationItem {
    id: string;
    label: string;
    icon: React.ElementType;
    path?: string; // Optional direct path
    onClick?: () => void; // Optional click handler
}

interface AppLayoutProps {
    children: React.ReactNode;
    title?: string;
    navigationItems: NavigationItem[];
    activeItem?: string;
    contextInfo?: {
        tenantName?: string;
        projectName?: string;
    };
    backButton?: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({
    children,
    title = 'VIP Memory',
    navigationItems,
    activeItem,
    contextInfo,
    backButton
}) => {
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    const { logout, user } = useAuthStore();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const NavItem = ({ item, isMobile = false }: { item: NavigationItem; isMobile?: boolean }) => {
        const Icon = item.icon;
        const isActive = activeItem === item.id;

        return (
            <button
                onClick={() => {
                    if (item.path) {
                        navigate(item.path);
                    } else if (item.onClick) {
                        item.onClick();
                    }
                    if (isMobile) setIsMobileMenuOpen(false);
                }}
                className={`flex items-center space-x-3 w-full px-4 py-3 text-sm font-medium rounded-lg transition-colors ${isActive
                    ? 'bg-blue-100 text-blue-700 border-r-2 border-blue-700'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    } ${isMobile ? 'justify-start' : 'justify-start'}`}
            >
                <Icon className="h-5 w-5" />
                <span>{item.label}</span>
            </button>
        );
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col lg:flex-row">
            {/* Mobile Header */}
            <div className="lg:hidden bg-white shadow-sm border-b border-gray-200">
                <div className="flex items-center justify-between px-4 py-3">
                    <div className="flex items-center space-x-3">
                        {backButton}
                        <Brain className="h-6 w-6 text-blue-600" />
                        <span className="text-lg font-bold text-gray-900">{title}</span>
                    </div>

                    <div className="flex items-center space-x-3">
                        <button
                            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                            className="p-2 text-gray-400 hover:text-gray-600"
                        >
                            {isMobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
                        </button>
                    </div>
                </div>

                {/* Context Info Mobile */}
                {contextInfo && (
                    <div className="px-4 py-2 bg-blue-50 border-t border-blue-100 flex items-center text-sm">
                        {contextInfo.tenantName && (
                            <span className="font-medium text-blue-800">{contextInfo.tenantName}</span>
                        )}
                        {contextInfo.projectName && (
                            <>
                                <span className="mx-2 text-blue-300">/</span>
                                <span className="text-blue-600">{contextInfo.projectName}</span>
                            </>
                        )}
                    </div>
                )}
            </div>

            {/* Mobile Menu Overlay */}
            {isMobileMenuOpen && (
                <div className="lg:hidden fixed inset-0 z-50 bg-black bg-opacity-50" onClick={() => setIsMobileMenuOpen(false)}>
                    <div className="fixed inset-y-0 left-0 w-64 bg-white shadow-xl flex flex-col" onClick={(e) => e.stopPropagation()}>
                        <div className="p-4 border-b border-gray-200 flex justify-between items-center">
                            <span className="font-bold text-lg">Menu</span>
                            <button onClick={() => setIsMobileMenuOpen(false)}><X className="h-5 w-5" /></button>
                        </div>
                        <div className="flex-1 p-4 overflow-y-auto">
                            <div className="space-y-1">
                                {navigationItems.map(item => <NavItem key={item.id} item={item} isMobile />)}
                            </div>
                        </div>
                        <div className="p-4 border-t border-gray-200">
                            <button onClick={handleLogout} className="flex items-center space-x-2 text-red-600">
                                <LogOut className="h-5 w-5" />
                                <span>退出登录</span>
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Desktop Sidebar */}
            <div className="hidden lg:flex lg:flex-col lg:w-64 lg:fixed lg:inset-y-0 bg-white shadow-lg z-10">
                <div className="flex items-center justify-center h-16 px-4 bg-blue-600 text-white shadow-md">
                    {backButton && <div className="mr-2">{backButton}</div>}
                    <Brain className="h-8 w-8 mr-2" />
                    <span className="text-xl font-bold">VIP Memory</span>
                </div>

                {/* Context Info Desktop */}
                {contextInfo && (
                    <div className="px-4 py-4 bg-gray-50 border-b border-gray-200">
                        {contextInfo.tenantName && (
                            <div className="text-xs text-gray-500 uppercase font-semibold mb-1">Space</div>
                        )}
                        {contextInfo.tenantName && (
                            <div className="font-medium text-gray-900 truncate mb-2">{contextInfo.tenantName}</div>
                        )}
                        {contextInfo.projectName && (
                            <>
                                <div className="text-xs text-gray-500 uppercase font-semibold mb-1">Project</div>
                                <div className="font-medium text-gray-900 truncate">{contextInfo.projectName}</div>
                            </>
                        )}
                    </div>
                )}

                <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
                    {navigationItems.map((item) => (
                        <NavItem key={item.id} item={item} />
                    ))}
                </nav>

                <div className="p-4 border-t border-gray-200">
                    <div className="flex items-center space-x-3 mb-4">
                        <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold">
                            {user?.name?.[0]?.toUpperCase() || 'U'}
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 truncate">{user?.name || 'User'}</p>
                            <p className="text-xs text-gray-500 truncate">{user?.email}</p>
                        </div>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="flex items-center space-x-3 w-full px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                        <LogOut className="h-4 w-4" />
                        <span>退出登录</span>
                    </button>
                </div>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 lg:ml-64 flex flex-col min-h-screen">
                {/* Desktop Top Bar */}
                <div className="hidden lg:flex lg:items-center lg:justify-between lg:h-16 lg:px-8 lg:bg-white lg:border-b lg:border-gray-200 shadow-sm sticky top-0 z-20">
                    <h1 className="text-xl font-semibold text-gray-800">{title}</h1>
                    <div className="flex items-center space-x-4">
                        <button className="p-2 text-gray-400 hover:text-gray-600 rounded-full transition-colors">
                            <Bell className="h-5 w-5" />
                        </button>
                    </div>
                </div>

                <main className="flex-1 p-4 lg:p-8 overflow-x-hidden">
                    {children}
                </main>
            </div>
        </div>
    );
};
