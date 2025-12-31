/**
 * Video Timeline Keyboard Shortcuts Hook
 *
 * Provides industry-standard video editing keyboard shortcuts:
 * - Space: Play/Pause
 * - Left/Right: Frame step (1 frame) or seek (5 seconds with Shift)
 * - J/K/L: Playback control (rewind/pause/forward)
 * - Home/End: Go to start/end
 * - ,/.: Frame step backward/forward (alternative)
 * - I/O: Set in/out points (if supported)
 *
 * This hook is designed to be used within video player components
 * and respects input focus states.
 */

import { useEffect, useCallback, useRef, useState } from 'react';

export interface VideoKeyboardShortcutsOptions {
  /** Called when play/pause is toggled */
  onPlayPause?: () => void;
  /** Called to seek to a specific time (in seconds) */
  onSeek?: (time: number) => void;
  /** Called to step by frames (positive = forward, negative = backward) */
  onFrameStep?: (frames: number) => void;
  /** Called when playback speed should change (for J/K/L control) */
  onPlaybackSpeedChange?: (speed: number) => void;
  /** Called to go to start of video */
  onGoToStart?: () => void;
  /** Called to go to end of video */
  onGoToEnd?: () => void;
  /** Called to go to previous scene/chapter */
  onPreviousScene?: () => void;
  /** Called to go to next scene/chapter */
  onNextScene?: () => void;
  /** Called to toggle mute */
  onToggleMute?: () => void;
  /** Called to toggle fullscreen */
  onToggleFullscreen?: () => void;
  /** Current video time (for seeking calculations) */
  currentTime?: number;
  /** Video duration (for bounds checking) */
  duration?: number;
  /** Frames per second (for frame stepping) - reserved for future use */
  fps?: number;
  /** Whether shortcuts are enabled */
  enabled?: boolean;
  /** Container element ref - shortcuts only work when this is focused or when no input is focused */
  containerRef?: React.RefObject<HTMLElement>;
}

export interface VideoKeyboardShortcut {
  key: string;
  description: string;
  category: string;
}

/**
 * Default video timeline shortcuts for display in help
 */
export const VIDEO_SHORTCUTS: VideoKeyboardShortcut[] = [
  // Playback
  { key: 'Space', description: 'Play / Pause', category: 'Video Playback' },
  { key: 'K', description: 'Pause (JKL mode)', category: 'Video Playback' },
  { key: 'J', description: 'Rewind / Decrease speed', category: 'Video Playback' },
  { key: 'L', description: 'Forward / Increase speed', category: 'Video Playback' },

  // Seeking
  { key: 'Left', description: 'Seek backward 5 seconds', category: 'Video Seeking' },
  { key: 'Right', description: 'Seek forward 5 seconds', category: 'Video Seeking' },
  { key: 'Shift+Left', description: 'Previous scene/chapter', category: 'Video Seeking' },
  { key: 'Shift+Right', description: 'Next scene/chapter', category: 'Video Seeking' },
  { key: 'Home', description: 'Go to start', category: 'Video Seeking' },
  { key: 'End', description: 'Go to end', category: 'Video Seeking' },

  // Frame stepping
  { key: ',', description: 'Step 1 frame backward', category: 'Video Frame Control' },
  { key: '.', description: 'Step 1 frame forward', category: 'Video Frame Control' },

  // Other controls
  { key: 'M', description: 'Toggle mute', category: 'Video Controls' },
  { key: 'F', description: 'Toggle fullscreen', category: 'Video Controls' },
];

/**
 * JKL playback speeds - industry standard non-linear speeds
 */
const JKL_SPEEDS = [-8, -4, -2, -1, -0.5, 0, 0.5, 1, 2, 4, 8];

/**
 * Hook for video timeline keyboard shortcuts.
 * Implements industry-standard video editing shortcuts.
 */
