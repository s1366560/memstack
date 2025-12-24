import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { memoryAPI } from '../../services/api'

// Types for our graph visualization
interface GraphNode {
    id: string
    type: 'project' | 'document' | 'person' | 'company' | 'note'
    label: string
    subLabel?: string
    x: number
    y: number
    color: string
    icon: string
}

interface GraphLink {
    source: string
    target: string
    type: 'solid' | 'dashed' | 'gradient'
    width: number
}

export const MemoryGraph: React.FC = () => {
    const { projectId } = useParams()
    const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
    const [isLoading, setIsLoading] = useState(false)
    
    // Mock data for initial visualization (matching static HTML)
    const nodes: GraphNode[] = [
        { id: '1', type: 'project', label: 'Project Alpha', x: 50, y: 45, color: 'bg-blue-600', icon: 'rocket_launch' },
        { id: '2', type: 'document', label: 'Budget_FY24.xlsx', subLabel: 'Budget_FY24.xlsx', x: 30, y: 60, color: 'bg-emerald-600', icon: 'description' },
        { id: '3', type: 'person', label: 'Sarah Chen', subLabel: 'Sarah Chen', x: 70, y: 30, color: 'bg-rose-600', icon: 'person' },
        { id: '4', type: 'document', label: 'Tech Specs', subLabel: 'Tech Specs', x: 45, y: 25, color: 'bg-emerald-700', icon: 'article' },
        { id: '5', type: 'company', label: 'TechFlow Inc.', subLabel: 'TechFlow Inc.', x: 65, y: 70, color: 'bg-purple-600', icon: 'apartment' },
        { id: '6', type: 'note', label: 'Meeting Notes', x: 80, y: 40, color: 'bg-emerald-800', icon: 'sticky_note_2' },
    ]

    useEffect(() => {
        // In a real implementation, we would fetch graph data here
        // const fetchGraph = async () => {
        //     setIsLoading(true)
        //     try {
        //         const data = await memoryAPI.getGraphData(projectId!)
        //         // process data...
        //     } catch (e) { ... }
        // }
        // if (projectId) fetchGraph()
        
        // Select the main node by default
        setSelectedNode(nodes[0])
    }, [projectId])

    return (
        <div className="flex h-[calc(100vh-4rem)] w-full overflow-hidden bg-[#111521] relative text-slate-200">
            {/* Grid Background */}
            <div className="absolute inset-0 bg-[radial-gradient(#2b324a_1px,transparent_1px)] [background-size:40px_40px] opacity-20 pointer-events-none"></div>

            {/* Toolbar (Top Left) */}
            <div className="absolute top-6 left-6 flex flex-col gap-2 z-10">
                <div className="bg-[#1e2332] border border-[#2b324a] rounded-lg shadow-xl overflow-hidden flex flex-col">
                    <button className="p-2.5 text-slate-400 hover:text-white hover:bg-[#2b324a] border-b border-[#2b324a] transition-colors" title="Select Tool">
                        <span className="material-symbols-outlined text-[20px]">arrow_selector_tool</span>
                    </button>
                    <button className="p-2.5 text-slate-400 hover:text-white hover:bg-[#2b324a] border-b border-[#2b324a] transition-colors" title="Pan Tool">
                        <span className="material-symbols-outlined text-[20px]">pan_tool</span>
                    </button>
                    <button className="p-2.5 text-slate-400 hover:text-white hover:bg-[#2b324a] transition-colors" title="Lasso Select">
                        <span className="material-symbols-outlined text-[20px]">lasso_select</span>
                    </button>
                </div>
                <div className="bg-[#1e2332] border border-[#2b324a] rounded-lg shadow-xl overflow-hidden flex flex-col mt-2">
                    <button className="p-2.5 text-slate-400 hover:text-white hover:bg-[#2b324a] border-b border-[#2b324a] transition-colors" title="Zoom In">
                        <span className="material-symbols-outlined text-[20px]">add</span>
                    </button>
                    <button className="p-2.5 text-slate-400 hover:text-white hover:bg-[#2b324a] transition-colors" title="Zoom Out">
                        <span className="material-symbols-outlined text-[20px]">remove</span>
                    </button>
                </div>
                <button className="bg-[#1e2332] border border-[#2b324a] rounded-lg shadow-xl p-2.5 text-slate-400 hover:text-white hover:bg-[#2b324a] mt-2 transition-colors" title="Center Graph">
                    <span className="material-symbols-outlined text-[20px]">center_focus_strong</span>
                </button>
            </div>

            {/* Filter Legend (Bottom Left) */}
            <div className="absolute bottom-6 left-6 z-10">
                <div className="bg-[#1e2332]/90 backdrop-blur border border-[#2b324a] rounded-lg p-3 shadow-xl">
                    <div className="text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">Entity Types</div>
                    <div className="flex flex-col gap-2">
                        <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer hover:text-white">
                            <span className="w-3 h-3 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.6)]"></span>
                            <span>Projects</span>
                        </label>
                        <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer hover:text-white">
                            <span className="w-3 h-3 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]"></span>
                            <span>Documents</span>
                        </label>
                        <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer hover:text-white">
                            <span className="w-3 h-3 rounded-full bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.6)]"></span>
                            <span>People</span>
                        </label>
                        <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer hover:text-white">
                            <span className="w-3 h-3 rounded-full border-2 border-slate-500 border-dashed"></span>
                            <span className="text-slate-400">Indirect Links</span>
                        </label>
                    </div>
                </div>
            </div>

            {/* Graph Visualization Area */}
            <div className="w-full h-full relative cursor-grab active:cursor-grabbing overflow-hidden">
                {/* SVG Connections Layer */}
                <svg className="absolute inset-0 w-full h-full pointer-events-none z-0">
                    <defs>
                        <linearGradient id="grad1" x1="0%" x2="100%" y1="0%" y2="0%">
                            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.6"></stop>
                            <stop offset="100%" stopColor="#10b981" stopOpacity="0.6"></stop>
                        </linearGradient>
                    </defs>
                    {/* Connections matching the static mockup */}
                    <line stroke="#475569" strokeWidth="2" x1="50%" x2="30%" y1="45%" y2="60%"></line>
                    <line stroke="#475569" strokeWidth="1.5" x1="50%" x2="70%" y1="45%" y2="30%"></line>
                    <line stroke="#475569" strokeDasharray="5,5" strokeWidth="1" x1="30%" x2="70%" y1="60%" y2="30%"></line>
                    <path d="M 50% 45% Q 60% 60% 65% 70%" fill="none" stroke="url(#grad1)" strokeWidth="2"></path>
                    <line stroke="#475569" strokeWidth="1" x1="50%" x2="45%" y1="45%" y2="25%"></line>
                    <line stroke="#475569" strokeWidth="1" x1="70%" x2="80%" y1="30%" y2="40%"></line>
                    <line stroke="#475569" strokeDasharray="4,4" strokeWidth="1" x1="30%" x2="20%" y1="60%" y2="50%"></line>
                </svg>

                {/* Render Nodes */}
                {nodes.map((node) => (
                    <div 
                        key={node.id}
                        className="absolute -translate-x-1/2 -translate-y-1/2 flex flex-col items-center z-10 group cursor-pointer"
                        style={{ top: `${node.y}%`, left: `${node.x}%` }}
                        onClick={() => setSelectedNode(node)}
                    >
                        <div className="relative">
                            <div className={`
                                rounded-full flex items-center justify-center text-white font-bold shadow-lg transition-transform duration-300 group-hover:scale-110
                                ${node.type === 'project' ? 'w-16 h-16 text-xl border-4 border-white/20' : 'w-12 h-12 text-lg border-2 border-white/20'}
                                ${node.color}
                                ${selectedNode?.id === node.id ? 'ring-4 ring-white/30' : ''}
                            `}>
                                <span className="material-symbols-outlined" style={{ fontSize: node.type === 'project' ? '32px' : '24px' }}>{node.icon}</span>
                            </div>
                            {node.type === 'project' && (
                                <div className="absolute inset-0 rounded-full border border-blue-500 animate-ping opacity-20"></div>
                            )}
                        </div>
                        {node.subLabel && (
                            <div className="mt-2 bg-[#111521]/80 px-2 py-0.5 rounded text-xs text-slate-200 border border-slate-700/50 backdrop-blur-sm">
                                {node.subLabel}
                            </div>
                        )}
                        {node.type === 'project' && (
                            <div className="mt-3 bg-[#111521]/80 px-3 py-1 rounded-full border border-blue-900/50 backdrop-blur-sm">
                                <span className="text-blue-100 font-bold text-sm whitespace-nowrap">{node.label}</span>
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {/* Right Side Detail Panel */}
            {selectedNode && (
                <div className="absolute top-6 right-6 bottom-6 w-80 bg-[#1e2332] border border-[#2b324a] shadow-2xl rounded-xl z-20 flex flex-col overflow-hidden animate-in slide-in-from-right duration-300">
                    {/* Panel Header */}
                    <div className="p-5 border-b border-[#2b324a] bg-gradient-to-r from-blue-900/20 to-transparent">
                        <div className="flex justify-between items-start mb-2">
                            <div className="bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide border border-blue-500/30">
                                {selectedNode.type} Entity
                            </div>
                            <button onClick={() => setSelectedNode(null)} className="text-slate-400 hover:text-white transition-colors">
                                <span className="material-symbols-outlined text-[20px]">close</span>
                            </button>
                        </div>
                        <h2 className="text-xl font-bold text-white leading-tight">{selectedNode.label}</h2>
                        <div className="flex items-center gap-2 mt-2 text-xs text-slate-400">
                            <span className="material-symbols-outlined text-[14px]">calendar_today</span>
                            <span>Created Oct 24, 2023</span>
                        </div>
                    </div>

                    {/* Panel Content */}
                    <div className="flex-1 overflow-y-auto p-5 space-y-6">
                        {/* Importance Metric */}
                        <div>
                            <div className="flex justify-between items-end mb-1">
                                <label className="text-xs font-semibold text-slate-400 uppercase">Impact Score</label>
                                <span className="text-emerald-400 font-bold text-sm">92/100</span>
                            </div>
                            <div className="w-full bg-[#111521] rounded-full h-1.5 overflow-hidden">
                                <div className="bg-gradient-to-r from-emerald-500 to-blue-600 h-full rounded-full" style={{ width: '92%' }}></div>
                            </div>
                        </div>

                        {/* Description */}
                        <div>
                            <label className="text-xs font-semibold text-slate-400 uppercase mb-2 block">Description</label>
                            <p className="text-sm text-slate-300 leading-relaxed">
                                Core initiative for Q4 platform migration. Connects multiple dependencies across engineering and design teams.
                            </p>
                        </div>

                        {/* Connected Nodes List */}
                        <div>
                            <div className="flex justify-between items-center mb-3">
                                <label className="text-xs font-semibold text-slate-400 uppercase">Connections (5)</label>
                                <button className="text-xs text-blue-400 hover:text-blue-300 font-medium">View All</button>
                            </div>
                            <div className="space-y-2">
                                <div className="flex items-center gap-3 p-2 rounded-lg bg-[#111521] border border-[#2b324a] hover:border-blue-500/50 transition-colors group cursor-pointer">
                                    <div className="w-8 h-8 rounded bg-emerald-900/50 flex items-center justify-center text-emerald-400 group-hover:bg-emerald-600 group-hover:text-white transition-colors">
                                        <span className="material-symbols-outlined text-[16px]">description</span>
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="text-sm font-medium text-slate-200 truncate">Budget_FY24.xlsx</div>
                                        <div className="text-[10px] text-slate-500">Financial • Direct Link</div>
                                    </div>
                                    <span className="material-symbols-outlined text-slate-600 text-[16px]">link</span>
                                </div>
                                <div className="flex items-center gap-3 p-2 rounded-lg bg-[#111521] border border-[#2b324a] hover:border-blue-500/50 transition-colors group cursor-pointer">
                                    <div className="w-8 h-8 rounded bg-rose-900/50 flex items-center justify-center text-rose-400 group-hover:bg-rose-600 group-hover:text-white transition-colors">
                                        <span className="material-symbols-outlined text-[16px]">person</span>
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="text-sm font-medium text-slate-200 truncate">Sarah Chen</div>
                                        <div className="text-[10px] text-slate-500">Owner • Strong Tie</div>
                                    </div>
                                    <span className="material-symbols-outlined text-slate-600 text-[16px]">link</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Panel Footer */}
                    <div className="p-4 border-t border-[#2b324a] bg-[#111521] flex gap-2">
                        <button className="flex-1 py-2 rounded-lg border border-[#2b324a] bg-[#1e2332] text-slate-300 text-sm font-medium hover:bg-[#2b324a] hover:text-white transition-colors">
                            Expand
                        </button>
                        <button className="flex-1 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-500 shadow-lg shadow-blue-600/20 transition-colors">
                            Edit Node
                        </button>
                    </div>
                </div>
            )}
        </div>
    )
}
