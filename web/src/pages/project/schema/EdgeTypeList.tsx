import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { schemaAPI } from '../../../services/api';
import {
    Plus,
    Search,
    Filter,
    Download,
    Code,
    Info,
    Pencil,
    Share2,
    Trash2,
    X,
    FileEdit,
    ChevronDown,
    History
} from 'lucide-react';

export default function EdgeTypeList() {
    const { projectId } = useParams<{ projectId: string }>();
    const [edges, setEdges] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingEdge, setEditingEdge] = useState<any>(null);

    // Form state
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        schema: {} as Record<string, any>
    });

    // Attribute builder state
    const [attributes, setAttributes] = useState<{ name: string, type: string, description: string, required: boolean }[]>([]);

    const loadData = useCallback(async () => {
        if (!projectId) return;
        try {
            const data = await schemaAPI.listEdgeTypes(projectId);
            setEdges(data);
            if (data.length > 0 && !selectedEdgeId) {
                setSelectedEdgeId(data[0].id);
            }
        } catch (error) {
            console.error('Failed to load edge types:', error);
        } finally {
            setLoading(false);
        }
    }, [projectId, selectedEdgeId]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const handleOpenModal = (edge: any = null) => {
        if (edge) {
            setEditingEdge(edge);
            const attrs = Object.entries(edge.schema || {}).map(([key, val]: [string, any]) => ({
                name: key,
                type: typeof val === 'string' ? val : val.type || 'String',
                description: typeof val === 'string' ? '' : val.description || '',
                required: false
            }));
            setFormData({
                name: edge.name,
                description: edge.description || '',
                schema: edge.schema
            });
            setAttributes(attrs);
        } else {
            setEditingEdge(null);
            setFormData({ name: '', description: '', schema: {} });
            setAttributes([]);
        }
        setIsModalOpen(true);
    };

    const handleSave = async () => {
        if (!projectId) return;

        const schemaDict: Record<string, any> = {};
        attributes.forEach(attr => {
            if (attr.name) {
                schemaDict[attr.name] = {
                    type: attr.type,
                    description: attr.description,
                    required: attr.required
                };
            }
        });

        const payload = {
            ...formData,
            schema: schemaDict
        };

        try {
            if (editingEdge) {
                await schemaAPI.updateEdgeType(projectId, editingEdge.id, payload);
            } else {
                await schemaAPI.createEdgeType(projectId, payload);
            }
            setIsModalOpen(false);
            loadData();
        } catch (error) {
            console.error('Failed to save edge type:', error);
            alert('Failed to save. Check if name is unique.');
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Are you sure? This will delete the edge type definition.')) return;
        if (!projectId) return;
        try {
            await schemaAPI.deleteEdgeType(projectId, id);
            if (selectedEdgeId === id) {
                setSelectedEdgeId(null);
            }
            loadData();
        } catch (error) {
            console.error('Failed to delete:', error);
        }
    };

    const addAttribute = () => {
        setAttributes([...attributes, { name: '', type: 'String', description: '', required: false }]);
    };

    const updateAttribute = (index: number, field: string, value: any) => {
        const newAttrs = [...attributes];
        newAttrs[index] = { ...newAttrs[index], [field]: value };
        setAttributes(newAttrs);
    };

    const removeAttribute = (index: number) => {
        setAttributes(attributes.filter((_, i) => i !== index));
    };

    const selectedEdge = edges.find(e => e.id === selectedEdgeId);

    if (loading) return <div className="p-8 text-center text-slate-500 dark:text-gray-500">Loading...</div>;

    return (
        <div className="flex flex-col h-full bg-slate-50 dark:bg-[#111521] text-slate-900 dark:text-white overflow-hidden">
            {/* Header */}
            <div className="w-full flex-none pt-6 pb-4 px-8 border-b border-slate-200 dark:border-[#2a324a]/50 bg-white dark:bg-[#121521]">
                <div className="max-w-[1600px] mx-auto flex flex-col gap-4">
                    <div className="flex flex-wrap justify-between items-end gap-4">
                        <div className="flex flex-col gap-2 max-w-2xl">
                            <h1 className="text-slate-900 dark:text-white text-3xl font-black leading-tight tracking-tight">Relationship Type Management</h1>
                            <p className="text-slate-500 dark:text-[#95a0c6] text-base font-normal">Define custom edge schemas and configure the valid connection rules between entity types.</p>
                        </div>
                        <div className="flex gap-2">
                            <span className="px-3 py-1 rounded-full bg-green-50 dark:bg-green-500/10 text-green-600 dark:text-green-400 text-xs font-medium border border-green-200 dark:border-green-500/20">System Status: Active</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-y-auto p-8 bg-slate-50 dark:bg-[#111521]">
                <div className="max-w-[1600px] mx-auto flex flex-col bg-white dark:bg-[#1e2128] rounded-xl border border-slate-200 dark:border-[#2d3748] overflow-hidden shadow-xl min-h-[600px]">

                    {/* Toolbar */}
                    <div className="flex flex-wrap justify-between items-center gap-4 px-6 py-4 border-b border-slate-200 dark:border-[#2d3748] bg-slate-50 dark:bg-[#181b25]">
                        <div className="flex items-center gap-3 flex-1">
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                                    <Search className="text-slate-400 dark:text-[#95a0c6] w-5 h-5" />
                                </div>
                                <input
                                    className="bg-white dark:bg-[#121521] border border-slate-200 dark:border-[#2d3748] text-slate-900 dark:text-white text-sm rounded-lg focus:ring-blue-600 dark:focus:ring-[#193db3] focus:border-blue-600 dark:focus:border-[#193db3] block w-64 pl-10 p-2.5 placeholder-slate-400 dark:placeholder-gray-500 transition-all focus:w-80 outline-none"
                                    placeholder="Search edge types..."
                                    type="text"
                                />
                            </div>
                            <div className="h-6 w-px bg-slate-200 dark:bg-[#2d3748] mx-2"></div>
                            <button className="p-2 text-slate-500 dark:text-[#95a0c6] hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-white/5 rounded-lg transition-colors" title="Filter">
                                <Filter className="w-5 h-5" />
                            </button>
                            <button className="p-2 text-slate-500 dark:text-[#95a0c6] hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-white/5 rounded-lg transition-colors" title="Download Schema">
                                <Download className="w-5 h-5" />
                            </button>
                        </div>
                        <button
                            onClick={() => handleOpenModal()}
                            className="flex items-center justify-center gap-2 bg-blue-600 dark:bg-[#193db3] hover:bg-blue-700 text-white px-4 py-2.5 rounded-lg text-sm font-bold shadow-lg shadow-blue-900/20 transition-all active:scale-95"
                        >
                            <Plus className="w-5 h-5" />
                            <span>Create Edge Type</span>
                        </button>
                    </div>

                    {/* Master-Detail Content Layout */}
                    <div className="flex flex-1 overflow-hidden h-[600px]">
                        {/* List Pane (Master) */}
                        <div className="w-1/3 border-r border-slate-200 dark:border-[#2d3748] overflow-y-auto bg-slate-50 dark:bg-[#151820]">
                            {edges.map(edge => (
                                <div
                                    key={edge.id}
                                    onClick={() => setSelectedEdgeId(edge.id)}
                                    className={`p-4 border-b border-slate-200 dark:border-[#2d3748] cursor-pointer transition-colors border-l-4 ${selectedEdgeId === edge.id ? 'bg-blue-50 dark:bg-[#193db3]/10 border-l-blue-600 dark:border-l-[#193db3] hover:bg-blue-100 dark:hover:bg-[#193db3]/20' : 'border-l-transparent hover:bg-slate-100 dark:hover:bg-white/5'}`}
                                >
                                    <div className="flex justify-between items-start mb-1">
                                        <h3 className="text-slate-900 dark:text-white font-semibold text-sm">{edge.name}</h3>
                                        {selectedEdgeId === edge.id && <span className="text-[10px] uppercase tracking-wider text-blue-600 dark:text-[#193db3] font-bold bg-blue-100 dark:bg-[#193db3]/20 px-1.5 py-0.5 rounded">Active</span>}
                                    </div>
                                    <p className="text-slate-500 dark:text-[#95a0c6] text-xs mb-3 line-clamp-2">{edge.description || 'No description provided.'}</p>
                                    <div className="flex items-center gap-4 text-xs text-slate-500 dark:text-[#95a0c6]">
                                        <div className="flex items-center gap-1">
                                            <Code className="w-3.5 h-3.5" />
                                            <span>{Object.keys(edge.schema || {}).length} Attributes</span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                            {edges.length === 0 && (
                                <div className="p-6 text-center text-slate-500 dark:text-[#95a0c6] text-sm">
                                    No edge types found.
                                </div>
                            )}
                        </div>

                        {/* Detail Pane (View/Edit) */}
                        <div className="flex-1 overflow-y-auto bg-white dark:bg-[#1e2128] p-8">
                            {selectedEdge ? (
                                <>
                                    {/* Detail Header */}
                                    <div className="flex justify-between items-start mb-8 pb-6 border-b border-slate-200 dark:border-[#2d3748]">
                                        <div>
                                            <div className="flex items-center gap-3 mb-2">
                                                <h2 className="text-2xl font-bold text-slate-900 dark:text-white">{selectedEdge.name}</h2>
                                                <div title={`ID: ${selectedEdge.id}`}>
                                                    <Info className="text-slate-400 dark:text-[#95a0c6] cursor-help w-5 h-5" />
                                                </div>
                                            </div>
                                            <p className="text-slate-500 dark:text-[#95a0c6] text-sm max-w-xl">{selectedEdge.description || 'No description provided.'}</p>
                                        </div>
                                        <div className="flex gap-2">
                                            <button
                                                onClick={() => handleDelete(selectedEdge.id)}
                                                className="px-3 py-1.5 text-sm font-medium text-slate-500 dark:text-[#95a0c6] hover:text-red-600 dark:hover:text-red-400 border border-slate-200 dark:border-[#2d3748] rounded bg-white dark:bg-[#151820] hover:bg-slate-50 dark:hover:bg-[#252d46] transition-colors flex items-center gap-2"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                                Delete
                                            </button>
                                            <button
                                                onClick={() => handleOpenModal(selectedEdge)}
                                                className="px-3 py-1.5 text-sm font-medium text-white bg-blue-600 dark:bg-[#193db3] hover:bg-blue-700 rounded transition-colors flex items-center gap-2"
                                            >
                                                <Pencil className="w-4 h-4" />
                                                Edit Schema
                                            </button>
                                        </div>
                                    </div>

                                    {/* Attributes Section */}
                                    <div className="mb-8">
                                        <div className="flex items-center justify-between mb-4">
                                            <h3 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                                                <Code className="text-blue-600 dark:text-[#193db3] w-5 h-5" />
                                                Schema Attributes
                                            </h3>
                                            <span className="text-xs text-slate-500 dark:text-[#95a0c6] font-mono bg-slate-100 dark:bg-[#121521] px-2 py-1 rounded border border-slate-200 dark:border-[#2d3748]">class {selectedEdge.name}(Edge)</span>
                                        </div>
                                        <div className="border border-slate-200 dark:border-[#2d3748] rounded-lg overflow-hidden">
                                            <table className="w-full text-left text-sm">
                                                <thead className="bg-slate-50 dark:bg-[#151820] text-slate-500 dark:text-[#95a0c6] border-b border-slate-200 dark:border-[#2d3748]">
                                                    <tr>
                                                        <th className="px-4 py-3 font-medium">Attribute Name</th>
                                                        <th className="px-4 py-3 font-medium">Type</th>
                                                        <th className="px-4 py-3 font-medium">Description</th>
                                                    </tr>
                                                </thead>
                                                <tbody className="divide-y divide-slate-200 dark:divide-[#2d3748] bg-white dark:bg-[#121521]/50">
                                                    {Object.entries(selectedEdge.schema || {}).map(([key, val]: [string, any]) => (
                                                        <tr key={key} className="group hover:bg-slate-50 dark:hover:bg-white/5 transition-colors">
                                                            <td className="px-4 py-3 text-slate-900 dark:text-white font-mono text-xs">{key}</td>
                                                            <td className="px-4 py-3 text-purple-600 dark:text-purple-400 font-mono text-xs">{typeof val === 'string' ? val : val.type}</td>
                                                            <td className="px-4 py-3 text-slate-500 dark:text-[#95a0c6] text-xs">{typeof val === 'string' ? '' : val.description}</td>
                                                        </tr>
                                                    ))}
                                                    {Object.keys(selectedEdge.schema || {}).length === 0 && (
                                                        <tr>
                                                            <td colSpan={3} className="px-4 py-8 text-center text-slate-500 dark:text-[#95a0c6]">No attributes defined</td>
                                                        </tr>
                                                    )}
                                                </tbody>
                                            </table>
                                            <div className="bg-slate-50 dark:bg-[#151820] px-4 py-2 border-t border-slate-200 dark:border-[#2d3748]">
                                                <button
                                                    onClick={() => handleOpenModal(selectedEdge)}
                                                    className="text-xs text-blue-600 dark:text-[#193db3] font-bold flex items-center gap-1 hover:text-blue-800 dark:hover:text-white transition-colors"
                                                >
                                                    <Plus className="w-4 h-4" />
                                                    Add Attribute
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <div className="flex flex-col items-center justify-center h-full text-slate-400 dark:text-[#95a0c6]">
                                    <Share2 className="w-12 h-12 mb-4 opacity-50" />
                                    <p>Select an edge type to view details</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Modal */}
            {isModalOpen && (
                <div aria-modal="true" className="fixed inset-0 z-50 flex justify-end" role="dialog">
                    <div className="absolute inset-0 bg-black/60 backdrop-blur-[2px] transition-opacity" onClick={() => setIsModalOpen(false)}></div>
                    <div className="relative w-full max-w-3xl bg-white dark:bg-[#111521] shadow-2xl flex flex-col h-full border-l border-slate-200 dark:border-[#2a324a] animate-in slide-in-from-right duration-300">
                        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-[#2a324a] bg-slate-50 dark:bg-[#1e2433]">
                            <div className="flex items-center gap-4">
                                <div className="flex items-center justify-center h-10 w-10 rounded-lg bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-500/20">
                                    <Share2 className="w-6 h-6" />
                                </div>
                                <div>
                                    <h3 className="text-lg font-bold text-slate-900 dark:text-white leading-none">
                                        {editingEdge ? `Edit Edge Type: ${editingEdge.name}` : 'New Edge Type'}
                                    </h3>
                                    <p className="text-xs text-slate-500 dark:text-[#95a0c6] mt-1 font-mono">{editingEdge?.id || 'New ID'}</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-3">
                                <button
                                    onClick={() => setIsModalOpen(false)}
                                    className="flex items-center justify-center w-8 h-8 rounded-lg text-slate-400 dark:text-[#95a0c6] hover:bg-slate-200 dark:hover:bg-[#2a324a] hover:text-slate-900 dark:hover:text-white transition-colors"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>
                        </div>
                        <div className="flex-1 overflow-y-auto">
                            <div className="flex border-b border-slate-200 dark:border-[#2a324a] sticky top-0 bg-white dark:bg-[#111521] z-10 px-6 pt-2">
                                <button className="px-4 py-3 text-sm font-bold text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400 transition-colors bg-blue-50 dark:bg-blue-500/5">Attributes & Schema</button>
                            </div>
                            <div className="p-6 flex flex-col gap-8">
                                {/* Basic Info */}
                                <div className="flex flex-col gap-4">
                                    <h4 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">Basic Information</h4>
                                    <div className="grid grid-cols-1 gap-4">
                                        <div>
                                            <label className="text-[10px] uppercase text-slate-500 dark:text-[#95a0c6] font-bold mb-1.5 block">Edge Type Name</label>
                                            <input
                                                className="w-full bg-slate-50 dark:bg-[#121521] border border-slate-200 dark:border-[#2a324a] rounded-lg text-sm text-slate-900 dark:text-white px-3 py-2 font-mono focus:border-blue-600 dark:focus:border-[#193db3] focus:ring-1 focus:ring-blue-600 dark:focus:ring-[#193db3] outline-none transition-colors"
                                                type="text"
                                                value={formData.name}
                                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                                placeholder="e.g. Employment"
                                                disabled={!!editingEdge}
                                            />
                                        </div>
                                        <div>
                                            <label className="text-[10px] uppercase text-slate-500 dark:text-[#95a0c6] font-bold mb-1.5 block">Description</label>
                                            <input
                                                className="w-full bg-slate-50 dark:bg-[#121521] border border-slate-200 dark:border-[#2a324a] rounded-lg text-sm text-slate-900 dark:text-white px-3 py-2 focus:border-blue-600 dark:focus:border-[#193db3] focus:ring-1 focus:ring-blue-600 dark:focus:ring-[#193db3] outline-none transition-colors"
                                                type="text"
                                                value={formData.description}
                                                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                                placeholder="Brief description of this edge type"
                                            />
                                        </div>
                                    </div>
                                </div>

                                <div className="flex flex-col gap-4">
                                    <div className="flex items-center justify-between">
                                        <h4 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">Defined Attributes</h4>
                                        <button
                                            onClick={addAttribute}
                                            className="text-blue-600 dark:text-[#193db3] text-xs font-bold flex items-center gap-1 hover:text-blue-700 dark:hover:text-[#254bcc] px-3 py-1.5 bg-blue-50 dark:bg-[#193db3]/10 rounded-lg border border-blue-200 dark:border-[#193db3]/20 transition-colors"
                                        >
                                            <Plus className="w-4 h-4" /> Add Attribute
                                        </button>
                                    </div>
                                    <div className="flex flex-col gap-4">
                                        {attributes.map((attr, idx) => (
                                            <div key={idx} className="border border-blue-200 dark:border-[#193db3]/50 bg-white dark:bg-[#1e2433] rounded-xl overflow-hidden shadow-xl shadow-black/5 dark:shadow-black/20 ring-1 ring-blue-100 dark:ring-[#193db3]/30">
                                                <div className="bg-slate-50 dark:bg-[#252d46] px-4 py-2 flex items-center justify-between border-b border-slate-200 dark:border-[#2a324a]">
                                                    <div className="flex items-center gap-2">
                                                        <FileEdit className="w-4 h-4 text-blue-600 dark:text-[#193db3]" />
                                                        <span className="text-xs font-bold text-slate-700 dark:text-white uppercase tracking-wide">Attribute #{idx + 1}</span>
                                                    </div>
                                                    <button
                                                        onClick={() => removeAttribute(idx)}
                                                        className="text-xs text-red-600 dark:text-red-400 hover:text-red-500 dark:hover:text-red-300 font-medium flex items-center gap-1"
                                                    >
                                                        Delete Field
                                                    </button>
                                                </div>
                                                <div className="p-5 flex flex-col gap-6">
                                                    <div className="grid grid-cols-12 gap-4">
                                                        <div className="col-span-5">
                                                            <label className="text-[10px] uppercase text-slate-500 dark:text-[#95a0c6] font-bold mb-1.5 block">Attribute Name (snake_case)</label>
                                                            <input
                                                                className="w-full bg-slate-50 dark:bg-[#121521] border border-slate-200 dark:border-[#2a324a] rounded-lg text-sm text-slate-900 dark:text-white px-3 py-2 font-mono focus:border-blue-600 dark:focus:border-[#193db3] focus:ring-1 focus:ring-blue-600 dark:focus:ring-[#193db3] outline-none transition-colors"
                                                                type="text"
                                                                value={attr.name}
                                                                onChange={(e) => updateAttribute(idx, 'name', e.target.value)}
                                                                placeholder="attribute_name"
                                                            />
                                                        </div>
                                                        <div className="col-span-4">
                                                            <label className="text-[10px] uppercase text-slate-500 dark:text-[#95a0c6] font-bold mb-1.5 block">Data Type</label>
                                                            <div className="relative">
                                                                <select
                                                                    className="w-full bg-slate-50 dark:bg-[#121521] border border-slate-200 dark:border-[#2a324a] rounded-lg text-sm text-slate-900 dark:text-white px-3 py-2 outline-none appearance-none focus:border-blue-600 dark:focus:border-[#193db3]"
                                                                    value={attr.type}
                                                                    onChange={(e) => updateAttribute(idx, 'type', e.target.value)}
                                                                >
                                                                    <option value="String">String</option>
                                                                    <option value="Integer">Integer</option>
                                                                    <option value="Float">Float</option>
                                                                    <option value="Boolean">Boolean</option>
                                                                    <option value="DateTime">DateTime</option>
                                                                    <option value="List">List</option>
                                                                    <option value="Dict">Dict</option>
                                                                </select>
                                                                <ChevronDown className="absolute right-2 top-2.5 w-4 h-4 text-slate-400 dark:text-[#95a0c6] pointer-events-none" />
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div>
                                                        <label className="text-[10px] uppercase text-slate-500 dark:text-[#95a0c6] font-bold mb-1.5 block">Description (Docstring)</label>
                                                        <input
                                                            className="w-full bg-slate-50 dark:bg-[#121521] border border-slate-200 dark:border-[#2a324a] rounded-lg text-sm text-slate-500 dark:text-[#95a0c6] px-3 py-2 focus:text-slate-900 dark:focus:text-white focus:border-blue-600 dark:focus:border-[#193db3] focus:ring-1 focus:ring-blue-600 dark:focus:ring-[#193db3] outline-none transition-colors"
                                                            type="text"
                                                            value={attr.description}
                                                            onChange={(e) => updateAttribute(idx, 'description', e.target.value)}
                                                            placeholder="Describe the attribute..."
                                                        />
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="border-t border-slate-200 dark:border-[#2a324a] p-4 bg-slate-50 dark:bg-[#1e2433] flex justify-between items-center gap-3">
                            <div className="text-xs text-slate-500 dark:text-[#95a0c6] flex items-center gap-1">
                                <History className="w-4 h-4" />
                                <span>Last saved: {editingEdge?.updated_at ? new Date(editingEdge.updated_at).toLocaleString() : 'Never'}</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <button
                                    onClick={() => setIsModalOpen(false)}
                                    className="px-4 py-2 text-sm font-medium text-slate-500 dark:text-[#95a0c6] hover:text-slate-900 dark:hover:text-white border border-slate-200 dark:border-[#2a324a] rounded-lg hover:bg-slate-100 dark:hover:bg-[#2a324a] transition-colors"
                                >
                                    Discard Changes
                                </button>
                                <button
                                    onClick={handleSave}
                                    className="px-5 py-2 text-sm font-bold text-white bg-blue-600 dark:bg-[#193db3] rounded-lg hover:bg-blue-700 dark:hover:bg-[#254bcc] shadow-lg shadow-blue-900/20 transition-all active:scale-95"
                                >
                                    Save Edge Type
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
