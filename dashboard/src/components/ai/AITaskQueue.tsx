import { useState } from 'react';
import {
  ListTodo,
  Play,
  Clock,
  CheckCircle,
  AlertCircle,
  ChevronRight,
  User,
  Sparkles,
} from 'lucide-react';
import clsx from 'clsx';

export interface AITask {
  id: string;
  type: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'pending' | 'claimed' | 'in_progress' | 'completed' | 'failed';
  created_at: string;
  claimed_by?: string;
  claimed_at?: string;
  completed_at?: string;
  document_path?: string;
  context?: Record<string, unknown>;
}

const priorityConfig = {
  critical: { color: 'text-error', badge: 'badge-error', label: 'Critical' },
  high: { color: 'text-warning', badge: 'badge-warning', label: 'High' },
  medium: { color: 'text-info', badge: 'badge-info', label: 'Medium' },
  low: { color: 'text-base-content/60', badge: 'badge-ghost', label: 'Low' },
};

const statusConfig = {
  pending: { icon: Clock, color: 'text-base-content/60', label: 'Pending' },
  claimed: { icon: User, color: 'text-info', label: 'Claimed' },
  in_progress: { icon: Play, color: 'text-primary', label: 'In Progress' },
  completed: { icon: CheckCircle, color: 'text-success', label: 'Complete' },
  failed: { icon: AlertCircle, color: 'text-error', label: 'Failed' },
};

interface AITaskCardProps {
  task: AITask;
  onClaim?: (taskId: string) => void;
  onClick?: (taskId: string) => void;
}

function AITaskCard({ task, onClaim, onClick }: AITaskCardProps) {
  const priority = priorityConfig[task.priority];
  const status = statusConfig[task.status];
  const StatusIcon = status.icon;

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

  return (
    <div
      className={clsx(
        'flex items-start gap-3 p-3 rounded-lg bg-base-200 group',
        onClick && 'cursor-pointer hover:bg-base-300 transition-colors'
      )}
      onClick={() => onClick?.(task.id)}
    >
      <StatusIcon size={18} className={clsx('flex-shrink-0 mt-0.5', status.color)} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className={clsx('badge badge-xs', priority.badge)}>{priority.label}</span>
          <span className="badge badge-xs badge-ghost">{task.type}</span>
        </div>
        <p className="text-sm font-medium">{task.description}</p>
        <p className="text-xs text-base-content/50 mt-1">
          {timeAgo(task.created_at)}
          {task.document_path && ` • ${task.document_path.split('/').pop()}`}
        </p>
      </div>
      {task.status === 'pending' && onClaim && (
        <button
          className="btn btn-primary btn-xs opacity-0 group-hover:opacity-100 transition-opacity"
          onClick={(e) => {
            e.stopPropagation();
            onClaim(task.id);
          }}
        >
          <Sparkles size={12} />
          Claim
        </button>
      )}
      {onClick && (
        <ChevronRight size={16} className="text-base-content/40 group-hover:text-base-content" />
      )}
    </div>
  );
}

interface AITaskQueueProps {
  tasks: AITask[];
  showCompleted?: boolean;
  maxItems?: number;
  onClaim?: (taskId: string) => void;
  onClick?: (taskId: string) => void;
}

export function AITaskQueue({
  tasks,
  showCompleted = false,
  maxItems,
  onClaim,
  onClick,
}: AITaskQueueProps) {
  const [showDone, setShowDone] = useState(showCompleted);

  // Filter tasks
  let filteredTasks = tasks;
  if (!showDone) {
    filteredTasks = filteredTasks.filter((t) => t.status !== 'completed');
  }

  // Sort by priority and status
  const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
  const statusOrder = { pending: 0, claimed: 1, in_progress: 2, failed: 3, completed: 4 };
  filteredTasks = [...filteredTasks].sort((a, b) => {
    const statusDiff = statusOrder[a.status] - statusOrder[b.status];
    if (statusDiff !== 0) return statusDiff;
    return priorityOrder[a.priority] - priorityOrder[b.priority];
  });

  const displayTasks = maxItems ? filteredTasks.slice(0, maxItems) : filteredTasks;
  const hasMore = maxItems && filteredTasks.length > maxItems;

  if (tasks.length === 0) {
    return (
      <div className="text-center py-8">
        <ListTodo size={32} className="mx-auto text-base-content/30 mb-3" />
        <p className="text-base-content/60">No tasks in queue</p>
        <p className="text-sm text-base-content/40 mt-1">
          Tasks are added when Claude identifies work to be done
        </p>
      </div>
    );
  }

  // Group by status
  const pending = displayTasks.filter((t) => t.status === 'pending');
  const inProgress = displayTasks.filter((t) => ['claimed', 'in_progress'].includes(t.status));
  const done = displayTasks.filter((t) => ['completed', 'failed'].includes(t.status));

  return (
    <div className="space-y-4">
      {/* Toggle */}
      <div className="flex justify-end">
        <label className="label cursor-pointer gap-2">
          <input
            type="checkbox"
            className="checkbox checkbox-xs"
            checked={showDone}
            onChange={(e) => setShowDone(e.target.checked)}
          />
          <span className="label-text text-xs">Show completed</span>
        </label>
      </div>

      {/* In Progress */}
      {inProgress.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-base-content/70 uppercase tracking-wide mb-2">
            In Progress ({inProgress.length})
          </h4>
          <div className="space-y-2">
            {inProgress.map((task) => (
              <AITaskCard key={task.id} task={task} onClaim={onClaim} onClick={onClick} />
            ))}
          </div>
        </div>
      )}

      {/* Pending */}
      {pending.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-base-content/70 uppercase tracking-wide mb-2">
            Pending ({pending.length})
          </h4>
          <div className="space-y-2">
            {pending.map((task) => (
              <AITaskCard key={task.id} task={task} onClaim={onClaim} onClick={onClick} />
            ))}
          </div>
        </div>
      )}

      {/* Completed */}
      {showDone && done.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-base-content/70 uppercase tracking-wide mb-2">
            Completed ({done.length})
          </h4>
          <div className="space-y-2 opacity-60">
            {done.map((task) => (
              <AITaskCard key={task.id} task={task} onClick={onClick} />
            ))}
          </div>
        </div>
      )}

      {filteredTasks.length === 0 && (
        <div className="text-center py-6 text-base-content/60 text-sm">
          No {showDone ? '' : 'pending '}tasks
        </div>
      )}

      {hasMore && (
        <div className="text-center">
          <button className="btn btn-ghost btn-sm">
            View all {filteredTasks.length} tasks
          </button>
        </div>
      )}
    </div>
  );
}
