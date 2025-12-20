import { useState } from 'react';
import { Sparkles } from 'lucide-react';
import clsx from 'clsx';
import { AIQuickModal } from './AIQuickModal';

interface AskAIButtonProps {
  /** Content to process */
  content: string;
  /** Title/identifier for the content */
  title: string;
  /** Path to the document */
  path: string;
  /** Content type (chapter, script, scene, etc.) */
  contentType: string;
  /** Optional target ID (e.g., scene ID) */
  targetId?: string;
  /** Optional notes attached to this content */
  notes?: Array<{ text: string; priority: string }>;
  /** Button size variant */
  size?: 'sm' | 'md';
  /** Additional class names */
  className?: string;
  /** Callback when AI processing completes */
  onComplete?: (result: { processed: string; changesSummary: string }) => void;
}

export function AskAIButton({
  content,
  title,
  path,
  contentType,
  targetId,
  notes,
  size = 'sm',
  className,
  onComplete,
}: AskAIButtonProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        onClick={() => setIsModalOpen(true)}
        className={clsx(
          'inline-flex items-center gap-1 rounded transition-colors',
          size === 'sm' && 'px-2 py-1 text-xs',
          size === 'md' && 'px-3 py-1.5 text-sm',
          'bg-accent/10 text-accent hover:bg-accent/20',
          'border border-accent/30 hover:border-accent/50',
          className
        )}
        title="Process with AI"
      >
        <Sparkles className={clsx(size === 'sm' ? 'h-3 w-3' : 'h-4 w-4')} />
        <span>Ask AI</span>
      </button>

      <AIQuickModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        content={content}
        title={title}
        path={path}
        contentType={contentType}
        targetId={targetId}
        notes={notes}
        onComplete={(result) => {
          onComplete?.(result);
          setIsModalOpen(false);
        }}
      />
    </>
  );
}
