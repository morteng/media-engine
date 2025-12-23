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
import type { HierarchyTreeNode } from '@/api/types';

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
const lifecycleBadges: Record<string, string> = {
  living: 'badge-success',
  snapshot: 'badge-info',
  deprecated: 'badge-warning',
  archived: 'badge-ghost',
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
    <div>
      <div
        className={clsx(
          'flex items-center gap-1 px-2 py-1.5 rounded-lg cursor-pointer transition-colors',
          {
            'bg-primary/20 text-primary': isSelected,
            'ring-2 ring-primary ring-offset-1 ring-offset-base-100': isFocused && !isSelected,
            'text-warning': node.is_stale && !isSelected,
            'hover:bg-base-300': !isSelected,
          }
        )}
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
          className="w-4 h-4 flex items-center justify-center text-base-content/50 hover:text-base-content"
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
          ) : null}
        </button>

        {/* Document Type Icon */}
        <Icon size={14} className={isSelected ? 'text-primary' : 'text-base-content/60'} />

        {/* Title */}
        <span className="flex-1 truncate text-sm">{node.title}</span>

        {/* Status Indicators */}
        <div className="flex items-center gap-1">
          {/* Stale indicator */}
          {node.is_stale && (
            <span className="tooltip tooltip-left" data-tip="Content is stale">
              <AlertTriangle size={12} className="text-warning" />
            </span>
          )}

          {/* Anchors indicator */}
          {node.has_anchors && (
            <span className="tooltip tooltip-left" data-tip="Defines anchors">
              <Anchor size={12} className="text-info" />
            </span>
          )}

          {/* Derivation indicator */}
          {node.derived_from_count > 0 && (
            <span className="tooltip tooltip-left" data-tip={`Derived from ${node.derived_from_count} source(s)`}>
              <GitBranch size={12} className="text-secondary" />
            </span>
          )}

          {/* Lifecycle badge */}
          {node.lifecycle !== 'living' && (
            <span className={`badge badge-xs ${lifecycleBadges[node.lifecycle]}`}>
              {node.lifecycle === 'archived' && <Archive size={10} className="mr-0.5" />}
              {node.lifecycle === 'deprecated' && <Clock size={10} className="mr-0.5" />}
              {node.lifecycle}
            </span>
          )}
        </div>
      </div>

      {/* Children */}
      {hasChildren && isExpanded && (
        <div role="group">
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
      <div className={clsx('flex flex-col items-center justify-center py-12 text-center', className)}>
        <FileText size={32} className="text-base-content/30 mb-2" />
        <p className="font-medium">No hierarchy data available</p>
        <span className="text-sm text-base-content/60">Documents need hierarchy metadata to appear here</span>
      </div>
    );
  }

  return (
    <div className={clsx('flex flex-col', className)}>
      {/* Toolbar */}
      <div className="flex items-center gap-2 p-2 border-b border-base-300">
        <button className="btn btn-ghost btn-xs" onClick={handleExpandAll}>
          Expand All
        </button>
        <button className="btn btn-ghost btn-xs" onClick={handleCollapseAll}>
          Collapse All
        </button>
      </div>

      {/* Tree */}
      <div
        ref={treeRef}
        className="flex-1 overflow-y-auto p-2"
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
        <div className="flex items-center gap-4 p-2 border-t border-base-300 text-xs text-base-content/60">
          <span className="font-medium">Legend:</span>
          <span className="flex items-center gap-1">
            <BookOpen size={12} /> Chapter
          </span>
          <span className="flex items-center gap-1">
            <Settings size={12} /> Operations
          </span>
          <span className="flex items-center gap-1">
            <AlertTriangle size={12} className="text-warning" /> Stale
          </span>
          <span className="flex items-center gap-1">
            <Anchor size={12} /> Anchors
          </span>
          <span className="flex items-center gap-1">
            <GitBranch size={12} /> Derived
          </span>
        </div>
      )}
    </div>
  );
}

export default HierarchyTree;
