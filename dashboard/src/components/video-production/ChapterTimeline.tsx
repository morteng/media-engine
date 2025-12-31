/**
 * ChapterTimeline - Timeline showing all video chapters with proportional widths
 *
 * Features:
 * - Proportional chapter blocks based on duration
 * - Click to seek within timeline
 * - Selected chapter highlighting
 * - Playhead indicator
 */

import { useCallback, useRef } from 'react';
import type { VideoChapter, ChapterTimelineData } from '@/api/types/video';

// Chapter colors for visual distinction
const CHAPTER_COLORS = [
  'bg-cyan-600',
  'bg-purple-600',
  'bg-emerald-600',
  'bg-amber-600',
  'bg-rose-600',
  'bg-indigo-600',
  'bg-teal-600',
  'bg-orange-600',
];

interface ChapterTimelineProps {
  /** Timeline data containing all chapters */
  timelineData: ChapterTimelineData;
  /** Currently selected chapter ID */
  selectedChapterId: string | null;
  /** Current global frame position */
  currentFrame: number;
  /** Called when user clicks to seek */
  onSeek: (globalFrame: number) => void;
  /** Called when user clicks a chapter */
  onChapterSelect: (chapterId: string) => void;
  /** Optional className */
  className?: string;
}

export function ChapterTimeline({
  timelineData,
  selectedChapterId,
  currentFrame,
  onSeek,
  onChapterSelect,
  className = '',
}: ChapterTimelineProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  const handleClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!containerRef.current || timelineData.totalFrames === 0) return;

      const rect = containerRef.current.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const percentage = clickX / rect.width;
      const globalFrame = Math.round(percentage * timelineData.totalFrames);

      onSeek(Math.max(0, Math.min(globalFrame, timelineData.totalFrames - 1)));
    },
    [timelineData.totalFrames, onSeek]
  );

  const handleChapterClick = useCallback(
    (e: React.MouseEvent, chapter: VideoChapter) => {
      e.stopPropagation();
      onChapterSelect(chapter.id);
    },
    [onChapterSelect]
  );

  // Calculate playhead position as percentage
  const playheadPosition =
    timelineData.totalFrames > 0
      ? (currentFrame / timelineData.totalFrames) * 100
      : 0;

  return (
    <div className={`relative ${className}`}>
      {/* Timeline container */}
      <div
        ref={containerRef}
        className="relative h-10 bg-base-300 rounded-lg overflow-hidden cursor-pointer"
        onClick={handleClick}
      >
        {/* Chapter blocks */}
        <div className="absolute inset-0 flex">
          {timelineData.chapters.map((chapter, index) => {
            const widthPercent =
              timelineData.totalFrames > 0
                ? (chapter.totalFrames / timelineData.totalFrames) * 100
                : 0;

            const isSelected = chapter.id === selectedChapterId;
            const colorClass = CHAPTER_COLORS[index % CHAPTER_COLORS.length];

            return (
              <div
                key={chapter.id}
                className={`
                  relative h-full transition-all duration-150
                  ${colorClass}
                  ${isSelected ? 'ring-2 ring-white ring-inset z-10' : 'opacity-80 hover:opacity-100'}
                  ${!chapter.hasVideo ? 'opacity-40' : ''}
                `}
                style={{ width: `${widthPercent}%` }}
                onClick={(e) => handleChapterClick(e, chapter)}
                title={`${chapter.name} (${formatDuration(chapter.duration)})`}
              >
                {/* Chapter label (only show if wide enough) */}
                {widthPercent > 8 && (
                  <div className="absolute inset-0 flex items-center justify-center px-1">
                    <span className="text-xs font-medium text-white truncate">
                      {chapter.name}
                    </span>
                  </div>
                )}

                {/* Chapter separator */}
                {index < timelineData.chapters.length - 1 && (
                  <div className="absolute right-0 top-0 bottom-0 w-px bg-base-100/50" />
                )}

                {/* No video indicator */}
                {!chapter.hasVideo && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-xs text-white/60">No video</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Playhead */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-white shadow-lg z-20 pointer-events-none"
          style={{ left: `${playheadPosition}%` }}
        >
          {/* Playhead handle */}
          <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-3 h-3 bg-white rounded-full shadow" />
        </div>
      </div>

      {/* Time labels */}
      <div className="flex justify-between mt-1 text-xs text-base-content/60">
        <span>{formatDuration(0)}</span>
        <span>{formatDuration(timelineData.totalDuration)}</span>
      </div>
    </div>
  );
}

/**
 * Format duration in seconds to MM:SS or HH:MM:SS
 */
function formatDuration(seconds: number): string {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  if (hrs > 0) {
    return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export default ChapterTimeline;
