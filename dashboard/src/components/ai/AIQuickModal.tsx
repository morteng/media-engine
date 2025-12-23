import { useState, useEffect } from 'react';
import { X, Sparkles, Copy, Check, AlertCircle } from 'lucide-react';
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
      <div className="relative w-full max-w-2xl max-h-[90vh] overflow-hidden rounded-lg bg-base-200 border border-base-300 shadow-xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-base-300">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            <h2 className="font-semibold text-lg">Ask AI</h2>
          </div>
          <button
            onClick={onClose}
            className="btn btn-ghost btn-sm btn-square"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {!isConfigured && (
            <div className="alert alert-warning">
              <AlertCircle className="h-5 w-5" />
              <div>
                <p className="font-medium">AI not configured</p>
                <p className="text-sm opacity-70">
                  Go to the AI Assist page to configure your API key.
                </p>
              </div>
            </div>
          )}

          {/* Source Preview */}
          <div className="form-control">
            <label className="label">
              <span className="label-text font-medium">Source</span>
            </label>
            <div className="p-3 rounded-lg bg-base-100 border border-base-300">
              <p className="font-medium text-sm">{title}</p>
              <p className="text-xs text-base-content/60 mt-1 truncate">{path}</p>
              {notes && notes.length > 0 && (
                <div className="mt-2 pt-2 border-t border-base-300">
                  <p className="text-xs text-base-content/60">
                    {notes.length} note{notes.length !== 1 ? 's' : ''} attached
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Operation */}
          <div className="form-control">
            <label className="label">
              <span className="label-text font-medium">Operation</span>
            </label>
            <select
              value={operation}
              onChange={(e) => setOperation(e.target.value)}
              className="select select-bordered w-full"
            >
              {operations.map((op) => (
                <option key={op.id} value={op.id}>
                  {op.name}
                </option>
              ))}
            </select>
          </div>

          {/* Target Language (for translate operation) */}
          {operation === 'translate' && (
            <div className="form-control">
              <label className="label">
                <span className="label-text font-medium">Target Language</span>
              </label>
              <input
                type="text"
                value={targetLanguage}
                onChange={(e) => setTargetLanguage(e.target.value)}
                placeholder="e.g., Norwegian, Spanish, French"
                className="input input-bordered w-full"
              />
            </div>
          )}

          {/* Instructions */}
          <div className="form-control">
            <label className="label">
              <span className="label-text font-medium">
                Instructions <span className="font-normal text-base-content/60">(optional)</span>
              </span>
            </label>
            <textarea
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              placeholder="Add specific instructions for the AI..."
              rows={3}
              className="textarea textarea-bordered w-full"
            />
          </div>

          {/* Result */}
          {result && (
            <div className="form-control">
              <div className="flex items-center justify-between mb-1">
                <label className="label">
                  <span className="label-text font-medium">Result</span>
                </label>
                <button
                  onClick={handleCopy}
                  className="btn btn-ghost btn-xs gap-1"
                >
                  {copied ? (
                    <>
                      <Check className="h-3 w-3" />
                      Copied
                    </>
                  ) : (
                    <>
                      <Copy className="h-3 w-3" />
                      Copy
                    </>
                  )}
                </button>
              </div>
              {result.changesSummary && (
                <p className="text-xs text-base-content/60 mb-2">{result.changesSummary}</p>
              )}
              <div className="p-3 rounded-lg bg-base-100 border border-base-300 max-h-48 overflow-y-auto">
                <pre className="text-sm whitespace-pre-wrap font-mono">{result.processed}</pre>
              </div>
            </div>
          )}

          {/* Error */}
          {processAI.isError && (
            <div className="alert alert-error">
              <AlertCircle className="h-5 w-5" />
              <div>
                <p className="font-medium">Processing failed</p>
                <p className="text-sm opacity-70">
                  {processAI.error instanceof Error ? processAI.error.message : 'Unknown error'}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 p-4 border-t border-base-300">
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
              <Sparkles className="h-4 w-4" />
              Process
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
