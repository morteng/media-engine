/**
 * PlaybackControls - Play/pause, scrub, speed controls
 */

import { useEffect, useRef, useCallback } from 'react';
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Rewind,
  FastForward,
} from 'lucide-react';
import clsx from 'clsx';

interface PlaybackControlsProps {
  currentFrame: number;
  totalFrames: number;
  fps: number;
  isPlaying: boolean;
  playbackSpeed: number;
  onFrameChange: (frame: number) => void;
  onPlayPause: () => void;
  onSpeedChange: (speed: number) => void;
}

const SPEED_OPTIONS = [0.25, 0.5, 1, 2];

function formatTimecode(frame: number, fps: number): string {
  const totalSeconds = frame / fps;
  const mins = Math.floor(totalSeconds / 60);
  const secs = Math.floor(totalSeconds % 60);
  const frames = Math.floor(frame % fps);
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}:${String(frames).padStart(2, '0')}`;
}

export function PlaybackControls({
  currentFrame,
  totalFrames,
  fps,
  isPlaying,
  playbackSpeed,
  onFrameChange,
  onPlayPause,
  onSpeedChange,
}: PlaybackControlsProps) {
  const animationRef = useRef<number | null>(null);
  const lastTimeRef = useRef<number>(0);

  // Handle playback animation
  useEffect(() => {
    if (isPlaying) {
      lastTimeRef.current = performance.now();

      const animate = (time: number) => {
        const deltaTime = time - lastTimeRef.current;
        lastTimeRef.current = time;

        // Calculate frames to advance based on speed
        const framesToAdvance = (deltaTime / 1000) * fps * playbackSpeed;
        const newFrame = currentFrame + framesToAdvance;

        if (newFrame >= totalFrames) {
          onFrameChange(0); // Loop back to start
        } else {
          onFrameChange(Math.floor(newFrame));
        }

        animationRef.current = requestAnimationFrame(animate);
      };

      animationRef.current = requestAnimationFrame(animate);
    } else {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isPlaying, playbackSpeed, fps, currentFrame, totalFrames, onFrameChange]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      switch (e.key) {
        case ' ':
          e.preventDefault();
          onPlayPause();
          break;
        case 'ArrowLeft':
          e.preventDefault();
          onFrameChange(Math.max(0, currentFrame - (e.shiftKey ? fps : 1)));
          break;
        case 'ArrowRight':
          e.preventDefault();
          onFrameChange(Math.min(totalFrames - 1, currentFrame + (e.shiftKey ? fps : 1)));
          break;
        case 'Home':
          e.preventDefault();
          onFrameChange(0);
          break;
        case 'End':
          e.preventDefault();
          onFrameChange(totalFrames - 1);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentFrame, totalFrames, fps, onFrameChange, onPlayPause]);

  const handleSliderChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onFrameChange(parseInt(e.target.value, 10));
    },
    [onFrameChange]
  );

  return (
    <div className="flex items-center gap-4 px-4 py-2 border-t border-base-300">
      {/* Transport controls */}
      <div className="flex items-center gap-1">
        <button
          className="btn btn-sm btn-ghost btn-square"
          onClick={() => onFrameChange(0)}
          title="Go to start (Home)"
        >
          <SkipBack size={16} />
        </button>
        <button
          className="btn btn-sm btn-ghost btn-square"
          onClick={() => onFrameChange(Math.max(0, currentFrame - fps))}
          title="Back 1 second (Shift+Left)"
        >
          <Rewind size={16} />
        </button>
        <button
          className={clsx('btn btn-sm btn-square', {
            'btn-primary': isPlaying,
            'btn-ghost': !isPlaying,
          })}
          onClick={onPlayPause}
          title={isPlaying ? 'Pause (Space)' : 'Play (Space)'}
        >
          {isPlaying ? <Pause size={16} /> : <Play size={16} />}
        </button>
        <button
          className="btn btn-sm btn-ghost btn-square"
          onClick={() => onFrameChange(Math.min(totalFrames - 1, currentFrame + fps))}
          title="Forward 1 second (Shift+Right)"
        >
          <FastForward size={16} />
        </button>
        <button
          className="btn btn-sm btn-ghost btn-square"
          onClick={() => onFrameChange(totalFrames - 1)}
          title="Go to end (End)"
        >
          <SkipForward size={16} />
        </button>
      </div>

      {/* Scrubber */}
      <div className="flex-1 flex items-center gap-3">
        <input
          type="range"
          min={0}
          max={totalFrames - 1}
          value={currentFrame}
          onChange={handleSliderChange}
          className="range range-xs range-primary flex-1"
        />
      </div>

      {/* Timecode display */}
      <div className="font-mono text-sm tabular-nums text-base-content/70 min-w-[140px] text-right">
        <span className="text-base-content">{formatTimecode(currentFrame, fps)}</span>
        <span className="text-base-content/40"> / </span>
        <span>{formatTimecode(totalFrames, fps)}</span>
      </div>

      {/* Speed selector */}
      <div className="flex items-center gap-1">
        {SPEED_OPTIONS.map((speed) => (
          <button
            key={speed}
            className={clsx('btn btn-xs', {
              'btn-primary': playbackSpeed === speed,
              'btn-ghost': playbackSpeed !== speed,
            })}
            onClick={() => onSpeedChange(speed)}
            title={`${speed}x speed`}
          >
            {speed}x
          </button>
        ))}
      </div>

      {/* Frame counter */}
      <div className="text-xs text-base-content/50">
        Frame {currentFrame} / {totalFrames}
      </div>
    </div>
  );
}
