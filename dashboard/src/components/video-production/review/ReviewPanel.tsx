/**
 * ReviewPanel - Video review comments management
 * Displays comments, allows adding new ones, and queuing for AI processing
 */

import { useState } from 'react';
import {
  MessageSquare,
  Plus,
  Clock,
  CheckCircle,
  AlertCircle,
  Bot,
  Send,
  Trash2,
  X,
} from 'lucide-react';
import { Spinner } from '@/components/ui';
import { useVideoReviewData } from '@/hooks/useVideoApi';
import type { CommentStatus, CommentPriority, VideoReviewComment } from '@/api/video';

const STATUS_CONFIG: Record<CommentStatus, { label: string; color: string; icon: typeof Clock }> = {
  pending: { label: 'Pending', color: 'badge-ghost', icon: Clock },
  queued: { label: 'Queued', color: 'badge-info', icon: Bot },
  processing: { label: 'Processing', color: 'badge-warning', icon: Bot },
  resolved: { label: 'Resolved', color: 'badge-success', icon: CheckCircle },
  rejected: { label: 'Rejected', color: 'badge-error', icon: AlertCircle },
};

const PRIORITY_CONFIG: Record<CommentPriority, { label: string; color: string }> = {
  low: { label: 'Low', color: 'text-base-content/50' },
  normal: { label: 'Normal', color: 'text-base-content' },
  high: { label: 'High', color: 'text-warning' },
  urgent: { label: 'Urgent', color: 'text-error' },
};

interface CommentCardProps {
  comment: VideoReviewComment;
  onQueueForAI: (id: string) => void;
  onResolve: (id: string) => void;
  onDelete: (id: string) => void;
  isProcessing: boolean;
}

function CommentCard({
  comment,
  onQueueForAI,
  onResolve,
  onDelete,
  isProcessing,
}: CommentCardProps) {
  const statusConfig = STATUS_CONFIG[comment.status];
  const priorityConfig = PRIORITY_CONFIG[comment.priority];
  const StatusIcon = statusConfig.icon;

  const formatTimestamp = (seconds?: number) => {
    if (!seconds) return null;
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="border border-base-300 rounded-lg p-3 space-y-2">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <span className={`badge ${statusConfig.color} gap-1 badge-sm`}>
            <StatusIcon size={10} />
            {statusConfig.label}
          </span>
          {comment.priority !== 'normal' && (
            <span className={`text-xs font-medium ${priorityConfig.color}`}>
              {priorityConfig.label}
            </span>
          )}
        </div>
        <span className="text-xs text-base-content/50">
          {new Date(comment.created_at).toLocaleDateString()}
        </span>
      </div>

      <p className="text-sm">{comment.text}</p>

      <div className="flex items-center justify-between text-xs text-base-content/60">
        <div className="flex items-center gap-2">
          <span>{comment.author}</span>
          {comment.timestamp && (
            <>
              <span>-</span>
              <span className="font-mono">{formatTimestamp(comment.timestamp)}</span>
            </>
          )}
        </div>

        {comment.status === 'pending' && (
          <div className="flex items-center gap-1">
            <button
              className="btn btn-ghost btn-xs"
              onClick={() => onQueueForAI(comment.id)}
              disabled={isProcessing}
            >
              <Bot size={12} />
              Queue AI
            </button>
            <button
              className="btn btn-ghost btn-xs"
              onClick={() => onResolve(comment.id)}
              disabled={isProcessing}
            >
              <CheckCircle size={12} />
              Resolve
            </button>
            <button
              className="btn btn-ghost btn-xs text-error"
              onClick={() => onDelete(comment.id)}
              disabled={isProcessing}
            >
              <Trash2 size={12} />
            </button>
          </div>
        )}
      </div>

      {comment.resolution && (
        <div className="bg-success/10 text-success-content p-2 rounded text-xs">
          <strong>Resolution:</strong> {comment.resolution}
        </div>
      )}
    </div>
  );
}

interface AddCommentFormProps {
  componentId: string;
  onSubmit: (text: string, priority: CommentPriority, timestamp?: number) => void;
  onCancel: () => void;
  isSubmitting: boolean;
}