export function useVideoKeyboardShortcuts({
  onPlayPause,
  onSeek,
  onFrameStep,
  onPlaybackSpeedChange,
  onGoToStart,
  onGoToEnd,
  onPreviousScene,
  onNextScene,
  onToggleMute,
  onToggleFullscreen,
  currentTime = 0,
  duration = 0,
  // fps is reserved for future use (e.g., precise frame timing)
  fps: _fps = 30,
  enabled = true,
  containerRef,
}: VideoKeyboardShortcutsOptions) {
  // Note: _fps is intentionally unused but reserved for future frame-accurate operations
  void _fps;
  // Track current JKL speed index for J/K/L shuttle control
  const [jklSpeedIndex, setJklSpeedIndex] = useState(5); // 5 = stopped (0 speed)
  const jklSpeedRef = useRef(jklSpeedIndex);

  // Keep ref in sync with state
  useEffect(() => {
    jklSpeedRef.current = jklSpeedIndex;
  }, [jklSpeedIndex]);

  /**
   * Check if we should handle keyboard events
   */
  const shouldHandleEvent = useCallback((event: KeyboardEvent): boolean => {
    if (!enabled) return false;

    const target = event.target as HTMLElement;

    // Don't handle if typing in input/textarea
    if (
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.isContentEditable
    ) {
      return false;
    }

    // If containerRef is provided, only handle if it contains the target
    // or if no specific element is focused
    if (containerRef?.current) {
      const container = containerRef.current;
      const isContainerFocused = container.contains(target) || target === document.body;
      return isContainerFocused;
    }

    return true;
  }, [enabled, containerRef]);

  /**
   * Handle JKL shuttle control
   * J = slower/rewind, K = pause, L = faster/forward
   */
  const handleJKL = useCallback((key: string) => {
    const currentIndex = jklSpeedRef.current;
    let newIndex = currentIndex;

    switch (key.toLowerCase()) {
      case 'j':
        // Decrease speed (move toward rewind)
        newIndex = Math.max(0, currentIndex - 1);
        break;
      case 'k':
        // Stop/Pause (reset to 0)
        newIndex = 5; // Index of 0 in JKL_SPEEDS
        break;
      case 'l':
        // Increase speed (move toward forward)
        newIndex = Math.min(JKL_SPEEDS.length - 1, currentIndex + 1);
        break;
    }

    if (newIndex !== currentIndex) {
      setJklSpeedIndex(newIndex);
      const newSpeed = JKL_SPEEDS[newIndex];
      onPlaybackSpeedChange?.(newSpeed);
    }
  }, [onPlaybackSpeedChange]);

  /**
   * Main keyboard event handler
   */
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!shouldHandleEvent(event)) return;

      const key = event.key;

      switch (key) {
        // Play/Pause
        case ' ':
          event.preventDefault();
          onPlayPause?.();
          break;

        // Arrow keys for seeking
        case 'ArrowLeft':
          event.preventDefault();
          if (event.shiftKey) {
            // Shift+Left = Previous scene
            onPreviousScene?.();
          } else {
            // Left = Seek backward 5 seconds
            const newTime = Math.max(0, currentTime - 5);
            onSeek?.(newTime);
          }
          break;

        case 'ArrowRight':
          event.preventDefault();
          if (event.shiftKey) {
            // Shift+Right = Next scene
            onNextScene?.();
          } else {
            // Right = Seek forward 5 seconds
            const newTime = Math.min(duration, currentTime + 5);
            onSeek?.(newTime);
          }
          break;

        // Home/End for start/end
        case 'Home':
          event.preventDefault();
          onGoToStart?.();
          break;

        case 'End':
          event.preventDefault();
          onGoToEnd?.();
          break;

        // JKL shuttle control
        case 'j':
        case 'J':
        case 'k':
        case 'K':
        case 'l':
        case 'L':
          event.preventDefault();
          handleJKL(key);
          break;

        // Frame stepping with , and .
        case ',':
        case '<':
          event.preventDefault();
          onFrameStep?.(-1);
          break;

        case '.':
        case '>':
          event.preventDefault();
          onFrameStep?.(1);
          break;

        // Mute toggle
        case 'm':
        case 'M':
          event.preventDefault();
          onToggleMute?.();
          break;

        // Fullscreen toggle
        case 'f':
        case 'F':
          event.preventDefault();
          onToggleFullscreen?.();
          break;
      }
    },
    [
      shouldHandleEvent,
      onPlayPause,
      onSeek,
      onFrameStep,
      onPreviousScene,
      onNextScene,
      onGoToStart,
      onGoToEnd,
      onToggleMute,
      onToggleFullscreen,
      handleJKL,
      currentTime,
      duration,
    ]
  );

  // Attach event listener
  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // Reset JKL speed when playback stops externally
  const resetJKLSpeed = useCallback(() => {
    setJklSpeedIndex(5);
  }, []);

  return {
    shortcuts: VIDEO_SHORTCUTS,
    jklSpeedIndex,
    currentJKLSpeed: JKL_SPEEDS[jklSpeedIndex],
    resetJKLSpeed,
  };
}

export default useVideoKeyboardShortcuts;
