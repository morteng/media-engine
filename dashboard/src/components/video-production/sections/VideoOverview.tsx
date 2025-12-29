/**
 * VideoOverview - Dashboard view for video production
 * Shows stats, recent scripts, and render queue
 */

import { Film, FileVideo, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { Spinner } from '@/components/ui';
import { useVideoOverviewData } from '@/hooks/useVideoApi';
import type { VideoScriptItem, RenderJob } from '@/api/types';

interface RenderJobCardProps {
  job: RenderJob;
  compact?: boolean;
}

function RenderJobCard({ job, compact = true }: RenderJobCardProps) {
  const statusIcons = {
    completed: <CheckCircle size={14} className="text-success" />,
    failed: <XCircle size={14} className="text-error" />,
    rendering: <Clock size={14} className="text-warning animate-pulse" />,
    queued: <AlertCircle size={14} className="text-info" />,
  };

  return (
    <div className="flex items-center gap-3 p-3 rounded-lg bg-base-300">
      {statusIcons[job.status as keyof typeof statusIcons] || statusIcons.queued}
      <div className="flex-1 min-w-0">
        <div className="font-medium truncate">{job.script_id}</div>
        {!compact && (
          <div className="text-xs text-base-content/60">
            {job.quality} quality
          </div>
        )}
      </div>
      <span className={`badge badge-sm ${
        job.status === 'completed' ? 'badge-success' :
        job.status === 'failed' ? 'badge-error' :
        job.status === 'rendering' ? 'badge-warning' :
        'badge-info'
      }`}>
        {job.status}
      </span>
    </div>
  );
}

export function VideoOverview() {
  const { scripts, queue, assets, isLoading, error } = useVideoOverviewData();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" className="text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-error">
        <span>Failed to load video data</span>
      </div>
    );
  }

  const renderedCount = scripts.filter((s: VideoScriptItem) => s.has_output).length;
  const activeRenders = queue.filter((j: RenderJob) => j.status === 'rendering').length;

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card bg-base-200">
          <div className="card-body p-4">
            <div className="text-2xl font-bold text-primary">{scripts.length}</div>
            <div className="text-sm text-base-content/60">Video Scripts</div>
          </div>
        </div>
        <div className="card bg-base-200">
          <div className="card-body p-4">
            <div className="text-2xl font-bold text-success">{renderedCount}</div>
            <div className="text-sm text-base-content/60">Rendered Videos</div>
          </div>
        </div>
        <div className="card bg-base-200">
          <div className="card-body p-4">
            <div className="text-2xl font-bold text-warning">{activeRenders}</div>
            <div className="text-sm text-base-content/60">Active Renders</div>
          </div>
        </div>
        <div className="card bg-base-200">
          <div className="card-body p-4">
            <div className="text-2xl font-bold text-info">{assets?.demos?.length || 0}</div>
            <div className="text-sm text-base-content/60">Demo Clips</div>
          </div>
        </div>
      </div>

      {/* Recent Scripts */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="font-semibold flex items-center gap-2 mb-4">
            <Film size={18} className="text-primary" />
            Video Scripts
          </h3>
          {scripts.length === 0 ? (
            <p className="text-base-content/60 text-sm">No video scripts found</p>
          ) : (
            <div className="space-y-2">
              {scripts.slice(0, 5).map((script: VideoScriptItem) => (
                <div key={script.id} className="flex items-center gap-3 p-3 rounded-lg bg-base-300">
                  <FileVideo size={16} className="text-primary" />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">{script.name}</div>
                    <div className="text-xs text-base-content/60">
                      {script.scenes} scenes • {script.duration}s
                    </div>
                  </div>
                  {script.has_output && (
                    <span className="badge badge-success badge-sm">Rendered</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recent Renders */}
      {queue.length > 0 && (
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="font-semibold flex items-center gap-2 mb-4">
              <Clock size={18} className="text-primary" />
              Recent Renders
            </h3>
            <div className="space-y-2">
              {queue.slice(0, 5).map((job: RenderJob) => (
                <RenderJobCard key={job.id} job={job} compact />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
