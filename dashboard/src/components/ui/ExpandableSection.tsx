import { useState, type ReactNode } from 'react';
import { ChevronDown, ChevronRight, Loader2 } from 'lucide-react';
import clsx from 'clsx';
import { InfoTooltip } from './InfoTooltip';

interface ExpandableSectionProps {
  title: string;
  description?: string;
  icon?: ReactNode;
  tooltip?: { title: string; content: string };
  badge?: ReactNode;
  defaultExpanded?: boolean;
  // Controlled mode props
  isExpanded?: boolean;
  onToggle?: () => void;
  isLoading?: boolean;
  isEmpty?: boolean;
  emptyMessage?: string;
  children: ReactNode;
  className?: string;
  headerClassName?: string;
  // Status indicators
  statusBadge?: 'success' | 'warning' | 'error' | 'info';
  statusCount?: number;
}

export function ExpandableSection({
  title,
  description,
  icon,
  tooltip,
  badge,
  defaultExpanded = false,
  isExpanded: controlledExpanded,
  onToggle,
  isLoading = false,
  isEmpty = false,
  emptyMessage = 'No data available',
  children,
  className,
  headerClassName,
  statusBadge,
  statusCount,
}: ExpandableSectionProps) {
  const [internalExpanded, setInternalExpanded] = useState(defaultExpanded);

  // Support both controlled and uncontrolled modes
  const isControlled = controlledExpanded !== undefined;
  const isExpanded = isControlled ? controlledExpanded : internalExpanded;
  const handleToggle = () => {
    if (onToggle) {
      onToggle();
    } else {
      setInternalExpanded(!internalExpanded);
    }
  };

  const statusColors = {
    success: 'badge-success',
    warning: 'badge-warning',
    error: 'badge-error',
    info: 'badge-info',
  };

  return (
    <div className={clsx('card bg-base-200', className)}>
      <button
        type="button"
        className={clsx(
          'flex items-center justify-between w-full p-4 hover:bg-base-300/50 transition-colors text-left',
          headerClassName
        )}
        onClick={handleToggle}
        aria-expanded={isExpanded}
      >
        <div className="flex items-center gap-3 min-w-0">
          {icon && <span className="flex-shrink-0 text-primary">{icon}</span>}
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-semibold">{title}</h3>
              {tooltip && (
                <InfoTooltip title={tooltip.title} content={tooltip.content} />
              )}
              {badge}
              {statusBadge && statusCount !== undefined && statusCount > 0 && (
                <span className={clsx('badge badge-sm', statusColors[statusBadge])}>
                  {statusCount}
                </span>
              )}
            </div>
            {description && (
              <p className="text-sm text-base-content/60 truncate">{description}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0 ml-2">
          {isLoading && <Loader2 size={16} className="animate-spin text-primary" />}
          {isExpanded ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
        </div>
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 border-t border-base-300">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 size={24} className="animate-spin text-primary" />
            </div>
          ) : isEmpty ? (
            <div className="text-center py-8 text-base-content/60">
              {emptyMessage}
            </div>
          ) : (
            <div className="pt-4">{children}</div>
          )}
        </div>
      )}
    </div>
  );
}

// Utility component for analysis module section in Quality
interface AnalysisModuleProps {
  title: string;
  description: string;
  icon: ReactNode;
  tooltip?: { title: string; content: string };
  available: boolean;
  error?: string;
  reason?: string;
  isLoading?: boolean;
  metrics?: { label: string; value: number | string; status?: 'success' | 'warning' | 'error' }[];
  children: ReactNode;
}

export function AnalysisModule({
  title,
  description,
  icon,
  tooltip,
  available,
  error,
  reason,
  isLoading = false,
  metrics,
  children,
}: AnalysisModuleProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Count issues for badge
  const issueCount = metrics?.filter(m => m.status === 'error' || m.status === 'warning').reduce((sum, m) => {
    const val = typeof m.value === 'number' ? m.value : 0;
    return sum + (m.status && val > 0 ? val : 0);
  }, 0) ?? 0;

  if (!available) {
    return (
      <div className="card bg-base-200">
        <div className="p-4 flex items-center gap-3">
          <span className="text-base-content/30">{icon}</span>
          <div className="flex-1">
            <h3 className="font-semibold text-base-content/50">{title}</h3>
            <p className="text-sm text-base-content/40">{reason || 'Not available'}</p>
          </div>
          <span className="badge badge-ghost">Unavailable</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card bg-base-200 border border-error/30">
        <div className="p-4 flex items-center gap-3">
          <span className="text-error">{icon}</span>
          <div className="flex-1">
            <h3 className="font-semibold">{title}</h3>
            <p className="text-sm text-error">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card bg-base-200">
      <button
        type="button"
        className="flex items-center justify-between w-full p-4 hover:bg-base-300/50 transition-colors text-left"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className="flex-shrink-0 text-primary">{icon}</span>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-semibold">{title}</h3>
              {tooltip && <InfoTooltip title={tooltip.title} content={tooltip.content} />}
              {issueCount > 0 && (
                <span className="badge badge-warning badge-sm">{issueCount} issues</span>
              )}
            </div>
            <p className="text-sm text-base-content/60">{description}</p>
          </div>
        </div>

        {/* Quick metrics preview */}
        {metrics && metrics.length > 0 && !isExpanded && (
          <div className="hidden sm:flex items-center gap-3 mx-4">
            {metrics.slice(0, 3).map((metric, idx) => (
              <div key={idx} className="text-center px-2">
                <div className={clsx(
                  'text-lg font-bold',
                  metric.status === 'error' && 'text-error',
                  metric.status === 'warning' && 'text-warning',
                  metric.status === 'success' && 'text-success',
                )}>
                  {metric.value}
                </div>
                <div className="text-xs text-base-content/50">{metric.label}</div>
              </div>
            ))}
          </div>
        )}

        <div className="flex items-center gap-2 flex-shrink-0">
          {isLoading && <Loader2 size={16} className="animate-spin text-primary" />}
          {isExpanded ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
        </div>
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 border-t border-base-300">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 size={24} className="animate-spin text-primary" />
            </div>
          ) : (
            <div className="pt-4">{children}</div>
          )}
        </div>
      )}
    </div>
  );
}
