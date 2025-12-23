/**
 * Data Adapters for converting API responses to Reagraph format
 */

import type {
  GraphNode as ApiGraphNode,
  GraphLink as ApiGraphLink,
  FlowGraphNode,
  FlowGraphEdge,
  DerivationGraphNode,
  DerivationGraphEdge,
} from '@/api/types';
import { getNodeColor, getEdgeColor } from './graphTheme';

// Reagraph node/edge types
export interface ReagraphNode {
  id: string;
  label?: string;
  fill?: string;
  size?: number;
  data?: Record<string, unknown>;
}

export interface ReagraphEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  fill?: string;
  size?: number;
}

/**
 * Convert knowledge graph API nodes to Reagraph format
 */
export function toReagraphNodesFromKnowledgeGraph(
  nodes: ApiGraphNode[],
  isDark: boolean
): ReagraphNode[] {
  return nodes.map((node) => ({
    id: node.id,
    label: node.title || node.document,
    fill: getNodeColor(node.type, isDark),
    size: Math.min(Math.max(Math.sqrt(node.word_count || 100) / 10, 3), 15),
    data: {
      document: node.document,
      type: node.type,
      status: node.status,
      language: node.language,
      wordCount: node.word_count,
    },
  }));
}

/**
 * Convert knowledge graph API edges to Reagraph format
 */
export function toReagraphEdgesFromKnowledgeGraph(
  edges: ApiGraphLink[]
): ReagraphEdge[] {
  return edges.map((edge, index) => ({
    id: `edge-${edge.source}-${edge.target}-${index}`,
    source: edge.source,
    target: edge.target,
    label: edge.type,
    fill: getEdgeColor(edge.type),
    size: Math.max(edge.weight * 2, 1),
  }));
}

/**
 * Convert flow graph nodes to Reagraph format
 */
export function toReagraphNodesFromFlowGraph(
  nodes: FlowGraphNode[],
  isDark: boolean
): ReagraphNode[] {
  return nodes.map((node) => ({
    id: node.id,
    label: node.title,
    fill: getNodeColor(node.doc_type, isDark, {
      isStale: node.is_stale,
    }),
    size: 8,
    data: {
      docType: node.doc_type,
      lifecycle: node.lifecycle,
      isStale: node.is_stale,
      level: node.level,
      sequenceOrder: node.sequence_order,
      position: node.position,
    },
  }));
}

/**
 * Convert flow graph edges to Reagraph format
 */
export function toReagraphEdgesFromFlowGraph(
  edges: FlowGraphEdge[]
): ReagraphEdge[] {
  return edges.map((edge, index) => ({
    id: `flow-${edge.source}-${edge.target}-${index}`,
    source: edge.source,
    target: edge.target,
    label: edge.type,
    fill: getEdgeColor(edge.type, edge.is_stale),
    size: edge.is_stale ? 2 : 1,
  }));
}

/**
 * Convert derivation graph nodes to Reagraph format
 */
export function toReagraphNodesFromDerivation(
  nodes: DerivationGraphNode[],
  isDark: boolean
): ReagraphNode[] {
  return nodes.map((node) => ({
    id: node.id,
    label: node.title,
    fill: getNodeColor(node.doc_type, isDark, {
      isStale: node.is_stale,
    }),
    size: 8,
    data: {
      docType: node.doc_type,
      lifecycle: node.lifecycle,
      isStale: node.is_stale,
    },
  }));
}

/**
 * Convert derivation graph edges to Reagraph format
 */
export function toReagraphEdgesFromDerivation(
  edges: DerivationGraphEdge[]
): ReagraphEdge[] {
  return edges.map((edge, index) => ({
    id: `deriv-${edge.source}-${edge.target}-${index}`,
    source: edge.source,
    target: edge.target,
    label: edge.relationship,
    fill: getEdgeColor(edge.relationship),
    size: 1,
  }));
}

/**
 * Convert orphan concepts to standalone nodes for visualization
 */
export function toReagraphNodesFromOrphans(
  orphans: Array<string | { concept: string; mention_count?: number }>,
  isDark: boolean
): ReagraphNode[] {
  return orphans.map((orphan, index) => {
    const concept = typeof orphan === 'string' ? orphan : orphan.concept;
    const mentionCount = typeof orphan === 'object' ? orphan.mention_count : 1;

    return {
      id: `orphan-${index}`,
      label: concept,
      fill: getNodeColor('orphan', isDark),
      size: Math.min(Math.max(Math.sqrt(mentionCount || 1) * 3, 4), 12),
      data: {
        type: 'orphan',
        concept,
        mentionCount,
      },
    };
  });
}

/**
 * Generic conversion with auto-detection of source format
 */
export function toReagraphFormat(
  data: {
    nodes?: unknown[];
    edges?: unknown[];
    links?: unknown[];
  },
  isDark: boolean
): { nodes: ReagraphNode[]; edges: ReagraphEdge[] } {
  const rawNodes = data.nodes || [];
  const rawEdges = data.edges || data.links || [];

  // Detect node format and convert
  const nodes: ReagraphNode[] = rawNodes.map((node: unknown, index: number) => {
    const n = node as Record<string, unknown>;

    // Determine type for coloring
    const type = (n.doc_type || n.type || 'default') as string;
    const isStale = Boolean(n.is_stale);

    return {
      id: String(n.id || `node-${index}`),
      label: String(n.title || n.label || n.document || n.id || `Node ${index}`),
      fill: getNodeColor(type, isDark, { isStale }),
      size: 8,
      data: n,
    };
  });

  // Convert edges
  const edges: ReagraphEdge[] = rawEdges.map((edge: unknown, index: number) => {
    const e = edge as Record<string, unknown>;
    const type = (e.type || e.relationship || 'default') as string;
    const isStale = Boolean(e.is_stale);

    return {
      id: String(e.id || `edge-${index}`),
      source: String(e.source),
      target: String(e.target),
      label: type !== 'default' ? type : undefined,
      fill: getEdgeColor(type, isStale),
      size: 1,
    };
  });

  return { nodes, edges };
}
