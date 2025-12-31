/**
 * VideoReview - Unified video review section
 *
 * Features:
 * - Unified video player with all chapters
 * - Chapter timeline with comment markers
 * - Comment sidebar with filtering
 * - Quick add comment at playhead
 * - AI queue workflow integration
 * - Comment click seeking to timestamp
 */

import { useState, useCallback, useMemo, useRef } from 'react';
import {
  MessageSquare,
  CheckCircle2,
  Trash2,
  AlertCircle,
  Clock,
  Bot,
  Play,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import {
  useChapterVideoData,
  useVideoReviewData,
} from '@/hooks/useVideoApi';
import { Spinner } from '@/components/ui';
import { UnifiedVideoPlayer } from '../UnifiedVideoPlayer';
import { ChapterSelector } from '../ChapterSelector';
import { QuickAddComment } from '../review/QuickAddComment';
import type { VideoReviewComment, CommentStatus } from '@/api/types/video';

// ============================================================================
// Comment Card Component
// ============================================================================

interface CommentCardProps {
  comment: VideoReviewComment;
  isSelected: boolean;
  isAtPlayhead: boolean;
  onClick: () => void;
  onJumpTo: () => void;
  onQueue: () => void;
  onResolve: () => void;
  onDelete: () => void;
  isQueuing: boolean;
  chapterName?: string;
}

function CommentCard({
  comment,
  isSelected,
  isAtPlayhead,
  onClick,
  onJumpTo,
  onQueue,
  onResolve,
  onDelete,
  isQueuing,
  chapterName,
}: CommentCardProps) {
  const formatTime = (seconds?: number) => {
    if (seconds === undefined) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const statusColors: Record<CommentStatus, string> = {
    pending: 'bg-warning/20 text-warning',
    queued: 'bg-info/20 text-info',
    processing: 'bg-amber-500/20 text-amber-500',
    resolved: 'bg-success/20 text-success',
    rejected: 'bg-error/20 text-error',
  };

  const priorityColors: Record<string, string> = {
    low: 'text-base-content/50',
    normal: 'text-base-content',
    high: 'text-warning',
    urgent: 'text-error',
  };

  return (
    <div
      onClick={onClick}
      className={cn(
        'p-3 border-b border-base-200 cursor-pointer transition-colors relative',
        isSelected ? 'bg-primary/10 border-l-2 border-l-primary' : 'hover:bg-base-200',
        isAtPlayhead && !isSelected && 'bg-warning/10 border-l-2 border-l-warning'
      )}
    >
      {/* Playhead indicator */}
      {isAtPlayhead && (
        <div className="absolute top-1 right-1">
          <span className="badge badge-xs badge-warning">NOW</span>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center gap-2 mb-1">
        <span className={cn('badge badge-sm', statusColors[comment.status])}>
          {comment.status}
        </span>
        {comment.priority !== 'normal' && (
          <span className={cn('text-xs font-medium', priorityColors[comment.priority])}>
            {comment.priority}
          </span>
        )}
        <span className="flex-1" />
        <span className="text-xs text-base-content/50">{formatTime(comment.timestamp)}</span>
      </div>

      {/* Comment text */}
      <p className="text-sm text-base-content mb-2 line-clamp-2">{comment.text}</p>

      {/* Footer */}
      <div className="flex items-center gap-2 text-xs text-base-content/50">
        <span>{comment.author}</span>
        {chapterName && (
          <>
            <span>&bull;</span>
            <span className="truncate">{chapterName}</span>
          </>
        )}
        <span className="flex-1" />

        {/* Jump to button */}
        {comment.timestamp !== undefined && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onJumpTo();
            }}
            className="btn btn-ghost btn-xs gap-1 text-primary"
            title="Jump to timestamp"
          >
            <Play size={12} />
            Jump
          </button>
        )}

        {/* Action buttons */}
        {comment.status === 'pending' && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onQueue();
            }}
            disabled={isQueuing}
            className="btn btn-ghost btn-xs gap-1"
            title="Queue for AI"
          >
            {isQueuing ? (
              <span className="loading loading-spinner loading-xs" />
            ) : (
              <Bot size={12} />
            )}
          </button>
        )}

        {(comment.status === 'pending' || comment.status === 'queued') && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onResolve();
            }}
            className="btn btn-ghost btn-xs gap-1 text-success"
            title="Mark resolved"
          >
            <CheckCircle2 size={12} />
          </button>
        )}

        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className="btn btn-ghost btn-xs gap-1 text-error"
          title="Delete comment"
        >
          <Trash2 size={12} />
        </button>
      </div>

      {/* Resolution */}
      {comment.resolution && (
        <div className="mt-2 p-2 bg-success/10 rounded text-xs text-success">
          <strong>Resolution:</strong> {comment.resolution}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Main VideoReview Component
// ============================================================================

interface VideoReviewProps {
  projectId: string | null;
  className?: string;
}

export function VideoReview({ projectId, className }: VideoReviewProps) {
  // State
  const [selectedChapterId, setSelectedChapterId] = useState<string | null>(null);
  const [selectedCommentId, setSelectedCommentId] = useState<string | null>(null);
  const [showResolved, setShowResolved] = useState(false);
  const [statusFilter, setStatusFilter] = useState<CommentStatus | 'all'>('all');
  const [currentFrame, setCurrentFrame] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [currentGlobalFrame, setCurrentGlobalFrame] = useState(0);

  // Refs for seeking and scrolling
  const seekToGlobalFrameRef = useRef<((frame: number) => void) | null>(null);
  const commentsListRef = useRef<HTMLDivElement>(null);
  const commentRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  // Data hooks
  const { chapters, timelineData, isLoading: chaptersLoading } = useChapterVideoData(projectId);
  const {
    comments,
    isLoading: commentsLoading,
    refetch: refetchComments,
    addComment,
    queueForAI,
    resolveComment,
    deleteComment,
  } = useVideoReviewData(projectId, { include_resolved: showResolved });

  // Current chapter
  const currentChapter = useMemo(() => {
    if (selectedChapterId) {
      return chapters.find((c) => c.id === selectedChapterId) || null;
    }
    return chapters[0] || null;
  }, [chapters, selectedChapterId]);

  // Filtered comments
  const filteredComments = useMemo(() => {
    let filtered = comments;

    if (statusFilter !== 'all') {
      filtered = filtered.filter((c) => c.status === statusFilter);
    }

    if (!showResolved) {
      filtered = filtered.filter((c) => c.status !== 'resolved' && c.status !== 'rejected');
    }

    return filtered;
  }, [comments, statusFilter, showResolved]);

  // Get chapter name for a comment
  const getChapterName = useCallback(
    (componentId: string) => {
      const chapter = chapters.find((c) => c.id === componentId);
      return chapter?.name;
    },
    [chapters]
  );

  // Check if a comment is near the current playhead (within 1 second / 30 frames)
  const isCommentAtPlayhead = useCallback(
    (comment: VideoReviewComment) => {
      if (comment.frame === undefined || !timelineData) return false;
      const chapter = timelineData.chapters.find((c) => c.id === comment.component_id);
      if (!chapter) return false;
      const commentGlobalFrame = chapter.startGlobalFrame + comment.frame;
      const threshold = 30; // ~1 second at 30fps
      return Math.abs(commentGlobalFrame - currentGlobalFrame) <= threshold;
    },
    [timelineData, currentGlobalFrame]
  );

  // Seek to a comment's timestamp
  const seekToComment = useCallback(
    (comment: VideoReviewComment) => {
      if (comment.frame === undefined || !timelineData) return;
      const chapter = timelineData.chapters.find((c) => c.id === comment.component_id);
      if (!chapter) return;
      const globalFrame = chapter.startGlobalFrame + comment.frame;
      seekToGlobalFrameRef.current?.(globalFrame);
    },
    [timelineData]
  );

  // Handle comment click - selects and seeks to the comment
  const handleCommentClick = useCallback(
    (comment: VideoReviewComment) => {
      setSelectedCommentId(comment.id);

      // Also select the chapter if different
      if (comment.component_id !== selectedChapterId) {
        setSelectedChapterId(comment.component_id);
      }

      // Seek to the comment's timestamp
      seekToComment(comment);

      // Scroll the comment into view
      const commentEl = commentRefs.current.get(comment.id);
      if (commentEl) {
        commentEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    },
    [selectedChapterId, seekToComment]
  );

  // Handle explicit jump to button click
  const handleJumpToComment = useCallback(
    (comment: VideoReviewComment) => {
      setSelectedCommentId(comment.id);

      if (comment.component_id !== selectedChapterId) {
        setSelectedChapterId(comment.component_id);
      }

      seekToComment(comment);

      // Scroll the comment into view
      const commentEl = commentRefs.current.get(comment.id);
      if (commentEl) {
        commentEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    },
    [selectedChapterId, seekToComment]
  );

  // Handle time update from video player
  const handleTimeUpdate = useCallback(
    (localFrame: number, localTime: number, globalFrame: number) => {
      setCurrentFrame(localFrame);
      setCurrentTime(localTime);
      setCurrentGlobalFrame(globalFrame);
    },
    []
  );

  // Register seek function from player
  const registerSeekFunction = useCallback((seekFn: (frame: number) => void) => {
    seekToGlobalFrameRef.current = seekFn;
  }, []);

  // Handle add comment
  const handleAddComment = useCallback(
    async (data: {
      componentId: string;
      text: string;
      frame: number;
      timestamp: number;
      priority: 'low' | 'normal' | 'high' | 'urgent';
    }) => {
      await addComment.mutateAsync({
        projectId: projectId!,
        componentId: data.componentId,
        text: data.text,
        frame: data.frame,
        timestamp: data.timestamp,
        priority: data.priority,
      });
      refetchComments();
    },
    [projectId, addComment, refetchComments]
  );

  // Handle queue for AI
  const handleQueue = useCallback(
    async (commentId: string) => {
      await queueForAI.mutateAsync({ projectId: projectId!, commentId });
      refetchComments();
    },
    [projectId, queueForAI, refetchComments]
  );

  // Handle resolve
  const handleResolve = useCallback(
    async (commentId: string) => {
      await resolveComment.mutateAsync({
        projectId: projectId!,
        commentId,
        resolution: 'Marked as resolved by reviewer',
      });
      refetchComments();
    },
    [projectId, resolveComment, refetchComments]
  );

  // Handle delete
  const handleDelete = useCallback(
    async (commentId: string) => {
      await deleteComment.mutateAsync({ projectId: projectId!, commentId });
      refetchComments();
    },
    [projectId, deleteComment, refetchComments]
  );

  // Loading state
  if (chaptersLoading) {
    return (
      <div className={cn('flex items-center justify-center h-96', className)}>
        <Spinner size="lg" />
      </div>
    );
  }

  // No project selected
  if (!projectId) {
    return (
      <div className={cn('flex flex-col items-center justify-center h-96', className)}>
        <AlertCircle size={48} className="text-base-content/30 mb-4" />
        <h3 className="text-lg font-medium text-base-content/70 mb-2">No Project Selected</h3>
        <p className="text-sm text-base-content/50">
          Select a video project from the Projects tab to review
        </p>
      </div>
    );
  }

  // No chapters available
  if (!timelineData || chapters.length === 0) {
    return (
      <div className={cn('flex flex-col items-center justify-center h-96', className)}>
        <MessageSquare size={48} className="text-base-content/30 mb-4" />
        <h3 className="text-lg font-medium text-base-content/70 mb-2">No Video Scripts</h3>
        <p className="text-sm text-base-content/50">
          Create video scripts to start the review workflow
        </p>
      </div>
    );
  }

  return (
    <div className={cn('flex h-full', className)}>
      {/* Chapter Sidebar */}
      <div className="w-64 flex-shrink-0 border-r border-base-300 bg-base-100">
        <ChapterSelector
          chapters={chapters}
          comments={comments}
          selectedChapterId={selectedChapterId || currentChapter?.id || null}
          onChapterSelect={setSelectedChapterId}
          className="h-full"
        />
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Video Player */}
        <div className="flex-shrink-0">
          <UnifiedVideoPlayer
            timelineData={timelineData}
            comments={comments}
            selectedChapterId={selectedChapterId || currentChapter?.id}
            onChapterSelect={setSelectedChapterId}
            onCommentClick={handleCommentClick}
            selectedCommentId={selectedCommentId}
            showResolvedComments={showResolved}
            onTimeUpdate={handleTimeUpdate}
            onRegisterSeek={registerSeekFunction}
            className="aspect-video max-h-[60vh]"
          />
        </div>

        {/* Quick Add Comment */}
        <div className="p-3 border-t border-base-300">
          <QuickAddComment
            currentChapter={currentChapter}
            currentFrame={currentFrame}
            currentTime={currentTime}
            onSubmit={handleAddComment}
            isSubmitting={addComment.isPending}
          />
        </div>
      </div>

      {/* Comments Sidebar */}
      <div className="w-80 flex-shrink-0 border-l border-base-300 flex flex-col bg-base-100">
        {/* Header */}
        <div className="px-3 py-2 border-b border-base-300">
          <div className="flex items-center gap-2">
            <MessageSquare size={16} className="text-base-content/70" />
            <h3 className="text-sm font-semibold text-base-content/70">
              Comments ({filteredComments.length})
            </h3>
          </div>

          {/* Filters */}
          <div className="flex items-center gap-2 mt-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as CommentStatus | 'all')}
              className="select select-xs select-bordered flex-1"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="queued">Queued</option>
              <option value="processing">Processing</option>
              <option value="resolved">Resolved</option>
            </select>

            <label className="flex items-center gap-1 text-xs cursor-pointer">
              <input
                type="checkbox"
                checked={showResolved}
                onChange={(e) => setShowResolved(e.target.checked)}
                className="checkbox checkbox-xs"
              />
              Resolved
            </label>
          </div>
        </div>

        {/* Comments list */}
        <div ref={commentsListRef} className="flex-1 overflow-y-auto">
          {commentsLoading ? (
            <div className="flex items-center justify-center h-32">
              <Spinner size="md" />
            </div>
          ) : filteredComments.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-32 text-center p-4">
              <MessageSquare size={24} className="text-base-content/30 mb-2" />
              <p className="text-sm text-base-content/50">No comments yet</p>
              <p className="text-xs text-base-content/40 mt-1">
                Add comments while watching
              </p>
            </div>
          ) : (
            filteredComments.map((comment) => (
              <div
                key={comment.id}
                ref={(el) => {
                  if (el) {
                    commentRefs.current.set(comment.id, el);
                  } else {
                    commentRefs.current.delete(comment.id);
                  }
                }}
              >
                <CommentCard
                  comment={comment}
                  isSelected={comment.id === selectedCommentId}
                  isAtPlayhead={isCommentAtPlayhead(comment)}
                  onClick={() => handleCommentClick(comment)}
                  onJumpTo={() => handleJumpToComment(comment)}
                  onQueue={() => handleQueue(comment.id)}
                  onResolve={() => handleResolve(comment.id)}
                  onDelete={() => handleDelete(comment.id)}
                  isQueuing={queueForAI.isPending}
                  chapterName={getChapterName(comment.component_id)}
                />
              </div>
            ))
          )}
        </div>

        {/* Stats footer */}
        <div className="px-3 py-2 border-t border-base-300 bg-base-200/50">
          <div className="flex items-center justify-between text-xs text-base-content/60">
            <span className="flex items-center gap-1">
              <Clock size={12} />
              {comments.filter((c) => c.status === 'pending').length} pending
            </span>
            <span className="flex items-center gap-1">
              <Bot size={12} />
              {comments.filter((c) => c.status === 'queued' || c.status === 'processing').length}{' '}
              in AI queue
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default VideoReview;
