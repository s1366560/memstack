import React, { useEffect, useRef, useState, useCallback } from 'react'
import cytoscape, { Core, ElementDefinition } from 'cytoscape'
import { graphitiService } from '../services/graphitiService'

// Cytoscape 样式定义
const cytoscapeStyles = [
    {
        selector: 'node',
        style: {
            'background-color': (ele: any) => {
                const type = ele.data('type')
                const entityType = ele.data('entity_type')

                if (type === 'Episodic') return '#10B981' // Emerald 500 (Documents/Episodes)
                if (type === 'Community') return '#7C3AED' // Violet 600

                // Entity types mapping
                switch (entityType) {
                    case 'Person': return '#E11D48' // Rose 600
                    case 'Organization': return '#9333EA' // Purple 600
                    case 'Location': return '#0891B2' // Cyan 600
                    case 'Event': return '#D97706' // Amber 600
                    case 'Product': return '#2563EB' // Blue 600
                    default: return '#3B82F6' // Blue 500
                }
            },
            'label': (ele: any) => {
                const name = ele.data('name') || ''
                return name.length > 20 ? name.substring(0, 20) + '...' : name
            },
            'width': (ele: any) => ele.data('type') === 'Community' ? 70 : 50,
            'height': (ele: any) => ele.data('type') === 'Community' ? 70 : 50,
            'font-size': '5px',
            'font-weight': '600',
            'font-family': 'Inter, "Noto Sans SC", sans-serif',
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': 6,

            // Border & Glow
            'border-width': 2,
            'border-color': '#ffffff',
            'border-opacity': 0.3,
            'shadow-blur': 20,
            'shadow-color': (ele: any) => {
                const type = ele.data('type')
                const entityType = ele.data('entity_type')
                if (type === 'Episodic') return 'rgba(16, 185, 129, 0.4)'
                if (type === 'Community') return 'rgba(124, 58, 237, 0.4)'
                switch (entityType) {
                    case 'Person': return 'rgba(225, 29, 72, 0.4)'
                    case 'Organization': return 'rgba(147, 51, 234, 0.4)'
                    default: return 'rgba(59, 130, 246, 0.4)'
                }
            },
            'shadow-opacity': 1,
            'z-index': 10,
        } as any,
    },
    {
        selector: 'node:selected',
        style: {

        },
    },
    {
        selector: 'edge',
        style: {
            'width': 1.5,
            'line-color': '#475569', // slate-600
            'target-arrow-color': '#475569',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'arrow-scale': 0.8,
            'opacity': 0.5,
            'label': (ele: any) => {
                const label = ele.data('label') || ''
                return label.length > 15 ? label.substring(0, 15) + '...' : label
            },
            'font-size': '5px',
            'font-family': 'Inter, "Noto Sans SC", sans-serif',
            'color': '#94A3B8', // slate-400
        },
    },
    {
        selector: 'edge:selected',
        style: {
            'width': 2,
            'opacity': 1,
            'z-index': 999,
        },
    },
]

interface CytoscapeGraphProps {
    projectId?: string
    tenantId?: string
    includeCommunities?: boolean
    minConnections?: number
    onNodeClick?: (node: any) => void
}

// Cytoscape 布局配置
const layoutOptions = {
    name: 'cose' as const,
    // 力导向参数
    animate: true,
    animationDuration: 500,
    animationEasing: 'ease-out',
    // 节点斥力
    idealEdgeLength: 120,
    nodeOverlap: 40,
    // 组件
    componentSpacing: 150,
    // 重力
    gravity: 0.8,
    numIter: 1000,
    initialTemp: 200,
    coolingFactor: 0.95,
    minTemp: 1.0,
}

