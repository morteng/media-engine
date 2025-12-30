/**
 * KeyframeTimeline - Visual timeline showing keyframes and current position
 */

import { useMemo } from 'react';
import clsx from 'clsx';
import type { CameraKeyframe } from './types';

interface KeyframeTimelineProps {
  keyframes: CameraKeyframe[];
  currentFrame: number;
  totalFrames: number;
  fps: number;
  onFrameClick: (frame: number) => void;
  onKeyframeClick?: (keyframe: CameraKeyframe) => void;
  height?: number;
}

export function KeyframeTimeline({
  keyframes,
  currentFrame,
  totalFrames,
  fps,
  onFrameClick,
  onKeyframeClick,
  height = 48,
}: KeyframeTimelineProps) {
  // Calculate time markers
  const timeMarkers = useMemo(() => {
    const markers: { frame: number; label: string }[] = [];
    const totalSeconds = totalFrames / fps;
    const interval = totalSeconds <= 5 ? 1 : totalSeconds <= 20 ? 5 : 10;

    for (let sec = 0; sec <= totalSeconds; sec += interval) {
      markers.push({
        frame: sec * fps,
        label: `${sec}s`,
      });
    }
    return markers;
  }, [totalFrames, fps]);

  // Handle click on timeline
  const handleTimelineClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = x / rect.width;
    const frame = Math.round(percentage * (totalFrames - 1));
    onFrameClick(Math.max(0, Math.min(totalFrames - 1, frame)));
  };

  // Calculate position percentage
  const getPosition = (frame: number) => {
    return totalFrames > 1 ? (frame / (totalFrames - 1)) * 100 : 0;
  };

  const playheadPosition = getPosition(currentFrame);

  return (
    <div className="bg-base-200 border-t border-base-300 px-3 py-2">
      {/* Timeline Container */}
      <div
        className="relative bg-base-300 rounded cursor-pointer"
        style={{ height }}
        onClick={handleTimelineClick}
      >
        {/* Time Markers */}
        {timeMarkers.map((marker) => (
          <div
            key={marker.frame}
            className="absolute top-0 h-full border-l border-base-content/10"
            style={{ left: `${getPosition(marker.frame)}%` }}
          >
            <span className="absolute -top-5 text-[10px] text-base-content/40 -translate-x-1/2">
              {marker.label}
            </span>
          </div>
        ))}

        {/* Keyframe Markers */}
        {keyframes.map((kf, index) => {
          const position = getPosition(kf.frame);
          const isActive = currentFrame >= kf.frame &&
            (index === keyframes.length - 1 || currentFrame < keyframes[index + 1].frame);

          return (
            <button
              key={kf.frame}
              className={clsx(
                'absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full border-2',
                'hover:scale-125 transition-transform',
                isActive
                  ? 'bg-primary border-primary-focus'
                  : 'bg-base-100 border-base-content/30 hover:border-primary'
              )}
              style={{ left: `${position}%`, marginLeft: -6 }}
              onClick={(e) => {
                e.stopPropagation();
                onFrameClick(kf.frame);
                onKeyframeClick?.(kf);
              }}
              title={`Frame ${kf.frame} - Zoom: ${kf.zoom.toFixed(2)}x`}
            />
          );
        })}

        {/* Zoom Visualization */}
        <div className="absolute inset-x-0 bottom-0 h-1/3">
          <svg
            className="w-full h-full"
            preserveAspectRatio="none"
            viewBox={`0 0 ${totalFrames} 100`}
          >
            <path
              d={generateZoomPath(keyframes, totalFrames)}
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              className="text-primary/30"
            />
          </svg>
        </div>

        {/* Playhead */}
        <div
          className="absolute top-0 h-full w-0.5 bg-primary shadow-lg"
          style={{
            left: `${playheadPosition}%`,
            transform: 'translateX(-50%)',
          }}
        >
          <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-primary rotate-45" />
        </div>
      </div>

      {/* Keyframe Info */}
      {keyframes.length > 0 && (
        <div className="flex justify-between mt-2 text-[10px] text-base-content/50">
          <span>{keyframes.length} keyframes</span>
          <span>
            Current zoom: {getCurrentZoom(keyframes, currentFrame).toFixed(2)}x
          </span>
        </div>
      )}
    </div>
  );
}

/**
 * Generate SVG path for zoom visualization
 */
function generateZoomPath(keyframes: CameraKeyframe[], totalFrames: number): string {
  if (keyframes.length === 0) {
    return `M 0 50 L ${totalFrames} 50`;
  }

  const points: string[] = [];
  const minZoom = Math.min(...keyframes.map((k) => k.zoom), 0.5);
  const maxZoom = Math.max(...keyframes.map((k) => k.zoom), 2);
  const range = maxZoom - minZoom || 1;

  // Start point
  const firstY = 100 - ((keyframes[0].zoom - minZoom) / range) * 100;
  points.push(`M 0 ${firstY}`);

  // Add keyframe points
  keyframes.forEach((kf) => {
    const y = 100 - ((kf.zoom - minZoom) / range) * 100;
    points.push(`L ${kf.frame} ${y}`);
  });

  // End point
  const lastKf = keyframes[keyframes.length - 1];
  const lastY = 100 - ((lastKf.zoom - minZoom) / range) * 100;
  points.push(`L ${totalFrames} ${lastY}`);

  return points.join(' ');
}

/**
 * Get current zoom level based on frame
 */
function getCurrentZoom(keyframes: CameraKeyframe[], frame: number): number {
  if (keyframes.length === 0) return 1;
  if (keyframes.length === 1) return keyframes[0].zoom;

  // Find surrounding keyframes
  let prev = keyframes[0];
  let next = keyframes[0];

  for (let i = 0; i < keyframes.length - 1; i++) {
    if (frame >= keyframes[i].frame && frame < keyframes[i + 1].frame) {
      prev = keyframes[i];
      next = keyframes[i + 1];
      break;
    }
    if (i === keyframes.length - 2) {
      prev = keyframes[i + 1];
      next = keyframes[i + 1];
    }
  }

  if (prev === next) return prev.zoom;

  // Linear interpolation
  const t = (frame - prev.frame) / (next.frame - prev.frame);
  return prev.zoom + (next.zoom - prev.zoom) * t;
}

export default KeyframeTimeline;
