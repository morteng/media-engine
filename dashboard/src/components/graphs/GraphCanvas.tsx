/**
 * GraphCanvas - Main graph visualization component wrapping Reagraph
 */

import { useRef, useCallback, useState, useMemo } from 'react';
import { GraphCanvas as ReagraphCanvas, useSelection } from 'reagraph';
import type { GraphCanvasRef } from 'reagraph';
import { useSettings } from '@/contexts';
import { getGraphTheme } from './graphTheme';
import { GraphToolbar } from './GraphToolbar';
import { GraphLegend } from './GraphLegend';
import type { ReagraphNode, ReagraphEdge } from './adapters';

// Reagraph layout types
type LayoutType = 'forceDirected2d' | 'forceDirected3d' | 'circular2d' | 'treeTd2d' | 'radialOut2d' | 'hierarchicalTd' | 'hierarchicalLr';

export interface GraphCanvasProps {
  /** Graph nodes */
  nodes: ReagraphNode[];
  /** Graph edges */
  edges: ReagraphEdge[];
  /** Called when a node is clicked */
  onNodeClick?: (node: ReagraphNode) => void;
  /** Called when a node is double-clicked */
  onNodeDoubleClick?: (node: ReagraphNode) => void;
  /** Layout type */
  layoutType?: LayoutType;
  /** Whether to show the toolbar */
  showToolbar?: boolean;
  /** Whether to show the legend */
  showLegend?: boolean;
  /** Legend items */
  legendItems?: Array<{ label: string; color: string }>;
  /** Additional CSS classes */
  className?: string;
  /** Height of the graph container */
  height?: string | number;
  /** Enable 3D mode */
  is3D?: boolean;
}

export function GraphCanvas({
  nodes,
  edges,
  onNodeClick,
  onNodeDoubleClick,
  layoutType = 'forceDirected2d',
  showToolbar = true,
  showLegend = true,
  legendItems,
  className = '',
  height = 500,
  is3D = false,
}: GraphCanvasProps) {
  const graphRef = useRef<GraphCanvasRef | null>(null);
  const { isDark } = useSettings();
  const theme = useMemo(() => getGraphTheme(isDark), [isDark]);
  const [currentLayout, setCurrentLayout] = useState(layoutType);
  const [show3D, setShow3D] = useState(is3D);

  // Handle node click
  const handleNodeClick = useCallback(
    (node: { id: string }) => {
      const fullNode = nodes.find((n) => n.id === node.id);
      if (fullNode && onNodeClick) {
        onNodeClick(fullNode);
      }
    },
    [nodes, onNodeClick]
  );

  // Handle node double-click
  const handleNodeDoubleClick = useCallback(
    (node: { id: string }) => {
      const fullNode = nodes.find((n) => n.id === node.id);
      if (fullNode && onNodeDoubleClick) {
        onNodeDoubleClick(fullNode);
      }
    },
    [nodes, onNodeDoubleClick]
  );

  // Toolbar actions
  const handleZoomIn = useCallback(() => {
    graphRef.current?.zoomIn?.();
  }, []);

  const handleZoomOut = useCallback(() => {
    graphRef.current?.zoomOut?.();
  }, []);

  const handleResetView = useCallback(() => {
    graphRef.current?.centerGraph?.();
  }, []);

  const handleToggle3D = useCallback(() => {
    setShow3D((prev) => !prev);
    // When toggling 3D, switch layout accordingly
    setCurrentLayout((prev) => {
      if (!show3D) return 'forceDirected3d';
      return prev === 'forceDirected3d' ? 'forceDirected2d' : prev;
    });
  }, [show3D]);

  const handleLayoutChange = useCallback((layout: string) => {
    setCurrentLayout(layout as typeof currentLayout);
  }, []);

  // Empty state
  if (!nodes.length) {
    return (
      <div
        className={`flex items-center justify-center bg-base-200 rounded-lg ${className}`}
        style={{ height }}
      >
        <div className="text-center text-base-content/60">
          <p className="text-lg font-medium">No graph data</p>
          <p className="text-sm">There are no nodes to display</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`} style={{ height }}>
      {showToolbar && (
        <GraphToolbar
          onZoomIn={handleZoomIn}
          onZoomOut={handleZoomOut}
          onResetView={handleResetView}
          onToggle3D={handleToggle3D}
          onLayoutChange={handleLayoutChange}
          is3D={show3D}
          currentLayout={currentLayout}
          className="absolute top-2 right-2 z-10"
        />
      )}

      {showLegend && legendItems && legendItems.length > 0 && (
        <GraphLegend items={legendItems} className="absolute bottom-2 left-2 z-10" />
      )}

      <ReagraphCanvas
        ref={graphRef}
        nodes={nodes}
        edges={edges}
        layoutType={show3D ? 'forceDirected3d' : currentLayout}
        theme={theme}
        cameraMode={show3D ? 'rotate' : 'pan'}
        onNodeClick={handleNodeClick}
        onNodeDoubleClick={handleNodeDoubleClick}
        labelType="auto"
        edgeLabelPosition="natural"
        edgeArrowPosition="end"
        animated
      />
    </div>
  );
}

/**
 * GraphCanvas with built-in selection support
 */
export function SelectableGraphCanvas({
  nodes,
  edges,
  onSelectionChange,
  ...props
}: GraphCanvasProps & {
  onSelectionChange?: (selectedNodes: ReagraphNode[]) => void;
}) {
  const graphRef = useRef<GraphCanvasRef | null>(null);
  const {
    selections,
    onNodeClick: selectionNodeClick,
  } = useSelection({
    ref: graphRef,
    nodes,
    edges,
    type: 'multi',
    focusOnSelect: true,
  });

  // Notify parent of selection changes
  const selectedNodes = useMemo(() => {
    return nodes.filter((n) => selections.includes(n.id));
  }, [nodes, selections]);

  // Call onSelectionChange when selection changes
  useMemo(() => {
    onSelectionChange?.(selectedNodes);
  }, [selectedNodes, onSelectionChange]);

  return (
    <GraphCanvas
      {...props}
      nodes={nodes}
      edges={edges}
      onNodeClick={(node) => {
        selectionNodeClick?.(node);
        props.onNodeClick?.(node);
      }}
    />
  );
}

export default GraphCanvas;