function AddCommentForm({ componentId: _componentId, onSubmit, onCancel, isSubmitting }: AddCommentFormProps) {
  const [text, setText] = useState('');
  const [priority, setPriority] = useState<CommentPriority>('normal');
  const [timestampInput, setTimestampInput] = useState('');

  const parseTimestamp = (input: string): number | undefined => {
    if (!input) return undefined;
    const parts = input.split(':').map(Number);
    if (parts.length === 2 && !parts.some(isNaN)) {
      return parts[0] * 60 + parts[1];
    }
    return undefined;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (text.trim()) {
      onSubmit(text.trim(), priority, parseTimestamp(timestampInput));
    }
  };

  return (
    <form onSubmit={handleSubmit} className="border border-base-300 rounded-lg p-3 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">Add Comment</span>
        <button type="button" className="btn btn-ghost btn-xs" onClick={onCancel}>
          <X size={14} />
        </button>
      </div>

      <textarea
        className="textarea textarea-bordered w-full text-sm"
        placeholder="Describe the issue or suggestion..."
        rows={3}
        value={text}
        onChange={(e) => setText(e.target.value)}
        autoFocus
      />

      <div className="flex items-center gap-3">
        <div className="form-control">
          <label className="label py-0">
            <span className="label-text text-xs">Priority</span>
          </label>
          <select
            className="select select-bordered select-sm"
            value={priority}
            onChange={(e) => setPriority(e.target.value as CommentPriority)}
          >
            <option value="low">Low</option>
            <option value="normal">Normal</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
          </select>
        </div>

        <div className="form-control">
          <label className="label py-0">
            <span className="label-text text-xs">Timestamp (m:ss)</span>
          </label>
          <input
            type="text"
            className="input input-bordered input-sm w-24"
            placeholder="0:00"
            value={timestampInput}
            onChange={(e) => setTimestampInput(e.target.value)}
          />
        </div>

        <div className="flex-1" />

        <button
          type="submit"
          className="btn btn-primary btn-sm"
          disabled={!text.trim() || isSubmitting}
        >
          {isSubmitting ? <Spinner size="sm" /> : <Send size={14} />}
          Submit
        </button>
      </div>
    </form>
  );
}

interface ReviewPanelProps {
  projectId: string;
  componentId?: string;
  showResolved?: boolean;
}

export function ReviewPanel({ projectId, componentId, showResolved = false }: ReviewPanelProps) {
  const [showAddForm, setShowAddForm] = useState(false);
  const [selectedComponentId, _setSelectedComponentId] = useState(componentId);

  const {
    comments,
    stats,
    isLoading,
    error,
    addComment,
    deleteComment,
    queueForAI,
    resolveComment,
  } = useVideoReviewData(projectId, { include_resolved: showResolved });

  // Filter by component if specified
  const filteredComments = selectedComponentId
    ? comments.filter((c) => c.component_id === selectedComponentId)
    : comments;

  const handleAddComment = (text: string, priority: CommentPriority, timestamp?: number) => {
    if (selectedComponentId) {
      addComment.mutate(
        {
          projectId,
          componentId: selectedComponentId,
          text,
          priority,
          timestamp,
        },
        {
          onSuccess: () => setShowAddForm(false),
        }
      );
    }
  };

  const handleQueueForAI = (commentId: string) => {
    queueForAI.mutate({ projectId, commentId });
  };

  const handleResolve = (commentId: string) => {
    resolveComment.mutate({
      projectId,
      commentId,
      resolution: 'Manually resolved',
    });
  };

  const handleDelete = (commentId: string) => {
    if (confirm('Delete this comment?')) {
      deleteComment.mutate({ projectId, commentId });
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <Spinner size="md" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-error">
        <AlertCircle size={16} />
        <span>Failed to load comments</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="font-semibold flex items-center gap-2">
          <MessageSquare size={18} className="text-primary" />
          Review Comments
          {stats && stats.pending > 0 && (
            <span className="badge badge-warning badge-sm">{stats.pending} pending</span>
          )}
        </h3>
        <button
          className="btn btn-ghost btn-sm gap-1"
          onClick={() => setShowAddForm(true)}
          disabled={!selectedComponentId}
        >
          <Plus size={14} />
          Add Comment
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="flex items-center gap-3 text-xs text-base-content/60">
          <span>{stats.total} total</span>
          <span>-</span>
          <span className="text-warning">{stats.pending} pending</span>
          <span className="text-info">{stats.queued} queued</span>
          <span className="text-success">{stats.resolved} resolved</span>
        </div>
      )}

      {/* Add Form */}
      {showAddForm && selectedComponentId && (
        <AddCommentForm
          componentId={selectedComponentId}
          onSubmit={handleAddComment}
          onCancel={() => setShowAddForm(false)}
          isSubmitting={addComment.isPending}
        />
      )}

      {/* Comments List */}
      {filteredComments.length === 0 ? (
        <div className="text-center text-base-content/50 py-8">
          <MessageSquare size={32} className="mx-auto mb-2 opacity-50" />
          <p>No comments yet</p>
          {selectedComponentId && (
            <button
              className="btn btn-ghost btn-sm mt-2"
              onClick={() => setShowAddForm(true)}
            >
              <Plus size={14} />
              Add First Comment
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          {filteredComments.map((comment) => (
            <CommentCard
              key={comment.id}
              comment={comment}
              onQueueForAI={handleQueueForAI}
              onResolve={handleResolve}
              onDelete={handleDelete}
              isProcessing={
                queueForAI.isPending ||
                resolveComment.isPending ||
                deleteComment.isPending
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default ReviewPanel;
