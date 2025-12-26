import React, { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { Network, Filter, ZoomIn, ZoomOut, RefreshCw, Download, Settings, Eye, EyeOff } from 'lucide-react';
import { useMemoryStore } from '../stores/memory';
import { useProjectStore } from '../stores/project';
import { useThemeStore } from '../stores/theme';

interface GraphVisualizationProps {
  width?: number;
  height?: number;
  showControls?: boolean;
}

interface GraphNode {
  id: string;
  label: string;
  type: string;
  x?: number;
  y?: number;
  size?: number;
  color?: string;
  entity?: any;
}

interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  type?: string;
  weight?: number;
  color?: string;
  relationship?: any;
}

const getNodeColor = (type: string): string => {
  const colors: Record<string, string> = {
    'person': '#3B82F6',    // blue
    'organization': '#10B981', // green
    'location': '#F59E0B',   // yellow
    'event': '#EF4444',      // red
    'concept': '#8B5CF6',    // purple
    'object': '#6B7280'      // gray
  };
  return colors[type] || '#6B7280';
};

const getEdgeColor = (type: string): string => {
  const colors: Record<string, string> = {
    'works_at': '#3B82F6',
    'located_in': '#10B981',
    'part_of': '#F59E0B',
    'knows': '#EF4444',
    'related_to': '#8B5CF6',
    'owns': '#6B7280'
  };
  return colors[type] || '#9CA3AF';
};

