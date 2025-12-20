import { useState, useEffect } from 'react';
import { X, Sparkles, ChevronDown, Copy, Check, AlertCircle } from 'lucide-react';
import { useAIOperations, useAIConfig, useProcessAI } from '@/hooks/useAI';
import { Button } from '@/components/ui/Button';

interface AIQuickModalProps {
  isOpen: boolean;
  onClose: () => void;
  content: string;
  title: string;
  path: string;
  contentType: string;
  targetId?: string;
  notes?: Array<{ text: string; priority: string }>;
  onComplete?: (result: { processed: string; changesSummary: string }) => void;
}

export function AIQuickModal({
  isOpen,
  onClose,
  content,
  title,
  path,
  contentType,
  targetId,
  notes,
  onComplete,
}: AIQuickModalProps) {
  const [operation, setOperation] = useState('improve');
  const [instructions, setInstructions] = useState('');
  const [targetLanguage, setTargetLanguage] = useState('');
  const [result, setResult] = useState<{ processed: string; changesSummary: string } | null>(null);
  const [copied, setCopied] = useState(false);

  const { data: operationsData } = useAIOperations();
  const { data: config } = useAIConfig();
  const processAI = useProcessAI();

  const operations = operationsData?.operations || [];

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setResult(null);
      setInstructions('');
      setCopied(false);
    }
  }, [isOpen]);

  const handleProcess = async () => {
    try {
      const response = await processAI.mutateAsync({
        operation,
        selections: [
          {
            path,
            content,
            title,
            content_type: contentType,
            target_id: targetId,
            notes: notes,
          },
        ],
        instructions,
        target_language: operation === 'translate' ? targetLanguage : undefined,
      });

      if (response.status === 'success' && response.results.length > 0) {
        const processed = {
          processed: response.results[0].processed,
          changesSummary: response.results[0].changes_summary,
        };
        setResult(processed);
      }
    } catch (error) {
      console.error('AI processing failed:', error);
    }
  };

  const handleCopy = () => {
    if (result) {
      navigator.clipboard.writeText(result.processed);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleApply = () => {
    if (result) {
      onComplete?.(result);
    }
  };

  if (!isOpen) return null;

  const isConfigured = config?.configured && config?.has_api_key;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-2xl max-h-[90vh] overflow-hidden rounded-lg bg-surface border border-border shadow-xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-accent" />
            <h2 className="font-semibold text-lg">Ask AI</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-surface-hover transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {!isConfigured && (
            <div className="flex items-start gap-2 p-3 rounded-lg bg-warning/10 border border-warning/30">
              <AlertCircle className="h-5 w-5 text-warning flex-shrink-0 mt-0.5" />
              <div className="text-sm">
                <p className="font-medium text-warning">AI not configured</p>
                <p className="text-text-secondary mt-1">
                  Go to the AI Assist page to configure your API key.
                </p>
              </div>
            </div>
          )}

          {/* Source Preview */}
          <div>
            <label className="block text-sm font-medium mb-1">Source</label>
            <div className="p-3 rounded-lg bg-background border border-border">
              <p className="font-medium text-sm">{title}</p>
              <p className="text-xs text-text-secondary mt-1 truncate">{path}</p>
              {notes && notes.length > 0 && (
                <div className="mt-2 pt-2 border-t border-border">
                  <p className="text-xs text-text-secondary mb-1">
                    {notes.length} note{notes.length !== 1 ? 's' : ''} attached
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Operation */}
          <div>
            <label className="block text-sm font-medium mb-1">Operation</label>
            <div className="relative">
              <select
                value={operation}
                onChange={(e) => setOperation(e.target.value)}
                className="w-full appearance-none bg-background border border-border rounded-lg px-3 py-2 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
              >
                {operations.map((op) => (
                  <option key={op.id} value={op.id}>
                    {op.name}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-secondary pointer-events-none" />
            </div>
          </div>

          {/* Target Language (for translate operation) */}
          {operation === 'translate' && (
            <div>
              <label className="block text-sm font-medium mb-1">Target Language</label>
              <input
                type="text"
                value={targetLanguage}
                onChange={(e) => setTargetLanguage(e.target.value)}
                placeholder="e.g., Norwegian, Spanish, French"
                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
              />
            </div>
          )}

          {/* Instructions */}
          <div>
            <label className="block text-sm font-medium mb-1">
              Instructions <span className="text-text-secondary font-normal">(optional)</span>
            </label>
            <textarea
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              placeholder="Add specific instructions for the AI..."
              rows={3}
              className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-accent/50"
            />
          </div>

          {/* Result */}
          {result && (
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-sm font-medium">Result</label>
                <button
                  onClick={handleCopy}
                  className="inline-flex items-center gap-1 text-xs text-text-secondary hover:text-text transition-colors"
                >
                  {copied ? (
                    <>
                      <Check className="h-3 w-3" />
                      <span>Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-3 w-3" />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              </div>
              {result.changesSummary && (
                <p className="text-xs text-text-secondary mb-2">{result.changesSummary}</p>
              )}
              <div className="p-3 rounded-lg bg-background border border-border max-h-48 overflow-y-auto">
                <pre className="text-sm whitespace-pre-wrap font-mono">{result.processed}</pre>
              </div>
            </div>
          )}

          {/* Error */}
          {processAI.isError && (
            <div className="flex items-start gap-2 p-3 rounded-lg bg-danger/10 border border-danger/30">
              <AlertCircle className="h-5 w-5 text-danger flex-shrink-0 mt-0.5" />
              <div className="text-sm">
                <p className="font-medium text-danger">Processing failed</p>
                <p className="text-text-secondary mt-1">
                  {processAI.error instanceof Error ? processAI.error.message : 'Unknown error'}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 p-4 border-t border-border">
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          {result ? (
            <Button onClick={handleApply}>
              Apply Changes
            </Button>
          ) : (
            <Button
              onClick={handleProcess}
              loading={processAI.isPending}
              disabled={!isConfigured || (operation === 'translate' && !targetLanguage)}
            >
              <Sparkles className="h-4 w-4 mr-1" />
              Process
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