export const CytoscapeGraph: React.FC<CytoscapeGraphProps> = ({
    projectId,
    tenantId,
    includeCommunities = true,
    minConnections = 0,
    onNodeClick,
}) => {
    const containerRef = useRef<HTMLDivElement>(null)
    const cyRef = useRef<Core | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [nodeCount, setNodeCount] = useState(0)
    const [edgeCount, setEdgeCount] = useState(0)
    const onNodeClickRef = useRef(onNodeClick)

    useEffect(() => {
        onNodeClickRef.current = onNodeClick
    }, [onNodeClick])

    // 加载图谱数据
    const loadGraphData = useCallback(async () => {
        if (!cyRef.current) return

        setLoading(true)
        setError(null)

        try {
            const data = await graphitiService.getGraphData({
                tenant_id: tenantId,
                project_id: projectId,
                limit: 500,
            })

            // 转换为 Cytoscape 格式
            const elements: ElementDefinition[] = []

            // 添加节点
            data.elements.nodes.forEach((node: any) => {
                const nodeType = node.data.label

                // 过滤条件
                if (!includeCommunities && nodeType === 'Community') return
                if (minConnections > 0) {
                    const connections = data.elements.edges.filter(
                        (e: any) => e.data.source === node.data.id || e.data.target === node.data.id
                    ).length
                    if (connections < minConnections) return
                }

                elements.push({
                    group: 'nodes',
                    data: {
                        id: node.data.id,
                        label: nodeType,
                        name: node.data.name || node.data.label,
                        type: nodeType,
                        uuid: node.data.uuid,
                        summary: node.data.summary,
                        entity_type: node.data.entity_type,
                        member_count: node.data.member_count,
                        tenant_id: node.data.tenant_id,
                        project_id: node.data.project_id,
                    },
                })
            })

            // 添加边
            data.elements.edges.forEach((edge: any) => {
                elements.push({
                    group: 'edges',
                    data: {
                        id: edge.data.id,
                        source: edge.data.source,
                        target: edge.data.target,
                        label: edge.data.label || '',
                    },
                })
            })

            // 更新 Cytoscape
            cyRef.current.json({ elements })
            cyRef.current.layout(layoutOptions).run()

            setNodeCount(elements.filter(e => e.group === 'nodes').length)
            setEdgeCount(elements.filter(e => e.group === 'edges').length)

        } catch (err) {
            console.error('Failed to load graph data:', err)
            setError('Failed to load graph data')
        } finally {
            setLoading(false)
        }
    }, [projectId, tenantId, includeCommunities, minConnections])

    // 初始化 Cytoscape
    useEffect(() => {
        if (!containerRef.current) return

        const cy = cytoscape({
            container: containerRef.current,
            style: cytoscapeStyles,
            minZoom: 0.1,
            maxZoom: 3,
            wheelSensitivity: 0.2,
        })

        cyRef.current = cy

        // 事件监听
        cy.on('tap', 'node', (evt) => {
            const node = evt.target
            console.log('Node clicked:', node.data())
            onNodeClick?.(node.data())
        })

        cy.on('tap', 'edge', (evt) => {
            const edge = evt.target
            console.log('Edge clicked:', edge.data())
        })

        // Background click to deselect
        cy.on('tap', (evt) => {
            if (evt.target === cy) {
                onNodeClick?.(null)
            }
        })

        // 启用节点选择框选
        cy.boxSelectionEnabled(true)

        return () => {
            cy.destroy()
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    // 加载数据
    useEffect(() => {
        if (cyRef.current) {
            loadGraphData()
        }
    }, [loadGraphData])

    // 导出图片功能
    const exportImage = () => {
        if (!cyRef.current) return

        const png = cyRef.current.png({
            full: true,
            scale: 2,
        })

        const link = document.createElement('a')
        link.href = png
        link.download = `graph-${Date.now()}.png`
        link.click()
    }

    // 重新布局
    const relayout = () => {
        if (!cyRef.current) return
        cyRef.current.layout(layoutOptions).run()
    }

    // 居中视图
    const fitView = () => {
        if (!cyRef.current) return
        cyRef.current.fit(undefined, 50)
    }

    return (
        <div className="flex flex-col h-full">
            {/* 工具栏 */}
            <div className="flex items-center justify-between p-4 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
                        <span>Nodes:</span>
                        <span className="font-semibold text-slate-900 dark:text-white">{nodeCount}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
                        <span>Edges:</span>
                        <span className="font-semibold text-slate-900 dark:text-white">{edgeCount}</span>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <button
                        onClick={relayout}
                        className="p-2 text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white rounded-md hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                        title="Relayout"
                    >
                        <span className="material-symbols-outlined">refresh</span>
                    </button>
                    <button
                        onClick={fitView}
                        className="p-2 text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white rounded-md hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                        title="Fit to View"
                    >
                        <span className="material-symbols-outlined">center_focus_strong</span>
                    </button>
                    <button
                        onClick={loadGraphData}
                        className="p-2 text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white rounded-md hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                        title="Reload Data"
                    >
                        <span className="material-symbols-outlined">sync</span>
                    </button>
                    <button
                        onClick={exportImage}
                        className="p-2 text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white rounded-md hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                        title="Export as PNG"
                    >
                        <span className="material-symbols-outlined">download</span>
                    </button>
                </div>
            </div>

            {/* Cytoscape 容器 */}
            <div className="flex-1 relative">
                {loading && (
                    <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm">
                        <div className="text-center">
                            <span className="material-symbols-outlined text-4xl text-blue-600 animate-spin">
                                progress_activity
                            </span>
                            <p className="text-slate-600 dark:text-slate-400 mt-2">Loading graph...</p>
                        </div>
                    </div>
                )}

                {error && (
                    <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm">
                        <div className="text-center">
                            <span className="material-symbols-outlined text-4xl text-red-600">error</span>
                            <p className="text-slate-600 dark:text-slate-400 mt-2">{error}</p>
                            <button
                                onClick={loadGraphData}
                                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-500"
                            >
                                Retry
                            </button>
                        </div>
                    </div>
                )}

                <div
                    ref={containerRef}
                    className="w-full h-full bg-slate-50 dark:bg-[#111521]"
                />
            </div>

            {/* 图例 */}
            <div className="p-4 bg-white dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700">
                <div className="flex items-center gap-6 text-sm">
                    <div className="flex items-center gap-2">
                        <div className="w-4 h-4 rounded-full bg-blue-600"></div>
                        <span className="text-slate-600 dark:text-slate-400">Entity</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-4 h-4 rounded-full bg-emerald-600"></div>
                        <span className="text-slate-600 dark:text-slate-400">Episode</span>
                    </div>
                    {includeCommunities && (
                        <div className="flex items-center gap-2">
                            <div className="w-6 h-6 rounded-full bg-purple-600"></div>
                            <span className="text-slate-600 dark:text-slate-400">Community</span>
                        </div>
                    )}
                    <div className="ml-auto text-slate-500 text-xs">
                        🖱️ Drag to pan • Scroll to zoom • Click to select
                    </div>
                </div>
            </div>
        </div>
    )
}

export default CytoscapeGraph
