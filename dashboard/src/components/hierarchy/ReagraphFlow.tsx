/**
 * ReagraphFlow - Reagraph-based flow diagram for document hierarchy
 *
 * An enhanced alternative to the SVG-based FlowDiagram using Reagraph
 * for better performance with large graphs and interactive features.
 */

import { useMemo, useCallback } from 'react';
import { useSettings } from '@/contexts';
import {
  GraphCanvas,
  toReagraphNodesFromFlowGraph,
  toReagraphEdgesFromFlowGraph,
  hierarchyGraphLegend,
} from '@/components/graphs';
import { AlertTriangle, BookOpen } from 'lucide-react';
import type { FlowGraphNode, FlowGraphEdge, StalenessSummary } from '@/api/types';

interface ReagraphFlowProps {
  nodes: FlowGraphNode[];
  edges: FlowGraphEdge[];
  stalenessSummary?: StalenessSummary;
  selectedNode?: string;
  onNodeClick?: (nodeId: string) => void;
  className?: string;
  height?: string | number;
}

export function ReagraphFlow({
  nodes,
  edges,
  stalenessSummary,
  selectedNode: _selectedNode,  // TODO: Implement node highlighting when selected
  onNodeClick,
  className = '',
  height = '100%',
}: ReagraphFlowProps) {
  const { isDark } = useSettings();

  // Convert flow graph data to Reagraph format
  const reagraphNodes = useMemo(() => {
    if (!nodes.length) return [];
    return toReagraphNodesFromFlowGraph(nodes, isDark);
  }, [nodes, isDark]);

  const reagraphEdges = useMemo(() => {
    if (!edges.length) return [];
    return toReagraphEdgesFromFlowGraph(edges);
  }, [edges]);

  // Handle node click - extract the original node ID
  const handleNodeClick = useCallback(
    (node: { id: string }) => {
      onNodeClick?.(node.id);
    },
    [onNodeClick]
  );

  if (nodes.length === 0) {
    return (
      <div className={`flex flex-col items-center justify-center py-12 text-center ${className}`}>
        <BookOpen size={32} className="text-base-content/30 mb-2" />
        <p className="font-medium">No hierarchy data available</p>
        <span className="text-sm text-base-content/60">
          Documents need hierarchy metadata to appear here
        </span>
      </div>
    );
  }

  return (
    <div className={`flex flex-col ${className}`} style={{ height }}>
      {/* Staleness Summary Header */}
      {stalenessSummary && (
        <div className="flex items-center justify-between px-3 py-2 border-b border-base-300 bg-base-200/50">
          <span className="text-xs text-base-content/60">
            {nodes.length} documents, {edges.length} relationships
          </span>
          {stalenessSummary.stale_nodes > 0 ? (
            <span className="badge badge-warning badge-sm gap-1">
              <AlertTriangle size={12} />
              {stalenessSummary.stale_nodes} stale ({stalenessSummary.stale_percentage}%)
            </span>
          ) : (
            <span className="badge badge-success badge-sm">All fresh</span>
          )}
        </div>
      )}

      {/* Graph Canvas */}
      <div className="flex-1 min-h-0">
        <GraphCanvas
          nodes={reagraphNodes}
          edges={reagraphEdges}
          height="100%"
          showToolbar={true}
          showLegend={true}
          legendItems={hierarchyGraphLegend}
          layoutType="forceDirected2d"
          onNodeClick={handleNodeClick}
        />
      </div>
    </div>
  );
}

export default ReagraphFlow;
