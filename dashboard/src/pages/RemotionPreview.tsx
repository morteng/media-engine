/**
 * RemotionPreview - Full Remotion integration page for camera animation preview
 *
 * Features:
 * - Real @remotion/player embedding with actual camera animations
 * - Demo recording browser with state selection
 * - Frame-accurate playback controls
 * - Keyframe timeline visualization
 * - Camera effects preview
 */

import { useState, useCallback, useMemo } from 'react';
import { Play, Video, Settings2, Layers } from 'lucide-react';
import { useDemoRecorderData } from '@/hooks/useVideoApi';
import { useDemoToRemotionProps } from '@/hooks/useDemoToRemotionProps';
import {
  RemotionPlayerWrapper,
  DemoStateBrowser,
  PreviewControls,
  KeyframeTimeline,
} from '@/components/remotion-preview';
import type { DemoRecordingState } from '@/api/video';

export function RemotionPreview() {
  // State for demo selection
  const [selectedDemoId, setSelectedDemoId] = useState<string | null>(null);
  const [selectedStateId, setSelectedStateId] = useState<string | null>(null);

  // Playback state
  const [currentFrame, setCurrentFrame] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [seekToFrame, setSeekToFrame] = useState<number | undefined>(undefined);

  // Fetch demo data
  const { demos, demosLoading, demoDetail } = useDemoRecorderData(selectedDemoId);

  // Transform demo data to Remotion props
  const { props: remotionProps, totalFrames, fps } = useDemoToRemotionProps(
    demoDetail,
    selectedStateId
  );

  // Get current state's camera keyframes
  const currentKeyframes = remotionProps?.keyframes || [];

  // Get states for the selected demo
  const states: DemoRecordingState[] = useMemo(() => {
    return demoDetail?.states || [];
  }, [demoDetail]);

  // Handle demo selection
  const handleSelectDemo = useCallback((demoId: string) => {
    setSelectedDemoId(demoId);
    setSelectedStateId(null);
    setCurrentFrame(0);
    setIsPlaying(false);
  }, []);

  // Handle state selection
  const handleSelectState = useCallback((stateId: string) => {
    setSelectedStateId(stateId);
    setCurrentFrame(0);
    setSeekToFrame(0);
    setIsPlaying(false);
  }, []);

  // Handle frame changes
  const handleFrameChange = useCallback((frame: number) => {
    setCurrentFrame(frame);
    setSeekToFrame(frame);
  }, []);

  // Handle play/pause
  const handlePlayPause = useCallback(() => {
    setIsPlaying((prev) => !prev);
  }, []);

  // Handle speed change
  const handleSpeedChange = useCallback((speed: number) => {
    setPlaybackSpeed(speed);
  }, []);

  // Handle player frame updates
  const handlePlayerFrameChange = useCallback((frame: number) => {
    setCurrentFrame(frame);
  }, []);

  // Handle player play state changes
  const handlePlayerPlayChange = useCallback((playing: boolean) => {
    setIsPlaying(playing);
  }, []);

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col">
      <div className="flex-1 flex min-h-0">
        {/* Left Panel - Demo & State Browser */}
        <div className="w-64 border-r border-base-300 flex flex-col bg-base-200">
          <DemoStateBrowser
            demos={demos}
            selectedDemoId={selectedDemoId}
            selectedStateId={selectedStateId}
            states={states}
            onSelectDemo={handleSelectDemo}
            onSelectState={handleSelectState}
            isLoading={demosLoading}
          />
        </div>

        {/* Center - Remotion Player */}
        <div className="flex-1 flex flex-col min-w-0 bg-base-100">
          {/* Player Area */}
          <div className="flex-1 relative flex items-center justify-center p-4 bg-base-300/30">
            {selectedDemoId && remotionProps ? (
              <div className="w-full h-full max-w-full max-h-full" style={{ aspectRatio: `${remotionProps.captureWidth}/${remotionProps.captureHeight}` }}>
                <RemotionPlayerWrapper
                  {...remotionProps}
                  showControls={false}
                  loop
                  playbackRate={playbackSpeed}
                  isPlaying={isPlaying}
                  seekToFrame={seekToFrame}
                  onFrameChange={handlePlayerFrameChange}
                  onPlayChange={handlePlayerPlayChange}
                />
              </div>
            ) : (
              <EmptyState />
            )}
          </div>

          {/* Timeline */}
          {selectedDemoId && remotionProps && (
            <KeyframeTimeline
              keyframes={currentKeyframes}
              currentFrame={currentFrame}
              totalFrames={totalFrames}
              fps={fps}
              onFrameClick={handleFrameChange}
            />
          )}

          {/* Playback Controls */}
          {selectedDemoId && remotionProps && (
            <PreviewControls
              currentFrame={currentFrame}
              totalFrames={totalFrames}
              fps={fps}
              isPlaying={isPlaying}
              playbackSpeed={playbackSpeed}
              onFrameChange={handleFrameChange}
              onPlayPause={handlePlayPause}
              onSpeedChange={handleSpeedChange}
            />
          )}
        </div>

        {/* Right Panel - Info & Stats */}
        <div className="w-72 border-l border-base-300 bg-base-200 flex flex-col">
          <InfoPanel
            demoDetail={demoDetail}
            selectedStateId={selectedStateId}
            currentFrame={currentFrame}
            totalFrames={totalFrames}
            fps={fps}
            keyframes={currentKeyframes}
          />
        </div>
      </div>
    </div>
  );
}

