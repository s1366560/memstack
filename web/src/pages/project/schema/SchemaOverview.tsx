import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { schemaAPI } from '../../../services/api';
import {
    Database,
    BoxSelect,
    ArrowLeftRight,
    Plus
} from 'lucide-react';

export default function SchemaOverview() {
    const { projectId } = useParams<{ projectId: string }>();
    const [stats, setStats] = useState({
        entityTypes: 0,
        edgeTypes: 0,
        mappings: 0
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            if (!projectId) return;
            try {
                const [entities, edges, mappings] = await Promise.all([
                    schemaAPI.listEntityTypes(projectId),
                    schemaAPI.listEdgeTypes(projectId),
                    schemaAPI.listEdgeMaps(projectId)
                ]);
                setStats({
                    entityTypes: entities.length,
                    edgeTypes: edges.length,
                    mappings: mappings.length
                });
            } catch (error) {
                console.error('Failed to fetch schema stats:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [projectId]);

    if (loading) {
        return <div className="p-4">Loading schema overview...</div>;
    }

    const cards = [
        {
            name: 'Entity Types',
            count: stats.entityTypes,
            icon: Database,
            href: `/project/${projectId}/schema/entities`,
            description: 'Define custom entity types and their attributes.'
        },
        {
            name: 'Edge Types',
            count: stats.edgeTypes,
            icon: BoxSelect,
            href: `/project/${projectId}/schema/edges`,
            description: 'Define relationship types between entities.'
        },
        {
            name: 'Edge Mappings',
            count: stats.mappings,
            icon: ArrowLeftRight,
            href: `/project/${projectId}/schema/mapping`,
            description: 'Configure allowed relationships between entity types.'
        }
    ];

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-semibold text-gray-900">Schema Management</h1>
            </div>

            <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
                {cards.map((card) => (
                    <div key={card.name} className="overflow-hidden rounded-lg bg-white shadow">
                        <div className="p-5">
                            <div className="flex items-center">
                                <div className="flex-shrink-0">
                                    <card.icon className="h-6 w-6 text-gray-400" aria-hidden="true" />
                                </div>
                                <div className="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt className="truncate text-sm font-medium text-gray-500">{card.name}</dt>
                                        <dd>
                                            <div className="text-lg font-medium text-gray-900">{card.count}</div>
                                        </dd>
                                    </dl>
                                </div>
                            </div>
                        </div>
                        <div className="bg-gray-50 px-5 py-3">
                            <div className="text-sm">
                                <Link to={card.href} className="font-medium text-indigo-700 hover:text-indigo-900">
                                    Manage {card.name}
                                </Link>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <div className="rounded-lg bg-white shadow">
                <div className="px-4 py-5 sm:p-6">
                    <h3 className="text-base font-semibold leading-6 text-gray-900">Quick Actions</h3>
                    <div className="mt-2 max-w-xl text-sm text-gray-500">
                        <p>Start by defining your entity types, then edge types, and finally link them using mappings.</p>
                    </div>
                    <div className="mt-5">
                        <Link
                            to={`/project/${projectId}/schema/entities`}
                            className="inline-flex items-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                        >
                            <Plus className="-ml-0.5 mr-1.5 h-5 w-5" aria-hidden="true" />
                            Add Entity Type
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}
