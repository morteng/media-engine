/**
 * ChapterSelector - Sidebar listing all video chapters
 *
 * Features:
 * - List all chapters with duration
 * - Comment count badges per chapter
 * - Selected state highlighting
 * - Video availability indicator
 */

import { useMemo } from 'react';
import {
  Film,
  Clock,
  MessageCircle,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';
import clsx from 'clsx';
import type { VideoChapter, VideoReviewComment } from '@/api/types/video';

interface ChapterSelectorProps {
  /** List of all chapters */
  chapters: VideoChapter[];
  /** All comments (used to show counts per chapter) */
  comments: VideoReviewComment[];
  /** Currently selected chapter ID */
  selectedChapterId: string | null;
  /** Called when a chapter is selected */
  onChapterSelect: (chapterId: string) => void;
  /** Optional className */
  className?: string;
}

export function ChapterSelector({
  chapters,
  comments,
  selectedChapterId,
  onChapterSelect,
  className = '',
}: ChapterSelectorProps) {
  // Calculate comment counts per chapter
  const commentCounts = useMemo(() => {
    const counts: Record<string, { total: number; pending: number }> = {};

    for (const comment of comments) {
      if (!counts[comment.component_id]) {
        counts[comment.component_id] = { total: 0, pending: 0 };
      }
      counts[comment.component_id].total++;
      if (comment.status === 'pending' || comment.status === 'queued') {
        counts[comment.component_id].pending++;
      }
    }

    return counts;
  }, [comments]);

  // Format duration
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (chapters.length === 0) {
    return (
      <div className={clsx('flex flex-col items-center justify-center p-4 text-center', className)}>
        <Film size={32} className="text-base-content/30 mb-2" />
        <p className="text-sm text-base-content/50">No video chapters found</p>
      </div>
    );
  }

  return (
    <div className={clsx('flex flex-col', className)}>
      <div className="px-3 py-2 border-b border-base-300">
        <h3 className="text-sm font-semibold text-base-content/70">
          Chapters ({chapters.length})
        </h3>
      </div>

      <div className="flex-1 overflow-y-auto">
        {chapters.map((chapter, index) => {
          const isSelected = chapter.id === selectedChapterId;
          const counts = commentCounts[chapter.id] || { total: 0, pending: 0 };
          const hasUnresolved = counts.pending > 0;

          return (
            <button
              key={chapter.id}
              onClick={() => onChapterSelect(chapter.id)}
              className={clsx(
                'w-full text-left px-3 py-2 border-b border-base-200 transition-colors',
                isSelected
                  ? 'bg-primary/10 border-l-2 border-l-primary'
                  : 'hover:bg-base-200 border-l-2 border-l-transparent'
              )}
            >
              <div className="flex items-start gap-2">
                {/* Chapter number */}
                <div
                  className={clsx(
                    'flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium',
                    isSelected
                      ? 'bg-primary text-primary-content'
                      : 'bg-base-300 text-base-content/70'
                  )}
                >
                  {index + 1}
                </div>

                {/* Chapter info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1">
                    <span
                      className={clsx(
                        'text-sm font-medium truncate',
                        isSelected ? 'text-primary' : 'text-base-content'
                      )}
                    >
                      {chapter.name}
                    </span>

                    {/* Video status icon */}
                    {chapter.hasVideo ? (
                      <CheckCircle2 size={12} className="flex-shrink-0 text-success" />
                    ) : (
                      <AlertCircle size={12} className="flex-shrink-0 text-warning" />
                    )}
                  </div>

                  {/* Metadata row */}
                  <div className="flex items-center gap-3 mt-0.5 text-xs text-base-content/50">
                    {/* Duration */}
                    <span className="flex items-center gap-1">
                      <Clock size={10} />
                      {formatDuration(chapter.duration)}
                    </span>

                    {/* Comment count */}
                    {counts.total > 0 && (
                      <span
                        className={clsx(
                          'flex items-center gap-1',
                          hasUnresolved ? 'text-warning' : 'text-success'
                        )}
                      >
                        <MessageCircle size={10} />
                        {counts.pending > 0 ? (
                          <span>
                            {counts.pending}/{counts.total}
                          </span>
                        ) : (
                          <span>{counts.total}</span>
                        )}
                      </span>
                    )}
                  </div>
                </div>

                {/* Comment badge */}
                {hasUnresolved && (
                  <div className="flex-shrink-0 badge badge-warning badge-sm">
                    {counts.pending}
                  </div>
                )}
              </div>
            </button>
          );
        })}
      </div>

      {/* Summary footer */}
      <div className="px-3 py-2 border-t border-base-300 bg-base-200/50">
        <div className="flex items-center justify-between text-xs text-base-content/60">
          <span className="flex items-center gap-1">
            <Clock size={12} />
            Total:{' '}
            {formatDuration(chapters.reduce((sum, ch) => sum + ch.duration, 0))}
          </span>
          <span className="flex items-center gap-1">
            <MessageCircle size={12} />
            {comments.length} comments
          </span>
        </div>
      </div>
    </div>
  );
}

export default ChapterSelector;
