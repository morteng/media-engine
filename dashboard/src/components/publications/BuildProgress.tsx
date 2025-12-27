import { CheckCircle, Loader2, Clock, FileOutput } from 'lucide-react';
import type { BuildLogEntry, BuildOutput } from '@/api/types';
import clsx from 'clsx';

interface BuildProgressProps {
  isBuilding: boolean;
  progress: number;
  logs: BuildLogEntry[];
  outputs: BuildOutput[];
  showLogs?: boolean;
  maxLogs?: number;
}

export function BuildProgress({
  isBuilding,
  progress,
  logs,
  outputs,
  showLogs = true,
  maxLogs = 10,
}: BuildProgressProps) {
  const recentLogs = logs.slice(-maxLogs);

  return (
    <div className="space-y-4">
      {/* Progress bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="flex items-center gap-2">
            {isBuilding ? (
              <>
                <Loader2 size={16} className="animate-spin text-primary" />
                Building...
              </>
            ) : progress === 100 ? (
              <>
                <CheckCircle size={16} className="text-success" />
                Complete
              </>
            ) : (
              <>
                <Clock size={16} className="text-base-content/60" />
                Ready
              </>
            )}
          </span>
          <span className="font-mono">{Math.round(progress)}%</span>
        </div>
        <progress
          className={clsx('progress w-full', {
            'progress-primary': isBuilding,
            'progress-success': !isBuilding && progress === 100,
          })}
          value={progress}
          max={100}
        />
      </div>

      {/* Log output */}
      {showLogs && recentLogs.length > 0 && (
        <div className="bg-base-300 rounded-lg p-3 max-h-48 overflow-y-auto">
          <div className="space-y-1 font-mono text-xs">
            {recentLogs.map((log, idx) => (
              <div
                key={idx}
                className={clsx('flex items-start gap-2', {
                  'text-success': log.level === 'success',
                  'text-warning': log.level === 'warning',
                  'text-error': log.level === 'error',
                  'text-base-content/80': log.level === 'info',
                })}
              >
                <span className="text-base-content/40 flex-shrink-0">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
                <span>{log.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Build outputs */}
      {outputs.length > 0 && !isBuilding && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium flex items-center gap-2">
            <FileOutput size={14} />
            Generated Files
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {outputs.map((output, idx) => (
              <div
                key={idx}
                className="flex items-center gap-3 p-3 bg-base-300 rounded-lg"
              >
                <div className="text-2xl font-bold text-primary uppercase">
                  {output.format}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{output.name}</p>
                  <p className="text-xs text-base-content/60">
                    {output.language.toUpperCase()} &bull;{' '}
                    {(output.size / 1024).toFixed(1)} KB
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
