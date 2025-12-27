import { Link } from 'react-router-dom';
import {
  Sparkles,
  History,
  StickyNote,
  ListTodo,
  BookOpen,
  ArrowRight,
  Play,
  AlertTriangle,
} from 'lucide-react';
import type { AISession } from './AISessionCard';
import type { AINote } from './AINoteCard';
import type { AITask } from './AITaskQueue';
import type { AIResearchEntry } from './AIResearchCard';

interface AIWorkspaceSummaryProps {
  sessions: AISession[];
  notes: AINote[];
  tasks: AITask[];
  research: AIResearchEntry[];
  linkPrefix?: string;
}

export function AIWorkspaceSummary({
  sessions,
  notes,
  tasks,
  research,
  linkPrefix = '/ai-assist',
}: AIWorkspaceSummaryProps) {
  const activeSessions = sessions.filter((s) => s.status === 'active');
  const unresolvedNotes = notes.filter((n) => !n.resolved);
  const humanReviewNotes = unresolvedNotes.filter((n) => n.type === 'human_review');
  const pendingTasks = tasks.filter((t) => t.status === 'pending');
  const staleResearch = research.filter((r) => r.is_stale);

  const hasActiveWork = activeSessions.length > 0;
  const needsAttention = humanReviewNotes.length > 0 || pendingTasks.length > 5;

  return (
    <div className="card bg-gradient-to-br from-base-200 to-base-300 shadow-sm">
      <div className="card-body p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <Sparkles size={20} className="text-primary" />
            AI Workspace
          </h2>
          <Link to={linkPrefix} className="btn btn-ghost btn-sm gap-1">
            Open <ArrowRight size={14} />
          </Link>
        </div>

        {/* Active session indicator */}
        {hasActiveWork && (
          <div className="mb-4 p-3 bg-success/10 rounded-lg flex items-center gap-3">
            <Play size={18} className="text-success" />
            <div className="flex-1">
              <p className="font-medium text-success">
                {activeSessions.length} Active Session{activeSessions.length !== 1 ? 's' : ''}
              </p>
              <p className="text-sm text-base-content/60">
                {activeSessions[0]?.task_id}
              </p>
            </div>
          </div>
        )}

        {/* Attention required */}
        {needsAttention && (
          <div className="mb-4 p-3 bg-warning/10 rounded-lg flex items-center gap-3">
            <AlertTriangle size={18} className="text-warning" />
            <div className="flex-1">
              <p className="font-medium text-warning">Attention Required</p>
              <p className="text-sm text-base-content/60">
                {humanReviewNotes.length > 0 && `${humanReviewNotes.length} items need review`}
                {humanReviewNotes.length > 0 && pendingTasks.length > 5 && ', '}
                {pendingTasks.length > 5 && `${pendingTasks.length} tasks pending`}
              </p>
            </div>
          </div>
        )}

        {/* Stats grid */}
        <div className="grid grid-cols-2 gap-3">
          <Link
            to={`${linkPrefix}/sessions`}
            className="flex items-center gap-3 p-3 rounded-lg bg-base-100 hover:bg-base-200 transition-colors"
          >
            <History size={18} className="text-primary" />
            <div>
              <p className="font-medium">{sessions.length}</p>
              <p className="text-xs text-base-content/60">Sessions</p>
            </div>
          </Link>

          <Link
            to={`${linkPrefix}/notes`}
            className="flex items-center gap-3 p-3 rounded-lg bg-base-100 hover:bg-base-200 transition-colors"
          >
            <StickyNote size={18} className={unresolvedNotes.length > 0 ? 'text-warning' : 'text-info'} />
            <div>
              <p className="font-medium">{unresolvedNotes.length}</p>
              <p className="text-xs text-base-content/60">Notes</p>
            </div>
          </Link>

          <Link
            to={`${linkPrefix}/queue`}
            className="flex items-center gap-3 p-3 rounded-lg bg-base-100 hover:bg-base-200 transition-colors"
          >
            <ListTodo size={18} className={pendingTasks.length > 0 ? 'text-warning' : 'text-success'} />
            <div>
              <p className="font-medium">{pendingTasks.length}</p>
              <p className="text-xs text-base-content/60">Tasks</p>
            </div>
          </Link>

          <Link
            to={`${linkPrefix}/research`}
            className="flex items-center gap-3 p-3 rounded-lg bg-base-100 hover:bg-base-200 transition-colors"
          >
            <BookOpen size={18} className={staleResearch.length > 0 ? 'text-warning' : 'text-success'} />
            <div>
              <p className="font-medium">{research.length}</p>
              <p className="text-xs text-base-content/60">Research</p>
            </div>
          </Link>
        </div>

        {/* Quick actions */}
        {!hasActiveWork && pendingTasks.length > 0 && (
          <div className="mt-4 pt-4 border-t border-base-300">
            <button className="btn btn-primary btn-sm w-full gap-1">
              <Sparkles size={14} />
              Start Processing Tasks
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
