/**
 * GraphToolbar - Controls for graph visualization
 */

import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  Box,
  Grid3X3,
  Circle,
  GitBranch,
  Sun,
} from 'lucide-react';
import clsx from 'clsx';

interface GraphToolbarProps {
  onZoomIn?: () => void;
  onZoomOut?: () => void;
  onResetView?: () => void;
  onToggle3D?: () => void;
  onLayoutChange?: (layout: string) => void;
  is3D?: boolean;
  currentLayout?: string;
  className?: string;
}

const layouts = [
  { id: 'forceDirected2d', label: 'Force', icon: Grid3X3 },
  { id: 'circular2d', label: 'Circular', icon: Circle },
  { id: 'hierarchicalTd', label: 'Tree', icon: GitBranch },
  { id: 'radialOut2d', label: 'Radial', icon: Sun },
];

export function GraphToolbar({
  onZoomIn,
  onZoomOut,
  onResetView,
  onToggle3D,
  onLayoutChange,
  is3D = false,
  currentLayout = 'forceDirected2d',
  className = '',
}: GraphToolbarProps) {
  return (
    <div
      className={clsx(
        'flex items-center gap-1 p-1 bg-base-300/90 backdrop-blur-sm rounded-lg shadow-lg',
        className
      )}
    >
      {/* Zoom controls */}
      <div className="flex items-center gap-0.5 border-r border-base-content/10 pr-1 mr-1">
        <button
          className="btn btn-ghost btn-xs btn-square"
          onClick={onZoomIn}
          title="Zoom in"
        >
          <ZoomIn size={14} />
        </button>
        <button
          className="btn btn-ghost btn-xs btn-square"
          onClick={onZoomOut}
          title="Zoom out"
        >
          <ZoomOut size={14} />
        </button>
        <button
          className="btn btn-ghost btn-xs btn-square"
          onClick={onResetView}
          title="Reset view"
        >
          <Maximize2 size={14} />
        </button>
      </div>

      {/* Layout selector */}
      <div className="flex items-center gap-0.5 border-r border-base-content/10 pr-1 mr-1">
        {layouts.map((layout) => {
          const Icon = layout.icon;
          const isActive = currentLayout === layout.id;
          return (
            <button
              key={layout.id}
              className={clsx(
                'btn btn-xs btn-square',
                isActive ? 'btn-primary' : 'btn-ghost'
              )}
              onClick={() => onLayoutChange?.(layout.id)}
              title={layout.label}
            >
              <Icon size={14} />
            </button>
          );
        })}
      </div>

      {/* 3D toggle */}
      <button
        className={clsx(
          'btn btn-xs btn-square',
          is3D ? 'btn-primary' : 'btn-ghost'
        )}
        onClick={onToggle3D}
        title={is3D ? 'Switch to 2D' : 'Switch to 3D'}
      >
        <Box size={14} />
      </button>
    </div>
  );
}

export default GraphToolbar;
