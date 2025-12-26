import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { schemaAPI } from '../../../services/api';
import { Plus, Pencil, Trash2 } from 'lucide-react';

export default function EdgeTypeList() {
    const { projectId } = useParams<{ projectId: string }>();
    const [edges, setEdges] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingEdge, setEditingEdge] = useState<any>(null);

    // Form state
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        schema: {} as Record<string, any>
    });

    // Attribute builder state
    const [attributes, setAttributes] = useState<{ name: string, type: string, description: string }[]>([]);

    const loadData = useCallback(async () => {
        if (!projectId) return;
        try {
            const data = await schemaAPI.listEdgeTypes(projectId);
            setEdges(data);
        } catch (error) {
            console.error('Failed to load edge types:', error);
        } finally {
            setLoading(false);
        }
    }, [projectId]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const handleOpenModal = (edge: any = null) => {
        if (edge) {
            setEditingEdge(edge);
            const attrs = Object.entries(edge.schema || {}).map(([key, val]: [string, any]) => ({
                name: key,
                type: typeof val === 'string' ? val : val.type || 'String',
                description: typeof val === 'string' ? '' : val.description || ''
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
                    description: attr.description
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
            loadData();
        } catch (error) {
            console.error('Failed to delete:', error);
        }
    };

    const addAttribute = () => {
        setAttributes([...attributes, { name: '', type: 'String', description: '' }]);
    };

    const updateAttribute = (index: number, field: string, value: string) => {
        const newAttrs = [...attributes];
        newAttrs[index] = { ...newAttrs[index], [field]: value };
        setAttributes(newAttrs);
    };

    const removeAttribute = (index: number) => {
        setAttributes(attributes.filter((_, i) => i !== index));
    };

    if (loading) return <div className="p-4">Loading...</div>;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-semibold text-gray-900">Edge Types</h1>
                <button
                    onClick={() => handleOpenModal()}
                    className="inline-flex items-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
                >
                    <Plus className="-ml-0.5 mr-1.5 h-5 w-5" />
                    Create Type
                </button>
            </div>

            <div className="overflow-hidden bg-white shadow sm:rounded-md">
                <ul role="list" className="divide-y divide-gray-200">
                    {edges.map((edge) => (
                        <li key={edge.id} className="px-4 py-4 sm:px-6 hover:bg-gray-50">
                            <div className="flex items-center justify-between">
                                <div className="truncate">
                                    <div className="flex text-sm">
                                        <p className="truncate font-medium text-indigo-600">{edge.name}</p>
                                    </div>
                                    <div className="mt-2 flex">
                                        <p className="text-sm text-gray-500 truncate">{edge.description || 'No description'}</p>
                                    </div>
                                    <div className="mt-1 text-xs text-gray-400">
                                        Attributes: {Object.keys(edge.schema || {}).join(', ') || 'None'}
                                    </div>
                                </div>
                                <div className="ml-2 flex flex-shrink-0">
                                    <button
                                        onClick={() => handleOpenModal(edge)}
                                        className="mr-2 text-gray-400 hover:text-gray-500"
                                    >
                                        <Pencil className="h-5 w-5" />
                                    </button>
                                    <button
                                        onClick={() => handleDelete(edge.id)}
                                        className="text-red-400 hover:text-red-500"
                                    >
                                        <Trash2 className="h-5 w-5" />
                                    </button>
                                </div>
                            </div>
                        </li>
                    ))}
                    {edges.length === 0 && (
                        <li className="px-4 py-8 text-center text-gray-500">No edge types defined yet.</li>
                    )}
                </ul>
            </div>

            {/* Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
                    <div className="flex min-h-screen items-end justify-center px-4 pb-20 pt-4 text-center sm:block sm:p-0">
                        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setIsModalOpen(false)}></div>

                        <div className="inline-block transform overflow-hidden rounded-lg bg-white text-left align-bottom shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-2xl sm:align-middle">
                            <div className="bg-white px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                                <div className="sm:flex sm:items-start">
                                    <div className="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left w-full">
                                        <h3 className="text-base font-semibold leading-6 text-gray-900" id="modal-title">
                                            {editingEdge ? 'Edit Edge Type' : 'New Edge Type'}
                                        </h3>
                                        <div className="mt-4 space-y-4">
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700">Name</label>
                                                <input
                                                    type="text"
                                                    value={formData.name}
                                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                                    disabled={!!editingEdge}
                                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700">Description</label>
                                                <textarea
                                                    value={formData.description}
                                                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                                                />
                                            </div>

                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-2">Attributes</label>
                                                {attributes.map((attr, idx) => (
                                                    <div key={idx} className="flex gap-2 mb-2 items-start">
                                                        <input
                                                            type="text"
                                                            placeholder="Name"
                                                            value={attr.name}
                                                            onChange={(e) => updateAttribute(idx, 'name', e.target.value)}
                                                            className="w-1/3 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                                                        />
                                                        <select
                                                            value={attr.type}
                                                            onChange={(e) => updateAttribute(idx, 'type', e.target.value)}
                                                            className="w-1/4 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                                                        >
                                                            <option value="String">String</option>
                                                            <option value="Integer">Integer</option>
                                                            <option value="Float">Float</option>
                                                            <option value="Boolean">Boolean</option>
                                                            <option value="DateTime">DateTime</option>
                                                            <option value="List">List</option>
                                                            <option value="Dict">Dict</option>
                                                        </select>
                                                        <input
                                                            type="text"
                                                            placeholder="Description"
                                                            value={attr.description}
                                                            onChange={(e) => updateAttribute(idx, 'description', e.target.value)}
                                                            className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                                                        />
                                                        <button onClick={() => removeAttribute(idx)} className="text-red-500 p-2">
                                                            <Trash2 className="h-4 w-4" />
                                                        </button>
                                                    </div>
                                                ))}
                                                <button
                                                    type="button"
                                                    onClick={addAttribute}
                                                    className="mt-2 inline-flex items-center text-sm text-indigo-600 hover:text-indigo-500"
                                                >
                                                    <Plus className="mr-1 h-4 w-4" /> Add Attribute
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div className="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                                <button
                                    type="button"
                                    onClick={handleSave}
                                    className="inline-flex w-full justify-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 sm:ml-3 sm:w-auto"
                                >
                                    Save
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setIsModalOpen(false)}
                                    className="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
