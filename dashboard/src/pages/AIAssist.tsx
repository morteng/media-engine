import { useState } from 'react';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import {
  useAIConfig,
  useAIOperations,
  useProcessAI,
  useUpdateAIConfig,
  useAITasks,
  useSubmitAITask,
  useCancelAITask,
} from '@/hooks/useAI';
import { useStatus } from '@/hooks/useApi';
import { getDocuments, getFile } from '@/api/client';
import type { AIContentSelection, AITask } from '@/api/client';
import {
  Wand2,
  FileText,
  Check,
  X,
  Settings,
  Copy,
  Plus,
  Trash2,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  CheckCircle,
  Sparkles,
  Clock,
  Zap,
  ListTodo,
  Bot,
} from 'lucide-react';

type ProcessingMode = 'direct' | 'claude_code';

interface SelectionItem {
  path: string;
  title: string;
  content: string;
  contentType: string;
  targetId?: string;
  notes: Array<{ text: string; priority: string }>;
  selected: boolean;
}

interface AIResult {
  path: string;
  original: string;
  processed: string;
  changesSummary: string;
  applied?: boolean;
  expanded?: boolean;
}

export function AIAssist() {
  const [selections, setSelections] = useState<SelectionItem[]>([]);
  const [instructions, setInstructions] = useState('');
  const [operation, setOperation] = useState('improve');
  const [targetLanguage, setTargetLanguage] = useState('');
  const [priority, setPriority] = useState('normal');
  const [results, setResults] = useState<AIResult[]>([]);
  const [showSettings, setShowSettings] = useState(false);
  const [showAddContent, setShowAddContent] = useState(false);
  const [newApiKey, setNewApiKey] = useState('');
  const [mode, setMode] = useState<ProcessingMode>('claude_code');
  const [showTaskQueue, setShowTaskQueue] = useState(true);

  const { data: aiConfig, isLoading: configLoading } = useAIConfig();
  const { data: operationsData } = useAIOperations();
  const { data: status } = useStatus();
  const { data: tasksData, isLoading: tasksLoading } = useAITasks();
  const processAI = useProcessAI();
  const submitTask = useSubmitAITask();
  const cancelTask = useCancelAITask();
  const updateConfig = useUpdateAIConfig();

  const languages = status?.languages || ['en'];

  const handleAddDocument = async (path: string) => {
    try {
      const fileData = await getFile(path);
      const newSelection: SelectionItem = {
        path,
        title: fileData.filename || path.split('/').pop() || path,
        content: fileData.content || '',
        contentType: 'document',
        notes: [],
        selected: true,
      };
      setSelections(prev => [...prev, newSelection]);
      setShowAddContent(false);
    } catch (error) {
      console.error('Failed to load document:', error);
    }
  };

  const handleRemoveSelection = (path: string) => {
    setSelections(prev => prev.filter(s => s.path !== path));
  };

  const handleToggleSelection = (path: string) => {
    setSelections(prev =>
      prev.map(s => (s.path === path ? { ...s, selected: !s.selected } : s))
    );
  };

  const handleAddNote = (path: string, note: string) => {
    setSelections(prev =>
      prev.map(s =>
        s.path === path
          ? { ...s, notes: [...s.notes, { text: note, priority: 'medium' }] }
          : s
      )
    );
  };

  const handleProcess = async () => {
    const selectedItems = selections.filter(s => s.selected);
    if (selectedItems.length === 0) return;

    const apiSelections: AIContentSelection[] = selectedItems.map(s => ({
      path: s.path,
      content: s.content,
      title: s.title,
      content_type: s.contentType,
      target_id: s.targetId,
      notes: s.notes,
    }));

    if (mode === 'claude_code') {
      // Submit to task queue for Claude Code processing
      try {
        await submitTask.mutateAsync({
          operation,
          selections: apiSelections,
          instructions,
          priority,
          target_language: operation === 'translate' ? targetLanguage : undefined,
        });
        // Clear selections after successful submission
        setSelections([]);
        setInstructions('');
      } catch (error) {
        console.error('Failed to submit task:', error);
      }
    } else {
      // Direct API processing
      try {
        const response = await processAI.mutateAsync({
          operation,
          selections: apiSelections,
          instructions,
          target_language: operation === 'translate' ? targetLanguage : undefined,
        });

        if (response.status === 'success' || response.status === 'partial') {
          setResults(
            response.results.map(r => ({
              path: r.path,
              original: r.original,
              processed: r.processed,
              changesSummary: r.changes_summary,
              applied: false,
              expanded: true,
            }))
          );
        } else if (response.error) {
          setResults([
            {
              path: 'error',
              original: '',
              processed: response.error,
              changesSummary: 'Error occurred',
              applied: false,
              expanded: true,
            },
          ]);
        }
      } catch (error) {
        console.error('AI processing failed:', error);
      }
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const handleSaveConfig = async () => {
    await updateConfig.mutateAsync({
      api_key: newApiKey || undefined,
    });
    setNewApiKey('');
    setShowSettings(false);
  };

  const handleCancelTask = async (taskId: string) => {
    try {
      await cancelTask.mutateAsync(taskId);
    } catch (error) {
      console.error('Failed to cancel task:', error);
    }
  };

  if (configLoading) {
    return (
      <div className="page ai-page">
        <div className="page-loading">
          <Spinner size="lg" />
          <p>Loading AI configuration...</p>
        </div>
      </div>
    );
  }

  const stats = tasksData?.stats;
  const pendingCount = stats?.pending || 0;
  const processingCount = stats?.processing || 0;

  return (
    <div className="page ai-page">
      <header className="page-header">
        <div>
          <h1>
            <Wand2 size={24} /> AI Assist
          </h1>
          <p className="text-secondary">AI-powered content processing via Claude Code</p>
        </div>
        <div className="header-actions">
          {(pendingCount > 0 || processingCount > 0) && (
            <Badge variant="info">
              <Clock size={12} /> {pendingCount} pending, {processingCount} processing
            </Badge>
          )}
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setShowSettings(!showSettings)}
          >
            <Settings size={16} /> Settings
          </Button>
        </div>
      </header>

      {showSettings && (
        <Card className="settings-card">
          <CardHeader title="AI Settings" />
          <CardContent>
            <div className="settings-grid">
              <div className="form-group">
                <label>Processing Mode</label>
                <div className="mode-toggle">
                  <button
                    className={`mode-btn ${mode === 'claude_code' ? 'active' : ''}`}
                    onClick={() => setMode('claude_code')}
                  >
                    <Bot size={16} />
                    <span>Claude Code</span>
                    <small>Full tool access, file editing</small>
                  </button>
                  <button
                    className={`mode-btn ${mode === 'direct' ? 'active' : ''}`}
                    onClick={() => setMode('direct')}
                  >
                    <Zap size={16} />
                    <span>Direct API</span>
                    <small>Fast, text-only responses</small>
                  </button>
                </div>
              </div>

              {mode === 'direct' && (
                <>
                  <div className="form-group">
                    <label>Backend</label>
                    <div className="backend-info">
                      <Badge variant="default">{aiConfig?.backend || 'anthropic'}</Badge>
                      <span className="text-secondary">
                        {aiConfig?.backend === 'claude_code'
                          ? 'Using Claude Code CLI'
                          : 'Using Anthropic API'}
                      </span>
                    </div>
                  </div>

                  <div className="form-group">
                    <label>API Key</label>
                    <div className="api-key-input">
                      <input
                        type="password"
                        value={newApiKey}
                        onChange={e => setNewApiKey(e.target.value)}
                        placeholder={aiConfig?.has_api_key ? '********' : 'Enter API key'}
                      />
                      <Button
                        size="sm"
                        onClick={handleSaveConfig}
                        disabled={!newApiKey}
                      >
                        Save
                      </Button>
                    </div>
                    <p className="text-secondary text-sm">
                      Or set ANTHROPIC_API_KEY environment variable
                    </p>
                  </div>
                </>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {mode === 'claude_code' && (
        <Card className="info-card">
          <CardContent>
            <div className="info-content">
              <Bot size={24} className="text-primary" />
              <div>
                <h3>Claude Code Integration</h3>
                <p>
                  Tasks are queued and processed by your running Claude Code session.
                  Claude Code can edit files directly, run quality checks, and use all available skills.
                  Say <code>/process-ai-queue</code> in Claude Code to process pending tasks.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {mode === 'direct' && !aiConfig?.configured && (
        <Card className="warning-card">
          <CardContent>
            <div className="warning-content">
              <AlertCircle size={24} />
              <div>
                <h3>AI Not Configured</h3>
                <p>
                  Set your Anthropic API key in settings or use the ANTHROPIC_API_KEY
                  environment variable to enable direct API processing.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="ai-layout">
        <div className="ai-sidebar">
          <Card>
            <CardHeader
              title="Content Selection"
              action={
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => setShowAddContent(!showAddContent)}
                >
                  <Plus size={14} /> Add
                </Button>
              }
            />
            <CardContent>
              {showAddContent && (
                <ContentPicker
                  languages={languages}
                  onSelect={handleAddDocument}
                  onClose={() => setShowAddContent(false)}
                />
              )}

              {selections.length === 0 ? (
                <div className="empty-selection">
                  <FileText size={32} className="text-muted" />
                  <p>No content selected</p>
                  <p className="text-secondary text-sm">
                    Add documents or scenes to process
                  </p>
                </div>
              ) : (
                <div className="selection-list">
                  {selections.map(item => (
                    <SelectionCard
                      key={item.path}
                      item={item}
                      onToggle={() => handleToggleSelection(item.path)}
                      onRemove={() => handleRemoveSelection(item.path)}
                      onAddNote={note => handleAddNote(item.path, note)}
                    />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="ai-main">
          <Card>
            <CardHeader title="Processing Options" />
            <CardContent>
              <div className="form-group">
                <label>Operation</label>
                <select
                  value={operation}
                  onChange={e => setOperation(e.target.value)}
                  className="select-input"
                >
                  {operationsData?.operations.map(op => (
                    <option key={op.id} value={op.id}>
                      {op.name} - {op.description}
                    </option>
                  ))}
                </select>
              </div>

              {operation === 'translate' && (
                <div className="form-group">
                  <label>Target Language</label>
                  <select
                    value={targetLanguage}
                    onChange={e => setTargetLanguage(e.target.value)}
                    className="select-input"
                  >
                    <option value="">Select language...</option>
                    {languages.map(lang => (
                      <option key={lang} value={lang}>
                        {lang.toUpperCase()}
                      </option>
                    ))}
                    <option value="es">Spanish (es)</option>
                    <option value="de">German (de)</option>
                    <option value="fr">French (fr)</option>
                  </select>
                </div>
              )}

              {mode === 'claude_code' && (
                <div className="form-group">
                  <label>Priority</label>
                  <select
                    value={priority}
                    onChange={e => setPriority(e.target.value)}
                    className="select-input"
                  >
                    <option value="low">Low</option>
                    <option value="normal">Normal</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>
              )}

              <div className="form-group">
                <label>Instructions</label>
                <textarea
                  value={instructions}
                  onChange={e => setInstructions(e.target.value)}
                  placeholder={
                    mode === 'claude_code'
                      ? 'Detailed instructions for Claude Code... (e.g., "Improve clarity, add examples, then run quality check")'
                      : 'Add specific instructions for the AI... (optional)'
                  }
                  rows={4}
                  className="textarea-input"
                />
              </div>

              <Button
                onClick={handleProcess}
                disabled={
                  (mode === 'claude_code' ? submitTask.isPending : processAI.isPending) ||
                  selections.filter(s => s.selected).length === 0 ||
                  (mode === 'direct' && !aiConfig?.configured)
                }
                className="process-button"
              >
                {(mode === 'claude_code' ? submitTask.isPending : processAI.isPending) ? (
                  <>
                    <Spinner size="sm" /> {mode === 'claude_code' ? 'Submitting...' : 'Processing...'}
                  </>
                ) : (
                  <>
                    {mode === 'claude_code' ? <ListTodo size={16} /> : <Sparkles size={16} />}
                    {mode === 'claude_code' ? 'Submit to Queue' : 'Process Content'}
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Task Queue (Claude Code mode) */}
          {mode === 'claude_code' && (
            <Card className="queue-card">
              <CardHeader
                title="Task Queue"
                action={
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setShowTaskQueue(!showTaskQueue)}
                  >
                    {showTaskQueue ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </Button>
                }
              />
              {showTaskQueue && (
                <CardContent>
                  {tasksLoading ? (
                    <div className="queue-loading">
                      <Spinner size="sm" />
                      <span>Loading tasks...</span>
                    </div>
                  ) : tasksData?.tasks.length === 0 ? (
                    <div className="queue-empty">
                      <ListTodo size={24} className="text-muted" />
                      <p>No tasks in queue</p>
                      <p className="text-secondary text-sm">
                        Submit content above to add tasks
                      </p>
                    </div>
                  ) : (
                    <div className="queue-list">
                      {tasksData?.tasks.map(task => (
                        <TaskCard
                          key={task.id}
                          task={task}
                          onCancel={() => handleCancelTask(task.id)}
                        />
                      ))}
                    </div>
                  )}
                </CardContent>
              )}
            </Card>
          )}

          {/* Results (Direct API mode) */}
          {mode === 'direct' && results.length > 0 && (
            <Card className="results-card">
              <CardHeader
                title="Results"
                action={
                  <Badge variant="success">
                    <CheckCircle size={12} /> {results.length} processed
                  </Badge>
                }
              />
              <CardContent>
                <div className="results-list">
                  {results.map((result, index) => (
                    <ResultCard
                      key={index}
                      result={result}
                      onCopy={() => handleCopy(result.processed)}
                      onToggleExpand={() =>
                        setResults(prev =>
                          prev.map((r, i) =>
                            i === index ? { ...r, expanded: !r.expanded } : r
                          )
                        )
                      }
                    />
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      <style>{`
        .ai-page .page-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1.5rem;
        }

        .ai-page .page-header h1 {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .ai-page .header-actions {
          display: flex;
          gap: 0.75rem;
          align-items: center;
        }

        .ai-page .settings-card,
        .ai-page .info-card,
        .ai-page .warning-card {
          margin-bottom: 1.5rem;
        }

        .ai-page .settings-grid {
          display: grid;
          gap: 1rem;
        }

        .ai-page .mode-toggle {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 0.75rem;
        }

        .ai-page .mode-btn {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.25rem;
          padding: 1rem;
          border: 2px solid var(--border);
          border-radius: 8px;
          background: var(--bg-secondary);
          color: var(--text-primary);
          cursor: pointer;
          transition: all 0.2s;
        }

        .ai-page .mode-btn:hover {
          border-color: var(--primary);
        }

        .ai-page .mode-btn.active {
          border-color: var(--primary);
          background: var(--primary-bg);
        }

        .ai-page .mode-btn small {
          font-size: 0.7rem;
          color: var(--text-secondary);
        }

        .ai-page .backend-info,
        .ai-page .model-info {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .ai-page .api-key-input {
          display: flex;
          gap: 0.5rem;
        }

        .ai-page .api-key-input input {
          flex: 1;
          padding: 0.5rem;
          border: 1px solid var(--border);
          border-radius: 4px;
          background: var(--bg-secondary);
          color: var(--text-primary);
        }

        .ai-page .info-card {
          border-color: var(--primary);
        }

        .ai-page .info-content {
          display: flex;
          gap: 1rem;
          align-items: flex-start;
        }

        .ai-page .info-content h3 {
          margin: 0 0 0.25rem 0;
        }

        .ai-page .info-content p {
          margin: 0;
          color: var(--text-secondary);
        }

        .ai-page .info-content code {
          background: var(--bg-secondary);
          padding: 0.1rem 0.3rem;
          border-radius: 3px;
          font-size: 0.85em;
        }

        .ai-page .warning-card {
          border-color: var(--warning);
        }

        .ai-page .warning-content {
          display: flex;
          gap: 1rem;
          align-items: flex-start;
          color: var(--warning);
        }

        .ai-page .warning-content h3 {
          margin: 0 0 0.25rem 0;
          color: var(--text-primary);
        }

        .ai-page .warning-content p {
          margin: 0;
          color: var(--text-secondary);
        }

        .ai-page .ai-layout {
          display: grid;
          grid-template-columns: 350px 1fr;
          gap: 1.5rem;
        }

        @media (max-width: 900px) {
          .ai-page .ai-layout {
            grid-template-columns: 1fr;
          }
        }

        .ai-page .empty-selection,
        .ai-page .queue-empty {
          text-align: center;
          padding: 2rem;
          color: var(--text-secondary);
        }

        .ai-page .empty-selection svg,
        .ai-page .queue-empty svg {
          margin-bottom: 0.5rem;
          opacity: 0.5;
        }

        .ai-page .selection-list,
        .ai-page .queue-list {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .ai-page .form-group {
          margin-bottom: 1rem;
        }

        .ai-page .form-group label {
          display: block;
          margin-bottom: 0.5rem;
          font-weight: 500;
        }

        .ai-page .select-input,
        .ai-page .textarea-input {
          width: 100%;
          padding: 0.5rem;
          border: 1px solid var(--border);
          border-radius: 4px;
          background: var(--bg-secondary);
          color: var(--text-primary);
          font-family: inherit;
        }

        .ai-page .textarea-input {
          resize: vertical;
          min-height: 80px;
        }

        .ai-page .process-button {
          width: 100%;
          justify-content: center;
        }

        .ai-page .queue-card {
          margin-top: 1.5rem;
        }

        .ai-page .queue-loading {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          justify-content: center;
          padding: 1rem;
          color: var(--text-secondary);
        }

        .ai-page .results-card {
          margin-top: 1.5rem;
        }

        .ai-page .results-list {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }
      `}</style>
    </div>
  );
}

// Sub-components

interface TaskCardProps {
  task: AITask;
  onCancel: () => void;
}

function TaskCard({ task, onCancel }: TaskCardProps) {
  const statusColors: Record<string, 'default' | 'info' | 'success' | 'warning' | 'error'> = {
    pending: 'default',
    claimed: 'info',
    processing: 'info',
    completed: 'success',
    failed: 'error',
  };

  const statusIcons: Record<string, React.ReactNode> = {
    pending: <Clock size={12} />,
    claimed: <Bot size={12} />,
    processing: <Spinner size="sm" />,
    completed: <CheckCircle size={12} />,
    failed: <AlertCircle size={12} />,
  };

  return (
    <div className="task-card">
      <div className="task-header">
        <div className="task-info">
          <Badge variant={statusColors[task.status] || 'default'}>
            {statusIcons[task.status]} {task.status}
          </Badge>
          <span className="task-op">{task.operation}</span>
          <Badge size="sm" variant="default">{task.priority}</Badge>
        </div>
        {task.status === 'pending' && (
          <button className="cancel-btn" onClick={onCancel} title="Cancel task">
            <X size={14} />
          </button>
        )}
      </div>

      <div className="task-selections">
        {task.selections.map((s, i) => (
          <span key={i} className="task-selection">
            <FileText size={12} /> {s.title}
            {s.notes_count > 0 && <Badge size="sm">{s.notes_count} notes</Badge>}
          </span>
        ))}
      </div>

      {task.instructions && (
        <div className="task-instructions">{task.instructions}</div>
      )}

      {task.summary && (
        <div className="task-summary">
          <CheckCircle size={14} className="text-success" />
          <span>{task.summary}</span>
        </div>
      )}

      {task.files_modified && task.files_modified.length > 0 && (
        <div className="task-files">
          <strong>Modified:</strong> {task.files_modified.join(', ')}
        </div>
      )}

      {task.error && (
        <div className="task-error">
          <AlertCircle size={14} />
          <span>{task.error}</span>
        </div>
      )}

      <style>{`
        .task-card {
          padding: 0.75rem;
          border: 1px solid var(--border);
          border-radius: 6px;
          background: var(--bg-secondary);
        }

        .task-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.5rem;
        }

        .task-info {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .task-op {
          font-weight: 500;
          text-transform: capitalize;
        }

        .cancel-btn {
          background: none;
          border: none;
          color: var(--text-secondary);
          cursor: pointer;
          padding: 0.25rem;
        }

        .cancel-btn:hover {
          color: var(--error);
        }

        .task-selections {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
          margin-bottom: 0.5rem;
        }

        .task-selection {
          display: inline-flex;
          align-items: center;
          gap: 0.25rem;
          font-size: 0.85rem;
          color: var(--text-secondary);
        }

        .task-instructions {
          font-size: 0.85rem;
          color: var(--text-secondary);
          margin-bottom: 0.5rem;
          padding: 0.5rem;
          background: var(--bg-primary);
          border-radius: 4px;
        }

        .task-summary {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 0.85rem;
          color: var(--success);
          margin-top: 0.5rem;
        }

        .task-files {
          font-size: 0.75rem;
          color: var(--text-secondary);
          margin-top: 0.25rem;
        }

        .task-error {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 0.85rem;
          color: var(--error);
          margin-top: 0.5rem;
        }
      `}</style>
    </div>
  );
}

interface SelectionCardProps {
  item: SelectionItem;
  onToggle: () => void;
  onRemove: () => void;
  onAddNote: (note: string) => void;
}

function SelectionCard({ item, onToggle, onRemove, onAddNote }: SelectionCardProps) {
  const [noteInput, setNoteInput] = useState('');
  const [showNoteInput, setShowNoteInput] = useState(false);

  const handleAddNote = () => {
    if (noteInput.trim()) {
      onAddNote(noteInput.trim());
      setNoteInput('');
      setShowNoteInput(false);
    }
  };

  return (
    <div className={`selection-card ${item.selected ? 'selected' : ''}`}>
      <div className="selection-header">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={item.selected}
            onChange={onToggle}
          />
          <span className="title">{item.title}</span>
        </label>
        <button className="remove-btn" onClick={onRemove}>
          <Trash2 size={14} />
        </button>
      </div>
      <div className="selection-path">{item.path}</div>

      {item.notes.length > 0 && (
        <div className="selection-notes">
          {item.notes.map((note, i) => (
            <div key={i} className="note-item">
              <Badge size="sm" variant="default">{note.priority}</Badge>
              <span>{note.text}</span>
            </div>
          ))}
        </div>
      )}

      {showNoteInput ? (
        <div className="note-input">
          <input
            type="text"
            value={noteInput}
            onChange={e => setNoteInput(e.target.value)}
            placeholder="Add a note..."
            onKeyDown={e => e.key === 'Enter' && handleAddNote()}
          />
          <Button size="sm" onClick={handleAddNote}>
            <Check size={12} />
          </Button>
          <Button size="sm" variant="secondary" onClick={() => setShowNoteInput(false)}>
            <X size={12} />
          </Button>
        </div>
      ) : (
        <button className="add-note-btn" onClick={() => setShowNoteInput(true)}>
          + Add note
        </button>
      )}

      <style>{`
        .selection-card {
          padding: 0.75rem;
          border: 1px solid var(--border);
          border-radius: 6px;
          background: var(--bg-secondary);
        }

        .selection-card.selected {
          border-color: var(--primary);
        }

        .selection-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .checkbox-label {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          cursor: pointer;
        }

        .checkbox-label .title {
          font-weight: 500;
        }

        .remove-btn {
          background: none;
          border: none;
          color: var(--text-secondary);
          cursor: pointer;
          padding: 0.25rem;
        }

        .remove-btn:hover {
          color: var(--error);
        }

        .selection-path {
          font-size: 0.75rem;
          color: var(--text-secondary);
          margin-top: 0.25rem;
          margin-left: 1.5rem;
        }

        .selection-notes {
          margin-top: 0.5rem;
          margin-left: 1.5rem;
        }

        .note-item {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 0.85rem;
          margin-top: 0.25rem;
        }

        .note-input {
          display: flex;
          gap: 0.25rem;
          margin-top: 0.5rem;
        }

        .note-input input {
          flex: 1;
          padding: 0.25rem 0.5rem;
          border: 1px solid var(--border);
          border-radius: 4px;
          background: var(--bg-primary);
          color: var(--text-primary);
          font-size: 0.85rem;
        }

        .add-note-btn {
          background: none;
          border: none;
          color: var(--primary);
          cursor: pointer;
          font-size: 0.75rem;
          margin-top: 0.5rem;
          margin-left: 1.5rem;
        }

        .add-note-btn:hover {
          text-decoration: underline;
        }
      `}</style>
    </div>
  );
}

interface ContentPickerProps {
  languages: string[];
  onSelect: (path: string) => void;
  onClose: () => void;
}

function ContentPicker({ languages, onSelect, onClose }: ContentPickerProps) {
  const [selectedLang, setSelectedLang] = useState(languages[0] || 'en');
  const [documents, setDocuments] = useState<Array<{ path: string; title: string }>>([]);
  const [loading, setLoading] = useState(false);

  const loadDocuments = async (lang: string) => {
    setLoading(true);
    try {
      const result = await getDocuments(lang);
      const docs: Array<{ path: string; title: string }> = [];
      for (const category of Object.values(result.categories)) {
        for (const doc of category) {
          docs.push({ path: doc.path, title: doc.title || doc.path });
        }
      }
      setDocuments(docs);
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
    setLoading(false);
  };

  useState(() => {
    loadDocuments(selectedLang);
  });

  return (
    <div className="content-picker">
      <div className="picker-header">
        <select
          value={selectedLang}
          onChange={e => {
            setSelectedLang(e.target.value);
            loadDocuments(e.target.value);
          }}
        >
          {languages.map(lang => (
            <option key={lang} value={lang}>
              {lang.toUpperCase()}
            </option>
          ))}
        </select>
        <button onClick={onClose}>
          <X size={14} />
        </button>
      </div>

      {loading ? (
        <div className="picker-loading">
          <Spinner size="sm" />
        </div>
      ) : (
        <div className="picker-list">
          {documents.map(doc => (
            <button
              key={doc.path}
              className="picker-item"
              onClick={() => onSelect(doc.path)}
            >
              <FileText size={14} />
              <span>{doc.title}</span>
            </button>
          ))}
        </div>
      )}

      <style>{`
        .content-picker {
          border: 1px solid var(--border);
          border-radius: 6px;
          margin-bottom: 1rem;
          background: var(--bg-primary);
        }

        .picker-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.5rem;
          border-bottom: 1px solid var(--border);
        }

        .picker-header select {
          padding: 0.25rem;
          border: 1px solid var(--border);
          border-radius: 4px;
          background: var(--bg-secondary);
          color: var(--text-primary);
        }

        .picker-header button {
          background: none;
          border: none;
          color: var(--text-secondary);
          cursor: pointer;
        }

        .picker-loading {
          padding: 1rem;
          text-align: center;
        }

        .picker-list {
          max-height: 200px;
          overflow-y: auto;
        }

        .picker-item {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          width: 100%;
          padding: 0.5rem;
          background: none;
          border: none;
          border-bottom: 1px solid var(--border);
          color: var(--text-primary);
          cursor: pointer;
          text-align: left;
        }

        .picker-item:hover {
          background: var(--bg-secondary);
        }

        .picker-item:last-child {
          border-bottom: none;
        }
      `}</style>
    </div>
  );
}

interface ResultCardProps {
  result: AIResult;
  onCopy: () => void;
  onToggleExpand: () => void;
}

function ResultCard({ result, onCopy, onToggleExpand }: ResultCardProps) {
  return (
    <div className="result-card">
      <div className="result-header">
        <div className="result-info">
          <span className="result-path">{result.path}</span>
          <span className="result-summary">{result.changesSummary}</span>
        </div>
        <div className="result-actions">
          <button onClick={onCopy} title="Copy to clipboard">
            <Copy size={14} />
          </button>
          <button onClick={onToggleExpand}>
            {result.expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        </div>
      </div>

      {result.expanded && (
        <div className="result-content">
          <pre>{result.processed}</pre>
        </div>
      )}

      <style>{`
        .result-card {
          border: 1px solid var(--border);
          border-radius: 6px;
          overflow: hidden;
        }

        .result-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.75rem;
          background: var(--bg-secondary);
        }

        .result-info {
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
        }

        .result-path {
          font-weight: 500;
          font-size: 0.9rem;
        }

        .result-summary {
          font-size: 0.75rem;
          color: var(--text-secondary);
        }

        .result-actions {
          display: flex;
          gap: 0.5rem;
        }

        .result-actions button {
          background: none;
          border: none;
          color: var(--text-secondary);
          cursor: pointer;
          padding: 0.25rem;
        }

        .result-actions button:hover {
          color: var(--primary);
        }

        .result-content {
          padding: 1rem;
          background: var(--bg-primary);
          border-top: 1px solid var(--border);
        }

        .result-content pre {
          margin: 0;
          white-space: pre-wrap;
          word-break: break-word;
          font-size: 0.85rem;
          max-height: 400px;
          overflow-y: auto;
        }
      `}</style>
    </div>
  );
}
