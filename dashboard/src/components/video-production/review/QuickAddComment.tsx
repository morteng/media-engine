/**
 * QuickAddComment - Inline form for adding comments at current playhead position
 *
 * Features:
 * - Auto-fills timestamp from playhead
 * - Priority selector
 * - Keyboard shortcut support (Ctrl+Enter to submit)
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { MessageSquarePlus, Clock, AlertTriangle, Send, X } from 'lucide-react';
import clsx from 'clsx';
import type { CommentPriority, VideoChapter } from '@/api/types/video';

interface QuickAddCommentProps {
  /** Current chapter for the comment */
  currentChapter: VideoChapter | null;
  /** Current local frame in the chapter */
  currentFrame: number;
  /** Current time in seconds */
  currentTime: number;
  /** Called when submitting a new comment */
  onSubmit: (data: {
    componentId: string;
    text: string;
    frame: number;
    timestamp: number;
    priority: CommentPriority;
  }) => Promise<void>;
  /** Whether currently submitting */
  isSubmitting?: boolean;
  /** Optional className */
  className?: string;
}

const PRIORITY_OPTIONS: { value: CommentPriority; label: string; color: string }[] = [
  { value: 'low', label: 'Low', color: 'text-base-content/50' },
  { value: 'normal', label: 'Normal', color: 'text-base-content' },
  { value: 'high', label: 'High', color: 'text-warning' },
  { value: 'urgent', label: 'Urgent', color: 'text-error' },
];

export function QuickAddComment({
  currentChapter,
  currentFrame,
  currentTime,
  onSubmit,
  isSubmitting = false,
  className = '',
}: QuickAddCommentProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [text, setText] = useState('');
  const [priority, setPriority] = useState<CommentPriority>('normal');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Focus textarea when expanded
  useEffect(() => {
    if (isExpanded && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [isExpanded]);

  // Format time for display
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Handle submit
  const handleSubmit = useCallback(async () => {
    if (!currentChapter || !text.trim()) return;

    await onSubmit({
      componentId: currentChapter.id,
      text: text.trim(),
      frame: currentFrame,
      timestamp: currentTime,
      priority,
    });

    // Reset form
    setText('');
    setPriority('normal');
    setIsExpanded(false);
  }, [currentChapter, text, currentFrame, currentTime, priority, onSubmit]);

  // Handle keyboard shortcuts
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        handleSubmit();
      } else if (e.key === 'Escape') {
        setIsExpanded(false);
        setText('');
      }
    },
    [handleSubmit]
  );

  // Cancel button
  const handleCancel = () => {
    setIsExpanded(false);
    setText('');
    setPriority('normal');
  };

  if (!currentChapter) {
    return (
      <div className={clsx('flex items-center gap-2 text-base-content/50', className)}>
        <MessageSquarePlus size={16} />
        <span className="text-sm">Select a chapter to add comments</span>
      </div>
    );
  }

  // Collapsed state - just a button
  if (!isExpanded) {
    return (
      <button
        onClick={() => setIsExpanded(true)}
        className={clsx(
          'btn btn-sm btn-outline btn-primary gap-2',
          className
        )}
      >
        <MessageSquarePlus size={16} />
        <span>Add Comment at {formatTime(currentTime)}</span>
      </button>
    );
  }

  // Expanded state - full form
  return (
    <div className={clsx('bg-base-200 rounded-lg p-3', className)}>
      <div className="flex items-center gap-2 mb-2">
        <Clock size={14} className="text-base-content/50" />
        <span className="text-sm text-base-content/70">
          Comment at {formatTime(currentTime)} in {currentChapter.name}
        </span>
        <div className="flex-1" />
        <button
          onClick={handleCancel}
          className="btn btn-ghost btn-xs btn-square"
        >
          <X size={14} />
        </button>
      </div>

      <textarea
        ref={textareaRef}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="What needs to change?"
        className="textarea textarea-bordered w-full resize-none text-sm"
        rows={2}
        disabled={isSubmitting}
      />

      <div className="flex items-center gap-3 mt-2">
        {/* Priority selector */}
        <div className="flex items-center gap-1">
          <AlertTriangle size={14} className="text-base-content/50" />
          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value as CommentPriority)}
            className="select select-xs select-bordered"
            disabled={isSubmitting}
          >
            {PRIORITY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex-1" />

        {/* Submit hint */}
        <span className="text-xs text-base-content/40">
          Ctrl+Enter to submit
        </span>

        {/* Submit button */}
        <button
          onClick={handleSubmit}
          disabled={!text.trim() || isSubmitting}
          className="btn btn-sm btn-primary gap-1"
        >
          {isSubmitting ? (
            <span className="loading loading-spinner loading-xs" />
          ) : (
            <Send size={14} />
          )}
          Add
        </button>
      </div>
    </div>
  );
}

export default QuickAddComment;