export const GraphVisualization: React.FC<GraphVisualizationProps> = ({
  width = 800,
  height = 600,
  showControls = true
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { currentProject } = useProjectStore();
  const { graphData, getGraphData, isLoading } = useMemoryStore();
  const { computedTheme } = useThemeStore();
  
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [filterTypes, setFilterTypes] = useState<string[]>([]);
  const [showLabels, setShowLabels] = useState(true);

  const nodes: GraphNode[] = useMemo(() => graphData?.entities.map((entity: any) => ({
    id: entity.id,
    label: entity.name,
    type: entity.type,
    size: 20 + (entity.importance || 1) * 5,
    color: getNodeColor(entity.type),
    entity
  })) || [], [graphData]);

  const edges: GraphEdge[] = useMemo(() => graphData?.relationships.map((relationship: any) => ({
    id: relationship.id,
    source: relationship.source_entity_id,
    target: relationship.target_entity_id,
    label: relationship.type,
    type: relationship.type,
    weight: relationship.weight || 1,
    color: getEdgeColor(relationship.type),
    relationship
  })) || [], [graphData]);

  const loadGraphData = useCallback(async () => {
    if (!currentProject) return;
    
    try {
      await getGraphData(currentProject.id, { limit: 100 });
    } catch (error) {
      console.error('Failed to load graph data:', error);
    }
  }, [currentProject, getGraphData]);

  useEffect(() => {
    if (currentProject) {
      loadGraphData();
    }
  }, [currentProject, loadGraphData]);

  const drawGraph = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const isDark = computedTheme === 'dark';

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Apply transformations
    ctx.save();
    ctx.translate(offset.x, offset.y);
    ctx.scale(scale, scale);

    // Filter nodes and edges based on type filters
    const filteredNodes = filterTypes.length > 0 
      ? nodes.filter(node => filterTypes.includes(node.type))
      : nodes;
    
    const filteredNodeIds = new Set(filteredNodes.map(n => n.id));
    const filteredEdges = edges.filter(edge => 
      filteredNodeIds.has(edge.source) && filteredNodeIds.has(edge.target)
    );

    // Draw edges
    filteredEdges.forEach(edge => {
      const sourceNode = nodes.find(n => n.id === edge.source);
      const targetNode = nodes.find(n => n.id === edge.target);
      
      if (!sourceNode || !targetNode) return;

      ctx.beginPath();
      ctx.moveTo(sourceNode.x || 0, sourceNode.y || 0);
      ctx.lineTo(targetNode.x || 0, targetNode.y || 0);
      ctx.strokeStyle = edge.color || (isDark ? '#4B5563' : '#9CA3AF');
      ctx.lineWidth = (edge.weight || 1) * 2;
      ctx.stroke();

      // Draw edge label
      if (showLabels && edge.label) {
        const midX = ((sourceNode.x || 0) + (targetNode.x || 0)) / 2;
        const midY = ((sourceNode.y || 0) + (targetNode.y || 0)) / 2;
        
        ctx.fillStyle = isDark ? '#D1D5DB' : '#374151';
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(edge.label, midX, midY - 5);
      }
    });

    // Draw nodes
    filteredNodes.forEach(node => {
      const x = node.x || 0;
      const y = node.y || 0;
      const size = node.size || 20;

      // Draw node circle
      ctx.beginPath();
      ctx.arc(x, y, size, 0, 2 * Math.PI);
      ctx.fillStyle = node.color || '#6B7280';
      ctx.fill();
      
      if (selectedNode?.id === node.id) {
        ctx.strokeStyle = isDark ? '#F3F4F6' : '#1F2937';
        ctx.lineWidth = 3;
        ctx.stroke();
      }

      // Draw node label
      if (showLabels) {
        ctx.fillStyle = isDark ? '#F3F4F6' : '#1F2937';
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(node.label, x, y + size + 20);
      }
    });

    ctx.restore();
  }, [nodes, edges, scale, offset, showLabels, filterTypes, selectedNode, computedTheme]);

  useEffect(() => {
    drawGraph();
  }, [drawGraph]);

  const handleMouseDown = (e: React.MouseEvent) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - offset.x) / scale;
    const y = (e.clientY - rect.top - offset.y) / scale;

    // Check if clicking on a node
    const clickedNode = nodes.find(node => {
      const dx = (node.x || 0) - x;
      const dy = (node.y || 0) - y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      return distance <= (node.size || 20);
    });

    if (clickedNode) {
      setSelectedNode(clickedNode);
    } else {
      setIsDragging(true);
      setDragStart({ x: e.clientX - offset.x, y: e.clientY - offset.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;

    setOffset({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleZoomIn = () => {
    setScale(prev => Math.min(prev * 1.2, 3));
  };

  const handleZoomOut = () => {
    setScale(prev => Math.max(prev / 1.2, 0.1));
  };

  const handleResetView = () => {
    setScale(1);
    setOffset({ x: 0, y: 0 });
    setSelectedNode(null);
  };

  const handleExportGraph = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const link = document.createElement('a');
    link.download = `graph-${Date.now()}.png`;
    link.href = canvas.toDataURL();
    link.click();
  };

  const availableTypes = Array.from(new Set(nodes.map(node => node.type)));

  if (!currentProject) {
    return (
      <div className="bg-white dark:bg-slate-900 rounded-lg shadow-sm border border-gray-200 dark:border-slate-800 p-8">
        <div className="text-center">
          <Network className="h-12 w-12 text-gray-400 dark:text-slate-600 mx-auto mb-3" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">请先选择项目</h3>
          <p className="text-gray-600 dark:text-slate-400">选择一个项目来查看知识图谱</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-slate-900 rounded-lg shadow-sm border border-gray-200 dark:border-slate-800 p-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 dark:border-blue-400"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-slate-900 rounded-lg shadow-sm border border-gray-200 dark:border-slate-800">
      {showControls && (
        <div className="p-4 border-b border-gray-200 dark:border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Network className="h-5 w-5 text-gray-600 dark:text-slate-400" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">知识图谱</h3>
              <span className="text-sm text-gray-500 dark:text-slate-500">
                ({nodes.length} 节点, {edges.length} 边)
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={handleZoomIn}
                className="p-1.5 text-gray-600 dark:text-slate-500 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-md transition-colors"
                title="放大"
              >
                <ZoomIn className="h-5 w-5" />
              </button>
              <button
                onClick={handleZoomOut}
                className="p-1.5 text-gray-600 dark:text-slate-500 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-md transition-colors"
                title="缩小"
              >
                <ZoomOut className="h-5 w-5" />
              </button>
              <button
                onClick={handleResetView}
                className="p-1.5 text-gray-600 dark:text-slate-500 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-md transition-colors"
                title="重置视图"
              >
                <RefreshCw className="h-5 w-5" />
              </button>
              <button
                onClick={handleExportGraph}
                className="p-1.5 text-gray-600 dark:text-slate-500 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-md transition-colors"
                title="导出图片"
              >
                <Download className="h-5 w-5" />
              </button>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <div className="flex items-center space-x-1 px-2 py-1 bg-gray-100 dark:bg-slate-800 rounded-md text-sm text-gray-600 dark:text-slate-400">
              <Filter className="h-3 w-3" />
              <span>筛选:</span>
            </div>
            {availableTypes.map(type => (
              <button
                key={type}
                onClick={() => {
                  setFilterTypes(prev => 
                    prev.includes(type) 
                      ? prev.filter(t => t !== type)
                      : [...prev, type]
                  );
                }}
                className={`px-2 py-1 rounded-md text-sm transition-colors ${
                  filterTypes.includes(type)
                    ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
                    : 'bg-gray-100 text-gray-600 dark:bg-slate-800 dark:text-slate-400 hover:bg-gray-200 dark:hover:bg-slate-700'
                }`}
              >
                {type}
              </button>
            ))}
            
            <div className="flex-1"></div>
            
            <button
              onClick={() => setShowLabels(!showLabels)}
              className={`flex items-center space-x-1 px-2 py-1 rounded-md text-sm transition-colors ${
                showLabels
                  ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
                  : 'bg-gray-100 text-gray-600 dark:bg-slate-800 dark:text-slate-400 hover:bg-gray-200 dark:hover:bg-slate-700'
              }`}
            >
              {showLabels ? <Eye className="h-3 w-3" /> : <EyeOff className="h-3 w-3" />}
              <span>标签</span>
            </button>
          </div>
        </div>
      )}

      <div className="relative overflow-hidden bg-gray-50 dark:bg-[#111521]" style={{ height }}>
        <canvas
          ref={canvasRef}
          width={width}
          height={height}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          className={`w-full h-full cursor-${isDragging ? 'grabbing' : selectedNode ? 'pointer' : 'grab'}`}
        />
        
        {selectedNode && (
          <div className="absolute top-4 right-4 w-64 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-gray-200 dark:border-slate-700 p-4">
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-medium text-gray-900 dark:text-white truncate" title={selectedNode.label}>
                {selectedNode.label}
              </h4>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-gray-400 dark:text-slate-500 hover:text-gray-600 dark:hover:text-slate-300"
              >
                <Settings className="h-4 w-4" />
              </button>
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-slate-400">类型:</span>
                <span className="text-gray-900 dark:text-white font-medium">{selectedNode.type}</span>
              </div>
              {selectedNode.entity?.description && (
                <div className="pt-2 border-t border-gray-100 dark:border-slate-700">
                  <p className="text-gray-600 dark:text-slate-300 line-clamp-3">
                    {selectedNode.entity.description}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
