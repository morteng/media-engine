/**
 * KeyframeTimeline - Visual timeline showing keyframe positions
 */

import { useRef, useEffect, useState } from 'react';
import clsx from 'clsx';
import type { DemoScene } from './types';

interface KeyframeTimelineProps {
  scenes: DemoScene[];
  selectedSceneIndex: number;
  onSelectScene: (index: number) => void;
  currentFrame: number;
  totalFrames: number;
  fps: number;
}

// Scene type colors
const SCENE_COLORS: Record<string, string> = {
  intro: 'bg-cyan-500',
  feature: 'bg-purple-500',
  demo: 'bg-green-500',
  split: 'bg-blue-500',
  outro: 'bg-orange-500',
  default: 'bg-gray-500',
};

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  const ms = Math.floor((seconds % 1) * 100);
  return `${mins}:${String(secs).padStart(2, '0')}.${String(ms).padStart(2, '0')}`;
}

export function KeyframeTimeline({
  scenes,
  selectedSceneIndex,
  onSelectScene,
  currentFrame,
  totalFrames,
  fps,
}: KeyframeTimelineProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [_timelineWidth, setTimelineWidth] = useState(800);

  useEffect(() => {
    const updateWidth = () => {
      if (containerRef.current) {
        setTimelineWidth(containerRef.current.offsetWidth - 32);
      }
    };
    updateWidth();
    window.addEventListener('resize', updateWidth);
    return () => window.removeEventListener('resize', updateWidth);
  }, []);

  const totalDuration = totalFrames / fps;
  // Reserved for future use: const currentTime = currentFrame / fps;

  // Generate time markers
  const markerInterval = totalDuration > 60 ? 10 : totalDuration > 30 ? 5 : 2;
  const markers = [];
  for (let t = 0; t <= totalDuration; t += markerInterval) {
    markers.push(t);
  }

  return (
    <div ref={containerRef} className="px-4 py-3">
      {/* Time markers */}
      <div className="relative h-4 mb-1">
        {markers.map((time) => (
          <div
            key={time}
            className="absolute text-xs text-base-content/50"
            style={{ left: `${(time / totalDuration) * 100}%`, transform: 'translateX(-50%)' }}
          >
            {formatTime(time)}
          </div>
        ))}
      </div>

      {/* Timeline track */}
      <div className="relative h-12 bg-base-300 rounded-lg overflow-hidden">
        {/* Scene blocks */}
        {scenes.map((scene, index) => {
          const startPercent = scene.startFrame
            ? (scene.startFrame / totalFrames) * 100
            : (index / scenes.length) * 100;
          const widthPercent = scene.durationFrames
            ? (scene.durationFrames / totalFrames) * 100
            : (1 / scenes.length) * 100;

          const colorClass = SCENE_COLORS[scene.type] || SCENE_COLORS.default;

          return (
            <button
              key={scene.id}
              onClick={() => onSelectScene(index)}
              className={clsx(
                'absolute h-full transition-all duration-150',
                'hover:brightness-110 focus:outline-none focus:ring-2 focus:ring-primary/50',
                colorClass,
                {
                  'ring-2 ring-white/50 z-10': selectedSceneIndex === index,
                  'opacity-70': selectedSceneIndex !== index,
                }
              )}
              style={{
                left: `${startPercent}%`,
                width: `${widthPercent}%`,
              }}
              title={`${scene.name || scene.id} (${scene.type})`}
            >
              <div className="h-full flex items-center justify-center px-2 overflow-hidden">
                <span className="text-xs font-medium text-white truncate">
                  {scene.name || scene.id}
                </span>
              </div>
            </button>
          );
        })}

        {/* Playhead */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-white shadow-lg z-20 pointer-events-none"
          style={{ left: `${(currentFrame / totalFrames) * 100}%` }}
        >
          <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-3 h-3 bg-white rounded-full shadow" />
        </div>

        {/* Keyframe markers (diamonds) */}
        {scenes.map((scene) => {
          const cameraData = (scene as any).cameraData;
          if (!cameraData?.keyframes) return null;

          return cameraData.keyframes.map((kf: any, kfIndex: number) => {
            const percent = (kf.frame / totalFrames) * 100;
            return (
              <div
                key={`${scene.id}-kf-${kfIndex}`}
                className="absolute top-1/2 -translate-y-1/2 w-2 h-2 bg-white rotate-45 z-15 pointer-events-none"
                style={{ left: `${percent}%`, marginLeft: '-4px' }}
                title={`Keyframe ${kfIndex + 1}: ${kf.zoom}x zoom`}
              />
            );
          });
        })}
      </div>

      {/* Scene legend */}
      <div className="flex items-center gap-4 mt-2 text-xs text-base-content/60">
        {Object.entries(SCENE_COLORS)
          .filter(([key]) => key !== 'default')
          .map(([type, colorClass]) => (
            <span key={type} className="flex items-center gap-1">
              <span className={clsx('w-2 h-2 rounded-sm', colorClass)} />
              {type}
            </span>
          ))}
      </div>
    </div>
  );
}
