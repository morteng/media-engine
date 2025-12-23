import { useState, useCallback, useRef, useEffect } from 'react';
import {
  ChevronRight,
  ChevronDown,
  FileText,
  BookOpen,
  Settings,
  HelpCircle,
  Lightbulb,
  BookMarked,
  AlertTriangle,
  Anchor,
  GitBranch,
  Archive,
  Clock,
} from 'lucide-react';
import clsx from 'clsx';
import { Badge } from '@/components/ui/Badge';
import type { HierarchyTreeNode } from '@/api/types';
import './HierarchyTree.css';

// Icons for document types
const docTypeIcons: Record<string, typeof FileText> = {
  chapter: BookOpen,
  operations: Settings,
  reference: FileText,
  tutorial: BookMarked,
  concept: Lightbulb,
  guide: HelpCircle,
};

// Colors for lifecycle states
const lifecycleColors: Record<string, string> = {
  living: 'success',
  snapshot: 'info',
  deprecated: 'warning',
  archived: 'default',
};

interface TreeNodeProps {
  node: HierarchyTreeNode;
  level: number;
  isExpanded: boolean;
  isSelected: boolean;
  isFocused: boolean;
  expandedNodes: Set<string>;
  onToggle: (path: string) => void;
  onSelect: (path: string) => void;
  onFocus: (path: string) => void;
}

