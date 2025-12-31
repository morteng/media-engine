/**
 * UnifiedVideoPlayer - Combines video playback with chapter timeline and comment markers
 *
 * Features:
 * - Play videos from any chapter
 * - Chapter timeline with proportional blocks
 * - Comment markers overlay on timeline
 * - Seamless chapter switching
 * - Global and local frame tracking
 * - Full keyboard shortcuts (JKL, Home/End, frame stepping)
 */

import { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Volume2,
  VolumeX,
  Maximize2,
  Minimize2,
  Film,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import clsx from 'clsx';
import type {
  ChapterTimelineData,
  VideoReviewComment,
} from '@/api/types/video';
import { ChapterTimeline } from './ChapterTimeline';
import { CommentMarkers } from './CommentMarkers';
import { globalToLocalFrame, localToGlobalFrame } from '@/hooks/useVideoApi';
import { useVideoKeyboardShortcuts } from '@/hooks/useVideoKeyboardShortcuts';

interface UnifiedVideoPlayerProps {
  /** Timeline data with all chapters */
  timelineData: ChapterTimelineData;
  /** All comments across all chapters */
  comments: VideoReviewComment[];
  /** Currently selected chapter ID (optional) */
  selectedChapterId?: string | null;
  /** Called when a chapter is selected */
  onChapterSelect?: (chapterId: string) => void;
  /** Called when a comment marker is clicked */
  onCommentClick?: (comment: VideoReviewComment) => void;
  /** Currently selected comment ID (for highlighting) */
  selectedCommentId?: string | null;
  /** Whether to show resolved comments */
  showResolvedComments?: boolean;
  /** Optional className */
  className?: string;
  /** Called when playback time updates (localFrame, localTime, globalFrame) */
  onTimeUpdate?: (localFrame: number, localTime: number, globalFrame: number) => void;
  /** Register the seek function for external seeking */
  onRegisterSeek?: (seekFn: (globalFrame: number) => void) => void;
}

const PLAYBACK_SPEEDS = [0.5, 0.75, 1, 1.25, 1.5, 2];

export function UnifiedVideoPlayer({
  timelineData,
  comments,
  selectedChapterId = null,
  onChapterSelect,
  onCommentClick,
  selectedCommentId = null,
  showResolvedComments = true,
  className,
  onTimeUpdate,
  onRegisterSeek,
}: UnifiedVideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Player state
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(1);
  const [currentLocalFrame, setCurrentLocalFrame] = useState(0);
  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [showSpeedMenu, setShowSpeedMenu] = useState(false);

  // Get current chapter
  const currentChapter = useMemo(() => {
    if (selectedChapterId) {
      return timelineData.chapters.find((c) => c.id === selectedChapterId) || null;
    }
    // Default to first chapter with video
    return timelineData.chapters.find((c) => c.hasVideo) || timelineData.chapters[0] || null;
  }, [timelineData.chapters, selectedChapterId]);

  // Calculate global frame from local frame
  const currentGlobalFrame = useMemo(() => {
    if (!currentChapter) return 0;
    return localToGlobalFrame(currentChapter, currentLocalFrame);
  }, [currentChapter, currentLocalFrame]);

  // Get video URL for current chapter
  const videoUrl = currentChapter?.videoUrl || null;
  const fps = currentChapter?.fps || timelineData.globalFps || 30;

  // Sync video time updates
  const handleTimeUpdate = useCallback(() => {
    if (videoRef.current && currentChapter) {
      const time = videoRef.current.currentTime;
      const frame = Math.floor(time * fps);
      setCurrentLocalFrame(frame);
      // Notify parent of time update
      const globalFrame = localToGlobalFrame(currentChapter, frame);
      onTimeUpdate?.(frame, time, globalFrame);
    }
  }, [fps, currentChapter, onTimeUpdate]);

  // Handle video loaded
  const handleLoadedMetadata = useCallback(() => {
    setIsLoaded(true);
    setError(null);
  }, []);

  // Handle video error
  const handleError = useCallback(() => {
    setError('Failed to load video');
    setIsLoaded(false);
  }, []);

  // Reset state when chapter changes
  useEffect(() => {
    setIsLoaded(false);
    setCurrentLocalFrame(0);
    setError(null);
  }, [currentChapter?.id]);

  // Register seek function with parent when available
  useEffect(() => {
    if (onRegisterSeek) {
      onRegisterSeek((globalFrame: number) => {
        const result = globalToLocalFrame(globalFrame, timelineData.chapters);
        if (!result) return;

        const { chapter, localFrame } = result;

        // If different chapter, switch to it
        if (chapter.id !== currentChapter?.id) {
          onChapterSelect?.(chapter.id);
          // Wait for chapter to load, then seek
          setTimeout(() => {
            if (videoRef.current) {
              videoRef.current.currentTime = localFrame / chapter.fps;
            }
          }, 100);
        } else if (videoRef.current) {
          const chapterFps = currentChapter?.fps || 30;
          videoRef.current.currentTime = localFrame / chapterFps;
          setCurrentLocalFrame(localFrame);
        }
      });
    }
  }, [onRegisterSeek, timelineData.chapters, currentChapter?.id, currentChapter?.fps, onChapterSelect]);

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

  // Seek to global frame
  const seekToGlobalFrame = useCallback(
    (globalFrame: number) => {
      const result = globalToLocalFrame(globalFrame, timelineData.chapters);
      if (!result) return;

      const { chapter, localFrame } = result;

      // If different chapter, switch to it
      if (chapter.id !== currentChapter?.id) {
        onChapterSelect?.(chapter.id);
        // Wait for chapter to load, then seek
        setTimeout(() => {
          if (videoRef.current) {
            videoRef.current.currentTime = localFrame / chapter.fps;
          }
        }, 100);
      } else if (videoRef.current) {
        videoRef.current.currentTime = localFrame / fps;
        setCurrentLocalFrame(localFrame);
      }
    },
    [timelineData.chapters, currentChapter?.id, fps, onChapterSelect]
  );

  // Navigate chapters
  const goToChapter = useCallback(
    (direction: 'prev' | 'next') => {
      const currentIndex = timelineData.chapters.findIndex((c) => c.id === currentChapter?.id);
      if (currentIndex === -1) return;

      const newIndex = direction === 'prev' ? currentIndex - 1 : currentIndex + 1;
      if (newIndex >= 0 && newIndex < timelineData.chapters.length) {
        onChapterSelect?.(timelineData.chapters[newIndex].id);
      }
    },
    [timelineData.chapters, currentChapter?.id, onChapterSelect]
  );

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

  // Navigate between comments
  const navigateComments = useCallback(
    (direction: 'prev' | 'next') => {
      const sortedComments = [...comments]
        .filter((c) => c.frame !== undefined)
        .sort((a, b) => {
          const chapterA = timelineData.chapters.find((ch) => ch.id === a.component_id);
          const chapterB = timelineData.chapters.find((ch) => ch.id === b.component_id);
          const globalA = chapterA ? chapterA.startGlobalFrame + (a.frame || 0) : 0;
          const globalB = chapterB ? chapterB.startGlobalFrame + (b.frame || 0) : 0;
          return globalA - globalB;
        });

      if (sortedComments.length === 0) return;

      let targetComment: VideoReviewComment | undefined;

      if (direction === 'next') {
        targetComment = sortedComments.find((c) => {
          const chapter = timelineData.chapters.find((ch) => ch.id === c.component_id);
          if (!chapter) return false;
          const commentGlobal = chapter.startGlobalFrame + (c.frame || 0);
          return commentGlobal > currentGlobalFrame;
        });
      } else {
        // Find last comment before current position
        for (let i = sortedComments.length - 1; i >= 0; i--) {
          const c = sortedComments[i];
          const chapter = timelineData.chapters.find((ch) => ch.id === c.component_id);
          if (!chapter) continue;
          const commentGlobal = chapter.startGlobalFrame + (c.frame || 0);
          if (commentGlobal < currentGlobalFrame) {
            targetComment = c;
            break;
          }
        }
      }

      if (targetComment) {
        onCommentClick?.(targetComment);
        const chapter = timelineData.chapters.find((ch) => ch.id === targetComment!.component_id);
        if (chapter) {
          seekToGlobalFrame(chapter.startGlobalFrame + (targetComment.frame || 0));
        }
      }
    },
    [comments, timelineData.chapters, currentGlobalFrame, onCommentClick, seekToGlobalFrame]
  );

  // Handle comment marker click
  const handleCommentMarkerClick = useCallback(
    (comment: VideoReviewComment) => {
      onCommentClick?.(comment);
      const chapter = timelineData.chapters.find((ch) => ch.id === comment.component_id);
      if (chapter) {
        seekToGlobalFrame(chapter.startGlobalFrame + (comment.frame || 0));
      }
    },
    [timelineData.chapters, onCommentClick, seekToGlobalFrame]
  );

  // Calculate current time and duration
  const currentTime = currentLocalFrame / fps;
  const duration = currentChapter?.duration || 0;

  // Format time
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Seek to local time
  const seekToLocalTime = useCallback((time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = Math.max(0, Math.min(duration, time));
    }
  }, [duration]);

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
        // For reverse playback, simulate by seeking backward
        videoRef.current.pause();
        setIsPlaying(false);
        const seekAmount = Math.abs(speed) * 0.5;
        seekToLocalTime(Math.max(0, (videoRef.current?.currentTime || 0) - seekAmount));
      } else {
        videoRef.current.playbackRate = speed;
        if (!isPlaying) {
          videoRef.current.play();
          setIsPlaying(true);
        }
        setPlaybackSpeed(speed);
      }
    }
  }, [isPlaying, seekToLocalTime]);

  // Get current local time for keyboard hook
  const currentLocalTime = currentLocalFrame / fps;

  // Use the video keyboard shortcuts hook
  const { currentJKLSpeed } = useVideoKeyboardShortcuts({
    onPlayPause: togglePlay,
    onSeek: seekToLocalTime,
    onFrameStep: handleFrameStep,
    onPlaybackSpeedChange: handlePlaybackSpeedChange,
    onGoToStart: () => seekToLocalTime(0),
    onGoToEnd: () => seekToLocalTime(duration),
    onPreviousScene: () => goToChapter('prev'),
    onNextScene: () => goToChapter('next'),
    onToggleMute: toggleMute,
    onToggleFullscreen: toggleFullscreen,
    currentTime: currentLocalTime,
    duration,
    fps,
    enabled: isLoaded,
    containerRef: containerRef as React.RefObject<HTMLElement>,
  });

  // Get chapter index for display
  const chapterIndex = timelineData.chapters.findIndex((c) => c.id === currentChapter?.id);

  return (
    <div
      ref={containerRef}
      className={clsx('flex flex-col bg-black rounded-lg overflow-hidden', className)}
    >
      {/* Video Area */}
      <div className="relative flex-1 flex items-center justify-center bg-black min-h-[300px]">
        {!currentChapter ? (
          <div className="flex flex-col items-center text-center p-8">
            <Film size={48} className="text-base-content/30 mb-4" />
            <h4 className="font-medium text-white/60 mb-2">No Videos Available</h4>
            <p className="text-sm text-white/40">No video scripts found in this project.</p>
          </div>
        ) : !videoUrl ? (
          <div className="flex flex-col items-center text-center p-8">
            <Film size={48} className="text-base-content/30 mb-4" />
            <h4 className="font-medium text-white/60 mb-2">{currentChapter.name}</h4>
            <p className="text-sm text-white/40">
              This chapter has not been rendered yet. Go to Render tab to create the video.
            </p>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center text-center p-8">
            <Film size={48} className="text-warning/60 mb-4" />
            <p className="text-white/60">{error}</p>
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

        {/* Play overlay */}
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

      {/* Chapter Timeline with Comment Markers */}
      {timelineData.chapters.length > 0 && (
        <div className="relative mx-2 mt-2">
          <ChapterTimeline
            timelineData={timelineData}
            selectedChapterId={currentChapter?.id || null}
            currentFrame={currentGlobalFrame}
            onSeek={seekToGlobalFrame}
            onChapterSelect={(id) => onChapterSelect?.(id)}
          />

          {/* Comment markers overlay */}
          <div className="absolute inset-0 -top-1">
            <CommentMarkers
              comments={comments}
              timelineData={timelineData}
              selectedCommentId={selectedCommentId}
              onMarkerClick={handleCommentMarkerClick}
              showResolved={showResolvedComments}
            />
          </div>
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

        {/* Previous/Next Chapter */}
        <button
          onClick={() => goToChapter('prev')}
          className="btn btn-ghost btn-sm btn-square"
          disabled={chapterIndex <= 0}
          title="Previous chapter (Shift+Left)"
        >
          <ChevronLeft size={16} />
        </button>
        <button
          onClick={() => goToChapter('next')}
          className="btn btn-ghost btn-sm btn-square"
          disabled={chapterIndex >= timelineData.chapters.length - 1}
          title="Next chapter (Shift+Right)"
        >
          <ChevronRight size={16} />
        </button>

        {/* Time Display */}
        <div className="text-sm font-mono text-base-content/70 min-w-[100px]">
          {formatTime(currentTime)} / {formatTime(duration)}
        </div>

        {/* Current Chapter Badge */}
        {currentChapter && (
          <span className="badge badge-sm badge-primary truncate max-w-[150px]">
            {chapterIndex + 1}. {currentChapter.name}
          </span>
        )}

        <div className="flex-1" />

        {/* Comment Navigation */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => navigateComments('prev')}
            className="btn btn-ghost btn-xs"
            title="Previous comment (J)"
          >
            <SkipBack size={14} />
          </button>
          <span className="text-xs text-base-content/50">
            {comments.length} comment{comments.length !== 1 ? 's' : ''}
          </span>
          <button
            onClick={() => navigateComments('next')}
            className="btn btn-ghost btn-xs"
            title="Next comment (K)"
          >
            <SkipForward size={14} />
          </button>
        </div>

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
      <div className="text-xs text-base-content/40 text-center py-1 bg-base-300/50">
        Space: Play/Pause | J/K/L: Shuttle | Arrows: Seek | ,/.: Frame step | Home/End: Start/End | ?: Help
        {currentJKLSpeed !== 0 && currentJKLSpeed !== 1 && (
          <span className="ml-2 text-primary">({currentJKLSpeed > 0 ? '+' : ''}{currentJKLSpeed}x)</span>
        )}
      </div>
    </div>
  );
}

export default UnifiedVideoPlayer;
