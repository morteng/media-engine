/**
 * LanguagePanelGraph - Side-by-side language visualization
 *
 * Shows EN documents on left, NO documents on right with translation
 * lines connecting them and dependency edges within each panel.
 */

import { useMemo, useCallback, useState } from 'react';
import { useSettings } from '@/contexts';
import {
  Languages,
  ArrowRight,
  ChevronDown,
  ChevronRight,
  FileText,
  AlertTriangle,
  CheckCircle,
  Filter,
} from 'lucide-react';

// Types for the unified graph API response
interface UnifiedNode {
  id: string;
  label: string;
  type: string;
  doc_type: string;
  lifecycle: string;
  is_stale: boolean;
  language: string;
}

interface UnifiedEdge {
  source: string;
  target: string;
  type: string;
  label: string;
  is_stale: boolean;
}

interface UnifiedGraphData {
  nodes: UnifiedNode[];
  edges: UnifiedEdge[];
  summary: {
    node_count: number;
    edge_count: number;
    edge_types: Record<string, number>;
  };
}

interface LanguagePanelGraphProps {
  data: UnifiedGraphData;
  onNodeClick?: (nodeId: string) => void;
  selectedNode?: string;
  className?: string;
}

// Edge type colors
const EDGE_COLORS: Record<string, { stroke: string; label: string }> = {
  translates: { stroke: '#22c55e', label: 'Translation' },
  depends_on: { stroke: '#3b82f6', label: 'Depends On' },
  implements: { stroke: '#a855f7', label: 'Implements' },
  extends: { stroke: '#f59e0b', label: 'Extends' },
  summarizes: { stroke: '#06b6d4', label: 'Summarizes' },
  references: { stroke: '#6b7280', label: 'References' },
  uses_asset: { stroke: '#ec4899', label: 'Uses Asset' },
  anchor_ref: { stroke: '#14b8a6', label: 'Anchor Ref' },
  parent: { stroke: '#8b5cf6', label: 'Parent' },
};

