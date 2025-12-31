/**
 * VideoScripts - Script editor tab for video production
 * Handles script list, editor, create/delete/duplicate operations
 * Supports batch selection and batch operations (regenerate voiceover/props)
 */

import { useState, useEffect, useCallback } from 'react';
import {
  Film,
  Code,
  FileVideo,
  Plus,
  Trash2,
  Copy,
  X,
  Loader2,
  CheckCircle,
  Mic,
  ChevronRight,
  RefreshCw,
  AlertTriangle,
  CheckSquare,
  Square,
  MinusSquare,
} from 'lucide-react';
import clsx from 'clsx';
import { Spinner, NoScriptsState, EmptyState } from '@/components/ui';
import { useVideoScriptsData, useVoiceoverStatus, useGenerateVoiceover, videoQueryKeys } from '@/hooks/useVideoApi';
import { DEFAULT_SCRIPT_TEMPLATE, getVideoProps } from '@/api/video';
import { VoiceoverPanel } from '../VoiceoverPanel';
import { YamlEditor } from '../YamlEditor';
import type { VideoScriptItem } from '@/api/types';
import { useQueryClient } from '@tanstack/react-query';

// Batch operation types
type BatchOperation = 'voiceover' | 'props';

interface BatchProgress {
  operation: BatchOperation;
  current: number;
  total: number;
  currentScriptId: string | null;
}

