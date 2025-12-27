/**
 * Scene Navigator Component
 *
 * Visual timeline with scene markers for video navigation.
 */

import { useState } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  Clock,
  Layers,
} from 'lucide-react';
import clsx from 'clsx';

interface Scene {
  id: string;
  type: string;
  title?: string;
  duration: number;
  startFrame: number;
  endFrame: number;
  background?: string;
  transition_in?: string;
}

interface SceneNavigatorProps {
  scenes: Scene[];
  currentFrame: number;
  fps: number;
  onSeek?: (frame: number) => void;
  onSceneSelect?: (sceneId: string) => void;
  className?: string;
}

const SCENE_TYPE_COLORS: Record<string, string> = {
  intro: 'bg-primary',
  feature: 'bg-secondary',
  demo: 'bg-accent',
  split: 'bg-info',
  outro: 'bg-success',
  default: 'bg-base-content/30',
};

export function SceneNavigator({
  scenes,
  currentFrame,
  fps,
  onSeek,
  onSceneSelect,
  className,
}: SceneNavigatorProps) {
  const [hoveredScene, setHoveredScene] = useState<string | null>(null);

  // Calculate total duration
  const totalFrames = scenes.reduce((max, s) => Math.max(max, s.endFrame), 0);
  const totalDuration = totalFrames / fps;

  // Find current scene
  const currentScene = scenes.find(
    (s) => currentFrame >= s.startFrame && currentFrame < s.endFrame
  );

  // Format time
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleTimelineClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!onSeek) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percent = x / rect.width;
    const frame = Math.floor(percent * totalFrames);
    onSeek(frame);
  };

  const goToScene = (direction: 'prev' | 'next') => {
    const currentIndex = scenes.findIndex((s) => s.id === currentScene?.id);
    if (direction === 'prev' && currentIndex > 0) {
      const prevScene = scenes[currentIndex - 1];
      onSeek?.(prevScene.startFrame);
      onSceneSelect?.(prevScene.id);
    } else if (direction === 'next' && currentIndex < scenes.length - 1) {
      const nextScene = scenes[currentIndex + 1];
      onSeek?.(nextScene.startFrame);
      onSceneSelect?.(nextScene.id);
    }
  };

  return (
    <div className={clsx('space-y-4', className)}>
      {/* Timeline Header */}
      <div className="flex items-center gap-4">
        <h4 className="font-semibold flex items-center gap-2">
          <Layers size={16} className="text-primary" />
          Scenes
          <span className="badge badge-ghost badge-sm">{scenes.length}</span>
        </h4>
        <div className="flex-1" />
        <span className="text-sm text-base-content/60 flex items-center gap-1">
          <Clock size={14} />
          {formatTime(totalDuration)}
        </span>
      </div>

      {/* Navigation Controls */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => goToScene('prev')}
          disabled={!currentScene || scenes.indexOf(currentScene) === 0}
          className="btn btn-ghost btn-sm btn-square"
        >
          <ChevronLeft size={16} />
        </button>

        <div className="flex-1 text-center">
          {currentScene ? (
            <span className="text-sm">
              <span className="font-medium">{currentScene.title || currentScene.type}</span>
              <span className="text-base-content/60 ml-2">
                ({formatTime(currentFrame / fps)})
              </span>
            </span>
          ) : (
            <span className="text-sm text-base-content/60">No scene selected</span>
          )}
        </div>

        <button
          onClick={() => goToScene('next')}
          disabled={!currentScene || scenes.indexOf(currentScene) === scenes.length - 1}
          className="btn btn-ghost btn-sm btn-square"
        >
          <ChevronRight size={16} />
        </button>
      </div>

      {/* Timeline */}
      <div
        className="h-12 bg-base-300 rounded-lg overflow-hidden cursor-pointer relative"
        onClick={handleTimelineClick}
      >
        {/* Scene Blocks */}
        {scenes.map((scene) => {
          const left = (scene.startFrame / totalFrames) * 100;
          const width = ((scene.endFrame - scene.startFrame) / totalFrames) * 100;
          const isActive = scene.id === currentScene?.id;
          const isHovered = scene.id === hoveredScene;

          return (
            <div
              key={scene.id}
              className={clsx(
                'absolute top-0 h-full transition-all',
                SCENE_TYPE_COLORS[scene.type] || SCENE_TYPE_COLORS.default,
                {
                  'ring-2 ring-white ring-offset-2 ring-offset-base-300': isActive,
                  'opacity-80': !isActive && !isHovered,
                  'brightness-110': isHovered,
                }
              )}
              style={{ left: `${left}%`, width: `${width}%` }}
              onMouseEnter={() => setHoveredScene(scene.id)}
              onMouseLeave={() => setHoveredScene(null)}
              onClick={(e) => {
                e.stopPropagation();
                onSeek?.(scene.startFrame);
                onSceneSelect?.(scene.id);
              }}
            >
              {/* Scene Label (if wide enough) */}
              {width > 10 && (
                <div className="absolute inset-0 flex items-center justify-center text-xs text-white font-medium truncate px-1">
                  {scene.title || scene.type}
                </div>
              )}
            </div>
          );
        })}

        {/* Playhead */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-white shadow-lg z-10"
          style={{ left: `${(currentFrame / totalFrames) * 100}%` }}
        >
          <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-3 h-3 bg-white rounded-full shadow" />
        </div>
      </div>

      {/* Scene List */}
      <div className="space-y-1 max-h-48 overflow-y-auto">
        {scenes.map((scene, index) => {
          const isActive = scene.id === currentScene?.id;
          return (
            <button
              key={scene.id}
              onClick={() => {
                onSeek?.(scene.startFrame);
                onSceneSelect?.(scene.id);
              }}
              className={clsx(
                'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left text-sm transition-colors',
                {
                  'bg-primary/20 text-primary': isActive,
                  'hover:bg-base-300': !isActive,
                }
              )}
            >
              <span className="text-base-content/40 w-6">{index + 1}</span>
              <div
                className={clsx(
                  'w-2 h-2 rounded-full',
                  SCENE_TYPE_COLORS[scene.type] || SCENE_TYPE_COLORS.default
                )}
              />
              <div className="flex-1 min-w-0">
                <div className="font-medium truncate">{scene.title || scene.type}</div>
                {scene.transition_in && (
                  <div className="text-xs text-base-content/50">{scene.transition_in}</div>
                )}
              </div>
              <span className="text-base-content/40 text-xs">{formatTime(scene.duration)}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default SceneNavigator;