// Get display name from path
function getDisplayName(path: string): string {
  const parts = path.split('/');
  const filename = parts[parts.length - 1];
  // Remove number prefix and extension
  return filename
    .replace(/^\d+_/, '')
    .replace(/\.md$/, '')
    .replace(/_/g, ' ')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

// Group nodes by language
function groupByLanguage(nodes: UnifiedNode[]): {
  en: UnifiedNode[];
  no: UnifiedNode[];
  other: UnifiedNode[];
} {
  const groups = { en: [] as UnifiedNode[], no: [] as UnifiedNode[], other: [] as UnifiedNode[] };

  for (const node of nodes) {
    if (node.language === 'en' || node.id.includes('/en/')) {
      groups.en.push(node);
    } else if (node.language === 'no' || node.id.includes('/no/')) {
      groups.no.push(node);
    } else {
      groups.other.push(node);
    }
  }

  // Sort by sequence order (number prefix in filename)
  const sortFn = (a: UnifiedNode, b: UnifiedNode) => {
    const aNum = parseInt(a.id.split('/').pop()?.match(/^(\d+)/)?.[1] || '999');
    const bNum = parseInt(b.id.split('/').pop()?.match(/^(\d+)/)?.[1] || '999');
    return aNum - bNum;
  };

  groups.en.sort(sortFn);
  groups.no.sort(sortFn);

  return groups;
}

// Find matching translation pairs
function findTranslationPairs(
  enNodes: UnifiedNode[],
  noNodes: UnifiedNode[],
  edges: UnifiedEdge[]
): Map<string, string> {
  const pairs = new Map<string, string>();

  // Find explicit translation edges
  for (const edge of edges) {
    if (edge.type === 'translates') {
      pairs.set(edge.source, edge.target);
      pairs.set(edge.target, edge.source);
    }
  }

  // Also try to match by filename pattern (01_intro.md -> 01_introduksjon.md)
  for (const enNode of enNodes) {
    if (pairs.has(enNode.id)) continue;

    const enNum = enNode.id.split('/').pop()?.match(/^(\d+)/)?.[1];
    if (!enNum) continue;

    for (const noNode of noNodes) {
      const noNum = noNode.id.split('/').pop()?.match(/^(\d+)/)?.[1];
      if (noNum === enNum) {
        pairs.set(enNode.id, noNode.id);
        pairs.set(noNode.id, enNode.id);
        break;
      }
    }
  }

  return pairs;
}

// Document node component
function DocumentNode({
  node,
  isSelected,
  onClick,
  hasTranslation,
  isDark,
}: {
  node: UnifiedNode;
  isSelected: boolean;
  onClick: () => void;
  hasTranslation: boolean;
  isDark: boolean;
}) {
  const bgColor = isSelected
    ? 'bg-primary/20 border-primary'
    : node.is_stale
    ? 'bg-warning/10 border-warning/30'
    : isDark
    ? 'bg-base-300 border-base-content/10'
    : 'bg-base-200 border-base-content/10';

  return (
    <button
      className={`w-full text-left px-3 py-2 rounded-lg border transition-all hover:border-primary/50 ${bgColor}`}
      onClick={onClick}
    >
      <div className="flex items-center gap-2">
        <FileText size={14} className="text-primary flex-shrink-0" />
        <span className="truncate text-sm font-medium">{getDisplayName(node.id)}</span>
        {node.is_stale && (
          <AlertTriangle size={12} className="text-warning flex-shrink-0" />
        )}
        {hasTranslation && (
          <CheckCircle size={12} className="text-success flex-shrink-0 ml-auto" />
        )}
      </div>
      <div className="flex items-center gap-2 mt-1">
        <span className="badge badge-ghost badge-xs">{node.doc_type}</span>
      </div>
    </button>
  );
}

// Edge type filter component
function EdgeTypeFilter({
  edgeTypes,
  enabledTypes,
  onToggle,
}: {
  edgeTypes: Record<string, number>;
  enabledTypes: Set<string>;
  onToggle: (type: string) => void;
}) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button
        className="btn btn-sm btn-ghost gap-1"
        onClick={() => setIsOpen(!isOpen)}
      >
        <Filter size={14} />
        Filter
        {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
      </button>

      {isOpen && (
        <div className="absolute top-full right-0 mt-1 z-20 bg-base-200 rounded-lg shadow-lg border border-base-300 p-2 min-w-48">
          {Object.entries(edgeTypes).map(([type, count]) => {
            const config = EDGE_COLORS[type] || { stroke: '#6b7280', label: type };
            const isEnabled = enabledTypes.has(type);

            return (
              <label
                key={type}
                className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-base-300 cursor-pointer"
              >
                <input
                  type="checkbox"
                  className="checkbox checkbox-xs"
                  checked={isEnabled}
                  onChange={() => onToggle(type)}
                />
                <span
                  className="w-3 h-3 rounded-full flex-shrink-0"
                  style={{ backgroundColor: config.stroke }}
                />
                <span className="text-sm flex-1">{config.label}</span>
                <span className="badge badge-ghost badge-xs">{count}</span>
              </label>
            );
          })}
        </div>
      )}
    </div>
  );
}

