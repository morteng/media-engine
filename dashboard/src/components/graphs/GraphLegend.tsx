/**
 * GraphLegend - Legend component for graph visualization
 */

import clsx from 'clsx';

export interface LegendItem {
  label: string;
  color: string;
  type?: 'node' | 'edge';
}

interface GraphLegendProps {
  items: LegendItem[];
  title?: string;
  className?: string;
  compact?: boolean;
}

export function GraphLegend({
  items,
  title,
  className = '',
  compact = false,
}: GraphLegendProps) {
  if (!items.length) return null;

  return (
    <div
      className={clsx(
        'bg-base-300/90 backdrop-blur-sm rounded-lg shadow-lg',
        compact ? 'p-1.5' : 'p-2',
        className
      )}
    >
      {title && (
        <div className="text-xs font-medium text-base-content/60 mb-1.5">
          {title}
        </div>
      )}
      <div className={clsx('flex flex-wrap gap-x-3', compact ? 'gap-y-1' : 'gap-y-2')}>
        {items.map((item, index) => (
          <div key={index} className="flex items-center gap-1.5">
            {item.type === 'edge' ? (
              // Edge indicator (line)
              <div
                className="w-4 h-0.5 rounded-full"
                style={{ backgroundColor: item.color }}
              />
            ) : (
              // Node indicator (circle)
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: item.color }}
              />
            )}
            <span className={clsx('text-base-content/80', compact ? 'text-[10px]' : 'text-xs')}>
              {item.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Predefined legend configurations
export const knowledgeGraphLegend: LegendItem[] = [
  { label: 'Document', color: '#00d4ff' },
  { label: 'Concept', color: '#a855f7' },
  { label: 'Orphan', color: '#f59e0b' },
  { label: 'Hub', color: '#22c55e' },
];

export const dependencyGraphLegend: LegendItem[] = [
  { label: 'Fresh', color: '#22c55e' },
  { label: 'Stale', color: '#ef4444' },
  { label: 'Dependencies', color: '#3b82f6', type: 'edge' },
];

export const hierarchyGraphLegend: LegendItem[] = [
  { label: 'Chapter', color: '#00d4ff' },
  { label: 'Reference', color: '#8b5cf6' },
  { label: 'Stale', color: '#ef4444' },
  { label: 'Implements', color: '#22c55e', type: 'edge' },
  { label: 'Derives From', color: '#3b82f6', type: 'edge' },
];

export default GraphLegend;