export function VideoScripts() {
  const [selectedScript, setSelectedScript] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newScriptName, setNewScriptName] = useState('');
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);
  const [showVoiceover, setShowVoiceover] = useState(false);
  const [showRegeneratePrompt, setShowRegeneratePrompt] = useState(false);
  const [needsRegenerate, setNeedsRegenerate] = useState(false);

  // Batch selection state
  const [selectedScriptIds, setSelectedScriptIds] = useState<Set<string>>(new Set());
  const [batchProgress, setBatchProgress] = useState<BatchProgress | null>(null);

  const queryClient = useQueryClient();

  const {
    scripts,
    scriptsLoading,
    scriptDetail,
    detailLoading,
    create,
    update,
    remove,
    duplicate,
  } = useVideoScriptsData(selectedScript);

  // Get voiceover status to show in script list
  const { data: voiceoverStatus, refetch: refetchVoiceoverStatus } = useVoiceoverStatus(selectedScript);

  // Voiceover generation mutation
  const generateVoiceover = useGenerateVoiceover();

  // Update edit content when script loads
  useEffect(() => {
    if (scriptDetail?.content) {
      setEditContent(scriptDetail.content);
    }
  }, [scriptDetail?.content]);

  // Clear selection when scripts change (e.g., after delete)
  useEffect(() => {
    // Remove any selected IDs that no longer exist in scripts
    const scriptIdSet = new Set(scripts.map((s: VideoScriptItem) => s.id));
    setSelectedScriptIds((prev) => {
      const newSet = new Set([...prev].filter((id) => scriptIdSet.has(id)));
      if (newSet.size !== prev.size) return newSet;
      return prev;
    });
  }, [scripts]);

  // Batch selection handlers
  const toggleScriptSelection = useCallback((scriptId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    setSelectedScriptIds((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(scriptId)) {
        newSet.delete(scriptId);
      } else {
        newSet.add(scriptId);
      }
      return newSet;
    });
  }, []);

  const toggleSelectAll = useCallback(() => {
    if (selectedScriptIds.size === scripts.length) {
      setSelectedScriptIds(new Set());
    } else {
      setSelectedScriptIds(new Set(scripts.map((s: VideoScriptItem) => s.id)));
    }
  }, [scripts, selectedScriptIds.size]);

  const clearSelection = useCallback(() => {
    setSelectedScriptIds(new Set());
  }, []);

  // Batch operation handlers
  const handleBatchRegenerateVoiceover = useCallback(async () => {
    const scriptIds = Array.from(selectedScriptIds);
    if (scriptIds.length === 0) return;

    setBatchProgress({
      operation: 'voiceover',
      current: 0,
      total: scriptIds.length,
      currentScriptId: null,
    });

    for (let i = 0; i < scriptIds.length; i++) {
      const scriptId = scriptIds[i];
      setBatchProgress({
        operation: 'voiceover',
        current: i + 1,
        total: scriptIds.length,
        currentScriptId: scriptId,
      });

      try {
        await generateVoiceover.mutateAsync({
          scriptId,
          mode: 'mock',
          force: true,
        });
      } catch {
        // Continue with next script on error
        console.error(`Failed to regenerate voiceover for ${scriptId}`);
      }
    }

    setBatchProgress(null);
    clearSelection();
  }, [selectedScriptIds, generateVoiceover, clearSelection]);

  const handleBatchRegenerateProps = useCallback(async () => {
    const scriptIds = Array.from(selectedScriptIds);
    if (scriptIds.length === 0) return;

    setBatchProgress({
      operation: 'props',
      current: 0,
      total: scriptIds.length,
      currentScriptId: null,
    });

    for (let i = 0; i < scriptIds.length; i++) {
      const scriptId = scriptIds[i];
      setBatchProgress({
        operation: 'props',
        current: i + 1,
        total: scriptIds.length,
        currentScriptId: scriptId,
      });

      try {
        // Calling getVideoProps triggers props regeneration on the backend
        await getVideoProps(scriptId);
        // Invalidate the cache to show updated data
        queryClient.invalidateQueries({
          queryKey: videoQueryKeys.props(scriptId),
        });
      } catch {
        // Continue with next script on error
        console.error(`Failed to regenerate props for ${scriptId}`);
      }
    }

    setBatchProgress(null);
    clearSelection();
  }, [selectedScriptIds, queryClient, clearSelection]);

  // Selection state helpers
  const isAllSelected = scripts.length > 0 && selectedScriptIds.size === scripts.length;
  const isPartiallySelected = selectedScriptIds.size > 0 && selectedScriptIds.size < scripts.length;
  const hasSelection = selectedScriptIds.size > 0;
  const isBatchOperationInProgress = batchProgress !== null;

  if (scriptsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" className="text-primary" />
      </div>
    );
  }

  const handleCreateScript = () => {
    if (!newScriptName.trim()) return;
    create.mutate(
      {
        name: newScriptName.trim(),
        content: DEFAULT_SCRIPT_TEMPLATE.replace('title: "New Video"', `title: "${newScriptName.trim()}"`),
      },
      {
        onSuccess: (data) => {
          setShowCreateModal(false);
          setNewScriptName('');
          if (data.id) {
            setSelectedScript(data.id);
          }
        },
      }
    );
  };

  const handleDuplicate = (scriptId: string, scriptName: string) => {
    duplicate.mutate(
      { sourceId: scriptId, newName: `${scriptName} (copy)` },
      {
        onSuccess: (data) => {
          if (data.id) {
            setSelectedScript(data.id);
          }
        },
      }
    );
  };

  const handleDelete = () => {
    if (!confirmDelete) return;
    remove.mutate(confirmDelete, {
      onSuccess: () => {
        setConfirmDelete(null);
        if (selectedScript === confirmDelete) {
          setSelectedScript(null);
          setEditContent('');
        }
      },
    });
  };

  return (
    <>
      <div className="flex gap-6 h-[calc(100vh-280px)]">
        {/* Script List */}
        <aside className="w-72 flex-shrink-0 flex flex-col bg-base-200 rounded-lg overflow-hidden">
          <div className="p-4 border-b border-base-300">
            <div className="flex items-center gap-2">
              {/* Select All checkbox */}
              {scripts.length > 0 && (
                <button
                  onClick={toggleSelectAll}
                  className="btn btn-ghost btn-xs p-1"
                  aria-label={isAllSelected ? 'Deselect all' : 'Select all'}
                  disabled={isBatchOperationInProgress}
                >
                  {isAllSelected ? (
                    <CheckSquare size={16} className="text-primary" />
                  ) : isPartiallySelected ? (
                    <MinusSquare size={16} className="text-primary" />
                  ) : (
                    <Square size={16} />
                  )}
                </button>
              )}
              <h3 className="font-semibold flex items-center gap-2 flex-1">
                <Film size={16} />
                Scripts
                <span className="badge badge-ghost badge-sm">{scripts.length}</span>
              </h3>
              <button
                onClick={() => setShowCreateModal(true)}
                className="btn btn-primary btn-xs gap-1"
                aria-label="Create new script"
                disabled={isBatchOperationInProgress}
              >
                <Plus size={12} />
                New
              </button>
            </div>
          </div>

          {/* Batch Action Toolbar */}
          {hasSelection && (
            <div className="p-2 border-b border-base-300 bg-primary/10">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm font-medium text-primary">
                  {selectedScriptIds.size} selected
                </span>
                <div className="flex-1" />
                <button
                  onClick={handleBatchRegenerateVoiceover}
                  disabled={isBatchOperationInProgress}
                  className="btn btn-xs btn-primary gap-1"
                  aria-label="Regenerate voiceover for selected scripts"
                >
                  {batchProgress?.operation === 'voiceover' ? (
                    <>
                      <Loader2 size={12} className="animate-spin" />
                      {batchProgress.current}/{batchProgress.total}
                    </>
                  ) : (
                    <>
                      <Mic size={12} />
                      Voiceover
                    </>
                  )}
                </button>
                <button
                  onClick={handleBatchRegenerateProps}
                  disabled={isBatchOperationInProgress}
                  className="btn btn-xs btn-secondary gap-1"
                  aria-label="Regenerate props for selected scripts"
                >
                  {batchProgress?.operation === 'props' ? (
                    <>
                      <Loader2 size={12} className="animate-spin" />
                      {batchProgress.current}/{batchProgress.total}
                    </>
                  ) : (
                    <>
                      <RefreshCw size={12} />
                      Props
                    </>
                  )}
                </button>
                <button
                  onClick={clearSelection}
                  disabled={isBatchOperationInProgress}
                  className="btn btn-xs btn-ghost"
                  aria-label="Clear selection"
                >
                  <X size={12} />
                </button>
              </div>
              {/* Progress indicator */}
              {batchProgress && (
                <div className="mt-2 text-xs text-base-content/70">
                  Regenerating {batchProgress.operation === 'voiceover' ? 'voiceover' : 'props'}{' '}
                  {batchProgress.current} of {batchProgress.total}...
                </div>
              )}
            </div>
          )}

          <nav className="flex-1 overflow-y-auto p-2 space-y-1">
            {scripts.length === 0 ? (
              <NoScriptsState onAdd={() => setShowCreateModal(true)} />
            ) : (
              scripts.map((script: VideoScriptItem) => (
                <div
                  key={script.id}
                  className={clsx(
                    'group flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors',
                    selectedScriptIds.has(script.id) && 'bg-primary/10',
                    selectedScript === script.id
                      ? 'bg-primary/20 text-primary'
                      : 'hover:bg-base-300 text-base-content/80'
                  )}
                >
                  {/* Checkbox for selection */}
                  <button
                    onClick={(e) => toggleScriptSelection(script.id, e)}
                    className="btn btn-ghost btn-xs p-0 min-h-0 h-auto"
                    aria-label={selectedScriptIds.has(script.id) ? 'Deselect script' : 'Select script'}
                    disabled={isBatchOperationInProgress}
                  >
                    {selectedScriptIds.has(script.id) ? (
                      <CheckSquare size={14} className="text-primary" />
                    ) : (
                      <Square size={14} className="opacity-50 group-hover:opacity-100" />
                    )}
                  </button>
                  <button
                    onClick={() => {
                      setSelectedScript(script.id);
                      setEditContent('');
                    }}
                    className="flex items-center gap-2 flex-1 min-w-0 text-left"
                    disabled={isBatchOperationInProgress}
                  >
                    <FileVideo size={14} className="flex-shrink-0" />
                    <span className="flex-1 truncate">{script.name}</span>
                    {script.has_output && <CheckCircle size={12} className="text-success flex-shrink-0" />}
                  </button>
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDuplicate(script.id, script.name);
                      }}
                      className="btn btn-ghost btn-xs p-1"
                      aria-label="Duplicate script"
                      disabled={isBatchOperationInProgress}
                    >
                      <Copy size={12} />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setConfirmDelete(script.id);
                      }}
                      className="btn btn-ghost btn-xs p-1 text-error"
                      aria-label="Delete script"
                      disabled={isBatchOperationInProgress}
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                </div>
              ))
            )}
          </nav>
        </aside>

        {/* Editor */}
        <main className="flex-1 min-w-0 flex flex-col overflow-hidden">
          {selectedScript ? (
            detailLoading ? (
              <div className="flex items-center justify-center h-full">
                <Spinner size="lg" className="text-primary" />
              </div>
            ) : scriptDetail ? (
              <>
                <div className="flex items-center gap-4 mb-4">
                  <h2 className="text-lg font-semibold">{scriptDetail.parsed?.title || selectedScript}</h2>
                  <span className="badge badge-ghost">{scriptDetail.parsed?.language || 'en'}</span>
                  {scriptDetail.parsed?.metadata?.version && (
                    <span className="badge badge-info">v{scriptDetail.parsed.metadata.version}</span>
                  )}
                  {voiceoverStatus?.has_voiceover && (
                    <span className="badge badge-success gap-1">
                      <Mic size={10} />
                      Audio
                    </span>
                  )}
                  <div className="flex-1" />
                  <button
                    onClick={() => setShowVoiceover(!showVoiceover)}
                    className={clsx(
                      'btn btn-sm gap-2',
                      showVoiceover ? 'btn-secondary' : 'btn-ghost'
                    )}
                    aria-label="Toggle voiceover panel"
                  >
                    <Mic size={14} />
                    Voiceover
                    <ChevronRight
                      size={14}
                      className={clsx('transition-transform', showVoiceover && 'rotate-180')}
                    />
                  </button>
                  <button
                    onClick={() => handleDuplicate(selectedScript, scriptDetail.parsed?.title || selectedScript)}
                    className="btn btn-ghost btn-sm gap-2"
                    aria-label="Duplicate this script"
                  >
                    <Copy size={14} />
                  </button>
                  <button
                    onClick={() => setConfirmDelete(selectedScript)}
                    className="btn btn-ghost btn-sm gap-2 text-error"
                    aria-label="Delete this script"
                  >
                    <Trash2 size={14} />
                  </button>
                  <button
                    onClick={() => {
                      update.mutate(
                        { scriptId: selectedScript, content: editContent },
                        {
                          onSuccess: () => {
                            // If voiceover exists, show regenerate prompt
                            if (voiceoverStatus?.has_voiceover) {
                              setNeedsRegenerate(true);
                              setShowRegeneratePrompt(true);
                            }
                          },
                        }
                      );
                    }}
                    disabled={update.isPending || editContent === scriptDetail.content}
                    className="btn btn-primary btn-sm gap-2"
                  >
                    {update.isPending ? (
                      <Loader2 size={14} className="animate-spin" />
                    ) : (
                      'Save'
                    )}
                  </button>
                </div>

                {/* Regenerate notification */}
                {needsRegenerate && showRegeneratePrompt && (
                  <div className="alert alert-warning py-2 mb-4">
                    <AlertTriangle size={16} />
                    <span className="text-sm">Script changed. Voiceover may need to be regenerated.</span>
                    <div className="flex gap-2">
                      <button
                        onClick={() => {
                          if (!selectedScript) return;
                          generateVoiceover.mutate(
                            { scriptId: selectedScript, mode: 'mock', force: true },
                            {
                              onSuccess: () => {
                                setNeedsRegenerate(false);
                                setShowRegeneratePrompt(false);
                                refetchVoiceoverStatus();
                              },
                            }
                          );
                        }}
                        disabled={generateVoiceover.isPending}
                        className="btn btn-warning btn-xs gap-1"
                      >
                        {generateVoiceover.isPending ? (
                          <Loader2 size={12} className="animate-spin" />
                        ) : (
                          <RefreshCw size={12} />
                        )}
                        Regenerate
                      </button>
                      <button
                        onClick={() => setShowRegeneratePrompt(false)}
                        className="btn btn-ghost btn-xs"
                      >
                        Dismiss
                      </button>
                    </div>
                  </div>
                )}

                <div className="flex flex-1 gap-4 min-h-0">
                  <YamlEditor
                    value={editContent || scriptDetail.content}
                    onChange={setEditContent}
                    placeholder="Script content..."
                    className="flex-1 bg-base-200"
                  />
                  {showVoiceover && (
                    <aside className="w-80 flex-shrink-0 bg-base-200 rounded-lg overflow-hidden">
                      <VoiceoverPanel
                        scriptId={selectedScript}
                        className="h-full"
                        onGenerated={() => {
                          setNeedsRegenerate(false);
                          setShowRegeneratePrompt(false);
                        }}
                      />
                    </aside>
                  )}
                </div>
              </>
            ) : (
              <div className="flex items-center justify-center h-full text-base-content/60">
                Failed to load script
              </div>
            )
          ) : (
            <EmptyState
              icon={<Code size={48} strokeWidth={1.5} />}
              title="Select a Script"
              description="Choose a video script to edit"
              action={{
                label: 'Create New Script',
                onClick: () => setShowCreateModal(true),
              }}
              variant="centered"
            />
          )}
        </main>
      </div>

      {/* Create Script Modal */}
      {showCreateModal && (
        <div className="modal modal-open">
          <div className="modal-box">
            <button
              onClick={() => {
                setShowCreateModal(false);
                setNewScriptName('');
              }}
              className="btn btn-sm btn-circle btn-ghost absolute right-2 top-2"
              aria-label="Close modal"
            >
              <X size={16} />
            </button>
            <h3 className="font-bold text-lg flex items-center gap-2">
              <Plus size={18} />
              Create New Video Script
            </h3>
            <p className="text-base-content/60 text-sm mt-2">
              A new script will be created with a starter template that you can customize.
            </p>
            <div className="form-control mt-4">
              <label className="label">
                <span className="label-text">Script Name</span>
              </label>
              <input
                type="text"
                placeholder="My Awesome Video"
                className="input input-bordered w-full"
                value={newScriptName}
                onChange={(e) => setNewScriptName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleCreateScript()}
                autoFocus
              />
            </div>
            <div className="modal-action">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setNewScriptName('');
                }}
                className="btn btn-ghost"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateScript}
                disabled={!newScriptName.trim() || create.isPending}
                className="btn btn-primary gap-2"
              >
                {create.isPending ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <Plus size={14} />
                )}
                Create Script
              </button>
            </div>
          </div>
          <div className="modal-backdrop" onClick={() => setShowCreateModal(false)} />
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {confirmDelete && (
        <div className="modal modal-open">
          <div className="modal-box">
            <h3 className="font-bold text-lg flex items-center gap-2 text-error">
              <Trash2 size={18} />
              Delete Script?
            </h3>
            <p className="text-base-content/60 mt-4">
              Are you sure you want to delete this script? This action cannot be undone.
            </p>
            <div className="modal-action">
              <button
                onClick={() => setConfirmDelete(null)}
                className="btn btn-ghost"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={remove.isPending}
                className="btn btn-error gap-2"
              >
                {remove.isPending ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <Trash2 size={14} />
                )}
                Delete
              </button>
            </div>
          </div>
          <div className="modal-backdrop" onClick={() => setConfirmDelete(null)} />
        </div>
      )}
    </>
  );
}
