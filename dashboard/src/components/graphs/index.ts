/**
 * Graph Visualization Components
 *
 * Reusable Reagraph-based components for visualizing
 * knowledge graphs, dependencies, and document hierarchies.
 */

// Main canvas components
export { GraphCanvas, SelectableGraphCanvas } from './GraphCanvas';
export type { GraphCanvasProps } from './GraphCanvas';

// Error boundary
export { GraphErrorBoundary } from './GraphErrorBoundary';

// Controls and UI
export { GraphToolbar } from './GraphToolbar';
export { GraphLegend, knowledgeGraphLegend, dependencyGraphLegend, hierarchyGraphLegend } from './GraphLegend';
export type { LegendItem } from './GraphLegend';

// Data adapters
export {
  toReagraphNodesFromKnowledgeGraph,
  toReagraphEdgesFromKnowledgeGraph,
  toReagraphNodesFromFlowGraph,
  toReagraphEdgesFromFlowGraph,
  toReagraphNodesFromDerivation,
  toReagraphEdgesFromDerivation,
  toReagraphNodesFromOrphans,
  toReagraphFormat,
} from './adapters';
export type { ReagraphNode, ReagraphEdge } from './adapters';

// Theme utilities
export {
  getGraphTheme,
  getNodeColor,
  getEdgeColor,
  graphThemes,
  nodeTypeColors,
  edgeTypeColors,
} from './graphTheme';
