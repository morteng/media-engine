/**
 * VideoScripts - Script editor tab for video production
 * Handles script list, editor, create/delete/duplicate operations
 */

import { useState, useEffect } from 'react';
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
} from 'lucide-react';
import clsx from 'clsx';
import { Spinner } from '@/components/ui';
import { useVideoScriptsData } from '@/hooks/useVideoApi';
import { DEFAULT_SCRIPT_TEMPLATE } from '@/api/video';
import type { VideoScriptItem } from '@/api/types';

export function VideoScripts() {
  const [selectedScript, setSelectedScript] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newScriptName, setNewScriptName] = useState('');
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

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

  // Update edit content when script loads
  useEffect(() => {
    if (scriptDetail?.content) {
      setEditContent(scriptDetail.content);
    }
  }, [scriptDetail?.content]);

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
              <h3 className="font-semibold flex items-center gap-2 flex-1">
                <Film size={16} />
                Scripts
                <span className="badge badge-ghost badge-sm">{scripts.length}</span>
              </h3>
              <button
                onClick={() => setShowCreateModal(true)}
                className="btn btn-primary btn-xs gap-1"
                aria-label="Create new script"
              >
                <Plus size={12} />
                New
              </button>
            </div>
          </div>
          <nav className="flex-1 overflow-y-auto p-2 space-y-1">
            {scripts.length === 0 ? (
              <div className="text-center py-8 text-base-content/60 text-sm">
                <FileVideo size={32} className="mx-auto mb-2 opacity-50" />
                <p>No scripts yet</p>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="btn btn-ghost btn-xs mt-2"
                >
                  Create your first script
                </button>
              </div>
            ) : (
              scripts.map((script: VideoScriptItem) => (
                <div
                  key={script.id}
                  className={clsx(
                    'group flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors',
                    selectedScript === script.id
                      ? 'bg-primary/20 text-primary'
                      : 'hover:bg-base-300 text-base-content/80'
                  )}
                >
                  <button
                    onClick={() => {
                      setSelectedScript(script.id);
                      setEditContent('');
                    }}
                    className="flex items-center gap-2 flex-1 min-w-0 text-left"
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
                  <div className="flex-1" />
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
                    onClick={() => update.mutate({ scriptId: selectedScript, content: editContent })}
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
                <textarea
                  className="textarea textarea-bordered flex-1 w-full font-mono text-sm resize-none"
                  value={editContent || scriptDetail.content}
                  onChange={(e) => setEditContent(e.target.value)}
                  placeholder="Script content..."
                />
              </>
            ) : (
              <div className="flex items-center justify-center h-full text-base-content/60">
                Failed to load script
              </div>
            )
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <Code size={48} className="text-base-content/30 mb-4" />
              <h3 className="text-lg font-semibold">Select a Script</h3>
              <p className="text-base-content/60 mb-4">Choose a video script to edit</p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="btn btn-primary btn-sm gap-2"
              >
                <Plus size={14} />
                Create New Script
              </button>
            </div>
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
