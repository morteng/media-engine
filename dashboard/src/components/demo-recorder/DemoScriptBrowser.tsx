/**
 * DemoScriptBrowser - Left panel showing demo recording definitions
 */

import { Film, Video, Layers, Globe, AlertCircle } from 'lucide-react';
import clsx from 'clsx';
import type { DemoRecording } from './types';

interface DemoScriptBrowserProps {
  demos: DemoRecording[];
  selectedDemoId: string | null;
  onSelectDemo: (id: string) => void;
  isLoading?: boolean;
}

export function DemoScriptBrowser({
  demos,
  selectedDemoId,
  onSelectDemo,
  isLoading,
}: DemoScriptBrowserProps) {
  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <span className="loading loading-spinner loading-md" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-3 border-b border-base-300">
        <h2 className="text-sm font-semibold text-base-content/70 uppercase tracking-wider flex items-center gap-2">
          <Film size={14} />
          Demo Recordings
        </h2>
        <p className="text-xs text-base-content/50 mt-1">
          {demos.length} demo definitions
        </p>
      </div>

      {/* Demo List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {demos.length === 0 ? (
          <div className="text-center py-8 text-base-content/50">
            <Video size={32} className="mx-auto mb-2 opacity-50" />
            <p className="text-sm">No demo recordings found</p>
            <p className="text-xs mt-1">
              Create demo YAML files in content/*/demos/
            </p>
          </div>
        ) : (
          demos.map((demo) => (
            <button
              key={demo.id}
              onClick={() => onSelectDemo(demo.id)}
              className={clsx(
                'w-full text-left p-3 rounded-lg transition-colors',
                'hover:bg-base-300',
                {
                  'bg-primary/20 border border-primary/30': selectedDemoId === demo.id,
                  'bg-base-200': selectedDemoId !== demo.id,
                }
              )}
            >
              <div className="flex items-start gap-2">
                <Video
                  size={16}
                  className={clsx('mt-0.5 flex-shrink-0', {
                    'text-primary': selectedDemoId === demo.id,
                    'text-base-content/50': selectedDemoId !== demo.id,
                  })}
                />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm truncate">{demo.name}</div>
                  <div className="flex items-center gap-3 mt-1 text-xs text-base-content/60">
                    {demo.states_count !== undefined && (
                      <span className="flex items-center gap-1">
                        <Layers size={12} />
                        {demo.states_count} states
                      </span>
                    )}
                    {demo.language && (
                      <span className="flex items-center gap-1">
                        <Globe size={12} />
                        {demo.language.toUpperCase()}
                      </span>
                    )}
                  </div>
                  {demo.viewport && (
                    <div className="text-xs text-base-content/50 mt-1">
                      {demo.viewport.width}x{demo.viewport.height}
                    </div>
                  )}
                  {demo.error && (
                    <div className="flex items-center gap-1 mt-1 text-xs text-error">
                      <AlertCircle size={12} />
                      Error loading
                    </div>
                  )}
                </div>
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}
