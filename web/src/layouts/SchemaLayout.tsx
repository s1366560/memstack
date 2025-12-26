import { Outlet, useLocation, useNavigate, useParams } from 'react-router-dom';
import { LayoutDashboard, Database, Network, ArrowLeftRight } from 'lucide-react';

export const SchemaLayout = () => {
    const { projectId } = useParams();
    const location = useLocation();
    const navigate = useNavigate();

    const tabs = [
        { name: 'Overview', path: '', icon: LayoutDashboard },
        { name: 'Entity Types', path: 'entities', icon: Database },
        { name: 'Edge Types', path: 'edges', icon: Network },
        { name: 'Mappings', path: 'mapping', icon: ArrowLeftRight },
    ];

    return (
        <div className="flex flex-col h-full bg-slate-50 dark:bg-[#111521] text-slate-900 dark:text-white">
             {/* Tab Navigation Bar */}
            <div className="flex items-center px-8 border-b border-slate-200 dark:border-[#2a324a] bg-white dark:bg-[#121521] shrink-0">
                {tabs.map((tab) => {
                    // Exact match for root path, startsWith for others to handle sub-routes if any
                    const isActive = tab.path === '' 
                        ? location.pathname.endsWith('/schema')
                        : location.pathname.includes(`/schema/${tab.path}`);
                    
                    return (
                        <button
                            key={tab.name}
                            onClick={() => navigate(tab.path === '' ? '.' : tab.path)}
                            className={`flex items-center gap-2 px-4 py-4 text-sm font-medium border-b-2 transition-colors ${
                                isActive 
                                    ? 'border-blue-600 dark:border-[#193db3] text-blue-600 dark:text-white' 
                                    : 'border-transparent text-slate-500 dark:text-[#95a0c6] hover:text-slate-900 dark:hover:text-white hover:border-slate-300 dark:hover:border-[#2a324a]'
                            }`}
                        >
                            <tab.icon className="w-4 h-4" />
                            {tab.name}
                        </button>
                    );
                })}
            </div>
            
            {/* Page Content */}
            <div className="flex-1 overflow-hidden relative">
                <Outlet />
            </div>
        </div>
    );
};