function TreeNode({
  node,
  level,
  isExpanded,
  isSelected,
  isFocused,
  expandedNodes,
  onToggle,
  onSelect,
  onFocus,
}: TreeNodeProps) {
  const Icon = docTypeIcons[node.doc_type] || FileText;
  const hasChildren = node.children && node.children.length > 0;

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onSelect(node.path);
  };

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (hasChildren) {
      onToggle(node.path);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onSelect(node.path);
    } else if (e.key === 'ArrowRight' && hasChildren && !isExpanded) {
      e.preventDefault();
      onToggle(node.path);
    } else if (e.key === 'ArrowLeft' && hasChildren && isExpanded) {
      e.preventDefault();
      onToggle(node.path);
    }
  };

  return (
    <div className="tree-node-container">
      <div
        className={clsx('tree-node', {
          'tree-node-selected': isSelected,
          'tree-node-focused': isFocused,
          'tree-node-stale': node.is_stale,
        })}
        style={{ paddingLeft: `${level * 16 + 8}px` }}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        onFocus={() => onFocus(node.path)}
        tabIndex={0}
        role="treeitem"
        aria-expanded={hasChildren ? isExpanded : undefined}
        aria-selected={isSelected}
      >
        {/* Expand/Collapse Button */}
        <button
          className="tree-toggle"
          onClick={handleToggle}
          aria-label={isExpanded ? 'Collapse' : 'Expand'}
          disabled={!hasChildren}
        >
          {hasChildren ? (
            isExpanded ? (
              <ChevronDown size={14} />
            ) : (
              <ChevronRight size={14} />
            )
          ) : (
            <span className="tree-toggle-placeholder" />
          )}
        </button>

        {/* Document Type Icon */}
        <Icon size={14} className={`tree-icon tree-icon-${node.doc_type}`} />

        {/* Title */}
        <span className="tree-title">{node.title}</span>

        {/* Status Indicators */}
        <div className="tree-indicators">
          {/* Stale indicator */}
          {node.is_stale && (
            <span className="tree-indicator stale" title="Content is stale">
              <AlertTriangle size={12} />
            </span>
          )}

          {/* Anchors indicator */}
          {node.has_anchors && (
            <span className="tree-indicator anchors" title="Defines anchors">
              <Anchor size={12} />
            </span>
          )}

          {/* Derivation indicator */}
          {node.derived_from_count > 0 && (
            <span className="tree-indicator derived" title={`Derived from ${node.derived_from_count} source(s)`}>
              <GitBranch size={12} />
            </span>
          )}

          {/* Lifecycle badge */}
          {node.lifecycle !== 'living' && (
            <Badge
              variant={lifecycleColors[node.lifecycle] as 'success' | 'info' | 'warning' | 'default'}
              size="sm"
            >
              {node.lifecycle === 'archived' && <Archive size={10} />}
              {node.lifecycle === 'deprecated' && <Clock size={10} />}
              {node.lifecycle}
            </Badge>
          )}
        </div>
      </div>

      {/* Children */}
      {hasChildren && isExpanded && (
        <div className="tree-children" role="group">
          {node.children.map((child) => (
            <TreeNode
              key={child.path}
              node={child}
              level={level + 1}
              isExpanded={expandedNodes.has(child.path)}
              isSelected={false}
              isFocused={false}
              expandedNodes={expandedNodes}
              onToggle={onToggle}
              onSelect={onSelect}
              onFocus={onFocus}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface HierarchyTreeProps {
  nodes: HierarchyTreeNode[];
  selectedPath?: string;
  onSelect?: (path: string) => void;
  className?: string;
  showLegend?: boolean;
}

export function HierarchyTree({
  nodes,
  selectedPath,
  onSelect,
  className,
  showLegend = true,
}: HierarchyTreeProps) {
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(() => {
    // Start with all root nodes expanded
    const initial = new Set<string>();
    nodes.forEach((node) => initial.add(node.path));
    return initial;
  });
  const [focusedPath, setFocusedPath] = useState<string | null>(null);
  const treeRef = useRef<HTMLDivElement>(null);

  // Expand all ancestors of selected path when it changes
  useEffect(() => {
    if (selectedPath) {
      const pathsToExpand = new Set(expandedNodes);
      // Find and expand ancestors
      const findAndExpand = (nodeList: HierarchyTreeNode[], path: string, ancestors: string[] = []): boolean => {
        for (const node of nodeList) {
          if (node.path === path) {
            ancestors.forEach((a) => pathsToExpand.add(a));
            return true;
          }
          if (node.children && node.children.length > 0) {
            if (findAndExpand(node.children, path, [...ancestors, node.path])) {
              return true;
            }
          }
        }
        return false;
      };
      findAndExpand(nodes, selectedPath);
      setExpandedNodes(pathsToExpand);
    }
  }, [selectedPath, nodes]);

  const handleToggle = useCallback((path: string) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  }, []);

  const handleSelect = useCallback(
    (path: string) => {
      onSelect?.(path);
    },
    [onSelect]
  );

  const handleExpandAll = () => {
    const allPaths = new Set<string>();
    const collectPaths = (nodeList: HierarchyTreeNode[]) => {
      nodeList.forEach((node) => {
        allPaths.add(node.path);
        if (node.children) {
          collectPaths(node.children);
        }
      });
    };
    collectPaths(nodes);
    setExpandedNodes(allPaths);
  };

  const handleCollapseAll = () => {
    setExpandedNodes(new Set());
  };

  // Keyboard navigation
  const getAllVisiblePaths = useCallback((): string[] => {
    const paths: string[] = [];
    const traverse = (nodeList: HierarchyTreeNode[]) => {
      nodeList.forEach((node) => {
        paths.push(node.path);
        if (node.children && expandedNodes.has(node.path)) {
          traverse(node.children);
        }
      });
    };
    traverse(nodes);
    return paths;
  }, [nodes, expandedNodes]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    const visiblePaths = getAllVisiblePaths();
    const currentIndex = focusedPath ? visiblePaths.indexOf(focusedPath) : -1;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      const nextIndex = Math.min(currentIndex + 1, visiblePaths.length - 1);
      setFocusedPath(visiblePaths[nextIndex]);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      const prevIndex = Math.max(currentIndex - 1, 0);
      setFocusedPath(visiblePaths[prevIndex]);
    } else if (e.key === 'Home') {
      e.preventDefault();
      setFocusedPath(visiblePaths[0]);
    } else if (e.key === 'End') {
      e.preventDefault();
      setFocusedPath(visiblePaths[visiblePaths.length - 1]);
    }
  };

  if (!nodes || nodes.length === 0) {
    return (
      <div className={clsx('hierarchy-tree-empty', className)}>
        <FileText size={32} />
        <p>No hierarchy data available</p>
        <span className="text-muted">Documents need hierarchy metadata to appear here</span>
      </div>
    );
  }

  return (
    <div className={clsx('hierarchy-tree', className)}>
      {/* Toolbar */}
      <div className="hierarchy-tree-toolbar">
        <button className="tree-toolbar-btn" onClick={handleExpandAll} title="Expand all">
          Expand All
        </button>
        <button className="tree-toolbar-btn" onClick={handleCollapseAll} title="Collapse all">
          Collapse All
        </button>
      </div>

      {/* Tree */}
      <div
        ref={treeRef}
        className="hierarchy-tree-content"
        role="tree"
        onKeyDown={handleKeyDown}
        aria-label="Document hierarchy"
      >
        {nodes.map((node) => (
          <TreeNode
            key={node.path}
            node={node}
            level={0}
            isExpanded={expandedNodes.has(node.path)}
            isSelected={selectedPath === node.path}
            isFocused={focusedPath === node.path}
            expandedNodes={expandedNodes}
            onToggle={handleToggle}
            onSelect={handleSelect}
            onFocus={setFocusedPath}
          />
        ))}
      </div>

      {/* Legend */}
      {showLegend && (
        <div className="hierarchy-tree-legend">
          <span className="legend-title">Legend:</span>
          <div className="legend-items">
            <span className="legend-item">
              <BookOpen size={12} /> Chapter
            </span>
            <span className="legend-item">
              <Settings size={12} /> Operations
            </span>
            <span className="legend-item">
              <AlertTriangle size={12} className="text-warning" /> Stale
            </span>
            <span className="legend-item">
              <Anchor size={12} /> Anchors
            </span>
            <span className="legend-item">
              <GitBranch size={12} /> Derived
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

export default HierarchyTree;