export function LanguagePanelGraph({
  data,
  onNodeClick,
  selectedNode,
  className = '',
}: LanguagePanelGraphProps) {
  const { isDark } = useSettings();
  const [enabledEdgeTypes, setEnabledEdgeTypes] = useState<Set<string>>(
    new Set(['translates', 'depends_on', 'implements', 'extends', 'summarizes'])
  );

  // Group nodes by language
  const { en: enNodes, no: noNodes } = useMemo(
    () => groupByLanguage(data.nodes),
    [data.nodes]
  );

  // Find translation pairs
  const translationPairs = useMemo(
    () => findTranslationPairs(enNodes, noNodes, data.edges),
    [enNodes, noNodes, data.edges]
  );

  // Filter edges by enabled types
  const filteredEdges = useMemo(
    () => data.edges.filter(edge => enabledEdgeTypes.has(edge.type)),
    [data.edges, enabledEdgeTypes]
  );

  // Group edges by type for the visualization
  const {
    translationEdges,
    enDependencyEdges,
    noDependencyEdges,
  } = useMemo(() => {
    const translation: UnifiedEdge[] = [];
    const enDeps: UnifiedEdge[] = [];
    const noDeps: UnifiedEdge[] = [];

    const enIds = new Set(enNodes.map(n => n.id));
    const noIds = new Set(noNodes.map(n => n.id));

    for (const edge of filteredEdges) {
      if (edge.type === 'translates') {
        translation.push(edge);
      } else if (enIds.has(edge.source) && enIds.has(edge.target)) {
        enDeps.push(edge);
      } else if (noIds.has(edge.source) && noIds.has(edge.target)) {
        noDeps.push(edge);
      }
      // Cross-language edges (other than translates) are not rendered in this view
    }

    return {
      translationEdges: translation,
      enDependencyEdges: enDeps,
      noDependencyEdges: noDeps,
    };
  }, [filteredEdges, enNodes, noNodes]);

  const handleNodeClick = useCallback(
    (nodeId: string) => {
      onNodeClick?.(nodeId);
    },
    [onNodeClick]
  );

  const toggleEdgeType = useCallback((type: string) => {
    setEnabledEdgeTypes(prev => {
      const next = new Set(prev);
      if (next.has(type)) {
        next.delete(type);
      } else {
        next.add(type);
      }
      return next;
    });
  }, []);

  // Calculate node positions for SVG connections
  const nodePositions = useMemo(() => {
    const positions = new Map<string, { x: number; y: number; col: 'en' | 'no' }>();

    enNodes.forEach((node, index) => {
      positions.set(node.id, { x: 200, y: 60 + index * 56, col: 'en' });
    });

    noNodes.forEach((node, index) => {
      positions.set(node.id, { x: 600, y: 60 + index * 56, col: 'no' });
    });

    return positions;
  }, [enNodes, noNodes]);

  const svgHeight = Math.max(enNodes.length, noNodes.length) * 56 + 120;

  if (data.nodes.length === 0) {
    return (
      <div className={`flex flex-col items-center justify-center py-12 text-center ${className}`}>
        <Languages size={32} className="text-base-content/30 mb-2" />
        <p className="font-medium">No documents found</p>
        <span className="text-sm text-base-content/60">
          Add content to see the language panel view
        </span>
      </div>
    );
  }

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-base-300 bg-base-200/50">
        <div className="flex items-center gap-4">
          <span className="text-xs text-base-content/60">
            {data.summary.node_count} documents, {data.summary.edge_count} relationships
          </span>
          <div className="flex items-center gap-2">
            <span className="badge badge-primary badge-sm">EN: {enNodes.length}</span>
            <ArrowRight size={12} className="text-success" />
            <span className="badge badge-secondary badge-sm">NO: {noNodes.length}</span>
          </div>
        </div>
        <EdgeTypeFilter
          edgeTypes={data.summary.edge_types}
          enabledTypes={enabledEdgeTypes}
          onToggle={toggleEdgeType}
        />
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-auto">
        <div className="relative min-h-full" style={{ minHeight: svgHeight }}>
          {/* SVG layer for connections */}
          <svg
            className="absolute inset-0 pointer-events-none"
            width="100%"
            height={svgHeight}
            style={{ minWidth: 800 }}
          >
            {/* Translation connections */}
            {translationEdges.map((edge, i) => {
              const sourcePos = nodePositions.get(edge.source);
              const targetPos = nodePositions.get(edge.target);
              if (!sourcePos || !targetPos) return null;

              // Swap if needed so EN is always on left
              const leftPos = sourcePos.col === 'en' ? sourcePos : targetPos;
              const rightPos = sourcePos.col === 'en' ? targetPos : sourcePos;

              return (
                <g key={`trans-${i}`}>
                  <line
                    x1={leftPos.x + 180}
                    y1={leftPos.y + 28}
                    x2={rightPos.x - 10}
                    y2={rightPos.y + 28}
                    stroke={EDGE_COLORS.translates.stroke}
                    strokeWidth={2}
                    strokeDasharray={edge.is_stale ? '4,4' : undefined}
                    opacity={0.6}
                  />
                  {/* Arrow */}
                  <polygon
                    points={`${rightPos.x - 10},${rightPos.y + 28} ${rightPos.x - 18},${rightPos.y + 24} ${rightPos.x - 18},${rightPos.y + 32}`}
                    fill={EDGE_COLORS.translates.stroke}
                    opacity={0.6}
                  />
                </g>
              );
            })}

            {/* EN dependency connections (curved on left side) */}
            {enDependencyEdges.map((edge, i) => {
              const sourcePos = nodePositions.get(edge.source);
              const targetPos = nodePositions.get(edge.target);
              if (!sourcePos || !targetPos) return null;

              const config = EDGE_COLORS[edge.type] || EDGE_COLORS.references;
              const midY = (sourcePos.y + targetPos.y) / 2 + 28;
              const curveX = sourcePos.x - 40 - Math.abs(sourcePos.y - targetPos.y) / 8;

              return (
                <g key={`en-dep-${i}`}>
                  <path
                    d={`M ${sourcePos.x - 10} ${sourcePos.y + 28} Q ${curveX} ${midY} ${targetPos.x - 10} ${targetPos.y + 28}`}
                    fill="none"
                    stroke={config.stroke}
                    strokeWidth={1.5}
                    strokeDasharray={edge.is_stale ? '4,4' : undefined}
                    opacity={0.5}
                  />
                  {/* Arrow */}
                  <circle
                    cx={targetPos.x - 10}
                    cy={targetPos.y + 28}
                    r={3}
                    fill={config.stroke}
                    opacity={0.6}
                  />
                </g>
              );
            })}

            {/* NO dependency connections (curved on right side) */}
            {noDependencyEdges.map((edge, i) => {
              const sourcePos = nodePositions.get(edge.source);
              const targetPos = nodePositions.get(edge.target);
              if (!sourcePos || !targetPos) return null;

              const config = EDGE_COLORS[edge.type] || EDGE_COLORS.references;
              const midY = (sourcePos.y + targetPos.y) / 2 + 28;
              const curveX = sourcePos.x + 210 + Math.abs(sourcePos.y - targetPos.y) / 8;

              return (
                <g key={`no-dep-${i}`}>
                  <path
                    d={`M ${sourcePos.x + 180} ${sourcePos.y + 28} Q ${curveX} ${midY} ${targetPos.x + 180} ${targetPos.y + 28}`}
                    fill="none"
                    stroke={config.stroke}
                    strokeWidth={1.5}
                    strokeDasharray={edge.is_stale ? '4,4' : undefined}
                    opacity={0.5}
                  />
                  {/* Arrow */}
                  <circle
                    cx={targetPos.x + 180}
                    cy={targetPos.y + 28}
                    r={3}
                    fill={config.stroke}
                    opacity={0.6}
                  />
                </g>
              );
            })}
          </svg>

          {/* Document panels */}
          <div className="flex gap-8 p-4" style={{ minWidth: 800 }}>
            {/* English panel */}
            <div className="flex-1 max-w-md">
              <div className="flex items-center gap-2 mb-3 px-2">
                <Languages size={16} className="text-primary" />
                <span className="font-semibold">English</span>
                <span className="badge badge-primary badge-sm">{enNodes.length}</span>
              </div>
              <div className="space-y-2">
                {enNodes.map(node => (
                  <DocumentNode
                    key={node.id}
                    node={node}
                    isSelected={selectedNode === node.id}
                    onClick={() => handleNodeClick(node.id)}
                    hasTranslation={translationPairs.has(node.id)}
                    isDark={isDark}
                  />
                ))}
              </div>
            </div>

            {/* Norwegian panel */}
            <div className="flex-1 max-w-md">
              <div className="flex items-center gap-2 mb-3 px-2">
                <Languages size={16} className="text-secondary" />
                <span className="font-semibold">Norwegian</span>
                <span className="badge badge-secondary badge-sm">{noNodes.length}</span>
              </div>
              <div className="space-y-2">
                {noNodes.map(node => (
                  <DocumentNode
                    key={node.id}
                    node={node}
                    isSelected={selectedNode === node.id}
                    onClick={() => handleNodeClick(node.id)}
                    hasTranslation={translationPairs.has(node.id)}
                    isDark={isDark}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 px-4 py-2 border-t border-base-300 bg-base-200/50 flex-wrap">
        <span className="text-xs text-base-content/60">Legend:</span>
        {Object.entries(EDGE_COLORS)
          .filter(([type]) => enabledEdgeTypes.has(type))
          .map(([type, config]) => (
            <div key={type} className="flex items-center gap-1">
              <span
                className="w-3 h-0.5 rounded"
                style={{ backgroundColor: config.stroke }}
              />
              <span className="text-xs text-base-content/70">{config.label}</span>
            </div>
          ))}
      </div>
    </div>
  );
}

export default LanguagePanelGraph;
