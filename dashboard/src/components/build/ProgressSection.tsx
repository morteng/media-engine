import { ChevronUp, ChevronDown } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';
import type { BuildLogEntry } from '@/api/types';

interface ProgressSectionProps {
  active: boolean;
  progress: number;
  logs: BuildLogEntry[];
}

export function ProgressSection({ active, progress, logs }: ProgressSectionProps) {
  const [expanded, setExpanded] = useState(true);
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Auto-expand when build starts
  useEffect(() => {
    if (active) {
      setExpanded(true);
    }
  }, [active]);

  // Auto-scroll to latest log
  useEffect(() => {
    if (expanded && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, expanded]);

  if (!active && logs.length === 0) {
    return null;
  }

  return (
    <div className="card bg-base-200">
      <div className="card-body">
        {/* Progress Bar */}
        {active && (
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Building...</span>
              <span className="text-sm text-base-content/60">{progress}%</span>
            </div>
            <div className="w-full bg-base-300 rounded-full h-2">
              <div
                className="bg-primary h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Logs Header */}
        {logs.length > 0 && (
          <>
            <div
              className="flex items-center justify-between cursor-pointer"
              onClick={() => setExpanded(!expanded)}
            >
              <h3 className="font-medium">
                {active ? 'Build Progress' : 'Build Complete'}
              </h3>
              <button className="btn btn-ghost btn-xs">
                {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </button>
            </div>

            {/* Logs Content */}
            {expanded && (
              <div className="mt-4 bg-base-300 rounded-lg p-4 max-h-48 overflow-y-auto font-mono text-xs">
                {logs.map((log, idx) => (
                  <div
                    key={idx}
                    className={`py-0.5 ${
                      log.level === 'error'
                        ? 'text-error'
                        : log.level === 'warning'
                        ? 'text-warning'
                        : log.level === 'success'
                        ? 'text-success'
                        : 'text-base-content/80'
                    }`}
                  >
                    <span className="text-base-content/40 mr-2">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                    {log.message}
                  </div>
                ))}
                <div ref={logsEndRef} />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
