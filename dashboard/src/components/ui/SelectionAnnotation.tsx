import { useState, useEffect, useCallback, useRef } from 'react';
import { X, Sparkles, MessageSquare, Edit2, Trash2 } from 'lucide-react';
import { submitAITask, type AIContentSelection } from '@/api/client';

interface SelectionAnnotationProps {
  documentPath: string;
  documentTitle: string;
  contentRef: React.RefObject<HTMLElement | null>;
  onAnnotationSubmitted?: () => void;
}

interface SelectionState {
  text: string;
  startOffset: number;
  endOffset: number;
  x: number;
  y: number;
}

interface Annotation {
  id: string;
  text: string;
  comment: string;
  startOffset: number;
  endOffset: number;
  submittedAt: Date;
}

// Generate a unique ID for annotations
function generateId(): string {
  return `ann-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
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
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [activeAnnotation, setActiveAnnotation] = useState<Annotation | null>(null);
  const [editingComment, setEditingComment] = useState('');
  const popupRef = useRef<HTMLDivElement>(null);
  const highlightRef = useRef<HTMLDivElement>(null);

  // Get text offset within the content element
  const getTextOffset = useCallback((node: Node, offset: number): number => {
    if (!contentRef.current) return 0;

    const walker = document.createTreeWalker(
      contentRef.current,
      NodeFilter.SHOW_TEXT,
      null
    );

    let totalOffset = 0;
    let currentNode = walker.nextNode();

    while (currentNode) {
      if (currentNode === node) {
        return totalOffset + offset;
      }
      totalOffset += currentNode.textContent?.length || 0;
      currentNode = walker.nextNode();
    }

    return totalOffset;
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

    // Get offsets
    const startOffset = getTextOffset(range.startContainer, range.startOffset);
    const endOffset = getTextOffset(range.endContainer, range.endOffset);

    // Get position for popup
    const rect = range.getBoundingClientRect();
    const x = rect.left + rect.width / 2;
    const y = rect.bottom + 10;

    setSelection({
      text: text.slice(0, 500), // Limit selection length
      startOffset,
      endOffset,
      x: Math.min(x, window.innerWidth - 220),
      y: Math.min(y, window.innerHeight - 200),
    });
    setComment('');
    setActiveAnnotation(null);
  }, [contentRef, getTextOffset]);

  const handleClose = useCallback(() => {
    setSelection(null);
    setComment('');
    setActiveAnnotation(null);
    setEditingComment('');
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
        target_id: `offset-${selection.startOffset}-${selection.endOffset}`,
        notes: [{
          text: comment.trim(),
          priority: 'normal',
        }],
        metadata: {
          startOffset: selection.startOffset,
          endOffset: selection.endOffset,
          selectedText: selection.text,
        },
      };

      await submitAITask({
        operation: 'analyze',
        selections: [contentSelection],
        instructions: `Review and analyze the following selection from "${documentTitle}":\n\n"${selection.text}"\n\nUser comment: ${comment.trim()}`,
        priority: 'normal',
      });

      // Store the annotation locally
      const newAnnotation: Annotation = {
        id: generateId(),
        text: selection.text,
        comment: comment.trim(),
        startOffset: selection.startOffset,
        endOffset: selection.endOffset,
        submittedAt: new Date(),
      };
      setAnnotations(prev => [...prev, newAnnotation]);

      handleClose();
      onAnnotationSubmitted?.();
    } catch (error) {
      console.error('Failed to submit annotation:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAnnotationClick = useCallback((annotation: Annotation, event: MouseEvent) => {
    event.stopPropagation();
    setActiveAnnotation(annotation);
    setEditingComment(annotation.comment);
    setSelection(null);
  }, []);

  const handleDeleteAnnotation = useCallback((id: string) => {
    setAnnotations(prev => prev.filter(a => a.id !== id));
    setActiveAnnotation(null);
  }, []);

  const handleUpdateAnnotation = useCallback(async () => {
    if (!activeAnnotation || !editingComment.trim()) return;

    // Resubmit to AI queue with updated comment
    setIsSubmitting(true);
    try {
      const contentSelection: AIContentSelection = {
        path: documentPath,
        title: documentTitle,
        content: activeAnnotation.text,
        content_type: 'document',
        target_id: `offset-${activeAnnotation.startOffset}-${activeAnnotation.endOffset}`,
        notes: [{
          text: editingComment.trim(),
          priority: 'normal',
        }],
        metadata: {
          startOffset: activeAnnotation.startOffset,
          endOffset: activeAnnotation.endOffset,
          selectedText: activeAnnotation.text,
          updated: true,
        },
      };

      await submitAITask({
        operation: 'analyze',
        selections: [contentSelection],
        instructions: `Review and analyze the following selection from "${documentTitle}":\n\n"${activeAnnotation.text}"\n\nUpdated user comment: ${editingComment.trim()}`,
        priority: 'normal',
      });

      // Update the annotation locally
      setAnnotations(prev => prev.map(a =>
        a.id === activeAnnotation.id
          ? { ...a, comment: editingComment.trim() }
          : a
      ));

      handleClose();
      onAnnotationSubmitted?.();
    } catch (error) {
      console.error('Failed to update annotation:', error);
    } finally {
      setIsSubmitting(false);
    }
  }, [activeAnnotation, editingComment, documentPath, documentTitle, handleClose, onAnnotationSubmitted]);

  // Apply highlights to content
  useEffect(() => {
    if (!contentRef.current || annotations.length === 0) return;

    // Remove existing highlights
    const existingHighlights = contentRef.current.querySelectorAll('.ai-annotation-highlight');
    existingHighlights.forEach(el => {
      const parent = el.parentNode;
      if (parent) {
        parent.replaceChild(document.createTextNode(el.textContent || ''), el);
        parent.normalize();
      }
    });

    // Sort annotations by start offset (descending) to apply from end to start
    const sortedAnnotations = [...annotations].sort((a, b) => b.startOffset - a.startOffset);

    // Apply highlights using Range API
    for (const annotation of sortedAnnotations) {
      try {
        const walker = document.createTreeWalker(
          contentRef.current,
          NodeFilter.SHOW_TEXT,
          null
        );

        let currentOffset = 0;
        let startNode: Node | null = null;
        let endNode: Node | null = null;
        let startNodeOffset = 0;
        let endNodeOffset = 0;
        let node = walker.nextNode();

        while (node) {
          const nodeLength = node.textContent?.length || 0;

          if (!startNode && currentOffset + nodeLength > annotation.startOffset) {
            startNode = node;
            startNodeOffset = annotation.startOffset - currentOffset;
          }

          if (!endNode && currentOffset + nodeLength >= annotation.endOffset) {
            endNode = node;
            endNodeOffset = annotation.endOffset - currentOffset;
            break;
          }

          currentOffset += nodeLength;
          node = walker.nextNode();
        }

        if (startNode && endNode) {
          const range = document.createRange();
          range.setStart(startNode, startNodeOffset);
          range.setEnd(endNode, endNodeOffset);

          const highlight = document.createElement('mark');
          highlight.className = 'ai-annotation-highlight bg-warning/30 hover:bg-warning/50 cursor-pointer rounded px-0.5 transition-colors';
          highlight.dataset.annotationId = annotation.id;
          highlight.title = `AI Comment: ${annotation.comment.slice(0, 50)}${annotation.comment.length > 50 ? '...' : ''}`;

          // Add click handler
          highlight.addEventListener('click', (e) => handleAnnotationClick(annotation, e));

          range.surroundContents(highlight);
        }
      } catch (error) {
        // Range operations can fail if DOM has changed
        console.warn('Could not apply highlight:', error);
      }
    }

    // Cleanup function
    return () => {
      if (!contentRef.current) return;
      const highlights = contentRef.current.querySelectorAll('.ai-annotation-highlight');
      highlights.forEach(el => {
        el.removeEventListener('click', handleAnnotationClick as unknown as EventListener);
      });
    };
  }, [annotations, contentRef, handleAnnotationClick]);

  // Close popup when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (popupRef.current && !popupRef.current.contains(e.target as Node)) {
        // Don't close if clicking on a highlight
        if ((e.target as HTMLElement).classList?.contains('ai-annotation-highlight')) {
          return;
        }
        handleClose();
      }
    };

    if (selection || activeAnnotation) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [selection, activeAnnotation, handleClose]);

  // Add mouseup listener to content area
  useEffect(() => {
    const element = contentRef.current;
    if (!element) return;

    element.addEventListener('mouseup', handleMouseUp);
    return () => element.removeEventListener('mouseup', handleMouseUp);
  }, [contentRef, handleMouseUp]);

  // Clear annotations when document changes
  useEffect(() => {
    setAnnotations([]);
    setActiveAnnotation(null);
    setSelection(null);
  }, [documentPath]);

  // Render popup for new selection
  if (selection) {
    return (
      <div
        ref={popupRef}
        className="fixed z-50 w-80 bg-base-200 rounded-xl shadow-2xl border border-base-300 overflow-hidden"
        style={{ left: selection.x, top: selection.y, transform: 'translateX(-50%)' }}
      >
        <div className="flex items-center justify-between px-3 py-2 bg-base-300 border-b border-base-content/10">
          <span className="flex items-center gap-2 text-sm font-medium">
            <MessageSquare size={14} className="text-primary" />
            Add AI Comment
          </span>
          <button
            className="btn btn-ghost btn-xs btn-square"
            onClick={handleClose}
          >
            <X size={14} />
          </button>
        </div>

        <div className="px-3 py-2 text-xs text-base-content/60 bg-base-300/50 border-b border-base-content/10 max-h-20 overflow-y-auto italic">
          "{selection.text}"
        </div>

        <div className="p-3">
          <textarea
            className="textarea textarea-bordered w-full text-sm resize-none"
            placeholder="Add your comment or question for AI review..."
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            rows={3}
            autoFocus
          />
        </div>

        <div className="flex items-center justify-end gap-2 px-3 py-2 border-t border-base-content/10">
          <button className="btn btn-ghost btn-sm" onClick={handleClose}>
            Cancel
          </button>
          <button
            className="btn btn-primary btn-sm gap-1"
            onClick={handleSubmit}
            disabled={!comment.trim() || isSubmitting}
          >
            <Sparkles size={14} />
            {isSubmitting ? 'Queuing...' : 'Queue for AI'}
          </button>
        </div>
      </div>
    );
  }

  // Render popup for viewing/editing existing annotation
  if (activeAnnotation) {
    return (
      <div
        ref={popupRef}
        className="fixed z-50 w-80 bg-base-200 rounded-xl shadow-2xl border border-base-300 overflow-hidden"
        style={{ left: '50%', top: '30%', transform: 'translateX(-50%)' }}
      >
        <div className="flex items-center justify-between px-3 py-2 bg-warning/20 border-b border-base-content/10">
          <span className="flex items-center gap-2 text-sm font-medium">
            <MessageSquare size={14} className="text-warning" />
            AI Comment
          </span>
          <button
            className="btn btn-ghost btn-xs btn-square"
            onClick={handleClose}
          >
            <X size={14} />
          </button>
        </div>

        <div className="px-3 py-2 text-xs text-base-content/60 bg-base-300/50 border-b border-base-content/10 max-h-20 overflow-y-auto italic">
          "{activeAnnotation.text}"
        </div>

        <div className="p-3">
          <textarea
            className="textarea textarea-bordered w-full text-sm resize-none"
            placeholder="Edit your comment..."
            value={editingComment}
            onChange={(e) => setEditingComment(e.target.value)}
            rows={3}
            autoFocus
          />
          <div className="text-xs text-base-content/50 mt-1">
            Submitted {activeAnnotation.submittedAt.toLocaleString()}
          </div>
        </div>

        <div className="flex items-center justify-between gap-2 px-3 py-2 border-t border-base-content/10">
          <button
            className="btn btn-ghost btn-sm btn-error gap-1"
            onClick={() => handleDeleteAnnotation(activeAnnotation.id)}
          >
            <Trash2 size={14} />
            Remove
          </button>
          <div className="flex gap-2">
            <button className="btn btn-ghost btn-sm" onClick={handleClose}>
              Cancel
            </button>
            <button
              className="btn btn-warning btn-sm gap-1"
              onClick={handleUpdateAnnotation}
              disabled={!editingComment.trim() || editingComment === activeAnnotation.comment || isSubmitting}
            >
              <Edit2 size={14} />
              {isSubmitting ? 'Updating...' : 'Update'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Render annotation count badge if there are annotations
  if (annotations.length > 0) {
    return (
      <div
        ref={highlightRef}
        className="fixed bottom-4 right-4 z-40"
      >
        <div className="badge badge-warning gap-1 shadow-lg">
          <MessageSquare size={12} />
          {annotations.length} comment{annotations.length !== 1 ? 's' : ''}
        </div>
      </div>
    );
  }

  return null;
}
