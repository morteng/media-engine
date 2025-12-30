/**
 * PreviewControls - Playback controls for the Remotion preview
 */

import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Rewind,
  FastForward,
} from 'lucide-react';
import clsx from 'clsx';
import type { PlayerControlsProps } from './types';

const SPEED_OPTIONS = [0.25, 0.5, 1, 1.5, 2];

export function PreviewControls({
  currentFrame,
  totalFrames,
  fps,
  isPlaying,
  playbackSpeed,
  onFrameChange,
  onPlayPause,
  onSpeedChange,
  onStepBackward,
  onStepForward,
  onJumpToStart,
  onJumpToEnd,
}: PlayerControlsProps) {
  const currentTime = currentFrame / fps;
  const totalTime = totalFrames / fps;

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 100);
    return `${mins}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(2, '0')}`;
  };

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFrameChange(parseInt(e.target.value, 10));
  };

  const handleStepBackward = () => {
    if (onStepBackward) {
      onStepBackward();
    } else {
      onFrameChange(Math.max(0, currentFrame - 1));
    }
  };

  const handleStepForward = () => {
    if (onStepForward) {
      onStepForward();
    } else {
      onFrameChange(Math.min(totalFrames - 1, currentFrame + 1));
    }
  };

  const handleJumpToStart = () => {
    if (onJumpToStart) {
      onJumpToStart();
    } else {
      onFrameChange(0);
    }
  };

  const handleJumpToEnd = () => {
    if (onJumpToEnd) {
      onJumpToEnd();
    } else {
      onFrameChange(totalFrames - 1);
    }
  };

  return (
    <div className="bg-base-200 border-t border-base-300 p-3">
      {/* Timeline Scrubber */}
      <div className="flex items-center gap-3 mb-3">
        <span className="text-xs font-mono text-base-content/70 w-20">
          {formatTime(currentTime)}
        </span>
        <input
          type="range"
          min={0}
          max={Math.max(0, totalFrames - 1)}
          value={currentFrame}
          onChange={handleSliderChange}
          className="flex-1 range range-xs range-primary"
        />
        <span className="text-xs font-mono text-base-content/70 w-20 text-right">
          {formatTime(totalTime)}
        </span>
      </div>

      {/* Controls Row */}
      <div className="flex items-center justify-between">
        {/* Left: Frame Counter */}
        <div className="text-xs font-mono text-base-content/60">
          Frame {currentFrame + 1} / {totalFrames}
        </div>

        {/* Center: Playback Controls */}
        <div className="flex items-center gap-1">
          <button
            onClick={handleJumpToStart}
            className="btn btn-ghost btn-xs btn-square"
            title="Jump to start"
          >
            <Rewind size={14} />
          </button>
          <button
            onClick={handleStepBackward}
            className="btn btn-ghost btn-xs btn-square"
            title="Step backward (1 frame)"
          >
            <SkipBack size={14} />
          </button>
          <button
            onClick={onPlayPause}
            className={clsx(
              'btn btn-sm btn-circle',
              isPlaying ? 'btn-primary' : 'btn-ghost'
            )}
            title={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? <Pause size={16} /> : <Play size={16} />}
          </button>
          <button
            onClick={handleStepForward}
            className="btn btn-ghost btn-xs btn-square"
            title="Step forward (1 frame)"
          >
            <SkipForward size={14} />
          </button>
          <button
            onClick={handleJumpToEnd}
            className="btn btn-ghost btn-xs btn-square"
            title="Jump to end"
          >
            <FastForward size={14} />
          </button>
        </div>

        {/* Right: Speed Selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-base-content/60">Speed:</span>
          <div className="flex gap-0.5">
            {SPEED_OPTIONS.map((speed) => (
              <button
                key={speed}
                onClick={() => onSpeedChange(speed)}
                className={clsx(
                  'btn btn-xs min-w-[2.5rem]',
                  playbackSpeed === speed ? 'btn-primary' : 'btn-ghost'
                )}
              >
                {speed}x
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default PreviewControls;
