/**
 * VideoProps - Dedicated tab for viewing and analyzing props.json
 *
 * Features:
 * - Script selector
 * - Props viewer with scene timing
 * - Render command copy
 * - Quality indicator
 */

import React, { useState } from 'react';
import { FileJson, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react';
import { cn } from '@/utils/cn';
import { useVideoPropsData } from '@/hooks/useVideoApi';
import { Spinner } from '@/components/ui';
import { PropsViewer } from '../PropsViewer';

// ============================================================================
// Main Component
// ============================================================================

export function VideoProps() {
  const [selectedScriptId, setSelectedScriptId] = useState<string | null>(null);

  const { scripts, scriptsLoading, props, propsLoading, propsError, refetchProps } =
    useVideoPropsData(selectedScriptId);

  // Auto-select first script
  React.useEffect(() => {
    if (!selectedScriptId && scripts.length > 0) {
      setSelectedScriptId(scripts[0].id);
    }
  }, [scripts, selectedScriptId]);

  // Find selected script details
  const selectedScript = scripts.find((s) => s.id === selectedScriptId);

  if (scriptsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <FileJson size={24} className="text-primary" />
          <div>
            <h2 className="text-lg font-semibold">Remotion Props</h2>
            <p className="text-sm text-base-content/60">
              View generated props.json with scene timing data
            </p>
          </div>
        </div>

        {/* Refresh button */}
        <button
          onClick={() => refetchProps()}
          disabled={!selectedScriptId || propsLoading}
          className="btn btn-ghost btn-sm gap-2"
        >
          <RefreshCw size={16} className={propsLoading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Script selector */}
      <div className="flex flex-wrap items-center gap-4 bg-base-200 rounded-lg p-4">
        <div className="flex-1 min-w-[200px]">
          <label className="text-sm text-base-content/60 mb-1 block">Script</label>
          <select
            value={selectedScriptId || ''}
            onChange={(e) => setSelectedScriptId(e.target.value || null)}
            className="select select-bordered w-full"
          >
            <option value="">Select a script...</option>
            {scripts.map((script) => (
              <option key={script.id} value={script.id}>
                {script.name} ({script.language})
              </option>
            ))}
          </select>
        </div>

        {/* Script info */}
        {selectedScript && (
          <div className="flex items-center gap-6 text-sm">
            <div>
              <span className="text-base-content/60">Scenes:</span>
              <span className="ml-2 font-medium">{selectedScript.scenes}</span>
            </div>
            {selectedScript.duration && (
              <div>
                <span className="text-base-content/60">Duration:</span>
                <span className="ml-2 font-medium">
                  {(selectedScript.duration / 60).toFixed(1)}m
                </span>
              </div>
            )}
            <div>
              <span className="text-base-content/60">Output:</span>
              {selectedScript.has_output ? (
                <span className="ml-2 badge badge-success badge-sm">
                  <CheckCircle size={12} className="mr-1" />
                  Generated
                </span>
              ) : (
                <span className="ml-2 badge badge-warning badge-sm">
                  <AlertCircle size={12} className="mr-1" />
                  Not generated
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Loading state */}
      {propsLoading && (
        <div className="flex items-center justify-center h-64">
          <Spinner size="lg" />
          <span className="ml-3 text-base-content/60">Loading props...</span>
        </div>
      )}

      {/* Error state */}
      {propsError && (
        <div className="bg-error/10 border border-error/30 rounded-lg p-6 text-center">
          <AlertCircle size={32} className="mx-auto text-error mb-3" />
          <h3 className="text-lg font-medium text-error mb-2">
            Failed to load props
          </h3>
          <p className="text-sm text-base-content/60 mb-4">
            {propsError instanceof Error ? propsError.message : 'Unknown error'}
          </p>
          <p className="text-sm text-base-content/60">
            Props are generated when you build the video with voiceover.
            <br />
            Make sure the script has been processed first.
          </p>
          <button
            onClick={() => refetchProps()}
            className="btn btn-error btn-sm mt-4"
          >
            <RefreshCw size={14} />
            Retry
          </button>
        </div>
      )}

      {/* Props viewer */}
      {props && !propsLoading && (
        <PropsViewer
          props={props}
          scriptId={selectedScriptId || undefined}
          showRenderCommand={true}
        />
      )}

      {/* Empty state - no script selected */}
      {!selectedScriptId && !scriptsLoading && (
        <div className="text-center py-16 text-base-content/40">
          <FileJson size={48} className="mx-auto mb-4 opacity-30" />
          <p className="text-lg">Select a script to view its props</p>
          <p className="text-sm mt-2">
            Props contain scene timing data used by Remotion for rendering
          </p>
        </div>
      )}

      {/* Empty state - script selected but no props */}
      {selectedScriptId && !props && !propsLoading && !propsError && (
        <div className="text-center py-16 text-base-content/40">
          <FileJson size={48} className="mx-auto mb-4 opacity-30" />
          <p className="text-lg">No props available</p>
          <p className="text-sm mt-2">
            Generate voiceover for this script to create props.json
          </p>
        </div>
      )}

      {/* Info box */}
      <div className="bg-base-200 rounded-lg p-4 text-sm">
        <h4 className="font-medium mb-2">About Props</h4>
        <p className="text-base-content/60">
          Props.json is generated by the video builder and contains all the data
          Remotion needs to render your video:
        </p>
        <ul className="list-disc list-inside mt-2 text-base-content/60 space-y-1">
          <li>
            <strong>Scene timing</strong> - Frame-accurate start/end positions
          </li>
          <li>
            <strong>Duration</strong> - Total length based on voiceover
          </li>
          <li>
            <strong>Resolution</strong> - Video dimensions and frame rate
          </li>
          <li>
            <strong>Quality</strong> - Whether output is release-ready
          </li>
        </ul>
      </div>
    </div>
  );
}

export default VideoProps;
