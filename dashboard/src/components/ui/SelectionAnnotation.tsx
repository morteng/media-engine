import { useState, useEffect, useCallback, useRef } from 'react';
import { X, Sparkles, MessageSquare } from 'lucide-react';
import { Button } from './Button';
import { submitAITask, type AIContentSelection } from '@/api/client';
import './SelectionAnnotation.css';

interface SelectionAnnotationProps {
  documentPath: string;
  documentTitle: string;
  contentRef: React.RefObject<HTMLElement | null>;
  onAnnotationSubmitted?: () => void;
}

interface SelectionState {
  text: string;
  startLine: number;
  endLine: number;
  x: number;
  y: number;
}

export function SelectionAnnotation({
  documentPath,
  documentTitle,
  contentRef,
  onAnnotationSubmitted,
}: SelectionAnnotationProps) {
  const [selection, setSelection] = useState<SelectionState | null>(null);
  const [comment, setComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const popupRef = useRef<HTMLDivElement>(null);

  const getLineNumber = useCallback((node: Node, offset: number): number => {
    if (!contentRef.current) return 1;

    // Get text content up to the selection point
    const range = document.createRange();
    range.setStart(contentRef.current, 0);
    range.setEnd(node, offset);
    const textBefore = range.toString();

    // Count newlines to determine line number
    return (textBefore.match(/\n/g) || []).length + 1;
  }, [contentRef]);

  const handleMouseUp = useCallback(() => {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || !contentRef.current) {
      return;
    }

    // Check if selection is within our content area
    const range = sel.getRangeAt(0);
    if (!contentRef.current.contains(range.commonAncestorContainer)) {
      return;
    }

    const text = sel.toString().trim();
    if (!text || text.length < 3) {
      return;
    }

    // Get line numbers
    const startLine = getLineNumber(range.startContainer, range.startOffset);
    const endLine = getLineNumber(range.endContainer, range.endOffset);

    // Get position for popup
    const rect = range.getBoundingClientRect();
    const x = rect.left + rect.width / 2;
    const y = rect.bottom + 10;

    setSelection({
      text: text.slice(0, 500), // Limit selection length
      startLine,
      endLine,
      x: Math.min(x, window.innerWidth - 220),
      y: Math.min(y, window.innerHeight - 200),
    });
    setComment('');
  }, [contentRef, getLineNumber]);

  const handleClose = useCallback(() => {
    setSelection(null);
    setComment('');
  }, []);

  const handleSubmit = async () => {
    if (!selection || !comment.trim()) return;

    setIsSubmitting(true);
    try {
      const contentSelection: AIContentSelection = {
        path: documentPath,
        title: documentTitle,
        content: selection.text,
        content_type: 'document',
        target_id: `lines-${selection.startLine}-${selection.endLine}`,
        notes: [{
          text: comment.trim(),
          priority: 'normal',
        }],
        metadata: {
          startLine: selection.startLine,
          endLine: selection.endLine,
          selectedText: selection.text,
        },
      };

      await submitAITask({
        operation: 'analyze',
        selections: [contentSelection],
        instructions: `Review and analyze the following selection from "${documentTitle}" (lines ${selection.startLine}-${selection.endLine}):\n\n"${selection.text}"\n\nUser comment: ${comment.trim()}`,
        priority: 'normal',
      });

      handleClose();
      onAnnotationSubmitted?.();
    } catch (error) {
      console.error('Failed to submit annotation:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Close popup when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (popupRef.current && !popupRef.current.contains(e.target as Node)) {
        handleClose();
      }
    };

    if (selection) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [selection, handleClose]);

  // Add mouseup listener to content area
  useEffect(() => {
    const element = contentRef.current;
    if (!element) return;

    element.addEventListener('mouseup', handleMouseUp);
    return () => element.removeEventListener('mouseup', handleMouseUp);
  }, [contentRef, handleMouseUp]);

  if (!selection) return null;

  return (
    <div
      ref={popupRef}
      className="selection-popup"
      style={{ left: selection.x, top: selection.y }}
    >
      <div className="selection-popup__header">
        <span className="selection-popup__title">
          <MessageSquare size={14} />
          Add Comment (L{selection.startLine}
          {selection.endLine !== selection.startLine && `-${selection.endLine}`})
        </span>
        <button className="selection-popup__close" onClick={handleClose}>
          <X size={14} />
        </button>
      </div>

      <div className="selection-popup__quote">
        "{selection.text}"
      </div>

      <textarea
        className="selection-popup__input"
        placeholder="Add your comment or question for AI review..."
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        autoFocus
      />

      <div className="selection-popup__actions">
        <Button variant="ghost" size="sm" onClick={handleClose}>
          Cancel
        </Button>
        <Button
          variant="primary"
          size="sm"
          onClick={handleSubmit}
          disabled={!comment.trim() || isSubmitting}
        >
          <Sparkles size={14} />
          {isSubmitting ? 'Queuing...' : 'Queue for AI'}
        </Button>
      </div>
    </div>
  );
}
