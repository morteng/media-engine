/**
 * DemoRecorder - Standalone page for demo recording preview and configuration
 *
 * Features:
 * - Demo recording browser (YAML definitions in content/{lang}/demos/)
 * - Camera path visualizer on canvas
 * - Keyframe timeline with playback controls
 * - Camera and effects configuration panels
 */

import { useState, useMemo } from 'react';
import { Video } from 'lucide-react';
import { useDemoRecorderData } from '@/hooks/useVideoApi';
import {
  DemoScriptBrowser,
  CameraPathPreview,
  KeyframeTimeline,
  PlaybackControls,
  CameraConfigPanel,
  EffectsPanel,
} from '@/components/demo-recorder';
import type { DemoScene } from '@/components/demo-recorder/types';

export function DemoRecorder() {
  const [selectedDemoId, setSelectedDemoId] = useState<string | null>(null);
  const [selectedStateIndex, setSelectedStateIndex] = useState<number>(0);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);

  // Fetch demo recordings
  const { demos, demosLoading, demoDetail } = useDemoRecorderData(selectedDemoId);

  // Convert demo states to scenes for the timeline/preview
  const scenes: DemoScene[] = useMemo(() => {
    if (!demoDetail?.states) return [];

    const fps = 30; // Default fps for demo recordings
    let frameOffset = 0;

    return demoDetail.states.map((state) => {
      const durationSecs = state.duration || 2; // Default 2 seconds
      const durationFrames = Math.floor(durationSecs * fps);
      const startFrame = frameOffset;
      frameOffset += durationFrames;

      return {
        id: state.id,
        type: 'demo',
        name: state.description || state.id,
        duration: durationSecs,
        startFrame,
        endFrame: startFrame + durationFrames,
        durationFrames,
        cameraData: state.camera ? {
          mode: state.camera.preset || 'static',
          capture_scale: 2,
          background: '#1a1a2e',
          shadow: true,
          viewport_width: demoDetail.viewport?.width || 1920,
          viewport_height: demoDetail.viewport?.height || 1080,
          fps,
          total_frames: durationFrames,
          keyframes: state.camera.keyframes || [],
          element_bounds: {},
        } : undefined,
      };
    });
  }, [demoDetail]);

  const currentScene = scenes[selectedStateIndex];
  const totalFrames = scenes.reduce((sum, s) => sum + (s.durationFrames || 0), 0);
  const fps = 30;

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col">
      {/* Main Content */}
      <div className="flex-1 flex min-h-0">
        {/* Left Panel - Demo Browser */}
        <div className="w-64 border-r border-base-300 flex flex-col">
          <DemoScriptBrowser
            demos={demos}
            selectedDemoId={selectedDemoId}
            onSelectDemo={setSelectedDemoId}
            isLoading={demosLoading}
          />
        </div>

        {/* Center - Camera Path Preview */}
        <div className="flex-1 flex flex-col min-w-0">
          <div className="flex-1 p-4 bg-base-100">
            {selectedDemoId && currentScene ? (
              <CameraPathPreview
                scene={currentScene}
                propsData={demoDetail}
                currentFrame={currentFrame}
                isPlaying={isPlaying}
              />
            ) : (
              <div className="h-full flex items-center justify-center text-base-content/50">
                <div className="text-center">
                  <Video size={48} className="mx-auto mb-4 opacity-50" />
                  <p className="text-lg font-medium">Select a demo to preview</p>
                  <p className="text-sm mt-1">
                    Choose a demo recording from the left panel
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Timeline */}
          <div className="border-t border-base-300 bg-base-200">
            <KeyframeTimeline
              scenes={scenes}
              selectedSceneIndex={selectedStateIndex}
              onSelectScene={setSelectedStateIndex}
              currentFrame={currentFrame}
              totalFrames={totalFrames}
              fps={fps}
            />
            <PlaybackControls
              currentFrame={currentFrame}
              totalFrames={totalFrames}
              fps={fps}
              isPlaying={isPlaying}
              playbackSpeed={playbackSpeed}
              onFrameChange={setCurrentFrame}
              onPlayPause={() => setIsPlaying(!isPlaying)}
              onSpeedChange={setPlaybackSpeed}
            />
          </div>
        </div>

        {/* Right Panel - Config */}
        <div className="w-80 border-l border-base-300 bg-base-200 flex flex-col">
          {/* Camera Config Panel */}
          <div className="flex-1 min-h-0 overflow-hidden border-b border-base-300">
            <CameraConfigPanel scene={currentScene || null} />
          </div>

          {/* Effects Panel */}
          <div className="h-[45%] overflow-y-auto p-3">
            <EffectsPanel scene={currentScene || null} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default DemoRecorder;
