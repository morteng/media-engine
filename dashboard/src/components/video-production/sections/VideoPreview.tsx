/**
 * VideoPreview - Preview tab for video production
 * Provides video player and Remotion studio preview
 */

import { useState, useMemo } from 'react';
import { Film, Play, Monitor } from 'lucide-react';
import clsx from 'clsx';
import { useVideoScripts, useVideoScript } from '@/hooks/useVideoApi';
import {
  RemotionPreview,
  SceneNavigator,
  SceneDetailPanel,
  VideoPlayer,
} from '@/components/video-production';
import type { VideoScriptItem } from '@/api/types';

interface TransformedScene {
  id: string;
  type: string;
  title: string;
  text?: string;
  voiceover?: string;
  duration: number;
  startFrame: number;
  endFrame: number;
  background?: string;
  transition_in?: string;
  transition_out?: string;
  text_effect?: string;
  visual?: any;
}

/**
 * Hook to transform raw scenes with frame calculations
 */
function useSceneTransform(rawScenes: any[], fps: number): TransformedScene[] {
  return useMemo(() => {
    let frameOffset = 0;
    return rawScenes.map((scene: any, index: number) => {
      const duration = scene.duration || 5;
      const durationFrames = duration * fps;
      const startFrame = frameOffset;
      const endFrame = startFrame + durationFrames;
      frameOffset = endFrame;

      return {
        id: scene.id || `scene-${index}`,
        type: scene.type || 'default',
        title: scene.title || scene.name,
        text: scene.text,
        voiceover: scene.voiceover,
        duration,
        startFrame,
        endFrame,
        background: scene.background || scene.visual?.background,
        transition_in: scene.transition_in || scene.visual?.transition_in,
        transition_out: scene.transition_out || scene.visual?.transition_out,
        text_effect: scene.text_effect || scene.visual?.text_effect,
        visual: scene.visual,
      };
    });
  }, [rawScenes, fps]);
}

export function VideoPreview() {
  const [selectedScript, setSelectedScript] = useState<string | null>(null);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [selectedSceneId, setSelectedSceneId] = useState<string | null>(null);
  const [previewMode, setPreviewMode] = useState<'video' | 'studio'>('video');

  const { data: scriptsData } = useVideoScripts();
  const { data: scriptDetail } = useVideoScript(selectedScript);

  const scripts: VideoScriptItem[] = scriptsData?.scripts || [];
  const rawScenes = scriptDetail?.parsed?.scenes || [];
  const fps = scriptDetail?.parsed?.settings?.fps || 30;

  // Transform scenes with frame calculations
  const transformedScenes = useSceneTransform(rawScenes, fps);

  // Check if video exists for selected script
  const selectedScriptData = scripts.find((s) => s.id === selectedScript);
  const hasVideo = selectedScriptData?.has_output;

  // Build video URL (path: output/{lang}/videos/{name}.mp4)
  const videoUrl = hasVideo && selectedScript
    ? `/api/video/file/output/${selectedScript.split('/')[0]}/videos/${selectedScript.split('/').pop()}.mp4`
    : null;

  // Find current scene based on frame position
  const currentScene = transformedScenes.find(
    (s) => currentFrame >= s.startFrame && currentFrame < s.endFrame
  ) || null;

  // Use selected scene if explicitly selected, otherwise use current scene from playhead
  const activeScene = selectedSceneId
    ? transformedScenes.find((s) => s.id === selectedSceneId) || currentScene
    : currentScene;

  const handleSceneSelect = (sceneId: string) => {
    setSelectedSceneId(sceneId);
    const scene = transformedScenes.find((s) => s.id === sceneId);
    if (scene) setCurrentFrame(scene.startFrame);
  };

  const handleSeek = (frame: number) => {
    setCurrentFrame(frame);
    // Clear explicit selection when seeking via timeline
    setSelectedSceneId(null);
  };

  const handleFrameChange = (frame: number) => {
    setCurrentFrame(frame);
    // Find which scene this frame belongs to and update selection
    const scene = transformedScenes.find(
      (s) => frame >= s.startFrame && frame < s.endFrame
    );
    if (scene) {
      setSelectedSceneId(scene.id);
    }
  };

  return (
    <div className="grid grid-cols-1 xl:grid-cols-4 gap-4 h-[calc(100vh-240px)]">
      {/* Left: Script & Scene Navigator */}
      <div className="space-y-4 overflow-y-auto">
        {/* Script Selection */}
        <div className="card bg-base-200">
          <div className="card-body p-4">
            <h3 className="font-semibold flex items-center gap-2 mb-3">
              <Film size={16} />
              Script
            </h3>
            <select
              className="select select-bordered select-sm w-full"
              value={selectedScript || ''}
              onChange={(e) => {
                setSelectedScript(e.target.value || null);
                setCurrentFrame(0);
                setSelectedSceneId(null);
              }}
            >
              <option value="">Choose a script...</option>
              {scripts.map((script) => (
                <option key={script.id} value={script.id}>
                  {script.name} {script.has_output ? '(rendered)' : ''}
                </option>
              ))}
            </select>
            {selectedScript && !hasVideo && (
              <p className="text-xs text-warning mt-2">
                No rendered video. Go to Render tab to create one.
              </p>
            )}
          </div>
        </div>

        {/* Scene Navigator */}
        {selectedScript && transformedScenes.length > 0 && (
          <div className="card bg-base-200">
            <div className="card-body p-4">
              <SceneNavigator
                scenes={transformedScenes}
                currentFrame={currentFrame}
                fps={fps}
                onSeek={handleSeek}
                onSceneSelect={handleSceneSelect}
              />
            </div>
          </div>
        )}
      </div>

      {/* Center: Preview Player */}
      <div className="xl:col-span-2 flex flex-col">
        {/* Preview Mode Toggle */}
        <div className="flex items-center gap-2 mb-2">
          <div className="tabs tabs-boxed tabs-sm bg-base-200">
            <button
              className={clsx('tab', previewMode === 'video' && 'tab-active')}
              onClick={() => setPreviewMode('video')}
            >
              <Play size={14} className="mr-1" />
              Video
            </button>
            <button
              className={clsx('tab', previewMode === 'studio' && 'tab-active')}
              onClick={() => setPreviewMode('studio')}
            >
              <Monitor size={14} className="mr-1" />
              Studio
            </button>
          </div>
          <span className="text-xs text-base-content/50">
            {previewMode === 'video' ? 'Play rendered video' : 'Live Remotion Studio'}
          </span>
        </div>

        {/* Player Area */}
        {previewMode === 'video' ? (
          <VideoPlayer
            videoUrl={videoUrl}
            scenes={transformedScenes}
            fps={fps}
            currentFrame={currentFrame}
            onFrameChange={handleFrameChange}
            onSceneChange={handleSceneSelect}
            className="flex-1 min-h-[400px]"
          />
        ) : (
          <RemotionPreview
            scriptId={selectedScript || undefined}
            className="flex-1 min-h-[400px] card bg-base-200"
          />
        )}
      </div>

      {/* Right: Scene Details */}
      <div className="overflow-y-auto">
        <SceneDetailPanel
          scene={activeScene}
          scriptPath={selectedScript}
          className="h-full"
          onNoteChange={(sceneId, note) => {
            console.log('Note updated:', sceneId, note);
          }}
          onSubmitToAI={(sceneId, operation, instructions) => {
            console.log('Submitted to AI:', sceneId, operation, instructions);
          }}
        />
      </div>
    </div>
  );
}
