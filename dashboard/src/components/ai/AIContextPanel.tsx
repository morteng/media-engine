import {
  Book,
  FileText,
  Clock,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  Sparkles,
  RefreshCw,
} from 'lucide-react';

export interface AIContextData {
  project: {
    name: string;
    languages: string[];
    document_count: number;
  };
  publications: {
    total: number;
    valid: number;
    stale: number;
  };
  active_session?: {
    id: string;
    task_id: string;
    progress: number;
  };
  pending_tasks: number;
  unresolved_notes: number;
  stale_research: number;
  recent_decisions: number;
  health_score: number;
  last_refresh: string;
}

interface AIContextPanelProps {
  context: AIContextData;
  compact?: boolean;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export function AIContextPanel({
  context,
  compact = false,
  onRefresh,
  isRefreshing = false,
}: AIContextPanelProps) {
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

  if (compact) {
    return (
      <div className="bg-base-200 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold flex items-center gap-2">
            <Sparkles size={16} className="text-primary" />
            AI Context
          </h3>
          {onRefresh && (
            <button
              className="btn btn-ghost btn-xs btn-square"
              onClick={onRefresh}
              disabled={isRefreshing}
            >
              <RefreshCw size={14} className={isRefreshing ? 'animate-spin' : ''} />
            </button>
          )}
        </div>

        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="flex items-center gap-2">
            <Book size={14} className="text-base-content/60" />
            <span>{context.publications.total} publications</span>
          </div>
          <div className="flex items-center gap-2">
            <FileText size={14} className="text-base-content/60" />
            <span>{context.project.document_count} docs</span>
          </div>
          {context.pending_tasks > 0 && (
            <div className="flex items-center gap-2 text-warning">
              <Clock size={14} />
              <span>{context.pending_tasks} tasks</span>
            </div>
          )}
          {context.unresolved_notes > 0 && (
            <div className="flex items-center gap-2 text-warning">
              <AlertTriangle size={14} />
              <span>{context.unresolved_notes} notes</span>
            </div>
          )}
        </div>

        {context.active_session && (
          <div className="mt-3 pt-3 border-t border-base-300">
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-base-content/70">Active Session</span>
              <span className="font-mono">{context.active_session.progress}%</span>
            </div>
            <progress
              className="progress progress-primary w-full h-2"
              value={context.active_session.progress}
              max={100}
            />
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="card bg-base-200 shadow-sm">
      <div className="card-body p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold flex items-center gap-2">
              <Sparkles size={24} className="text-primary" />
              AI Context
            </h2>
            <p className="text-sm text-base-content/60 mt-1">
              {context.project.name} • Updated {timeAgo(context.last_refresh)}
            </p>
          </div>
          {onRefresh && (
            <button
              className="btn btn-ghost btn-sm gap-1"
              onClick={onRefresh}
              disabled={isRefreshing}
            >
              <RefreshCw size={14} className={isRefreshing ? 'animate-spin' : ''} />
              Refresh
            </button>
          )}
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center p-3 bg-base-300 rounded-lg">
            <Book size={24} className="mx-auto text-primary mb-1" />
            <div className="text-2xl font-bold">{context.publications.total}</div>
            <div className="text-xs text-base-content/60">Publications</div>
          </div>
          <div className="text-center p-3 bg-base-300 rounded-lg">
            <FileText size={24} className="mx-auto text-info mb-1" />
            <div className="text-2xl font-bold">{context.project.document_count}</div>
            <div className="text-xs text-base-content/60">Documents</div>
          </div>
          <div className="text-center p-3 bg-base-300 rounded-lg">
            <TrendingUp size={24} className="mx-auto text-success mb-1" />
            <div className="text-2xl font-bold">{context.health_score}%</div>
            <div className="text-xs text-base-content/60">Health Score</div>
          </div>
          <div className="text-center p-3 bg-base-300 rounded-lg">
            <CheckCircle size={24} className="mx-auto text-success mb-1" />
            <div className="text-2xl font-bold">{context.recent_decisions}</div>
            <div className="text-xs text-base-content/60">Decisions</div>
          </div>
        </div>

        {/* Status indicators */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className={`flex items-center gap-3 p-3 rounded-lg ${
            context.pending_tasks > 0 ? 'bg-warning/10' : 'bg-base-300'
          }`}>
            <Clock size={18} className={context.pending_tasks > 0 ? 'text-warning' : 'text-base-content/60'} />
            <div>
              <p className="font-medium">{context.pending_tasks} Pending Tasks</p>
              <p className="text-xs text-base-content/60">Awaiting processing</p>
            </div>
          </div>

          <div className={`flex items-center gap-3 p-3 rounded-lg ${
            context.unresolved_notes > 0 ? 'bg-warning/10' : 'bg-base-300'
          }`}>
            <AlertTriangle size={18} className={context.unresolved_notes > 0 ? 'text-warning' : 'text-base-content/60'} />
            <div>
              <p className="font-medium">{context.unresolved_notes} Unresolved Notes</p>
              <p className="text-xs text-base-content/60">Need attention</p>
            </div>
          </div>

          <div className={`flex items-center gap-3 p-3 rounded-lg ${
            context.stale_research > 0 ? 'bg-warning/10' : 'bg-base-300'
          }`}>
            <RefreshCw size={18} className={context.stale_research > 0 ? 'text-warning' : 'text-base-content/60'} />
            <div>
              <p className="font-medium">{context.stale_research} Stale Research</p>
              <p className="text-xs text-base-content/60">May need refresh</p>
            </div>
          </div>
        </div>

        {/* Active session */}
        {context.active_session && (
          <div className="mt-6 pt-6 border-t border-base-300">
            <h3 className="font-semibold mb-3">Active Session</h3>
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <p className="font-medium">{context.active_session.task_id}</p>
                <progress
                  className="progress progress-primary w-full mt-2"
                  value={context.active_session.progress}
                  max={100}
                />
              </div>
              <div className="text-right">
                <span className="text-2xl font-bold">{context.active_session.progress}%</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
