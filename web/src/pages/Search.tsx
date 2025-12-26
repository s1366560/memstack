import React, { useState } from 'react';
import {
    LayoutDashboard,
    Search as SearchIcon,
    Folder,
    Users,
    Settings,
    Mic,
    ZoomIn,
    ZoomOut,
    Maximize,
    FileText,
    Image as ImageIcon,
    ExternalLink,
    Filter,
    ArrowRight
} from 'lucide-react';
import { AppLayout, NavigationGroup } from '../components/AppLayout';

export const Search: React.FC = () => {
    const [searchQuery, setSearchQuery] = useState('Project Alpha architecture decisions');
    const [timeRange] = useState('Last 30 Days');
    const [similarity, setSimilarity] = useState(85);

    const navGroups: NavigationGroup[] = [
        {
            items: [
                { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, path: '/spaces' },
                { id: 'smart-search', label: 'Smart Search', icon: SearchIcon, path: '/search' },
                { id: 'projects', label: 'Projects', icon: Folder, path: '/projects' },
                { id: 'agents', label: 'Agents', icon: Users, path: '/agents' },
                { id: 'settings', label: 'Settings', icon: Settings, path: '/settings' },
            ]
        }
    ];

    const Header = (
        <div className="bg-white dark:bg-slate-900 border-b border-gray-200 dark:border-slate-800 sticky top-0 z-20 px-8 py-3 flex items-center justify-between h-16">
             <div className="flex items-center text-sm text-gray-500 dark:text-slate-400">
                <span className="hover:text-gray-700 dark:hover:text-slate-200 cursor-pointer">Acme Corp</span>
                <span className="mx-2 text-gray-300 dark:text-slate-600">/</span>
                <span className="hover:text-gray-700 dark:hover:text-slate-200 cursor-pointer">Engineering</span>
                <span className="mx-2 text-gray-300 dark:text-slate-600">/</span>
                <span className="font-medium text-gray-900 dark:text-white">Memory Graph</span>
            </div>

            <div className="flex-1 max-w-2xl mx-8 relative">
                <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <SearchIcon className="h-4 w-4 text-gray-400 dark:text-slate-500" />
                    </div>
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="block w-full pl-10 pr-10 py-2 border border-gray-200 dark:border-slate-700 rounded-lg leading-5 bg-gray-50 dark:bg-slate-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-slate-500 focus:outline-none focus:bg-white dark:focus:bg-slate-900 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                        placeholder="Search resources..."
                    />
                    <div className="absolute inset-y-0 right-0 pr-3 flex items-center cursor-pointer">
                        <Mic className="h-4 w-4 text-gray-400 dark:text-slate-500 hover:text-gray-600 dark:hover:text-slate-300" />
                    </div>
                </div>
            </div>

            <div className="flex items-center space-x-3">
                <div className="flex bg-gray-100 dark:bg-slate-800 rounded-lg p-1">
                    <button className="px-3 py-1 bg-white dark:bg-slate-700 shadow-sm rounded-md text-sm font-medium text-gray-900 dark:text-white">Smart Search</button>
                    <button className="px-3 py-1 text-sm font-medium text-gray-500 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white">Literal</button>
                </div>
                <button className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                    <span>Retrieve</span>
                    <ArrowRight className="h-4 w-4" />
                </button>
            </div>
        </div>
    );

    return (
        <AppLayout
            title="Memory Graph"
            navigationGroups={navGroups}
            activeItem="smart-search"
            customHeader={Header}
        >
            <div className="flex h-[calc(100vh-8rem)] gap-6">
                {/* Left Filter Panel */}
                <div className="w-64 flex-shrink-0 bg-white dark:bg-surface-dark rounded-xl shadow-sm border border-gray-200 dark:border-slate-800 p-5 overflow-y-auto">
                    {/* Time Range */}
                    <div className="mb-8">
                        <div className="flex justify-between items-center mb-3">
                            <h3 className="text-xs font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider">Time Range</h3>
                            <button className="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium">Reset</button>
                        </div>
                        <div className="space-y-2">
                            {['All Time', 'Last 30 Days', 'Custom Range'].map((option) => (
                                <label key={option} className="flex items-center space-x-3 cursor-pointer group">
                                    <div className={`w-4 h-4 rounded-full border flex items-center justify-center ${timeRange === option ? 'border-blue-600 dark:border-blue-500' : 'border-gray-300 dark:border-slate-600 group-hover:border-blue-400'}`}>
                                        {timeRange === option && <div className="w-2 h-2 rounded-full bg-blue-600 dark:bg-blue-500" />}
                                    </div>
                                    <span className={`text-sm ${timeRange === option ? 'text-gray-900 dark:text-white font-medium' : 'text-gray-600 dark:text-slate-400'}`}>{option}</span>
                                </label>
                            ))}
                        </div>
                    </div>

                    {/* Similarity */}
                    <div className="mb-8">
                        <div className="flex justify-between items-center mb-3">
                            <h3 className="text-xs font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider">Similarity</h3>
                            <span className="text-xs font-bold text-gray-900 dark:text-white">{similarity}%</span>
                        </div>
                        <input
                            type="range"
                            min="0"
                            max="100"
                            value={similarity}
                            onChange={(e) => setSimilarity(parseInt(e.target.value))}
                            className="w-full h-1.5 bg-gray-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
                        />
                        <div className="flex justify-between mt-2 text-xs text-gray-400 dark:text-slate-500">
                            <span>Broad</span>
                            <span>Exact</span>
                        </div>
                    </div>

                    {/* Tags */}
                    <div className="mb-8">
                        <h3 className="text-xs font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-3">Tags</h3>
                        <div className="flex flex-wrap gap-2">
                            {['#architecture', '#meeting', '#decisions', '#Q3'].map((tag) => (
                                <span
                                    key={tag}
                                    className={`px-2.5 py-1 rounded-full text-xs font-medium cursor-pointer transition-colors ${tag === '#architecture'
                                            ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 border border-blue-100 dark:border-blue-800'
                                            : 'bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-slate-400 border border-transparent hover:bg-gray-200 dark:hover:bg-slate-700'
                                        }`}
                                >
                                    {tag}
                                </span>
                            ))}
                        </div>
                    </div>

                    {/* Entity Type */}
                    <div>
                        <h3 className="text-xs font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-3">Entity Type</h3>
                        <div className="space-y-2">
                            {[
                                { label: 'Documents', checked: true },
                                { label: 'Conversations', checked: true },
                                { label: 'Images', checked: false }
                            ].map((type) => (
                                <label key={type.label} className="flex items-center space-x-3 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        defaultChecked={type.checked}
                                        className="w-4 h-4 text-blue-600 border-gray-300 dark:border-slate-600 rounded focus:ring-blue-500 dark:bg-slate-800"
                                    />
                                    <span className="text-sm text-gray-700 dark:text-slate-300">{type.label}</span>
                                </label>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Center Canvas */}
                <div className="flex-1 bg-white dark:bg-[#111521] rounded-xl shadow-sm border border-gray-200 dark:border-slate-800 relative overflow-hidden bg-dot-pattern">
                    {/* Canvas Controls */}
                    <div className="absolute top-4 left-4 flex flex-col space-y-2 bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-gray-200 dark:border-slate-700 p-1">
                        <button className="p-1.5 hover:bg-gray-50 dark:hover:bg-slate-700 rounded text-gray-600 dark:text-slate-400"><ZoomIn className="h-4 w-4" /></button>
                        <button className="p-1.5 hover:bg-gray-50 dark:hover:bg-slate-700 rounded text-gray-600 dark:text-slate-400"><ZoomOut className="h-4 w-4" /></button>
                        <button className="p-1.5 hover:bg-gray-50 dark:hover:bg-slate-700 rounded text-gray-600 dark:text-slate-400"><Maximize className="h-4 w-4" /></button>
                    </div>

                    {/* Mock Graph Visualization */}
                    <div className="absolute inset-0 flex items-center justify-center">
                        <div className="relative w-full h-full">
                            <svg className="absolute inset-0 w-full h-full pointer-events-none">
                                {/* Connections */}
                                <line x1="45%" y1="40%" x2="55%" y2="55%" stroke="#cbd5e1" strokeWidth="2" className="dark:stroke-slate-600" />
                                <line x1="55%" y1="55%" x2="65%" y2="35%" stroke="#cbd5e1" strokeWidth="2" className="dark:stroke-slate-600" />
                                <line x1="55%" y1="55%" x2="68%" y2="50%" stroke="#cbd5e1" strokeWidth="2" className="dark:stroke-slate-600" />
                                <line x1="55%" y1="55%" x2="58%" y2="75%" stroke="#cbd5e1" strokeWidth="2" strokeDasharray="4 4" className="dark:stroke-slate-600" />
                            </svg>

                            {/* Node: Assets */}
                            <div className="absolute top-[35%] left-[42%] flex flex-col items-center">
                                <div className="w-12 h-12 bg-orange-100 dark:bg-orange-900/40 rounded-full flex items-center justify-center shadow-sm border-2 border-white dark:border-slate-700">
                                    <Folder className="h-6 w-6 text-orange-500 dark:text-orange-400" />
                                </div>
                                <span className="mt-2 text-xs font-medium text-gray-700 dark:text-slate-300 bg-white dark:bg-slate-800 px-2 py-0.5 rounded shadow-sm border border-transparent dark:border-slate-700">Assets</span>
                            </div>

                            {/* Node: Project Alpha (Center) */}
                            <div className="absolute top-[50%] left-[52%] flex flex-col items-center z-10">
                                <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center shadow-lg ring-4 ring-blue-50 dark:ring-blue-900/30">
                                    <div className="text-white">
                                        <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                        </svg>
                                    </div>
                                </div>
                                <span className="mt-3 text-sm font-bold text-gray-800 dark:text-white bg-white dark:bg-slate-800 px-3 py-1 rounded-full shadow-md border border-transparent dark:border-slate-700">Project Alpha</span>
                            </div>

                            {/* Node: Specs.pdf */}
                            <div className="absolute top-[30%] left-[63%] flex flex-col items-center">
                                <div className="w-10 h-10 bg-green-100 dark:bg-green-900/40 rounded-full flex items-center justify-center shadow-sm border-2 border-white dark:border-slate-700">
                                    <FileText className="h-5 w-5 text-green-600 dark:text-green-400" />
                                </div>
                                <span className="mt-2 text-xs font-medium text-gray-700 dark:text-slate-300 bg-white dark:bg-slate-800 px-2 py-0.5 rounded shadow-sm border border-transparent dark:border-slate-700">Specs.pdf</span>
                            </div>

                            {/* Node: Sarah J. */}
                            <div className="absolute top-[45%] left-[66%] flex flex-col items-center">
                                <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/40 rounded-full flex items-center justify-center shadow-sm border-2 border-white dark:border-slate-700">
                                    <Users className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                                </div>
                                <span className="mt-2 text-xs font-medium text-gray-700 dark:text-slate-300 bg-white dark:bg-slate-800 px-2 py-0.5 rounded shadow-sm border border-transparent dark:border-slate-700">Sarah J.</span>
                            </div>

                            {/* Node: External Ref */}
                            <div className="absolute top-[72%] left-[56%] flex flex-col items-center">
                                <div className="w-10 h-10 bg-gray-100 dark:bg-slate-700 rounded-full flex items-center justify-center shadow-sm border-2 border-white dark:border-slate-600">
                                    <ExternalLink className="h-5 w-5 text-gray-500 dark:text-slate-400" />
                                </div>
                                <span className="mt-2 text-xs font-medium text-gray-700 dark:text-slate-300 bg-white dark:bg-slate-800 px-2 py-0.5 rounded shadow-sm border border-transparent dark:border-slate-700">External Ref</span>
                            </div>
                        </div>
                    </div>

                    <div className="absolute bottom-4 left-4 bg-white/90 dark:bg-slate-800/90 backdrop-blur-sm px-3 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 shadow-sm">
                        <span className="text-xs text-gray-600 dark:text-slate-300 font-medium">24 nodes found</span>
                    </div>
                </div>

                {/* Right Results Panel */}
                <div className="w-80 flex-shrink-0 bg-white dark:bg-surface-dark rounded-xl shadow-sm border border-gray-200 dark:border-slate-800 flex flex-col overflow-hidden">
                    <div className="p-4 border-b border-gray-200 dark:border-slate-800 flex justify-between items-center bg-gray-50/50 dark:bg-slate-800/50">
                        <h3 className="font-semibold text-gray-900 dark:text-white">Results <span className="text-gray-500 dark:text-slate-500 font-normal">(24)</span></h3>
                        <div className="flex items-center text-xs text-gray-500 dark:text-slate-500 cursor-pointer hover:text-gray-700 dark:hover:text-slate-300">
                            <Filter className="h-3 w-3 mr-1" />
                            <span>Relevance</span>
                        </div>
                    </div>
                    <div className="flex-1 overflow-y-auto p-4 space-y-4">
                        {/* Result 1 */}
                        <div className="bg-white dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700 p-4 hover:shadow-md hover:border-blue-300 dark:hover:border-blue-500 transition-all cursor-pointer group">
                            <div className="flex justify-between items-start mb-2">
                                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 uppercase tracking-wide">PDF</span>
                                <span className="text-xs font-bold text-blue-600 dark:text-blue-400">98% Match</span>
                            </div>
                            <h4 className="font-bold text-gray-900 dark:text-white text-sm mb-1 group-hover:text-blue-600 dark:group-hover:text-blue-400">Architecture Specs v2.pdf</h4>
                            <p className="text-xs text-gray-500 dark:text-slate-400 mb-3 line-clamp-2">...final decision regarding the <span className="bg-yellow-100 dark:bg-yellow-900/30 text-gray-900 dark:text-white">architecture</span> of Project Alpha was to utilize microservices...</p>
                            <div className="flex justify-between items-center text-[10px] text-gray-400 dark:text-slate-500">
                                <span className="text-gray-500 dark:text-slate-400">#specs</span>
                                <span>Oct 12, 2023</span>
                            </div>
                        </div>

                        {/* Result 2 */}
                        <div className="bg-white dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700 p-4 hover:shadow-md hover:border-blue-300 dark:hover:border-blue-500 transition-all cursor-pointer group">
                            <div className="flex justify-between items-start mb-2">
                                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 uppercase tracking-wide">Slack</span>
                                <span className="text-xs font-bold text-blue-600 dark:text-blue-400">85% Match</span>
                            </div>
                            <h4 className="font-bold text-gray-900 dark:text-white text-sm mb-1 group-hover:text-blue-600 dark:group-hover:text-blue-400">#engineering-general</h4>
                            <p className="text-xs text-gray-500 dark:text-slate-400 mb-3 line-clamp-2">Alex: I think we should reconsider the database choice for the <span className="bg-yellow-100 dark:bg-yellow-900/30 text-gray-900 dark:text-white">Alpha</span> project timeline...</p>
                            <div className="flex justify-between items-center text-[10px] text-gray-400 dark:text-slate-500">
                                <span className="text-gray-500 dark:text-slate-400">#discussion</span>
                                <span>Oct 10, 2023</span>
                            </div>
                        </div>

                         {/* Result 3 */}
                         <div className="bg-white dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700 p-4 hover:shadow-md hover:border-blue-300 dark:hover:border-blue-500 transition-all cursor-pointer group">
                            <div className="flex justify-between items-start mb-2">
                                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 uppercase tracking-wide">IMG</span>
                                <span className="text-xs font-bold text-blue-600 dark:text-blue-400">72% Match</span>
                            </div>
                            <h4 className="font-bold text-gray-900 dark:text-white text-sm mb-1 group-hover:text-blue-600 dark:group-hover:text-blue-400">Whiteboard_Session_3.png</h4>
                             <div className="h-24 bg-gray-100 dark:bg-slate-700 rounded mb-3 overflow-hidden relative">
                                {/* Placeholder for image thumbnail */}
                                <div className="absolute inset-0 flex items-center justify-center text-gray-400 dark:text-slate-500">
                                    <ImageIcon className="h-8 w-8 opacity-20" />
                                </div>
                             </div>
                            <div className="flex justify-between items-center text-[10px] text-gray-400 dark:text-slate-500">
                                <span className="text-gray-500 dark:text-slate-400">#diagram</span>
                                <span>Sep 28, 2023</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </AppLayout>
    );
};
