import {
  AlertTriangle,
  Lightbulb,
  HelpCircle,
  CheckCircle,
  ListTodo,
  AlertCircle,
  Info,
  CheckSquare,
} from 'lucide-react';
import clsx from 'clsx';

export type NoteType =
  | 'uncertainty'
  | 'suggestion'
  | 'human_review'
  | 'decision'
  | 'todo'
  | 'warning'
  | 'info';

export interface AINote {
  id: string;
  type: NoteType;
  content: string;
  context?: string;
  document_path?: string;
  created_at: string;
  resolved: boolean;
  resolved_at?: string;
  resolution?: string;
}

const noteConfig: Record<NoteType, {
  icon: React.ComponentType<{ size?: number; className?: string }>;
  color: string;
  badge: string;
  label: string;
}> = {
  uncertainty: { icon: HelpCircle, color: 'text-warning', badge: 'badge-warning', label: 'Uncertainty' },
  suggestion: { icon: Lightbulb, color: 'text-info', badge: 'badge-info', label: 'Suggestion' },
  human_review: { icon: AlertTriangle, color: 'text-error', badge: 'badge-error', label: 'Needs Review' },
  decision: { icon: CheckCircle, color: 'text-success', badge: 'badge-success', label: 'Decision' },
  todo: { icon: ListTodo, color: 'text-primary', badge: 'badge-primary', label: 'Todo' },
  warning: { icon: AlertCircle, color: 'text-warning', badge: 'badge-warning', label: 'Warning' },
  info: { icon: Info, color: 'text-info', badge: 'badge-info', label: 'Info' },
};

interface AINoteCardProps {
  note: AINote;
  compact?: boolean;
  onResolve?: (noteId: string, resolution: string) => void;
  onClick?: (noteId: string) => void;
}

export function AINoteCard({ note, compact = false, onResolve, onClick }: AINoteCardProps) {
  const config = noteConfig[note.type] || noteConfig.info;
  const NoteIcon = config.icon;

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
      <div
        className={clsx(
          'flex items-start gap-3 p-3 rounded-lg bg-base-200',
          { 'opacity-60': note.resolved },
          onClick && 'cursor-pointer hover:bg-base-300 transition-colors'
        )}
        onClick={() => onClick?.(note.id)}
      >
        <NoteIcon size={16} className={clsx('flex-shrink-0 mt-0.5', config.color)} />
        <div className="flex-1 min-w-0">
          <p className={clsx('text-sm', { 'line-through': note.resolved })}>
            {note.content}
          </p>
          <p className="text-xs text-base-content/50 mt-1">
            {timeAgo(note.created_at)}
            {note.document_path && ` • ${note.document_path.split('/').pop()}`}
          </p>
        </div>
        {note.resolved && <CheckSquare size={16} className="text-success flex-shrink-0" />}
      </div>
    );
  }

  return (
    <div className={clsx('card bg-base-200 shadow-sm', { 'opacity-70': note.resolved })}>
      <div className="card-body p-4">
        {/* Header */}
        <div className="flex items-start gap-3">
          <div className={clsx('p-2 rounded-lg bg-base-300', config.color)}>
            <NoteIcon size={18} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className={clsx('badge badge-sm', config.badge)}>{config.label}</span>
              {note.resolved && (
                <span className="badge badge-sm badge-success gap-1">
                  <CheckSquare size={10} />
                  Resolved
                </span>
              )}
            </div>
            <p className={clsx('text-sm', { 'line-through opacity-70': note.resolved })}>
              {note.content}
            </p>
          </div>
        </div>

        {/* Context */}
        {note.context && (
          <div className="mt-3 p-2 bg-base-300 rounded text-xs text-base-content/70">
            {note.context}
          </div>
        )}

        {/* Document link */}
        {note.document_path && (
          <p className="text-xs text-base-content/50 mt-2">
            Document: <code className="text-primary">{note.document_path}</code>
          </p>
        )}

        {/* Resolution */}
        {note.resolved && note.resolution && (
          <div className="mt-3 p-2 bg-success/10 rounded border border-success/20">
            <p className="text-xs text-success font-medium mb-1">Resolution:</p>
            <p className="text-sm">{note.resolution}</p>
          </div>
        )}

        {/* Metadata and actions */}
        <div className="flex items-center justify-between mt-3 pt-3 border-t border-base-300">
          <span className="text-xs text-base-content/50">
            {timeAgo(note.created_at)}
          </span>
          {!note.resolved && note.type === 'human_review' && onResolve && (
            <button
              className="btn btn-success btn-xs gap-1"
              onClick={() => onResolve(note.id, 'Reviewed and approved')}
            >
              <CheckSquare size={12} />
              Resolve
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
