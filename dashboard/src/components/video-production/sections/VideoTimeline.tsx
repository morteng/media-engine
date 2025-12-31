/**
 * VideoTimeline - Visual scene timeline with frame-accurate editing
 *
 * Features:
 * - Full-width timeline with frame markers
 * - Scene blocks with type colors
 * - Click/drag to seek
 * - Zoom in/out controls
 * - Scene list sidebar
 * - Video player integration
 */

import React, { useState, useMemo, useCallback } from 'react';
import {
  ZoomIn,
  ZoomOut,
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Maximize2,
  List,
  LayoutGrid,
  Film,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { useVideoTimelineData, useVideoAssets } from '@/hooks/useVideoApi';
import { Spinner, EmptyState } from '@/components/ui';
import { SceneCard, SceneList } from '../SceneCard';
import { VideoPlayer } from '../VideoPlayer';
import { getSceneTypeColors } from '@/utils/statusMappings';
import type { UnifiedScene } from '@/api/types/video';

// ============================================================================
// Timeline Bar Component
// ============================================================================

interface TimelineBarProps {
  scenes: UnifiedScene[];
  totalFrames: number;
  currentFrame: number;
  fps: number;
  zoom: number;
  onSeek: (frame: number) => void;
  onSelectScene: (sceneId: string) => void;
  selectedSceneId: string | null;
}

function TimelineBar({
  scenes,
  totalFrames,
  currentFrame,
  fps,
  zoom,
  onSeek,
  onSelectScene,
  selectedSceneId,
}: TimelineBarProps) {
  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = x / rect.width;
    const frame = Math.round(percentage * totalFrames);
    onSeek(frame);
  };

  const playheadPosition = totalFrames > 0 ? (currentFrame / totalFrames) * 100 : 0;

  return (
    <div className="relative">
      {/* Scene blocks */}
      <div
        className="h-16 bg-base-300 rounded-lg overflow-hidden flex cursor-pointer relative"
        onClick={handleClick}
        style={{ transform: `scaleX(${zoom})`, transformOrigin: 'left' }}
      >
        {scenes.map((scene) => {
          const width = totalFrames > 0 ? ((scene.durationFrames || 0) / totalFrames) * 100 : 0;
          const colors = getSceneTypeColors(scene.type);
          const isSelected = selectedSceneId === scene.id;

          return (
            <div
              key={scene.id}
              onClick={(e) => {
                e.stopPropagation();
                onSelectScene(scene.id);
              }}
              className={cn(
                'h-full border-r border-base-100 flex flex-col items-center justify-center',
                'transition-all duration-150 hover:brightness-110',
                colors.bg,
                isSelected && 'ring-2 ring-inset ring-white/50'
              )}
              style={{ width: `${width}%` }}
              title={`${scene.title || scene.id}\n${scene.durationFrames} frames (${((scene.durationFrames || 0) / fps).toFixed(1)}s)`}
            >
              {width > 3 && (
                <>
                  <span className={cn('text-xs font-medium truncate px-1', colors.text)}>
                    {scene.title || scene.id}
                  </span>
                  {width > 8 && (
                    <span className="text-[10px] text-base-content/40">
                      {((scene.durationFrames || 0) / fps).toFixed(1)}s
                    </span>
                  )}
                </>
              )}
            </div>
          );
        })}

        {/* Playhead */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-white shadow-lg pointer-events-none z-10"
          style={{ left: `${playheadPosition}%` }}
        >
          <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-3 h-3 bg-white rotate-45" />
        </div>
      </div>

      {/* Frame markers */}
      <div className="flex justify-between text-xs text-base-content/40 font-mono mt-1 px-1">
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
// Scene Detail Panel
// ============================================================================

interface SceneDetailProps {
  scene: UnifiedScene | null;
  fps: number;
}

function SceneDetail({ scene, fps }: SceneDetailProps) {
  if (!scene) {
    return (
      <div className="flex items-center justify-center h-full text-base-content/40">
        Select a scene to view details
      </div>
    );
  }

  const colors = getSceneTypeColors(scene.type);
  const durationSecs = (scene.durationFrames || 0) / fps;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className={cn('p-4 rounded-lg', colors.bg)}>
        <div className="flex items-center justify-between mb-2">
          <span className={cn('badge', colors.text, colors.border)}>{scene.type}</span>
          <span className="text-sm font-mono text-base-content/60">
            {scene.startFrame} - {scene.endFrame}
          </span>
        </div>
        <h3 className={cn('text-lg font-semibold', colors.text)}>
          {scene.title || scene.name || scene.id}
        </h3>
        <p className="text-sm text-base-content/60 mt-1">
          {scene.durationFrames} frames ({durationSecs.toFixed(2)}s)
        </p>
      </div>

      {/* Voiceover */}
      {scene.text && (
        <div className="bg-base-200 rounded-lg p-4">
          <h4 className="text-sm font-medium mb-2">Voiceover</h4>
          <p className="text-sm text-base-content/70">{scene.text}</p>
        </div>
      )}

      {/* Visual settings */}
      {scene.visual && (
        <div className="bg-base-200 rounded-lg p-4">
          <h4 className="text-sm font-medium mb-2">Visual Settings</h4>
          <div className="flex flex-wrap gap-2">
            {scene.visual.background && (
              <span className="badge badge-sm badge-ghost">
                bg: {scene.visual.background}
              </span>
            )}
            {scene.visual.transition_in && (
              <span className="badge badge-sm badge-ghost">
                in: {scene.visual.transition_in}
              </span>
            )}
            {scene.visual.text_effect && (
              <span className="badge badge-sm badge-ghost">
                fx: {scene.visual.text_effect}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function VideoTimeline() {
  const [selectedScriptId, setSelectedScriptId] = useState<string | null>(null);
  const [selectedSceneId, setSelectedSceneId] = useState<string | null>(null);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [zoom, setZoom] = useState(1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');
  const [showPlayer, setShowPlayer] = useState(true);

  const { scripts, scriptsLoading, props, propsLoading } = useVideoTimelineData(selectedScriptId);
  const { data: assets } = useVideoAssets();

  // Auto-select first script
  React.useEffect(() => {
    if (!selectedScriptId && scripts.length > 0) {
      setSelectedScriptId(scripts[0].id);
    }
  }, [scripts, selectedScriptId]);

  // Computed values
  const scenes = props?.scenes || [];
  const fps = props?.fps || 30;
  const totalFrames = scenes.reduce((max, s) => Math.max(max, s.endFrame || 0), 0);

  const selectedScene = useMemo(
    () => scenes.find((s) => s.id === selectedSceneId) || null,
    [scenes, selectedSceneId]
  );

  // Find video URL for current script from assets
  const videoUrl = useMemo(() => {
    if (!selectedScriptId || !assets?.outputs) return null;
    // Look for rendered video matching script ID
    const video = assets.outputs.find((f: { name: string; path: string }) =>
      f.name.includes(selectedScriptId) && (f.name.endsWith('.mp4') || f.name.endsWith('.webm'))
    );
    return video ? `/api/assets/output/${encodeURIComponent(video.name)}` : null;
  }, [selectedScriptId, assets]);

  // Prepare scenes for VideoPlayer (map UnifiedScene to expected format)
  const playerScenes = useMemo(() =>
    scenes.map((s) => ({
      id: s.id,
      type: s.type,
      title: s.title || s.name,
      duration: (s.durationFrames || 0) / fps,
      startFrame: s.startFrame || 0,
      endFrame: s.endFrame || 0,
    })),
    [scenes, fps]
  );

  // Handlers
  const handleSeek = useCallback((frame: number) => {
    setCurrentFrame(Math.max(0, Math.min(frame, totalFrames)));
    // Find which scene this frame is in and select it
    const scene = scenes.find(
      (s) => frame >= (s.startFrame || 0) && frame < (s.endFrame || 0)
    );
    if (scene) {
      setSelectedSceneId(scene.id);
    }
  }, [scenes, totalFrames]);

  // Handle frame changes from VideoPlayer
  const handleFrameChange = useCallback((frame: number) => {
    setCurrentFrame(frame);
    // Update selected scene based on current frame
    const scene = scenes.find(
      (s) => frame >= (s.startFrame || 0) && frame < (s.endFrame || 0)
    );
    if (scene && scene.id !== selectedSceneId) {
      setSelectedSceneId(scene.id);
    }
  }, [scenes, selectedSceneId]);

  // Handle scene selection from VideoPlayer
  const handleSceneChange = useCallback((sceneId: string) => {
    setSelectedSceneId(sceneId);
    const scene = scenes.find((s) => s.id === sceneId);
    if (scene) {
      setCurrentFrame(scene.startFrame || 0);
    }
  }, [scenes]);

  const handleZoomIn = () => setZoom((z) => Math.min(z + 0.25, 3));
  const handleZoomOut = () => setZoom((z) => Math.max(z - 0.25, 0.5));
  const handleReset = () => setZoom(1);

  if (scriptsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {/* Script selector */}
          <select
            value={selectedScriptId || ''}
            onChange={(e) => {
              setSelectedScriptId(e.target.value || null);
              setSelectedSceneId(null);
              setCurrentFrame(0);
            }}
            className="select select-bordered select-sm"
          >
            <option value="">Select script...</option>
            {scripts.map((script) => (
              <option key={script.id} value={script.id}>
                {script.name} ({script.language})
              </option>
            ))}
          </select>

          {/* View mode toggle */}
          <div className="join">
            <button
              onClick={() => setViewMode('list')}
              className={cn('join-item btn btn-sm', viewMode === 'list' && 'btn-active')}
            >
              <List size={16} />
            </button>
            <button
              onClick={() => setViewMode('grid')}
              className={cn('join-item btn btn-sm', viewMode === 'grid' && 'btn-active')}
            >
              <LayoutGrid size={16} />
            </button>
          </div>
        </div>

        {/* Zoom controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowPlayer(!showPlayer)}
            className={cn('btn btn-sm gap-2', showPlayer ? 'btn-secondary' : 'btn-ghost')}
            title="Toggle video player"
          >
            <Film size={16} />
            Player
          </button>
          <div className="divider divider-horizontal mx-1" />
          <button onClick={handleZoomOut} className="btn btn-ghost btn-sm">
            <ZoomOut size={16} />
          </button>
          <span className="text-sm font-mono w-12 text-center">{(zoom * 100).toFixed(0)}%</span>
          <button onClick={handleZoomIn} className="btn btn-ghost btn-sm">
            <ZoomIn size={16} />
          </button>
          <button onClick={handleReset} className="btn btn-ghost btn-sm">
            <Maximize2 size={16} />
          </button>
        </div>
      </div>

      {/* Loading state for props */}
      {propsLoading && (
        <div className="flex items-center justify-center h-32">
          <Spinner />
          <span className="ml-2 text-base-content/60">Loading props...</span>
        </div>
      )}

      {/* Video Player */}
      {showPlayer && props && (
        <div className="mb-4">
          <VideoPlayer
            videoUrl={videoUrl}
            scenes={playerScenes}
            fps={fps}
            currentFrame={currentFrame}
            onFrameChange={handleFrameChange}
            onSceneChange={handleSceneChange}
            className="h-80 w-full"
          />
        </div>
      )}

      {/* Timeline section */}
      {props && (
        <>
          {/* Playback controls */}
          <div className="flex items-center gap-4 bg-base-200 rounded-lg p-3">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentFrame(0)}
                className="btn btn-ghost btn-sm"
              >
                <SkipBack size={16} />
              </button>
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="btn btn-primary btn-sm"
              >
                {isPlaying ? <Pause size={16} /> : <Play size={16} />}
              </button>
              <button
                onClick={() => setCurrentFrame(totalFrames)}
                className="btn btn-ghost btn-sm"
              >
                <SkipForward size={16} />
              </button>
            </div>

            <div className="flex-1 text-center">
              <span className="font-mono text-lg">
                {Math.floor(currentFrame / fps / 60)}:
                {((currentFrame / fps) % 60).toFixed(2).padStart(5, '0')}
              </span>
              <span className="text-base-content/40 text-sm ml-2">
                / {Math.floor(totalFrames / fps / 60)}:
                {((totalFrames / fps) % 60).toFixed(2).padStart(5, '0')}
              </span>
            </div>

            <div className="text-sm text-base-content/60 font-mono">
              Frame {currentFrame} / {totalFrames}
            </div>
          </div>

          {/* Timeline visualization */}
          <div className="overflow-x-auto">
            <TimelineBar
              scenes={scenes}
              totalFrames={totalFrames}
              currentFrame={currentFrame}
              fps={fps}
              zoom={zoom}
              onSeek={handleSeek}
              onSelectScene={setSelectedSceneId}
              selectedSceneId={selectedSceneId}
            />
          </div>

          {/* Two-panel: Scene list + Detail */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
            {/* Scene list/grid */}
            <div className="lg:col-span-2">
              <h3 className="text-sm font-medium mb-3">
                Scenes ({scenes.length})
              </h3>
              {viewMode === 'list' ? (
                <SceneList
                  scenes={scenes}
                  selectedSceneId={selectedSceneId}
                  fps={fps}
                  onSelectScene={setSelectedSceneId}
                  showFrames
                />
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {scenes.map((scene) => (
                    <SceneCard
                      key={scene.id}
                      scene={scene}
                      isSelected={selectedSceneId === scene.id}
                      fps={fps}
                      onClick={() => setSelectedSceneId(scene.id)}
                      compact
                      showFrames
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Scene detail */}
            <div className="bg-base-200 rounded-lg p-4">
              <h3 className="text-sm font-medium mb-3">Scene Details</h3>
              <SceneDetail scene={selectedScene} fps={fps} />
            </div>
          </div>
        </>
      )}

      {/* Empty state */}
      {!props && !propsLoading && selectedScriptId && (
        <EmptyState
          icon={<Film size={48} strokeWidth={1.5} />}
          title="No props generated for this script"
          description="Generate voiceover first to create scene timing data"
        />
      )}
    </div>
  );
}

export default VideoTimeline;
