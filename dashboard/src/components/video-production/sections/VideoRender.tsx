/**
 * VideoRender - Render control tab for video production
 * Handles starting renders and monitoring the render queue
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

export function VideoRender() {
  const [selectedScript, setSelectedScript] = useState<string>('');
  const [quality, setQuality] = useState<'preview' | 'production'>('production');

  const { data: scriptsData } = useVideoScripts();
  const { data: queueData, refetch: refetchQueue } = useRenderQueue({ polling: true });
  const renderMutation = useRenderMutation();

  const scripts: VideoScriptItem[] = scriptsData?.scripts || [];
  const queue = queueData || { jobs: [], active: 0, completed: 0, failed: 0 };

  const handleStartRender = () => {
    renderMutation.mutate(
      { scriptId: selectedScript, quality },
      { onSuccess: () => setSelectedScript('') }
    );
  };

  return (
    <div className="space-y-6">
      {/* Render Controls */}
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
                  <option key={script.id} value={script.id}>
                    {script.name}
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

      {/* Render Queue */}
      <div className="card bg-base-200">
        <div className="card-body">
          <div className="flex items-center gap-2 mb-4">
            <h3 className="font-semibold flex items-center gap-2">
              <Clock size={18} />
              Render Queue
            </h3>
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
