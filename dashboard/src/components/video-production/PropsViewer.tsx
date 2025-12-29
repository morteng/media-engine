/**
 * PropsViewer - View and inspect Remotion props.json data
 *
 * Features:
 * - JSON tree view with collapsible sections
 * - Scene timing visualization (visual timeline)
 * - Frame-to-time conversion display
 * - Copy-to-clipboard for Remotion render command
 */

import React, { useState } from 'react';
import {
  Copy,
  Check,
  Clock,
  Film,
  ChevronDown,
  ChevronRight,
  Layers,
  Settings,
  Terminal,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import type { VideoProps, UnifiedScene } from '@/api/types/video';
import { getSceneTypeColors } from '@/utils/statusMappings';

// ============================================================================
// Types
// ============================================================================

interface PropsViewerProps {
  props: VideoProps;
  /** Script ID for render command */
  scriptId?: string;
  /** Show render command section */
  showRenderCommand?: boolean;
  /** Additional className */
  className?: string;
}

// ============================================================================
// Helpers
// ============================================================================

function formatTime(frames: number, fps: number): string {
  const totalSeconds = frames / fps;
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toFixed(2).padStart(5, '0')}`;
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  if (mins === 0) return `${secs.toFixed(1)}s`;
  return `${mins}m ${secs.toFixed(0)}s`;
}

// ============================================================================
// Collapsible JSON Section
// ============================================================================

interface JsonSectionProps {
  title: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

function JsonSection({ title, icon, children, defaultOpen = false }: JsonSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border border-base-300 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-2 p-3 bg-base-200 hover:bg-base-300 transition-colors"
      >
        {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        {icon}
        <span className="font-medium">{title}</span>
      </button>
      {isOpen && (
        <div className="p-3 bg-base-100 border-t border-base-300">
          {children}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Timeline Visualization
// ============================================================================

interface TimelineVizProps {
  scenes: UnifiedScene[];
  totalFrames: number;
  fps: number;
}

function TimelineVisualization({ scenes, totalFrames, fps }: TimelineVizProps) {
  return (
    <div className="space-y-2">
      {/* Visual timeline bar */}
      <div className="h-8 bg-base-300 rounded-lg overflow-hidden flex">
        {scenes.map((scene) => {
          const width = ((scene.durationFrames || 0) / totalFrames) * 100;
          const colors = getSceneTypeColors(scene.type);

          return (
            <div
              key={scene.id}
              className={cn(
                'h-full border-r border-base-100 flex items-center justify-center',
                'text-xs font-medium truncate px-1',
                colors.bg,
                colors.text
              )}
              style={{ width: `${width}%` }}
              title={`${scene.id}: ${scene.durationFrames} frames`}
            >
              {width > 5 && scene.id}
            </div>
          );
        })}
      </div>

      {/* Frame markers */}
      <div className="flex justify-between text-xs text-base-content/40 font-mono">
        <span>0</span>
        <span>{Math.floor(totalFrames / 4)}</span>
        <span>{Math.floor(totalFrames / 2)}</span>
        <span>{Math.floor((totalFrames * 3) / 4)}</span>
        <span>{totalFrames}</span>
      </div>
    </div>
  );
}

// ============================================================================
// Scene Table
// ============================================================================

interface SceneTableProps {
  scenes: UnifiedScene[];
  fps: number;
}

function SceneTable({ scenes, fps }: SceneTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="table table-sm">
        <thead>
          <tr>
            <th>ID</th>
            <th>Type</th>
            <th className="text-right">Start</th>
            <th className="text-right">End</th>
            <th className="text-right">Frames</th>
            <th className="text-right">Duration</th>
          </tr>
        </thead>
        <tbody className="font-mono text-sm">
          {scenes.map((scene) => {
            const colors = getSceneTypeColors(scene.type);
            return (
              <tr key={scene.id} className="hover">
                <td className="font-medium">{scene.id}</td>
                <td>
                  <span className={cn('badge badge-sm', colors.bg, colors.text, colors.border)}>
                    {scene.type}
                  </span>
                </td>
                <td className="text-right text-base-content/60">
                  {scene.startFrame ?? '-'}
                </td>
                <td className="text-right text-base-content/60">
                  {scene.endFrame ?? '-'}
                </td>
                <td className="text-right">
                  {scene.durationFrames ?? '-'}
                </td>
                <td className="text-right text-base-content/60">
                  {scene.durationFrames
                    ? formatTime(scene.durationFrames, fps)
                    : '-'}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ============================================================================
// Render Command
// ============================================================================

interface RenderCommandProps {
  scriptId: string;
  props: VideoProps;
}

function RenderCommand({ scriptId, props }: RenderCommandProps) {
  const [copied, setCopied] = useState(false);

  const command = `cd remotion && npx remotion render Main out/${scriptId}.mp4 --props ../demo/output/${props.language}/videos/${scriptId}.props.json`;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(command);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm text-base-content/60">Render command:</span>
        <button
          onClick={handleCopy}
          className="btn btn-ghost btn-xs gap-1"
        >
          {copied ? (
            <>
              <Check size={14} className="text-success" />
              Copied
            </>
          ) : (
            <>
              <Copy size={14} />
              Copy
            </>
          )}
        </button>
      </div>
      <pre className="bg-base-300 rounded-lg p-3 text-sm font-mono overflow-x-auto whitespace-pre-wrap break-all">
        {command}
      </pre>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function PropsViewer({
  props,
  scriptId,
  showRenderCommand = true,
  className,
}: PropsViewerProps) {
  const totalFrames = props.scenes.reduce(
    (max, s) => Math.max(max, s.endFrame || 0),
    0
  );

  return (
    <div className={cn('space-y-4', className)}>
      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-base-200 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold">{props.scenes.length}</div>
          <div className="text-xs text-base-content/60">Scenes</div>
        </div>
        <div className="bg-base-200 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold font-mono">{totalFrames}</div>
          <div className="text-xs text-base-content/60">Total Frames</div>
        </div>
        <div className="bg-base-200 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold">{formatDuration(props.duration)}</div>
          <div className="text-xs text-base-content/60">Duration</div>
        </div>
        <div className="bg-base-200 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold">
            {props.width}x{props.height}
          </div>
          <div className="text-xs text-base-content/60">{props.fps} fps</div>
        </div>
      </div>

      {/* Timeline visualization */}
      <JsonSection
        title="Timeline"
        icon={<Layers size={16} />}
        defaultOpen={true}
      >
        <TimelineVisualization
          scenes={props.scenes}
          totalFrames={totalFrames}
          fps={props.fps}
        />
      </JsonSection>

      {/* Scene timing table */}
      <JsonSection
        title="Scene Timing"
        icon={<Clock size={16} />}
        defaultOpen={true}
      >
        <SceneTable scenes={props.scenes} fps={props.fps} />
      </JsonSection>

      {/* Video settings */}
      <JsonSection
        title="Video Settings"
        icon={<Settings size={16} />}
      >
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-base-content/60">Resolution:</span>
            <span className="ml-2 font-mono">{props.width} x {props.height}</span>
          </div>
          <div>
            <span className="text-base-content/60">Frame Rate:</span>
            <span className="ml-2 font-mono">{props.fps} fps</span>
          </div>
          <div>
            <span className="text-base-content/60">Quality:</span>
            <span className={cn(
              'ml-2 badge badge-sm',
              props.quality === 'production' ? 'badge-success' : 'badge-warning'
            )}>
              {props.quality}
            </span>
          </div>
          <div>
            <span className="text-base-content/60">Releasable:</span>
            <span className={cn(
              'ml-2 badge badge-sm',
              props.is_releasable ? 'badge-success' : 'badge-error'
            )}>
              {props.is_releasable ? 'Yes' : 'No'}
            </span>
          </div>
          <div>
            <span className="text-base-content/60">Language:</span>
            <span className="ml-2">{props.language}</span>
          </div>
          <div>
            <span className="text-base-content/60">Title:</span>
            <span className="ml-2">{props.title}</span>
          </div>
        </div>
      </JsonSection>

      {/* Render command */}
      {showRenderCommand && scriptId && (
        <JsonSection
          title="Render Command"
          icon={<Terminal size={16} />}
        >
          <RenderCommand scriptId={scriptId} props={props} />
        </JsonSection>
      )}

      {/* Raw JSON (collapsed by default) */}
      <JsonSection
        title="Raw JSON"
        icon={<Film size={16} />}
      >
        <pre className="bg-base-300 rounded-lg p-3 text-xs font-mono overflow-auto max-h-96">
          {JSON.stringify(props, null, 2)}
        </pre>
      </JsonSection>
    </div>
  );
}

export default PropsViewer;
