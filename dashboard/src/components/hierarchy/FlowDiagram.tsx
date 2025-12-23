import { useState, useRef, useCallback, useMemo } from 'react';
import {
  BookOpen,
  AlertTriangle,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Download,
} from 'lucide-react';
import clsx from 'clsx';
import type { FlowGraphNode, FlowGraphEdge, StalenessSummary } from '@/api/types';

// Edge colors by relationship type
const edgeColors: Record<string, { stroke: string; stale: string }> = {
  implements: { stroke: '#10b981', stale: '#ef4444' },
  extends: { stroke: '#3b82f6', stale: '#ef4444' },
  summarizes: { stroke: '#8b5cf6', stale: '#ef4444' },
  supplements: { stroke: '#06b6d4', stale: '#ef4444' },
  visualizes: { stroke: '#f59e0b', stale: '#ef4444' },
  translates: { stroke: '#a855f7', stale: '#ef4444' },
  generates: { stroke: '#64748b', stale: '#ef4444' },
};

interface FlowDiagramProps {
  nodes: FlowGraphNode[];
  edges: FlowGraphEdge[];
  stalenessSummary?: StalenessSummary;
  selectedNode?: string;
  onNodeClick?: (nodeId: string) => void;
  className?: string;
}

export function FlowDiagram({
  nodes,
  edges,
  stalenessSummary,
  selectedNode,
  onNodeClick,
  className,
}: FlowDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Create node lookup map
  const nodeMap = useMemo(() => {
    const map: Record<string, FlowGraphNode> = {};
    nodes.forEach(node => {
      map[node.id] = node;
    });
    return map;
  }, [nodes]);

  // Calculate SVG bounds
  const bounds = useMemo(() => {
    if (nodes.length === 0) return { width: 800, height: 600, minX: 0, minY: 0 };

    const xs = nodes.map(n => n.position.x);
    const ys = nodes.map(n => n.position.y);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);

    return {
      width: Math.max(maxX - minX + 400, 800),
      height: Math.max(maxY - minY + 200, 600),
      minX: minX - 100,
      minY: minY - 50,
    };
  }, [nodes]);

  // Handle zoom
  const handleZoomIn = () => setZoom(z => Math.min(z + 0.25, 2));
  const handleZoomOut = () => setZoom(z => Math.max(z - 0.25, 0.25));
  const handleResetZoom = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  // Handle pan
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 0) {
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Handle export
  const handleExport = useCallback(() => {
    const svg = containerRef.current?.querySelector('svg');
    if (!svg) return;

    const svgData = new XMLSerializer().serializeToString(svg);
    const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    const svgUrl = URL.createObjectURL(svgBlob);

    const link = document.createElement('a');
    link.href = svgUrl;
    link.download = 'hierarchy-flow.svg';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(svgUrl);
  }, []);

  if (nodes.length === 0) {
    return (
      <div className={clsx('flex flex-col items-center justify-center py-12 text-center', className)}>
        <BookOpen size={32} className="text-base-content/30 mb-2" />
        <p className="font-medium">No hierarchy data available</p>
        <span className="text-sm text-base-content/60">Documents need hierarchy metadata to appear here</span>
      </div>
    );
  }

  return (
    <div className={clsx('flex flex-col h-full', className)}>
      {/* Toolbar */}
      <div className="flex items-center justify-between p-2 border-b border-base-300 bg-base-200">
        <div className="flex items-center gap-1">
          <button className="btn btn-ghost btn-xs btn-square" onClick={handleZoomOut} title="Zoom out">
            <ZoomOut size={14} />
          </button>
          <span className="px-2 text-xs text-base-content/60 tabular-nums min-w-[50px] text-center">
            {Math.round(zoom * 100)}%
          </span>
          <button className="btn btn-ghost btn-xs btn-square" onClick={handleZoomIn} title="Zoom in">
            <ZoomIn size={14} />
          </button>
          <button className="btn btn-ghost btn-xs btn-square" onClick={handleResetZoom} title="Reset view">
            <Maximize2 size={14} />
          </button>
        </div>

        <div className="flex items-center gap-2">
          <button className="btn btn-ghost btn-xs btn-square" onClick={handleExport} title="Export SVG">
            <Download size={14} />
          </button>

          {stalenessSummary && (
            <div>
              {stalenessSummary.stale_nodes > 0 ? (
                <span className="badge badge-warning gap-1">
                  <AlertTriangle size={12} />
                  {stalenessSummary.stale_nodes} stale ({stalenessSummary.stale_percentage}%)
                </span>
              ) : (
                <span className="badge badge-success">All fresh</span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Canvas */}
      <div
        ref={containerRef}
        className="flex-1 overflow-hidden bg-base-300/50"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
      >
        <svg
          width="100%"
          height="100%"
          viewBox={`${bounds.minX - pan.x / zoom} ${bounds.minY - pan.y / zoom} ${bounds.width / zoom} ${bounds.height / zoom}`}
          style={{ transform: `scale(${zoom})`, transformOrigin: 'center' }}
        >
          {/* Edges */}
          <defs>
            <marker
              id="arrow"
              viewBox="0 0 10 10"
              refX="9"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor" />
            </marker>
            <marker
              id="arrow-stale"
              viewBox="0 0 10 10"
              refX="9"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#ef4444" />
            </marker>
          </defs>

          <g>
            {edges.map((edge, idx) => {
              const sourceNode = nodeMap[edge.source];
              const targetNode = nodeMap[edge.target];
              if (!sourceNode || !targetNode) return null;

              const colors = edgeColors[edge.type] || edgeColors.implements;
              const strokeColor = edge.is_stale ? colors.stale : colors.stroke;

              // Calculate edge path (bezier curve)
              const sx = sourceNode.position.x + 80;
              const sy = sourceNode.position.y + 20;
              const tx = targetNode.position.x + 80;
              const ty = targetNode.position.y + 20;
              const midY = (sy + ty) / 2;

              const path = `M ${sx} ${sy} C ${sx} ${midY}, ${tx} ${midY}, ${tx} ${ty}`;

              return (
                <g key={idx}>
                  <path
                    d={path}
                    fill="none"
                    stroke={strokeColor}
                    strokeWidth={edge.is_stale ? 2 : 1.5}
                    strokeDasharray={edge.type === 'summarizes' ? '4,2' : edge.type === 'translates' ? '2,2' : undefined}
                    markerEnd={edge.is_stale ? 'url(#arrow-stale)' : 'url(#arrow)'}
                    style={{ color: strokeColor }}
                  />
                </g>
              );
            })}
          </g>

          {/* Nodes */}
          <g>
            {nodes.map((node) => {
              const isSelected = selectedNode === node.id;

              return (
                <g
                  key={node.id}
                  transform={`translate(${node.position.x}, ${node.position.y})`}
                  onClick={() => onNodeClick?.(node.id)}
                  style={{ cursor: 'pointer' }}
                >
                  {/* Node background */}
                  <rect
                    x="0"
                    y="0"
                    width="160"
                    height="40"
                    rx="6"
                    fill={isSelected ? '#6366f1' : node.is_stale ? '#fef3c7' : '#f8fafc'}
                    stroke={node.is_stale ? '#f59e0b' : isSelected ? '#6366f1' : '#e2e8f0'}
                    strokeWidth={isSelected ? 2 : 1}
                  />

                  {/* Stale indicator */}
                  {node.is_stale && (
                    <circle cx="150" cy="8" r="6" fill="#f59e0b" />
                  )}

                  {/* Title */}
                  <text
                    x="12"
                    y="24"
                    fontSize="12"
                    fill={isSelected ? '#ffffff' : '#1f2937'}
                    fontWeight="500"
                  >
                    {node.title.length > 18 ? node.title.slice(0, 18) + '...' : node.title}
                  </text>

                  {/* Doc type badge */}
                  <text
                    x="12"
                    y="36"
                    fontSize="9"
                    fill={isSelected ? '#c7d2fe' : '#6b7280'}
                  >
                    {node.doc_type}
                  </text>
                </g>
              );
            })}
          </g>
        </svg>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 p-2 border-t border-base-300 text-xs text-base-content/60">
        <span className="font-medium">Edge Types:</span>
        <span className="flex items-center gap-1">
          <span className="w-4 h-0.5 rounded" style={{ background: edgeColors.implements.stroke }} />
          implements
        </span>
        <span className="flex items-center gap-1">
          <span className="w-4 h-0.5 rounded" style={{ background: edgeColors.extends.stroke }} />
          extends
        </span>
        <span className="flex items-center gap-1">
          <span className="w-4 h-0.5 rounded border-dashed border-t-2" style={{ borderColor: edgeColors.summarizes.stroke }} />
          summarizes
        </span>
        <span className="flex items-center gap-1">
          <span className="w-4 h-0.5 rounded" style={{ background: '#ef4444' }} />
          stale
        </span>
      </div>
    </div>
  );
}

export default FlowDiagram;
