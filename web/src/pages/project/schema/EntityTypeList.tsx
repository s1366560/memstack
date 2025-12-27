import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { schemaAPI } from '../../../services/api';
import {
    Plus,
    Search,
    ChevronDown,
    List,
    Grid,
    User,
    FileEdit,
    X,
    Info,
    History,
    Trash2,
} from 'lucide-react';

export default function EntityTypeList() {
    const { projectId } = useParams<{ projectId: string }>();
    const [entities, setEntities] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingEntity, setEditingEntity] = useState<any>(null);
    const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');

    // Form state
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        schema: {} as Record<string, any> // { fieldName: { type: "String", description: "" } }
    });

    // Attribute builder state
    const [attributes, setAttributes] = useState<{ name: string, type: string, description: string, required: boolean }[]>([]);

    const loadData = useCallback(async () => {
        if (!projectId) return;
        try {
            const data = await schemaAPI.listEntityTypes(projectId);
            setEntities(data);
        } catch (error) {
            console.error('Failed to load entity types:', error);
        } finally {
            setLoading(false);
        }
    }, [projectId]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const handleOpenModal = (entity: any = null) => {
        if (entity) {
            setEditingEntity(entity);
            // Parse schema back to attributes list
            const attrs = Object.entries(entity.schema || {}).map(([key, val]: [string, any]) => ({
                name: key,
                type: typeof val === 'string' ? val : val.type || 'String',
                description: typeof val === 'string' ? '' : val.description || '',
                required: typeof val === 'string' ? false : !!val.required
            }));
            setFormData({
                name: entity.name,
                description: entity.description || '',
                schema: entity.schema
            });
            setAttributes(attrs);
        } else {
            setEditingEntity(null);
            setFormData({ name: '', description: '', schema: {} });
            setAttributes([]);
        }
        setIsModalOpen(true);
    };

    const handleSave = async () => {
        if (!projectId) return;

        // Convert attributes to schema dict
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
            if (editingEntity) {
                await schemaAPI.updateEntityType(projectId, editingEntity.id, payload);
            } else {
                await schemaAPI.createEntityType(projectId, payload);
            }
            setIsModalOpen(false);
            loadData();
        } catch (error) {
            console.error('Failed to save entity type:', error);
            alert('Failed to save. Check if name is unique.');
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Are you sure? This will delete the entity type definition.')) return;
        if (!projectId) return;
        try {
            await schemaAPI.deleteEntityType(projectId, id);
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

    if (loading) return <div className="p-8 text-center text-slate-500 dark:text-gray-500">Loading...</div>;

    return (
        <div className="flex flex-col h-full bg-slate-50 dark:bg-[#111521] text-slate-900 dark:text-white overflow-hidden">
            {/* Header Section */}
            <div className="w-full flex-none pt-8 pb-4 px-8 border-b border-slate-200 dark:border-[#2a324a]/50 bg-white dark:bg-[#121521]">
                <div className="max-w-7xl mx-auto flex flex-col gap-4">
                    <div className="flex flex-wrap justify-between items-center gap-4">
                        <div>
                            <h2 className="text-slate-900 dark:text-white text-3xl font-bold tracking-tight">Entity Type Management</h2>
                            <p className="text-slate-500 dark:text-[#95a0c6] text-sm mt-1">Define data models, attributes, and validation rules for the knowledge graph.</p>
                        </div>
                        <button
                            onClick={() => handleOpenModal()}
                            className="flex items-center gap-2 cursor-pointer rounded-lg h-10 px-5 bg-blue-600 dark:bg-[#193db3] hover:bg-blue-700 dark:hover:bg-[#254bcc] text-white text-sm font-bold shadow-lg shadow-blue-900/20 transition-all active:scale-95"
                        >
                            <Plus className="w-5 h-5" />
                            <span>Create Entity Type</span>
                        </button>
                    </div>
                </div>
            </div>

            {/* Content Section */}
            <div className="flex-1 overflow-y-auto bg-slate-50 dark:bg-[#111521] p-8">
                <div className="max-w-7xl mx-auto flex flex-col gap-6">
                    {/* Toolbar */}
                    <div className="flex flex-wrap items-center justify-between gap-4 bg-white dark:bg-[#1e2433] p-4 rounded-xl border border-slate-200 dark:border-[#2a324a]">
                        <div className="flex flex-1 max-w-md">
                            <label className="flex w-full items-center h-10 rounded-lg bg-slate-100 dark:bg-[#252d46] border border-transparent focus-within:border-blue-500 dark:focus-within:border-[#193db3]/50 transition-colors">
                                <div className="text-slate-400 dark:text-[#95a0c6] flex items-center justify-center pl-3">
                                    <Search className="w-5 h-5" />
                                </div>
                                <input className="w-full bg-transparent border-none text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-[#95a0c6] focus:ring-0 text-sm px-3 outline-none" placeholder="Search entity types..." />
                            </label>
                        </div>
                        <div className="flex items-center gap-3">
                            <button className="flex h-9 items-center gap-2 rounded-lg bg-slate-100 dark:bg-[#252d46] hover:bg-slate-200 dark:hover:bg-[#2f3956] border border-slate-200 dark:border-[#2a324a] px-3 transition-colors">
                                <span className="text-slate-700 dark:text-white text-sm font-medium">Project: All</span>
                                <ChevronDown className="w-4 h-4 text-slate-400 dark:text-[#95a0c6]" />
                            </button>
                            <div className="h-6 w-px bg-slate-200 dark:bg-[#2a324a] mx-1"></div>
                            <button
                                onClick={() => setViewMode('list')}
                                className={`flex items-center justify-center h-9 w-9 rounded-lg transition-colors ${viewMode === 'list' ? 'bg-slate-200 dark:bg-[#252d46] text-slate-900 dark:text-white' : 'bg-transparent text-slate-400 dark:text-[#95a0c6] hover:text-slate-900 dark:hover:text-white'}`}
                                title="List View"
                            >
                                <List className="w-5 h-5" />
                            </button>
                            <button
                                onClick={() => setViewMode('grid')}
                                className={`flex items-center justify-center h-9 w-9 rounded-lg transition-colors ${viewMode === 'grid' ? 'bg-slate-200 dark:bg-[#252d46] text-slate-900 dark:text-white' : 'bg-transparent text-slate-400 dark:text-[#95a0c6] hover:text-slate-900 dark:hover:text-white'}`}
                                title="Grid View"
                            >
                                <Grid className="w-5 h-5" />
                            </button>
                        </div>
                    </div>

                    {/* List View */}
                    <div className="flex flex-col rounded-xl border border-slate-200 dark:border-[#2a324a] bg-white dark:bg-[#1e2433] overflow-hidden shadow-xl">
                        <div className="grid grid-cols-12 gap-4 border-b border-slate-200 dark:border-[#2a324a] bg-slate-50 dark:bg-[#252d46]/50 px-6 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-[#95a0c6]">
                            <div className="col-span-2 flex items-center">Entity Type</div>
                            <div className="col-span-2 flex items-center">Internal ID</div>
                            <div className="col-span-3 flex items-center">Schema Definition</div>
                            <div className="col-span-1 flex items-center">Status</div>
                            <div className="col-span-1 flex items-center">Source</div>
                            <div className="col-span-2 flex items-center">Last Modified</div>
                            <div className="col-span-1 flex items-center justify-end">Actions</div>
                        </div>
                        <div className="divide-y divide-slate-200 dark:divide-[#2a324a]">
                            {entities.map((entity) => (
                                <div key={entity.id} className="grid grid-cols-12 gap-4 px-6 py-4 hover:bg-slate-50 dark:hover:bg-[#252d46] transition-colors group items-start">
                                    <div className="col-span-2 flex items-center gap-4">
                                        <div className="flex items-center justify-center h-10 w-10 rounded-lg bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-500/20">
                                            <User className="w-6 h-6" />
                                        </div>
                                        <div className="flex flex-col">
                                            <span className="text-slate-900 dark:text-white font-medium text-sm">{entity.name}</span>
                                            <div className="flex items-center gap-2 mt-0.5">
                                                <span className="h-1.5 w-1.5 rounded-full bg-blue-500"></span>
                                                <span className="text-xs text-slate-500 dark:text-[#95a0c6]">{entity.description || 'Core Model'}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="col-span-2 flex items-center">
                                        <code className="text-xs font-mono bg-slate-100 dark:bg-[#121521] px-2 py-1 rounded text-slate-500 dark:text-[#95a0c6] border border-slate-200 dark:border-[#2a324a]">
                                            {entity.id.slice(0, 8)}...
                                        </code>
                                    </div>
                                    <div className="col-span-3 flex flex-col gap-1.5">
                                        {Object.entries(entity.schema || {}).slice(0, 3).map(([key, val]: [string, any]) => (
                                            <div key={key} className="flex items-center gap-2 text-xs">
                                                <span className="text-emerald-600 dark:text-emerald-300 font-mono">{key}</span>
                                                <span className="text-slate-500 dark:text-[#95a0c6] text-[10px]">: {typeof val === 'string' ? val : val.type}</span>
                                            </div>
                                        ))}
                                        {Object.keys(entity.schema || {}).length > 3 && (
                                            <div className="text-[10px] text-slate-500 dark:text-[#95a0c6] mt-1 font-medium">+ {Object.keys(entity.schema || {}).length - 3} more attributes</div>
                                        )}
                                        {Object.keys(entity.schema || {}).length === 0 && (
                                            <div className="text-[10px] text-slate-400 dark:text-[#95a0c6] italic">No attributes defined</div>
                                        )}
                                    </div>
                                    <div className="col-span-1 flex items-center">
                                        <span className={`px-2 py-1 rounded-full text-[10px] font-bold uppercase tracking-wide border ${
                                            entity.status === 'ENABLED' 
                                                ? 'bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-200 dark:border-emerald-500/20' 
                                                : 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 border-slate-200 dark:border-slate-700'
                                        }`}>
                                            {entity.status || 'ENABLED'}
                                        </span>
                                    </div>
                                    <div className="col-span-1 flex items-center">
                                        <span className={`px-2 py-1 rounded-full text-[10px] font-bold uppercase tracking-wide border ${
                                            entity.source === 'generated'
                                                ? 'bg-purple-50 dark:bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-200 dark:border-purple-500/20'
                                                : 'bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-200 dark:border-blue-500/20'
                                        }`}>
                                            {entity.source || 'user'}
                                        </span>
                                    </div>
                                    <div className="col-span-2 flex flex-col justify-start pt-1">
                                        <span className="text-sm text-slate-700 dark:text-white">{new Date(entity.created_at || Date.now()).toLocaleDateString()}</span>
                                        <span className="text-xs text-slate-400 dark:text-[#95a0c6]">by Admin</span>
                                    </div>
                                    <div className="col-span-1 flex items-center justify-end gap-2 opacity-80 group-hover:opacity-100 transition-opacity">
                                        <button
                                            onClick={() => handleOpenModal(entity)}
                                            className="p-2 rounded-lg hover:bg-blue-50 dark:hover:bg-[#193db3]/20 text-slate-400 dark:text-[#95a0c6] hover:text-blue-600 dark:hover:text-[#193db3] transition-colors"
                                            title="Edit Schema"
                                        >
                                            <FileEdit className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => handleDelete(entity.id)}
                                            className="p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-500/20 text-slate-400 dark:text-[#95a0c6] hover:text-red-600 dark:hover:text-red-400 transition-colors"
                                            title="Delete"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            ))}
                            {entities.length === 0 && (
                                <div className="px-6 py-8 text-center text-slate-500 dark:text-[#95a0c6]">
                                    No entity types defined yet. Click "Create Entity Type" to add one.
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
                                    <User className="w-6 h-6" />
                                </div>
                                <div>
                                    <h3 className="text-lg font-bold text-slate-900 dark:text-white leading-none">
                                        {editingEntity ? `Edit Entity Type: ${editingEntity.name}` : 'New Entity Type'}
                                    </h3>
                                    <p className="text-xs text-slate-500 dark:text-[#95a0c6] mt-1 font-mono">{editingEntity?.id || 'New ID'}</p>
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
                                <div className="bg-blue-50 dark:bg-blue-500/5 border border-blue-200 dark:border-blue-500/20 rounded-lg p-4 flex gap-3">
                                    <Info className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" />
                                    <div className="flex flex-col gap-1">
                                        <h4 className="text-sm font-bold text-blue-900 dark:text-blue-100">Schema Configuration</h4>
                                        <p className="text-xs text-blue-700 dark:text-blue-200/70">Define the attributes for this entity type. These definitions map directly to Pydantic models for data validation.</p>
                                    </div>
                                </div>

                                {/* Basic Info */}
                                <div className="flex flex-col gap-4">
                                    <h4 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">Basic Information</h4>
                                    <div className="grid grid-cols-1 gap-4">
                                        <div>
                                            <label className="text-[10px] uppercase text-slate-500 dark:text-[#95a0c6] font-bold mb-1.5 block">Entity Type Name</label>
                                            <input
                                                className="w-full bg-slate-50 dark:bg-[#121521] border border-slate-200 dark:border-[#2a324a] rounded-lg text-sm text-slate-900 dark:text-white px-3 py-2 font-mono focus:border-blue-600 dark:focus:border-[#193db3] focus:ring-1 focus:ring-blue-600 dark:focus:ring-[#193db3] outline-none transition-colors"
                                                type="text"
                                                value={formData.name}
                                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                                placeholder="e.g. Person"
                                                disabled={!!editingEntity}
                                            />
                                        </div>
                                        <div>
                                            <label className="text-[10px] uppercase text-slate-500 dark:text-[#95a0c6] font-bold mb-1.5 block">Description</label>
                                            <input
                                                className="w-full bg-slate-50 dark:bg-[#121521] border border-slate-200 dark:border-[#2a324a] rounded-lg text-sm text-slate-900 dark:text-white px-3 py-2 focus:border-blue-600 dark:focus:border-[#193db3] focus:ring-1 focus:ring-blue-600 dark:focus:ring-[#193db3] outline-none transition-colors"
                                                type="text"
                                                value={formData.description}
                                                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                                placeholder="Brief description of this entity type"
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
                                                        <div className="col-span-3 flex items-end pb-2">
                                                            <label className="flex items-center gap-2 cursor-pointer select-none">
                                                                <div className="relative">
                                                                    <input
                                                                        type="checkbox"
                                                                        className="peer sr-only"
                                                                        checked={attr.required}
                                                                        onChange={(e) => updateAttribute(idx, 'required', e.target.checked)}
                                                                    />
                                                                    <div className="w-9 h-5 bg-slate-200 dark:bg-[#2a324a] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600 dark:peer-checked:bg-[#193db3]"></div>
                                                                </div>
                                                                <span className="text-xs font-medium text-slate-500 dark:text-[#95a0c6] peer-checked:text-slate-900 dark:peer-checked:text-white">Required</span>
                                                            </label>
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
                                <span>Last saved: {editingEntity?.updated_at ? new Date(editingEntity.updated_at).toLocaleString() : 'Never'}</span>
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
                                    Save Entity Type
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
