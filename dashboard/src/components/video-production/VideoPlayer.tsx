/**
 * Video Player Component
 *
 * Custom video player with scene-aware timeline for video preview.
 * Supports:
 * - Playing rendered video files
 * - Scene markers on timeline
 * - Seeking to specific scenes
 * - Full keyboard shortcuts (space, arrows, JKL, Home/End)
 * - Playback speed control
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Volume2,
  VolumeX,
  Maximize2,
  Minimize2,
  AlertCircle,
  Film,
} from 'lucide-react';
import clsx from 'clsx';
import { useVideoKeyboardShortcuts } from '@/hooks/useVideoKeyboardShortcuts';

interface Scene {
  id: string;
  type: string;
  title?: string;
  duration: number;
  startFrame: number;
  endFrame: number;
}

interface VideoPlayerProps {
  videoUrl: string | null;
  scenes: Scene[];
  fps: number;
  currentFrame: number;
  onFrameChange?: (frame: number) => void;
  onSceneChange?: (sceneId: string) => void;
  className?: string;
}

const SCENE_TYPE_COLORS: Record<string, string> = {
  intro: 'bg-primary',
  feature: 'bg-secondary',
  demo: 'bg-accent',
  split: 'bg-info',
  outro: 'bg-success',
  default: 'bg-base-content/50',
};

const PLAYBACK_SPEEDS = [0.5, 0.75, 1, 1.25, 1.5, 2];

export function VideoPlayer({
  videoUrl,
  scenes,
  fps,
  currentFrame,
  onFrameChange,
  onSceneChange,
  className,
}: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(1);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [showSpeedMenu, setShowSpeedMenu] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Calculate total frames
  const totalFrames = scenes.reduce((max, s) => Math.max(max, s.endFrame), 0);

  // Sync video time with external currentFrame
  useEffect(() => {
    if (videoRef.current && isLoaded && !isPlaying) {
      const targetTime = currentFrame / fps;
      if (Math.abs(videoRef.current.currentTime - targetTime) > 0.1) {
        videoRef.current.currentTime = targetTime;
      }
    }
  }, [currentFrame, fps, isLoaded, isPlaying]);

  // Handle video time updates
  const handleTimeUpdate = useCallback(() => {
    if (videoRef.current) {
      const time = videoRef.current.currentTime;
      setCurrentTime(time);
      const frame = Math.floor(time * fps);
      onFrameChange?.(frame);
    }
  }, [fps, onFrameChange]);

  // Handle video loaded
  const handleLoadedMetadata = useCallback(() => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
      setIsLoaded(true);
      setError(null);
    }
  }, []);

  // Handle video error
  const handleError = useCallback(() => {
    setError('Failed to load video. Make sure the video has been rendered.');
    setIsLoaded(false);
  }, []);

  // Play/Pause
  const togglePlay = useCallback(() => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  }, [isPlaying]);

  // Mute/Unmute
  const toggleMute = useCallback(() => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  }, [isMuted]);

  // Volume change
  const handleVolumeChange = useCallback((value: number) => {
    if (videoRef.current) {
      videoRef.current.volume = value;
      setVolume(value);
      setIsMuted(value === 0);
    }
  }, []);

  // Seek to time
  const seekTo = useCallback((time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time;
      setCurrentTime(time);
      onFrameChange?.(Math.floor(time * fps));
    }
  }, [fps, onFrameChange]);

  // Seek to scene
  const seekToScene = useCallback((scene: Scene) => {
    const time = scene.startFrame / fps;
    seekTo(time);
    onSceneChange?.(scene.id);
  }, [fps, seekTo, onSceneChange]);

  // Previous/Next scene
  const goToScene = useCallback((direction: 'prev' | 'next') => {
    const currentSceneIndex = scenes.findIndex(
      (s) => currentTime >= s.startFrame / fps && currentTime < s.endFrame / fps
    );

    if (direction === 'prev' && currentSceneIndex > 0) {
      seekToScene(scenes[currentSceneIndex - 1]);
    } else if (direction === 'next' && currentSceneIndex < scenes.length - 1) {
      seekToScene(scenes[currentSceneIndex + 1]);
    }
  }, [scenes, currentTime, fps, seekToScene]);

  // Playback speed
  const setSpeed = useCallback((speed: number) => {
    if (videoRef.current) {
      videoRef.current.playbackRate = speed;
      setPlaybackSpeed(speed);
      setShowSpeedMenu(false);
    }
  }, []);

  // Fullscreen
  const toggleFullscreen = useCallback(() => {
    if (!containerRef.current) return;

    if (!isFullscreen) {
      containerRef.current.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
  }, [isFullscreen]);

  // Listen for fullscreen changes
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  // Handle frame stepping
  const handleFrameStep = useCallback((frames: number) => {
    if (videoRef.current) {
      const frameDuration = 1 / fps;
      const newTime = videoRef.current.currentTime + (frames * frameDuration);
      videoRef.current.currentTime = Math.max(0, Math.min(duration, newTime));
    }
  }, [fps, duration]);

  // Handle playback speed change (for JKL control)
  const handlePlaybackSpeedChange = useCallback((speed: number) => {
    if (videoRef.current) {
      if (speed === 0) {
        videoRef.current.pause();
        setIsPlaying(false);
      } else if (speed < 0) {
        // For reverse playback, we simulate by seeking backward
        // Real reverse playback is complex, so we just seek and pause
        videoRef.current.pause();
        setIsPlaying(false);
        const seekAmount = Math.abs(speed) * 0.5; // Seek by half-second increments
        seekTo(Math.max(0, currentTime - seekAmount));
      } else {
        videoRef.current.playbackRate = speed;
        if (!isPlaying) {
          videoRef.current.play();
          setIsPlaying(true);
        }
        setPlaybackSpeed(speed);
      }
    }
  }, [currentTime, isPlaying, seekTo]);

  // Use the video keyboard shortcuts hook
  const { currentJKLSpeed } = useVideoKeyboardShortcuts({
    onPlayPause: togglePlay,
    onSeek: seekTo,
    onFrameStep: handleFrameStep,
    onPlaybackSpeedChange: handlePlaybackSpeedChange,
    onGoToStart: () => seekTo(0),
    onGoToEnd: () => seekTo(duration),
    onPreviousScene: () => goToScene('prev'),
    onNextScene: () => goToScene('next'),
    onToggleMute: toggleMute,
    onToggleFullscreen: toggleFullscreen,
    currentTime,
    duration,
    fps,
    enabled: isLoaded,
    containerRef: containerRef as React.RefObject<HTMLElement>,
  });

  // Format time
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Timeline click handler
  const handleTimelineClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percent = x / rect.width;
    seekTo(percent * duration);
  };

  // Find current scene
  const currentScene = scenes.find(
    (s) => currentTime >= s.startFrame / fps && currentTime < s.endFrame / fps
  );

  if (!videoUrl) {
    return (
      <div className={clsx('flex flex-col items-center justify-center bg-base-300 rounded-lg', className)}>
        <Film size={48} className="text-base-content/30 mb-4" />
        <h4 className="font-medium text-base-content/60 mb-2">No Video Available</h4>
        <p className="text-sm text-base-content/50 text-center max-w-xs">
          Select a script and render it to preview the video here.
        </p>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={clsx('flex flex-col bg-black rounded-lg overflow-hidden', className)}
    >
      {/* Video Element */}
      <div className="relative flex-1 flex items-center justify-center bg-black">
        {error ? (
          <div className="flex flex-col items-center text-center p-8">
            <AlertCircle size={48} className="text-warning mb-4" />
            <p className="text-white/80 mb-2">{error}</p>
            <p className="text-white/50 text-sm">
              Go to Render tab to create the video first.
            </p>
          </div>
        ) : (
          <video
            ref={videoRef}
            src={videoUrl}
            className="max-w-full max-h-full"
            onTimeUpdate={handleTimeUpdate}
            onLoadedMetadata={handleLoadedMetadata}
            onError={handleError}
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
            onEnded={() => setIsPlaying(false)}
            onClick={togglePlay}
            playsInline
          />
        )}

        {/* Play overlay on click */}
        {isLoaded && !isPlaying && !error && (
          <button
            onClick={togglePlay}
            className="absolute inset-0 flex items-center justify-center bg-black/30 opacity-0 hover:opacity-100 transition-opacity"
          >
            <div className="w-20 h-20 rounded-full bg-white/20 flex items-center justify-center">
              <Play size={40} className="text-white ml-1" />
            </div>
          </button>
        )}
      </div>

      {/* Scene Timeline */}
      {scenes.length > 0 && isLoaded && (
        <div
          className="h-8 bg-base-300 cursor-pointer relative mx-2 mt-2 rounded overflow-hidden"
          onClick={handleTimelineClick}
        >
          {/* Scene blocks */}
          {scenes.map((scene) => {
            const left = (scene.startFrame / totalFrames) * 100;
            const width = ((scene.endFrame - scene.startFrame) / totalFrames) * 100;
            const isActive = scene.id === currentScene?.id;

            return (
              <div
                key={scene.id}
                className={clsx(
                  'absolute top-0 h-full transition-opacity',
                  SCENE_TYPE_COLORS[scene.type] || SCENE_TYPE_COLORS.default,
                  isActive ? 'opacity-100' : 'opacity-60 hover:opacity-80'
                )}
                style={{ left: `${left}%`, width: `${width}%` }}
                onClick={(e) => {
                  e.stopPropagation();
                  seekToScene(scene);
                }}
                title={scene.title || scene.type}
              >
                {width > 8 && (
                  <span className="absolute inset-0 flex items-center justify-center text-xs text-white font-medium truncate px-1">
                    {scene.title || scene.type}
                  </span>
                )}
              </div>
            );
          })}

          {/* Playhead */}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-white z-10"
            style={{ left: `${(currentTime / duration) * 100}%` }}
          />
        </div>
      )}

      {/* Controls */}
      <div className="flex items-center gap-2 px-3 py-2 bg-base-200">
        {/* Play/Pause */}
        <button
          onClick={togglePlay}
          className="btn btn-ghost btn-sm btn-square"
          disabled={!isLoaded}
        >
          {isPlaying ? <Pause size={18} /> : <Play size={18} />}
        </button>

        {/* Previous/Next Scene */}
        <button
          onClick={() => goToScene('prev')}
          className="btn btn-ghost btn-sm btn-square"
          disabled={!isLoaded}
          title="Previous scene (Shift+Left)"
        >
          <SkipBack size={16} />
        </button>
        <button
          onClick={() => goToScene('next')}
          className="btn btn-ghost btn-sm btn-square"
          disabled={!isLoaded}
          title="Next scene (Shift+Right)"
        >
          <SkipForward size={16} />
        </button>

        {/* Time Display */}
        <div className="text-sm font-mono text-base-content/70 min-w-[100px]">
          {formatTime(currentTime)} / {formatTime(duration)}
        </div>

        {/* Current Scene */}
        {currentScene && (
          <span className="badge badge-sm badge-ghost truncate max-w-[120px]">
            {currentScene.title || currentScene.type}
          </span>
        )}

        <div className="flex-1" />

        {/* Playback Speed */}
        <div className="relative">
          <button
            onClick={() => setShowSpeedMenu(!showSpeedMenu)}
            className="btn btn-ghost btn-sm"
          >
            {playbackSpeed}x
          </button>
          {showSpeedMenu && (
            <div className="absolute bottom-full right-0 mb-1 bg-base-300 rounded-lg shadow-lg p-1 z-20">
              {PLAYBACK_SPEEDS.map((speed) => (
                <button
                  key={speed}
                  onClick={() => setSpeed(speed)}
                  className={clsx(
                    'block w-full px-3 py-1 text-sm text-left rounded hover:bg-base-content/10',
                    playbackSpeed === speed && 'bg-primary/20 text-primary'
                  )}
                >
                  {speed}x
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Volume */}
        <div className="flex items-center gap-1">
          <button onClick={toggleMute} className="btn btn-ghost btn-sm btn-square">
            {isMuted ? <VolumeX size={16} /> : <Volume2 size={16} />}
          </button>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={isMuted ? 0 : volume}
            onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
            className="range range-xs w-16"
          />
        </div>

        {/* Fullscreen */}
        <button
          onClick={toggleFullscreen}
          className="btn btn-ghost btn-sm btn-square"
          title="Fullscreen (F)"
        >
          {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
        </button>
      </div>

      {/* Keyboard shortcuts hint */}
      {isLoaded && (
        <div className="text-xs text-base-content/40 text-center py-1 bg-base-300/50">
          Space: Play/Pause | J/K/L: Shuttle | Arrows: Seek | ,/.: Frame step | Home/End: Start/End | ?: Help
          {currentJKLSpeed !== 0 && currentJKLSpeed !== 1 && (
            <span className="ml-2 text-primary">({currentJKLSpeed > 0 ? '+' : ''}{currentJKLSpeed}x)</span>
          )}
        </div>
      )}
    </div>
  );
}

export default VideoPlayer;
