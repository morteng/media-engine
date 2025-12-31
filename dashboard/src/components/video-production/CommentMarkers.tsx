/**
 * CommentMarkers - Visual markers for comments on the timeline
 *
 * Features:
 * - Diamond markers at comment positions
 * - Color-coded by status
 * - Hover tooltip with preview
 * - Click to select and jump
 * - Processing animation for queued comments
 */

import { useCallback, useState } from 'react';
import type {
  VideoReviewComment,
  CommentStatus,
  ChapterTimelineData,
} from '@/api/types/video';

// Marker colors by status
const MARKER_COLORS: Record<CommentStatus, string> = {
  pending: '#facc15', // yellow-400
  queued: '#3b82f6', // blue-500
  processing: '#f59e0b', // amber-500
  resolved: '#22c55e', // green-500
  rejected: '#ef4444', // red-500
};

interface CommentMarkersProps {
  /** All comments to display */
  comments: VideoReviewComment[];
  /** Timeline data for calculating positions */
  timelineData: ChapterTimelineData;
  /** Currently selected comment ID */
  selectedCommentId: string | null;
  /** Called when a marker is clicked */
  onMarkerClick: (comment: VideoReviewComment) => void;
  /** Whether to show resolved comments */
  showResolved?: boolean;
  /** Optional className */
  className?: string;
}

export function CommentMarkers({
  comments,
  timelineData,
  selectedCommentId,
  onMarkerClick,
  showResolved = true,
  className = '',
}: CommentMarkersProps) {
  const [hoveredComment, setHoveredComment] = useState<VideoReviewComment | null>(null);

  // Filter comments based on visibility settings
  const visibleComments = showResolved
    ? comments
    : comments.filter((c) => c.status !== 'resolved' && c.status !== 'rejected');

  // Calculate marker position from frame number
  const getMarkerPosition = useCallback(
    (comment: VideoReviewComment): number | null => {
      if (comment.frame === undefined || timelineData.totalFrames === 0) {
        return null;
      }

      // Find which chapter this comment belongs to
      const chapter = timelineData.chapters.find((c) => c.id === comment.component_id);
      if (!chapter) return null;

      // Calculate global frame position
      const globalFrame = chapter.startGlobalFrame + (comment.frame || 0);
      return (globalFrame / timelineData.totalFrames) * 100;
    },
    [timelineData]
  );

  return (
    <div className={`absolute inset-0 pointer-events-none ${className}`}>
      {visibleComments.map((comment) => {
        const position = getMarkerPosition(comment);
        if (position === null) return null;

        const isSelected = comment.id === selectedCommentId;
        const isHovered = hoveredComment?.id === comment.id;
        const isProcessing = comment.status === 'processing';
        const color = MARKER_COLORS[comment.status];

        return (
          <div
            key={comment.id}
            className="absolute top-0 bottom-0 pointer-events-auto"
            style={{ left: `${position}%` }}
          >
            {/* Marker diamond */}
            <button
              className={`
                absolute top-1/2 -translate-x-1/2 -translate-y-1/2
                w-3 h-3 rotate-45
                transition-all duration-150
                hover:scale-125 focus:outline-none focus:ring-2 focus:ring-offset-1
                ${isSelected ? 'scale-125 ring-2 ring-white' : ''}
                ${isProcessing ? 'animate-pulse' : ''}
              `}
              style={{
                backgroundColor: color,
                boxShadow: isSelected ? `0 0 8px ${color}` : undefined,
              }}
              onClick={() => onMarkerClick(comment)}
              onMouseEnter={() => setHoveredComment(comment)}
              onMouseLeave={() => setHoveredComment(null)}
              title={comment.text}
            />

            {/* Tooltip on hover */}
            {isHovered && (
              <div
                className="absolute z-50 bottom-full mb-2 left-1/2 -translate-x-1/2
                           bg-base-100 border border-base-300 rounded-lg shadow-lg
                           p-2 w-48 text-sm pointer-events-none"
              >
                <div className="flex items-center gap-2 mb-1">
                  <div
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: color }}
                  />
                  <span className="text-xs text-base-content/60 capitalize">
                    {comment.status}
                  </span>
                  {comment.priority !== 'normal' && (
                    <span
                      className={`text-xs px-1 rounded ${
                        comment.priority === 'urgent'
                          ? 'bg-error/20 text-error'
                          : comment.priority === 'high'
                            ? 'bg-warning/20 text-warning'
                            : 'bg-base-300 text-base-content/60'
                      }`}
                    >
                      {comment.priority}
                    </span>
                  )}
                </div>
                <p className="text-base-content line-clamp-2">{comment.text}</p>
                <div className="mt-1 text-xs text-base-content/50">
                  {comment.author} &bull; {formatTimestamp(comment.timestamp)}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

/**
 * Format timestamp in seconds to MM:SS
 */
function formatTimestamp(seconds?: number): string {
  if (seconds === undefined) return '--:--';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export default CommentMarkers;
