/**
 * DemoStateBrowser - Left panel for browsing demos and selecting states
 */

import { Film, Video, Layers, Globe, ChevronRight, ImageIcon } from 'lucide-react';
import clsx from 'clsx';
import type { DemoRecording, DemoRecordingState } from '@/api/video';

interface DemoStateBrowserProps {
  demos: DemoRecording[];
  selectedDemoId: string | null;
  selectedStateId: string | null;
  states: DemoRecordingState[];
  onSelectDemo: (demoId: string) => void;
  onSelectState: (stateId: string) => void;
  isLoading?: boolean;
  hasScreenshots?: Record<string, boolean>;
}

export function DemoStateBrowser({
  demos,
  selectedDemoId,
  selectedStateId,
  states,
  onSelectDemo,
  onSelectState,
  isLoading,
  hasScreenshots = {},
}: DemoStateBrowserProps) {
  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <span className="loading loading-spinner loading-md" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="p-3 border-b border-base-300 flex-shrink-0">
        <h2 className="text-sm font-semibold text-base-content/70 uppercase tracking-wider flex items-center gap-2">
          <Film size={14} />
          Demos & States
        </h2>
        <p className="text-xs text-base-content/50 mt-1">
          {demos.length} demos available
        </p>
      </div>

      {/* Demo List */}
      <div className="flex-1 overflow-y-auto">
        {demos.length === 0 ? (
          <div className="text-center py-8 text-base-content/50 px-4">
            <Video size={32} className="mx-auto mb-2 opacity-50" />
            <p className="text-sm">No demo recordings found</p>
            <p className="text-xs mt-1">
              Create demo YAML files in content/*/demos/
            </p>
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {demos.map((demo) => (
              <div key={demo.id}>
                {/* Demo Item */}
                <button
                  onClick={() => onSelectDemo(demo.id)}
                  className={clsx(
                    'w-full text-left p-2 rounded-lg transition-colors',
                    'hover:bg-base-300',
                    {
                      'bg-primary/10 border border-primary/20': selectedDemoId === demo.id,
                      'bg-base-200/50': selectedDemoId !== demo.id,
                    }
                  )}
                >
                  <div className="flex items-start gap-2">
                    <ChevronRight
                      size={14}
                      className={clsx(
                        'mt-1 flex-shrink-0 transition-transform',
                        selectedDemoId === demo.id && 'rotate-90'
                      )}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate">{demo.name}</div>
                      <div className="flex items-center gap-2 mt-0.5 text-xs text-base-content/60">
                        {demo.states_count !== undefined && (
                          <span className="flex items-center gap-1">
                            <Layers size={10} />
                            {demo.states_count} states
                          </span>
                        )}
                        {demo.language && (
                          <span className="flex items-center gap-1">
                            <Globe size={10} />
                            {demo.language.toUpperCase()}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </button>

                {/* States List (when demo is selected) */}
                {selectedDemoId === demo.id && states.length > 0 && (
                  <div className="ml-4 mt-1 space-y-0.5 border-l-2 border-base-300 pl-2">
                    {states.map((state, index) => {
                      const hasScreenshot = hasScreenshots[state.id] ?? false;
                      return (
                        <button
                          key={state.id}
                          onClick={() => onSelectState(state.id)}
                          className={clsx(
                            'w-full text-left px-2 py-1.5 rounded transition-colors text-xs',
                            'hover:bg-base-300',
                            {
                              'bg-primary/20 text-primary font-medium': selectedStateId === state.id,
                              'text-base-content/70': selectedStateId !== state.id,
                            }
                          )}
                        >
                          <div className="flex items-center gap-2">
                            <span className="text-base-content/40 font-mono text-[10px]">
                              {String(index + 1).padStart(2, '0')}
                            </span>
                            <span className="truncate flex-1">
                              {state.description || state.id}
                            </span>
                            {hasScreenshot && (
                              <ImageIcon size={10} className="text-success flex-shrink-0" />
                            )}
                          </div>
                          {state.duration && (
                            <div className="text-[10px] text-base-content/40 ml-6">
                              {state.duration}s
                            </div>
                          )}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default DemoStateBrowser;
