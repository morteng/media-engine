import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bot, Sparkles, Clock, CheckCircle, AlertCircle, ChevronRight, X } from 'lucide-react';
import clsx from 'clsx';
import { useAITasks, useAIQueueStats } from '@/hooks/useAI';

interface AgentActivityPanelProps {
  variant?: 'compact' | 'full';
}

/**
 * Compact indicator showing AI agent activity status.
 * Displays in the header to provide visibility into active sessions and pending tasks.
 */
export function AgentActivityPanel({ variant = 'compact' }: AgentActivityPanelProps) {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  const { data: tasksData } = useAITasks('pending', 10000);
  const { data: statsData } = useAIQueueStats();

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close on escape
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  const stats = statsData || { pending: 0, in_progress: 0, completed_today: 0 };
  const tasks = tasksData?.tasks || [];
  const hasActivity = stats.pending > 0 || stats.in_progress > 0;
  const isProcessing = stats.in_progress > 0;

  const handleOpenWorkspace = () => {
    setIsOpen(false);
    navigate('/ai-assist');
  };

  if (variant === 'compact') {
    return (
      <div className="relative" ref={panelRef}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={clsx(
            'flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors',
            'hover:bg-base-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary',
            {
              'bg-primary/10 text-primary': isProcessing,
              'text-base-content/70': !isProcessing,
            }
          )}
          aria-label={`AI Agent status: ${stats.in_progress} active, ${stats.pending} pending`}
          aria-expanded={isOpen}
          aria-haspopup="true"
        >
          <Bot
            size={18}
            className={clsx({
              'animate-pulse': isProcessing,
            })}
            aria-hidden="true"
          />
          {hasActivity && (
            <span className="text-sm font-medium">
              {stats.in_progress > 0 ? (
                <span className="flex items-center gap-1">
                  <Sparkles size={12} className="animate-spin" aria-hidden="true" />
                  {stats.in_progress}
                </span>
              ) : (
                stats.pending
              )}
            </span>
          )}
          {stats.pending > 0 && stats.in_progress === 0 && (
            <span className="absolute -top-1 -right-1 w-2 h-2 bg-warning rounded-full" aria-hidden="true" />
          )}
        </button>

        {/* Dropdown panel */}
        {isOpen && (
          <div
            className="absolute right-0 top-full mt-2 w-80 bg-base-200 rounded-lg shadow-xl border border-base-300 z-50"
            role="dialog"
            aria-label="Agent activity details"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-base-300">
              <h3 className="font-semibold text-sm">AI Agent Activity</h3>
              <button
                onClick={() => setIsOpen(false)}
                className="btn btn-ghost btn-xs btn-square"
                aria-label="Close panel"
              >
                <X size={14} aria-hidden="true" />
              </button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-2 p-3 border-b border-base-300">
              <div className="text-center">
                <div className={clsx('text-lg font-bold', { 'text-primary': stats.in_progress > 0 })}>
                  {stats.in_progress}
                </div>
                <div className="text-xs text-base-content/60">Active</div>
              </div>
              <div className="text-center">
                <div className={clsx('text-lg font-bold', { 'text-warning': stats.pending > 0 })}>
                  {stats.pending}
                </div>
                <div className="text-xs text-base-content/60">Pending</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-success">{stats.completed_today}</div>
                <div className="text-xs text-base-content/60">Today</div>
              </div>
            </div>

            {/* Recent tasks */}
            <div className="p-3 max-h-64 overflow-y-auto">
              {tasks.length === 0 ? (
                <div className="text-center py-4 text-base-content/60">
                  <CheckCircle size={24} className="mx-auto mb-2 text-success" aria-hidden="true" />
                  <p className="text-sm">No pending tasks</p>
                </div>
              ) : (
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold text-base-content/70 uppercase tracking-wide">
                    Pending Tasks
                  </h4>
                  {tasks.slice(0, 5).map((task) => (
                    <TaskItem key={task.id} task={task} />
                  ))}
                  {tasks.length > 5 && (
                    <p className="text-xs text-base-content/50 text-center">
                      +{tasks.length - 5} more tasks
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-base-300">
              <button
                onClick={handleOpenWorkspace}
                className="btn btn-primary btn-sm w-full gap-2"
              >
                <Sparkles size={14} aria-hidden="true" />
                Open AI Workspace
                <ChevronRight size={14} aria-hidden="true" />
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Full variant for embedding in pages
  return (
    <div className="card bg-base-200 shadow-sm">
      <div className="card-body p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold flex items-center gap-2">
            <Bot size={18} aria-hidden="true" />
            Agent Activity
          </h3>
          {isProcessing && (
            <span className="badge badge-primary badge-sm gap-1">
              <Sparkles size={10} className="animate-spin" aria-hidden="true" />
              Processing
            </span>
          )}
        </div>

        <div className="grid grid-cols-3 gap-3 mb-4">
          <StatBox label="Active" value={stats.in_progress} variant={stats.in_progress > 0 ? 'primary' : 'default'} />
          <StatBox label="Pending" value={stats.pending} variant={stats.pending > 0 ? 'warning' : 'default'} />
          <StatBox label="Today" value={stats.completed_today} variant="success" />
        </div>

        {tasks.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-base-content/70 uppercase tracking-wide">
              Upcoming Tasks
            </h4>
            {tasks.slice(0, 3).map((task) => (
              <TaskItem key={task.id} task={task} />
            ))}
          </div>
        )}

        {tasks.length === 0 && (
          <div className="text-center py-4 text-base-content/60">
            <CheckCircle size={24} className="mx-auto mb-2 text-success" aria-hidden="true" />
            <p className="text-sm">All caught up!</p>
          </div>
        )}
      </div>
    </div>
  );
}

interface TaskItemProps {
  task: {
    id: string;
    type: string;
    description: string;
    priority: 'low' | 'medium' | 'high' | 'critical';
    status: string;
  };
}

function TaskItem({ task }: TaskItemProps) {
  const priorityColors = {
    critical: 'badge-error',
    high: 'badge-warning',
    medium: 'badge-info',
    low: 'badge-ghost',
  };

  const statusIcons = {
    pending: Clock,
    in_progress: Sparkles,
    completed: CheckCircle,
    failed: AlertCircle,
  };

  const StatusIcon = statusIcons[task.status as keyof typeof statusIcons] || Clock;

  return (
    <div className="flex items-start gap-2 p-2 rounded-lg bg-base-300/50">
      <StatusIcon
        size={14}
        className={clsx('flex-shrink-0 mt-0.5', {
          'text-base-content/50': task.status === 'pending',
          'text-primary animate-pulse': task.status === 'in_progress',
          'text-success': task.status === 'completed',
          'text-error': task.status === 'failed',
        })}
        aria-hidden="true"
      />
      <div className="flex-1 min-w-0">
        <p className="text-sm truncate">{task.description}</p>
        <div className="flex items-center gap-2 mt-1">
          <span className={clsx('badge badge-xs', priorityColors[task.priority])}>
            {task.priority}
          </span>
          <span className="text-xs text-base-content/50">{task.type}</span>
        </div>
      </div>
    </div>
  );
}

interface StatBoxProps {
  label: string;
  value: number;
  variant?: 'default' | 'primary' | 'warning' | 'success';
}

function StatBox({ label, value, variant = 'default' }: StatBoxProps) {
  const colorClasses = {
    default: '',
    primary: 'text-primary',
    warning: 'text-warning',
    success: 'text-success',
  };

  return (
    <div className="text-center p-2 bg-base-300/50 rounded-lg">
      <div className={clsx('text-xl font-bold', colorClasses[variant])}>{value}</div>
      <div className="text-xs text-base-content/60">{label}</div>
    </div>
  );
}

export default AgentActivityPanel;
