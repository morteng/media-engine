/**
 * VideoRender - Render control tab for video production
 * Handles starting renders, batch operations, and monitoring the render queue
 */

import { useState, type ReactNode } from 'react';
import {
  Settings,
  Clock,
  Play,
  RefreshCw,
  Loader2,
  CheckCircle,
  XCircle,
  Download,
  Layers,
  CheckSquare,
  Square,
  Film,
} from 'lucide-react';
import clsx from 'clsx';
import { useVideoScripts, useRenderQueue, useRenderMutation } from '@/hooks/useVideoApi';
import { downloadRender } from '@/api/video';
import type { VideoScriptItem, RenderJob } from '@/api/types';

interface RenderJobCardProps {
  job: RenderJob;
  showDetails?: boolean;
}

function RenderJobCard({ job, showDetails = false }: RenderJobCardProps) {
  const [isDownloading, setIsDownloading] = useState(false);

  const statusIcons: Record<string, ReactNode> = {
    queued: <Clock size={16} className="text-info" />,
    rendering: <Loader2 size={16} className="text-warning animate-spin" />,
    completed: <CheckCircle size={16} className="text-success" />,
    failed: <XCircle size={16} className="text-error" />,
    cancelled: <XCircle size={16} className="text-base-content/40" />,
  };

  const statusColors: Record<string, string> = {
    queued: 'badge-info',
    rendering: 'badge-warning',
    completed: 'badge-success',
    failed: 'badge-error',
    cancelled: 'badge-ghost',
  };

  const handleDownload = async () => {
    setIsDownloading(true);
    try {
      await downloadRender(job.id);
    } catch (error) {
      console.error('Download failed:', error);
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="p-3 rounded-lg bg-base-300">
      <div className="flex items-center gap-3">
        {statusIcons[job.status]}
        <div className="flex-1 min-w-0">
          <div className="font-medium text-sm truncate">{job.script_id}</div>
          {showDetails && (
            <div className="text-xs text-base-content/60">
              {job.stage} • {job.quality}
            </div>
          )}
        </div>
        {job.status === 'completed' && (
          <button
            onClick={handleDownload}
            disabled={isDownloading}
            className="btn btn-ghost btn-xs gap-1"
            aria-label="Download video"
          >
            {isDownloading ? (
              <Loader2 size={12} className="animate-spin" />
            ) : (
              <Download size={12} />
            )}
            Download
          </button>
        )}
        <span className={clsx('badge badge-sm', statusColors[job.status])}>
          {job.status}
        </span>
      </div>
      {job.status === 'rendering' && (
        <div className="mt-2">
          <progress
            className="progress progress-primary w-full"
            value={job.progress}
            max={100}
          />
          <div className="text-xs text-base-content/60 mt-1">{job.progress}%</div>
        </div>
      )}
      {job.error && (
        <div className="text-xs text-error mt-2">{job.error}</div>
      )}
    </div>
  );
}

// Script item for batch selection
interface ScriptSelectItemProps {
  script: VideoScriptItem;
  selected: boolean;
  onToggle: () => void;
}

function ScriptSelectItem({ script, selected, onToggle }: ScriptSelectItemProps) {
  return (
    <label
      className={clsx(
        'flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors',
        selected ? 'bg-primary/10 border border-primary' : 'bg-base-300 hover:bg-base-content/5'
      )}
    >
      <input
        type="checkbox"
        checked={selected}
        onChange={onToggle}
        className="checkbox checkbox-primary checkbox-sm"
      />
      <div className="flex-1 min-w-0">
        <div className="font-medium text-sm truncate">{script.name}</div>
        <div className="text-xs text-base-content/60">
          {script.language} • {script.has_output ? 'Props ready' : 'No props'}
        </div>
      </div>
      {script.has_output ? (
        <CheckCircle size={14} className="text-success flex-shrink-0" />
      ) : (
        <div className="badge badge-sm badge-ghost">Needs voiceover</div>
      )}
    </label>
  );
}

export function VideoRender() {
  const [selectedScript, setSelectedScript] = useState<string>('');
  const [selectedScripts, setSelectedScripts] = useState<Set<string>>(new Set());
  const [quality, setQuality] = useState<'preview' | 'production'>('production');
  const [batchMode, setBatchMode] = useState(false);
  const [batchProgress, setBatchProgress] = useState<{ current: number; total: number } | null>(null);

  const { data: scriptsData } = useVideoScripts();
  const { data: queueData, refetch: refetchQueue } = useRenderQueue({ polling: true });
  const renderMutation = useRenderMutation();

  const scripts: VideoScriptItem[] = scriptsData?.scripts || [];
  const queue = queueData || { jobs: [], active: 0, completed: 0, failed: 0 };

  // Filter scripts that are ready (have voiceover/props)
  const readyScripts = scripts.filter((s) => s.has_output);

  const handleStartRender = () => {
    renderMutation.mutate(
      { scriptId: selectedScript, quality },
      { onSuccess: () => setSelectedScript('') }
    );
  };

  // Batch render handlers
  const handleToggleScript = (scriptId: string) => {
    setSelectedScripts((prev) => {
      const next = new Set(prev);
      if (next.has(scriptId)) {
        next.delete(scriptId);
      } else {
        next.add(scriptId);
      }
      return next;
    });
  };

  const handleSelectAll = () => {
    setSelectedScripts(new Set(readyScripts.map((s) => s.id)));
  };

  const handleSelectNone = () => {
    setSelectedScripts(new Set());
  };

  const handleBatchRender = async () => {
    const scriptsToRender = Array.from(selectedScripts);
    if (scriptsToRender.length === 0) return;

    setBatchProgress({ current: 0, total: scriptsToRender.length });

    for (let i = 0; i < scriptsToRender.length; i++) {
      const scriptId = scriptsToRender[i];
      setBatchProgress({ current: i + 1, total: scriptsToRender.length });

      try {
        await new Promise<void>((resolve, reject) => {
          renderMutation.mutate(
            { scriptId, quality },
            {
              onSuccess: () => resolve(),
              onError: () => reject(),
            }
          );
        });
      } catch (e) {
        console.error(`Failed to queue render for ${scriptId}`);
      }
    }

    setBatchProgress(null);
    setSelectedScripts(new Set());
  };

  return (
    <div className="space-y-6">
      {/* Mode Toggle */}
      <div className="flex items-center gap-4">
        <div className="join">
          <button
            onClick={() => setBatchMode(false)}
            className={clsx('join-item btn btn-sm', !batchMode && 'btn-active')}
          >
            <Film size={14} className="mr-1" />
            Single
          </button>
          <button
            onClick={() => setBatchMode(true)}
            className={clsx('join-item btn btn-sm', batchMode && 'btn-active')}
          >
            <Layers size={14} className="mr-1" />
            Batch
          </button>
        </div>
        <span className="text-sm text-base-content/60">
          {batchMode
            ? `${readyScripts.length} scripts ready for rendering`
            : 'Render a single script'}
        </span>
      </div>

      {/* Single Render Controls */}
      {!batchMode && (
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="font-semibold flex items-center gap-2 mb-4">
              <Settings size={18} />
              Start New Render
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="label">
                  <span className="label-text">Script</span>
                </label>
                <select
                  className="select select-bordered w-full"
                  value={selectedScript}
                  onChange={(e) => setSelectedScript(e.target.value)}
                >
                  <option value="">Select a script...</option>
                  {scripts.map((script) => (
                    <option key={script.id} value={script.id} disabled={!script.has_output}>
                      {script.name} {!script.has_output && '(needs voiceover)'}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">
                  <span className="label-text">Quality</span>
                </label>
                <select
                  className="select select-bordered w-full"
                  value={quality}
                  onChange={(e) => setQuality(e.target.value as 'preview' | 'production')}
                >
                  <option value="preview">Preview (720p, fast)</option>
                  <option value="production">Production (1080p, high quality)</option>
                </select>
              </div>
              <div className="flex items-end">
                <button
                  onClick={handleStartRender}
                  disabled={!selectedScript || renderMutation.isPending}
                  className="btn btn-primary w-full gap-2"
                >
                  {renderMutation.isPending ? (
                    <Loader2 size={16} className="animate-spin" />
                  ) : (
                    <Play size={16} />
                  )}
                  Start Render
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Batch Render Controls */}
      {batchMode && (
        <div className="card bg-base-200">
          <div className="card-body">
            <div className="flex items-center gap-2 mb-4">
              <h3 className="font-semibold flex items-center gap-2">
                <Layers size={18} />
                Batch Render
              </h3>
              <div className="flex-1" />
              <select
                className="select select-bordered select-sm"
                value={quality}
                onChange={(e) => setQuality(e.target.value as 'preview' | 'production')}
              >
                <option value="preview">Preview Quality</option>
                <option value="production">Production Quality</option>
              </select>
            </div>

            {/* Selection actions */}
            <div className="flex items-center gap-2 mb-3">
              <button
                onClick={handleSelectAll}
                className="btn btn-ghost btn-xs gap-1"
              >
                <CheckSquare size={12} />
                Select All ({readyScripts.length})
              </button>
              <button
                onClick={handleSelectNone}
                className="btn btn-ghost btn-xs gap-1"
              >
                <Square size={12} />
                Select None
              </button>
              <div className="flex-1" />
              <span className="text-sm text-base-content/60">
                {selectedScripts.size} selected
              </span>
            </div>

            {/* Script list */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 max-h-80 overflow-y-auto">
              {readyScripts.map((script) => (
                <ScriptSelectItem
                  key={script.id}
                  script={script}
                  selected={selectedScripts.has(script.id)}
                  onToggle={() => handleToggleScript(script.id)}
                />
              ))}
              {readyScripts.length === 0 && (
                <p className="col-span-full text-center py-8 text-base-content/60">
                  No scripts ready for rendering. Generate voiceover first.
                </p>
              )}
            </div>

            {/* Batch action */}
            <div className="mt-4 flex items-center gap-4">
              <button
                onClick={handleBatchRender}
                disabled={selectedScripts.size === 0 || batchProgress !== null}
                className="btn btn-primary gap-2"
              >
                {batchProgress !== null ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Queuing {batchProgress.current} / {batchProgress.total}
                  </>
                ) : (
                  <>
                    <Play size={16} />
                    Render {selectedScripts.size} Script{selectedScripts.size !== 1 ? 's' : ''}
                  </>
                )}
              </button>
              {batchProgress !== null && (
                <progress
                  className="progress progress-primary flex-1"
                  value={batchProgress.current}
                  max={batchProgress.total}
                />
              )}
            </div>
          </div>
        </div>
      )}

      {/* Render Queue */}
      <div className="card bg-base-200">
        <div className="card-body">
          <div className="flex items-center gap-2 mb-4">
            <h3 className="font-semibold flex items-center gap-2">
              <Clock size={18} />
              Render Queue
            </h3>
            <div className="flex gap-2 text-sm">
              {queue.active > 0 && (
                <span className="badge badge-warning badge-sm">{queue.active} active</span>
              )}
              {queue.completed > 0 && (
                <span className="badge badge-success badge-sm">{queue.completed} done</span>
              )}
              {queue.failed > 0 && (
                <span className="badge badge-error badge-sm">{queue.failed} failed</span>
              )}
            </div>
            <div className="flex-1" />
            <button
              onClick={() => refetchQueue()}
              className="btn btn-ghost btn-sm"
              aria-label="Refresh queue"
            >
              <RefreshCw size={14} />
            </button>
          </div>

          {queue.jobs.length === 0 ? (
            <p className="text-base-content/60 text-sm">No render jobs</p>
          ) : (
            <div className="space-y-3">
              {queue.jobs.map((job: RenderJob) => (
                <RenderJobCard key={job.id} job={job} showDetails />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
