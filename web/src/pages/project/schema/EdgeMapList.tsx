import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { schemaAPI } from '../../../services/api';
import { Plus, Trash2 } from 'lucide-react';

export default function EdgeMapList() {
    const { projectId } = useParams<{ projectId: string }>();
    const [mappings, setMappings] = useState<any[]>([]);
    const [entityTypes, setEntityTypes] = useState<any[]>([]);
    const [edgeTypes, setEdgeTypes] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    // New mapping form
    const [newMap, setNewMap] = useState({
        source_type: '',
        target_type: '',
        edge_type: ''
    });

    const loadData = useCallback(async () => {
        if (!projectId) return;
        try {
            const [maps, entities, edges] = await Promise.all([
                schemaAPI.listEdgeMaps(projectId),
                schemaAPI.listEntityTypes(projectId),
                schemaAPI.listEdgeTypes(projectId)
            ]);
            setMappings(maps);
            setEntityTypes(entities);
            setEdgeTypes(edges);

            // Default to first option if available
            const systemTypes = ["Entity", "Person", "Organization", "Location", "Concept", "Event", "Artifact"];
            const allEntityNames = [...systemTypes, ...entities.map((e: any) => e.name)];

            if (allEntityNames.length > 0 && edges.length > 0) {
                setNewMap(prev => ({
                    ...prev,
                    source_type: prev.source_type || allEntityNames[0],
                    target_type: prev.target_type || allEntityNames[0],
                    edge_type: prev.edge_type || edges[0].name
                }));
            }
        } catch (error) {
            console.error('Failed to load data:', error);
        } finally {
            setLoading(false);
        }
    }, [projectId]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const handleCreate = async () => {
        if (!projectId) return;
        try {
            await schemaAPI.createEdgeMap(projectId, newMap);
            loadData();
        } catch (error) {
            console.error('Failed to create mapping:', error);
            alert('Failed to create mapping. It might already exist.');
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Are you sure?')) return;
        if (!projectId) return;
        try {
            await schemaAPI.deleteEdgeMap(projectId, id);
            loadData();
        } catch (error) {
            console.error('Failed to delete:', error);
        }
    };

    if (loading) return <div className="p-4">Loading...</div>;

    const systemTypes = ["Entity", "Person", "Organization", "Location", "Concept", "Event", "Artifact"];
    const allEntityNames = [...systemTypes, ...entityTypes.map(e => e.name)];

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-semibold text-gray-900">Edge Mappings</h1>
            </div>

            {/* Create Form */}
            <div className="bg-white shadow sm:rounded-lg p-4">
                <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">Add New Mapping</h3>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-4 items-end">
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Source Entity</label>
                        <select
                            value={newMap.source_type}
                            onChange={(e) => setNewMap({ ...newMap, source_type: e.target.value })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                        >
                            <option value="">Select Entity</option>
                            {allEntityNames.map(name => (
                                <option key={name} value={name}>{name}</option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Edge Type</label>
                        <select
                            value={newMap.edge_type}
                            onChange={(e) => setNewMap({ ...newMap, edge_type: e.target.value })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                        >
                            <option value="">Select Edge</option>
                            {edgeTypes.map(edge => (
                                <option key={edge.id} value={edge.name}>{edge.name}</option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Target Entity</label>
                        <select
                            value={newMap.target_type}
                            onChange={(e) => setNewMap({ ...newMap, target_type: e.target.value })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                        >
                            <option value="">Select Entity</option>
                            {allEntityNames.map(name => (
                                <option key={name} value={name}>{name}</option>
                            ))}
                        </select>
                    </div>
                    <button
                        onClick={handleCreate}
                        disabled={!newMap.source_type || !newMap.target_type || !newMap.edge_type}
                        className="inline-flex items-center justify-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:bg-gray-300"
                    >
                        <Plus className="-ml-0.5 mr-1.5 h-5 w-5" />
                        Add Mapping
                    </button>
                </div>
            </div>

            <div className="overflow-hidden bg-white shadow sm:rounded-md">
                <ul role="list" className="divide-y divide-gray-200">
                    {mappings.map((map) => (
                        <li key={map.id} className="px-4 py-4 sm:px-6 hover:bg-gray-50">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-4 text-sm">
                                    <span className="font-medium text-gray-900">{map.source_type}</span>
                                    <span className="text-gray-400">→</span>
                                    <span className="font-medium text-indigo-600">{map.edge_type}</span>
                                    <span className="text-gray-400">→</span>
                                    <span className="font-medium text-gray-900">{map.target_type}</span>
                                </div>
                                <div className="ml-2 flex flex-shrink-0">
                                    <button
                                        onClick={() => handleDelete(map.id)}
                                        className="text-red-400 hover:text-red-500"
                                    >
                                        <Trash2 className="h-5 w-5" />
                                    </button>
                                </div>
                            </div>
                        </li>
                    ))}
                    {mappings.length === 0 && (
                        <li className="px-4 py-8 text-center text-gray-500">No mappings defined yet.</li>
                    )}
                </ul>
            </div>
        </div>
    );
}