/**
 * Empty state when no demo is selected
 */
function EmptyState() {
  return (
    <div className="text-center text-base-content/50">
      <Video size={64} className="mx-auto mb-4 opacity-30" />
      <h3 className="text-lg font-medium">Remotion Preview</h3>
      <p className="text-sm mt-2 max-w-sm">
        Select a demo recording from the left panel to preview
        real camera animations using @remotion/player
      </p>
      <div className="flex items-center justify-center gap-4 mt-6 text-xs">
        <div className="flex items-center gap-1">
          <Play size={14} />
          Real-time playback
        </div>
        <div className="flex items-center gap-1">
          <Layers size={14} />
          Catmull-Rom splines
        </div>
        <div className="flex items-center gap-1">
          <Settings2 size={14} />
          Visual effects
        </div>
      </div>
    </div>
  );
}

/**
 * Info panel showing demo details and camera state
 */
function InfoPanel({
  demoDetail,
  selectedStateId,
  currentFrame,
  totalFrames,
  fps,
  keyframes,
}: {
  demoDetail: ReturnType<typeof useDemoRecorderData>['demoDetail'];
  selectedStateId: string | null;
  currentFrame: number;
  totalFrames: number;
  fps: number;
  keyframes: { frame: number; centerX: number; centerY: number; zoom: number }[];
}) {
  const currentState = demoDetail?.states.find((s) => s.id === selectedStateId);

  // Calculate current camera values by interpolating keyframes
  const currentCamera = useMemo(() => {
    if (keyframes.length === 0) {
      return { centerX: 960, centerY: 540, zoom: 1 };
    }
    if (keyframes.length === 1) {
      return keyframes[0];
    }

    // Find surrounding keyframes
    let prev = keyframes[0];
    let next = keyframes[keyframes.length - 1];

    for (let i = 0; i < keyframes.length - 1; i++) {
      if (currentFrame >= keyframes[i].frame && currentFrame < keyframes[i + 1].frame) {
        prev = keyframes[i];
        next = keyframes[i + 1];
        break;
      }
    }

    if (prev.frame === next.frame) return prev;

    const t = (currentFrame - prev.frame) / (next.frame - prev.frame);
    return {
      centerX: prev.centerX + (next.centerX - prev.centerX) * t,
      centerY: prev.centerY + (next.centerY - prev.centerY) * t,
      zoom: prev.zoom + (next.zoom - prev.zoom) * t,
    };
  }, [keyframes, currentFrame]);

  return (
    <div className="flex flex-col h-full">
      {/* Demo Info */}
      <div className="p-3 border-b border-base-300">
        <h3 className="text-sm font-semibold text-base-content/70 uppercase tracking-wider">
          Demo Info
        </h3>
        {demoDetail ? (
          <div className="mt-2 space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-base-content/60">Name</span>
              <span className="font-medium truncate ml-2">{demoDetail.name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-base-content/60">States</span>
              <span>{demoDetail.states.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-base-content/60">Viewport</span>
              <span>
                {demoDetail.viewport?.width}x{demoDetail.viewport?.height}
              </span>
            </div>
          </div>
        ) : (
          <p className="text-sm text-base-content/50 mt-2">No demo selected</p>
        )}
      </div>

      {/* Current State */}
      <div className="p-3 border-b border-base-300">
        <h3 className="text-sm font-semibold text-base-content/70 uppercase tracking-wider">
          Current State
        </h3>
        {currentState ? (
          <div className="mt-2 space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-base-content/60">ID</span>
              <span className="font-mono text-xs">{currentState.id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-base-content/60">Duration</span>
              <span>{currentState.duration || 2}s</span>
            </div>
            <div className="flex justify-between">
              <span className="text-base-content/60">Preset</span>
              <span>{currentState.camera?.preset || 'static'}</span>
            </div>
          </div>
        ) : (
          <p className="text-sm text-base-content/50 mt-2">No state selected</p>
        )}
      </div>

      {/* Camera State */}
      <div className="p-3 border-b border-base-300">
        <h3 className="text-sm font-semibold text-base-content/70 uppercase tracking-wider">
          Camera
        </h3>
        <div className="mt-2 space-y-1 text-sm">
          <div className="flex justify-between">
            <span className="text-base-content/60">Zoom</span>
            <span className="font-mono">{currentCamera.zoom.toFixed(3)}x</span>
          </div>
          <div className="flex justify-between">
            <span className="text-base-content/60">Center X</span>
            <span className="font-mono">{Math.round(currentCamera.centerX)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-base-content/60">Center Y</span>
            <span className="font-mono">{Math.round(currentCamera.centerY)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-base-content/60">Keyframes</span>
            <span>{keyframes.length}</span>
          </div>
        </div>
      </div>

      {/* Playback Stats */}
      <div className="p-3 flex-1">
        <h3 className="text-sm font-semibold text-base-content/70 uppercase tracking-wider">
          Playback
        </h3>
        <div className="mt-2 space-y-1 text-sm">
          <div className="flex justify-between">
            <span className="text-base-content/60">Frame</span>
            <span className="font-mono">
              {currentFrame}/{totalFrames}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-base-content/60">Time</span>
            <span className="font-mono">
              {(currentFrame / fps).toFixed(2)}s / {(totalFrames / fps).toFixed(2)}s
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-base-content/60">FPS</span>
            <span>{fps}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default RemotionPreview;
