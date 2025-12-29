import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
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
  useDeleteAITask,
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
  const [operation, setOperation] = useState('general');
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
  const deleteTask = useDeleteAITask();
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
    if (selectedItems.length === 0 && !instructions.trim()) return;

    const apiSelections: AIContentSelection[] = selectedItems.map(s => ({
      path: s.path,
      content: s.content,
      title: s.title,
      content_type: s.contentType,
      target_id: s.targetId,
      notes: s.notes,
    }));

    if (mode === 'claude_code') {
      try {
        await submitTask.mutateAsync({
          operation,
          selections: apiSelections,
          instructions,
          priority,
          target_language: operation === 'translate' ? targetLanguage : undefined,
        });
        setSelections([]);
        setInstructions('');
      } catch (error) {
        console.error('Failed to submit task:', error);
      }
    } else {
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

  const handleDeleteTask = async (taskId: string) => {
    try {
      await deleteTask.mutateAsync(taskId);
    } catch (error) {
      console.error('Failed to delete task:', error);
    }
  };

  if (configLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12 gap-4">
        <Spinner size="lg" />
        <p className="text-base-content/60">Loading AI configuration...</p>
      </div>
    );
  }

  const stats = tasksData?.stats;
  const pendingCount = stats?.pending || 0;
  const processingCount = stats?.processing || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Wand2 size={24} /> AI Assist
          </h1>
          <p className="text-base-content/60">AI-powered content processing via Claude Code</p>
        </div>
        <div className="flex items-center gap-3">
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
      </div>

      {/* Settings Card */}
      {showSettings && (
        <Card>
          <CardHeader><CardTitle>AI Settings</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="form-control">
                <label className="label">
                  <span className="label-text font-medium">Processing Mode</span>
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    className={`flex flex-col items-center gap-1 p-4 border-2 rounded-lg transition-colors ${
                      mode === 'claude_code'
                        ? 'border-primary bg-primary/10'
                        : 'border-base-300 bg-base-200 hover:border-primary/50'
                    }`}
                    onClick={() => setMode('claude_code')}
                  >
                    <Bot size={20} />
                    <span className="font-medium">Claude Code</span>
                    <span className="text-xs text-base-content/60">Full tool access, file editing</span>
                  </button>
                  <button
                    className={`flex flex-col items-center gap-1 p-4 border-2 rounded-lg transition-colors ${
                      mode === 'direct'
                        ? 'border-primary bg-primary/10'
                        : 'border-base-300 bg-base-200 hover:border-primary/50'
                    }`}
                    onClick={() => setMode('direct')}
                  >
                    <Zap size={20} />
                    <span className="font-medium">Direct API</span>
                    <span className="text-xs text-base-content/60">Fast, text-only responses</span>
                  </button>
                </div>
              </div>

              {mode === 'direct' && (
                <>
                  <div className="form-control">
                    <label className="label">
                      <span className="label-text font-medium">Backend</span>
                    </label>
                    <div className="flex items-center gap-2">
                      <Badge>{aiConfig?.backend || 'anthropic'}</Badge>
                      <span className="text-sm text-base-content/60">
                        {aiConfig?.backend === 'claude_code'
                          ? 'Using Claude Code CLI'
                          : 'Using Anthropic API'}
                      </span>
                    </div>
                  </div>

                  <div className="form-control">
                    <label className="label">
                      <span className="label-text font-medium">API Key</span>
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="password"
                        value={newApiKey}
                        onChange={e => setNewApiKey(e.target.value)}
                        placeholder={aiConfig?.has_api_key ? '********' : 'Enter API key'}
                        className="input input-bordered flex-1"
                      />
                      <Button size="sm" onClick={handleSaveConfig} disabled={!newApiKey}>
                        Save
                      </Button>
                    </div>
                    <label className="label">
                      <span className="label-text-alt text-base-content/60">
                        Or set ANTHROPIC_API_KEY environment variable
                      </span>
                    </label>
                  </div>
                </>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Claude Code Info */}
      {mode === 'claude_code' && (
        <Card className="border-primary/30">
          <CardContent className="pt-4">
            <div className="flex gap-4 items-start">
              <Bot size={24} className="text-primary shrink-0" />
              <div>
                <h3 className="font-semibold">Claude Code Integration</h3>
                <p className="text-sm text-base-content/60 mt-1">
                  Tasks are queued and processed by your running Claude Code session.
                  Claude Code can edit files directly, run quality checks, and use all available skills.
                  Say <code className="px-1.5 py-0.5 bg-base-300 rounded text-xs">/process-ai-queue</code> in Claude Code to process pending tasks.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Not Configured Warning */}
      {mode === 'direct' && !aiConfig?.configured && (
        <Card className="border-warning/50">
          <CardContent className="pt-4">
            <div className="flex gap-4 items-start text-warning">
              <AlertCircle size={24} className="shrink-0" />
              <div>
                <h3 className="font-semibold text-base-content">AI Not Configured</h3>
                <p className="text-sm text-base-content/60 mt-1">
                  Set your Anthropic API key in settings or use the ANTHROPIC_API_KEY
                  environment variable to enable direct API processing.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-[350px_1fr] gap-6">
        {/* Sidebar - Content Selection */}
        <div>
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
                <div className="text-center py-8 text-base-content/60">
                  <FileText size={32} className="mx-auto mb-2 opacity-50" />
                  <p className="font-medium">No content selected</p>
                  <p className="text-sm">Add documents or scenes to process</p>
                </div>
              ) : (
                <div className="space-y-3">
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

        {/* Main - Processing Options */}
        <div className="space-y-6">
          <Card>
            <CardHeader><CardTitle>Processing Options</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="form-control">
                  <label className="label">
                    <span className="label-text font-medium">Operation</span>
                  </label>
                  <select
                    value={operation}
                    onChange={e => setOperation(e.target.value)}
                    className="select select-bordered w-full"
                  >
                    <option value="general">General Task - Any custom request or instruction</option>
                    {operationsData?.operations.map(op => (
                      <option key={op.id} value={op.id}>
                        {op.name} - {op.description}
                      </option>
                    ))}
                  </select>
                </div>

                {operation === 'translate' && (
                  <div className="form-control">
                    <label className="label">
                      <span className="label-text font-medium">Target Language</span>
                    </label>
                    <select
                      value={targetLanguage}
                      onChange={e => setTargetLanguage(e.target.value)}
                      className="select select-bordered w-full"
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
                  <div className="form-control">
                    <label className="label">
                      <span className="label-text font-medium">Priority</span>
                    </label>
                    <select
                      value={priority}
                      onChange={e => setPriority(e.target.value)}
                      className="select select-bordered w-full"
                    >
                      <option value="low">Low</option>
                      <option value="normal">Normal</option>
                      <option value="high">High</option>
                      <option value="urgent">Urgent</option>
                    </select>
                  </div>
                )}

                <div className="form-control">
                  <label className="label">
                    <span className="label-text font-medium">
                      Instructions
                      {selections.filter(s => s.selected).length === 0 && (
                        <span className="text-error ml-1">*</span>
                      )}
                    </span>
                  </label>
                  <textarea
                    value={instructions}
                    onChange={e => setInstructions(e.target.value)}
                    placeholder={
                      mode === 'claude_code'
                        ? selections.filter(s => s.selected).length === 0
                          ? 'Enter a general task for Claude Code... (e.g., "Create a new chapter about API integration")'
                          : 'Detailed instructions for Claude Code...'
                        : 'Add specific instructions for the AI... (optional)'
                    }
                    rows={4}
                    className="textarea textarea-bordered w-full"
                  />
                  {selections.filter(s => s.selected).length === 0 && (
                    <label className="label">
                      <span className="label-text-alt text-base-content/60">
                        No documents selected — submit a general task with just instructions
                      </span>
                    </label>
                  )}
                </div>

                <Button
                  onClick={handleProcess}
                  disabled={
                    (mode === 'claude_code' ? submitTask.isPending : processAI.isPending) ||
                    (selections.filter(s => s.selected).length === 0 && !instructions.trim()) ||
                    (mode === 'direct' && !aiConfig?.configured)
                  }
                  className="w-full"
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
              </div>
            </CardContent>
          </Card>

          {/* Task Queue (Claude Code mode) */}
          {mode === 'claude_code' && (
            <Card>
              <CardHeader
                title="Task Queue"
                action={
                  <Button
                    size="icon"
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
                    <div className="flex items-center justify-center gap-2 py-4 text-base-content/60">
                      <Spinner size="sm" />
                      <span>Loading tasks...</span>
                    </div>
                  ) : tasksData?.tasks.length === 0 ? (
                    <div className="text-center py-8 text-base-content/60">
                      <ListTodo size={24} className="mx-auto mb-2 opacity-50" />
                      <p>No tasks in queue</p>
                      <p className="text-sm">Submit content above to add tasks</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {tasksData?.tasks.map(task => (
                        <TaskCard
                          key={task.id}
                          task={task}
                          onCancel={() => handleCancelTask(task.id)}
                          onDelete={() => handleDeleteTask(task.id)}
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
            <Card>
              <CardHeader
                title="Results"
                action={
                  <Badge variant="success">
                    <CheckCircle size={12} /> {results.length} processed
                  </Badge>
                }
              />
              <CardContent>
                <div className="space-y-4">
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
    </div>
  );
}

// Sub-components

interface TaskCardProps {
  task: AITask;
  onCancel: () => void;
  onDelete: () => void;
}

function TaskCard({ task, onCancel, onDelete }: TaskCardProps) {
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
    <div className="p-3 border border-base-300 rounded-lg bg-base-200">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Badge variant={statusColors[task.status] || 'default'}>
            {statusIcons[task.status]} {task.status}
          </Badge>
          <span className="font-medium capitalize">{task.operation}</span>
          <Badge size="sm">{task.priority}</Badge>
        </div>
        <div className="flex gap-1">
          {task.status === 'pending' && (
            <button
              className="btn btn-ghost btn-xs btn-square text-base-content/60 hover:text-error"
              onClick={onCancel}
              title="Cancel task"
            >
              <X size={14} />
            </button>
          )}
          {['completed', 'failed', 'cancelled'].includes(task.status) && (
            <button
              className="btn btn-ghost btn-xs btn-square text-base-content/60 hover:text-error"
              onClick={onDelete}
              title="Delete task"
            >
              <Trash2 size={14} />
            </button>
          )}
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mb-2">
        {task.selections.map((s, i) => (
          <span key={i} className="inline-flex items-center gap-1 text-sm text-base-content/60">
            <FileText size={12} /> {s.title}
            {s.notes_count > 0 && <Badge size="sm">{s.notes_count} notes</Badge>}
          </span>
        ))}
      </div>

      {task.instructions && (
        <div className="text-sm text-base-content/60 p-2 bg-base-100 rounded mb-2">
          {task.instructions}
        </div>
      )}

      {task.summary && (
        <div className="flex items-center gap-2 text-sm text-success mt-2">
          <CheckCircle size={14} />
          <span>{task.summary}</span>
        </div>
      )}

      {task.files_modified && task.files_modified.length > 0 && (
        <div className="text-xs text-base-content/60 mt-1">
          <strong>Modified:</strong> {task.files_modified.join(', ')}
        </div>
      )}

      {task.error && (
        <div className="flex items-center gap-2 text-sm text-error mt-2">
          <AlertCircle size={14} />
          <span>{task.error}</span>
        </div>
      )}
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
    <div className={`p-3 border rounded-lg bg-base-200 ${item.selected ? 'border-primary' : 'border-base-300'}`}>
      <div className="flex items-center justify-between">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={item.selected}
            onChange={onToggle}
            className="checkbox checkbox-sm checkbox-primary"
          />
          <span className="font-medium">{item.title}</span>
        </label>
        <button
          className="btn btn-ghost btn-xs btn-square text-base-content/60 hover:text-error"
          onClick={onRemove}
        >
          <Trash2 size={14} />
        </button>
      </div>
      <div className="text-xs text-base-content/60 mt-1 ml-6">{item.path}</div>

      {item.notes.length > 0 && (
        <div className="mt-2 ml-6 space-y-1">
          {item.notes.map((note, i) => (
            <div key={i} className="flex items-center gap-2 text-sm">
              <Badge size="sm">{note.priority}</Badge>
              <span>{note.text}</span>
            </div>
          ))}
        </div>
      )}

      {showNoteInput ? (
        <div className="flex gap-1 mt-2">
          <input
            type="text"
            value={noteInput}
            onChange={e => setNoteInput(e.target.value)}
            placeholder="Add a note..."
            className="input input-bordered input-sm flex-1"
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
        <button
          className="text-xs text-primary mt-2 ml-6 hover:underline"
          onClick={() => setShowNoteInput(true)}
        >
          + Add note
        </button>
      )}
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
    <div className="border border-base-300 rounded-lg mb-4 bg-base-100 overflow-hidden">
      <div className="flex items-center justify-between p-2 border-b border-base-300">
        <select
          value={selectedLang}
          onChange={e => {
            setSelectedLang(e.target.value);
            loadDocuments(e.target.value);
          }}
          className="select select-bordered select-xs"
        >
          {languages.map(lang => (
            <option key={lang} value={lang}>
              {lang.toUpperCase()}
            </option>
          ))}
        </select>
        <button className="btn btn-ghost btn-xs btn-square" onClick={onClose}>
          <X size={14} />
        </button>
      </div>

      {loading ? (
        <div className="p-4 text-center">
          <Spinner size="sm" />
        </div>
      ) : (
        <div className="max-h-48 overflow-y-auto">
          {documents.map(doc => (
            <button
              key={doc.path}
              className="flex items-center gap-2 w-full p-2 text-left border-b border-base-300 last:border-b-0 hover:bg-base-200 transition-colors"
              onClick={() => onSelect(doc.path)}
            >
              <FileText size={14} />
              <span className="text-sm">{doc.title}</span>
            </button>
          ))}
        </div>
      )}
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
    <div className="border border-base-300 rounded-lg overflow-hidden">
      <div className="flex items-center justify-between p-3 bg-base-200">
        <div>
          <span className="font-medium text-sm">{result.path}</span>
          <div className="text-xs text-base-content/60">{result.changesSummary}</div>
        </div>
        <div className="flex gap-2">
          <button
            className="btn btn-ghost btn-xs btn-square"
            onClick={onCopy}
            title="Copy to clipboard"
          >
            <Copy size={14} />
          </button>
          <button className="btn btn-ghost btn-xs btn-square" onClick={onToggleExpand}>
            {result.expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        </div>
      </div>

      {result.expanded && (
        <div className="p-4 bg-base-100 border-t border-base-300">
          <pre className="text-sm whitespace-pre-wrap break-words max-h-96 overflow-y-auto">
            {result.processed}
          </pre>
        </div>
      )}
    </div>
  );
}
