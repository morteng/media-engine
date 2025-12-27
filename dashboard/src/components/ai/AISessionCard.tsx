import { CheckCircle, PauseCircle, XCircle, Play, ChevronRight } from 'lucide-react';
import clsx from 'clsx';

export interface AISession {
  id: string;
  task_id: string;
  status: 'active' | 'paused' | 'completed' | 'failed';
  started_at: string;
  last_active?: string;
  completed_at?: string;
  progress: {
    total_steps: number;
    completed_steps: number;
    current_step?: string;
  };
  changes: Array<{
    type: string;
    path: string;
    description: string;
    timestamp: string;
  }>;
}

interface AISessionCardProps {
  session: AISession;
  compact?: boolean;
  onResume?: (sessionId: string) => void;
  onClick?: (sessionId: string) => void;
}

const statusConfig = {
  active: { icon: Play, color: 'text-success', badge: 'badge-success', label: 'Active' },
  paused: { icon: PauseCircle, color: 'text-warning', badge: 'badge-warning', label: 'Paused' },
  completed: { icon: CheckCircle, color: 'text-success', badge: 'badge-success', label: 'Complete' },
  failed: { icon: XCircle, color: 'text-error', badge: 'badge-error', label: 'Failed' },
};

export function AISessionCard({ session, compact = false, onResume, onClick }: AISessionCardProps) {
  const config = statusConfig[session.status];
  const StatusIcon = config.icon;
  const progressPercent = session.progress.total_steps > 0
    ? Math.round((session.progress.completed_steps / session.progress.total_steps) * 100)
    : 0;

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
      <button
        className="flex items-center gap-3 p-3 w-full text-left rounded-lg bg-base-200 hover:bg-base-300 transition-colors group"
        onClick={() => onClick?.(session.id)}
      >
        <StatusIcon size={18} className={config.color} />
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm truncate">{session.task_id}</p>
          <p className="text-xs text-base-content/60">
            {progressPercent}% &bull; {timeAgo(session.last_active || session.started_at)}
          </p>
        </div>
        <ChevronRight size={16} className="text-base-content/40 group-hover:text-base-content" />
      </button>
    );
  }

  return (
    <div className="card bg-base-200 shadow-sm">
      <div className="card-body p-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-3">
            <div className={clsx('p-2 rounded-lg bg-base-300', config.color)}>
              <StatusIcon size={20} />
            </div>
            <div>
              <h4 className="font-semibold">{session.task_id}</h4>
              <p className="text-xs text-base-content/60">
                Started {timeAgo(session.started_at)}
              </p>
            </div>
          </div>
          <span className={clsx('badge badge-sm', config.badge)}>{config.label}</span>
        </div>

        {/* Progress */}
        <div className="mt-4">
          <div className="flex justify-between text-sm mb-1">
            <span className="text-base-content/70">Progress</span>
            <span className="font-mono">
              {session.progress.completed_steps}/{session.progress.total_steps}
            </span>
          </div>
          <progress
            className={clsx('progress w-full', {
              'progress-success': session.status === 'completed',
              'progress-primary': session.status === 'active',
              'progress-warning': session.status === 'paused',
              'progress-error': session.status === 'failed',
            })}
            value={progressPercent}
            max={100}
          />
          {session.progress.current_step && session.status === 'active' && (
            <p className="text-xs text-base-content/60 mt-1 truncate">
              {session.progress.current_step}
            </p>
          )}
        </div>

        {/* Recent changes */}
        {session.changes.length > 0 && (
          <div className="mt-4">
            <h5 className="text-xs font-medium text-base-content/70 mb-2">Recent Changes</h5>
            <div className="space-y-1">
              {session.changes.slice(-3).map((change, idx) => (
                <div key={idx} className="flex items-center gap-2 text-xs">
                  <span className="badge badge-xs badge-ghost">{change.type}</span>
                  <span className="truncate flex-1">{change.description}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        {session.status === 'paused' && onResume && (
          <div className="card-actions justify-end mt-4">
            <button
              className="btn btn-primary btn-sm gap-1"
              onClick={() => onResume(session.id)}
            >
              <Play size={14} />
              Resume
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
