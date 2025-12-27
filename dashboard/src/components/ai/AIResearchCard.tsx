import { BookOpen, Clock, Tag, ChevronRight, RefreshCw } from 'lucide-react';
import clsx from 'clsx';

export interface AIResearchEntry {
  key: string;
  value: unknown;
  context?: string;
  tags: string[];
  created_at: string;
  updated_at: string;
  is_stale: boolean;
  confidence?: number;
}

interface AIResearchCardProps {
  entry: AIResearchEntry;
  compact?: boolean;
  onRefresh?: (key: string) => void;
  onClick?: (key: string) => void;
}

export function AIResearchCard({ entry, compact = false, onRefresh, onClick }: AIResearchCardProps) {
  const timeAgo = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${Math.floor(diffHours / 24)}d ago`;
  };

  // Format the value for display
  const formatValue = (value: unknown): string => {
    if (typeof value === 'string') return value;
    if (typeof value === 'number') return value.toString();
    if (typeof value === 'boolean') return value ? 'Yes' : 'No';
    if (Array.isArray(value)) return value.join(', ');
    if (typeof value === 'object' && value !== null) {
      return JSON.stringify(value, null, 2);
    }
    return String(value);
  };

  if (compact) {
    return (
      <div
        className={clsx(
          'flex items-center gap-3 p-3 rounded-lg bg-base-200 group',
          { 'border-l-2 border-warning': entry.is_stale },
          onClick && 'cursor-pointer hover:bg-base-300 transition-colors'
        )}
        onClick={() => onClick?.(entry.key)}
      >
        <BookOpen size={16} className="text-primary flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm truncate">{entry.key}</p>
          <p className="text-xs text-base-content/60 truncate">
            {formatValue(entry.value).slice(0, 50)}
            {formatValue(entry.value).length > 50 && '...'}
          </p>
        </div>
        {entry.is_stale && (
          <span className="badge badge-xs badge-warning">Stale</span>
        )}
        <ChevronRight size={16} className="text-base-content/40 group-hover:text-base-content" />
      </div>
    );
  }

  return (
    <div className={clsx(
      'card bg-base-200 shadow-sm',
      { 'border-l-4 border-warning': entry.is_stale }
    )}>
      <div className="card-body p-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <BookOpen size={18} className="text-primary" />
            <h4 className="font-semibold">{entry.key}</h4>
          </div>
          {entry.is_stale ? (
            <span className="badge badge-warning gap-1">
              <Clock size={10} />
              Stale
            </span>
          ) : entry.confidence !== undefined && (
            <span className={clsx('badge badge-sm', {
              'badge-success': entry.confidence >= 0.8,
              'badge-warning': entry.confidence >= 0.5 && entry.confidence < 0.8,
              'badge-error': entry.confidence < 0.5,
            })}>
              {Math.round(entry.confidence * 100)}% confidence
            </span>
          )}
        </div>

        {/* Value */}
        <div className="mt-2 p-3 bg-base-300 rounded text-sm font-mono overflow-x-auto">
          <pre className="whitespace-pre-wrap">{formatValue(entry.value)}</pre>
        </div>

        {/* Context */}
        {entry.context && (
          <p className="text-sm text-base-content/70 mt-2">{entry.context}</p>
        )}

        {/* Tags */}
        {entry.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {entry.tags.map((tag) => (
              <span key={tag} className="badge badge-xs badge-ghost gap-1">
                <Tag size={10} />
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between mt-3 pt-3 border-t border-base-300">
          <span className="text-xs text-base-content/50">
            Updated {timeAgo(entry.updated_at)}
          </span>
          {entry.is_stale && onRefresh && (
            <button
              className="btn btn-ghost btn-xs gap-1"
              onClick={() => onRefresh(entry.key)}
            >
              <RefreshCw size={12} />
              Refresh
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
