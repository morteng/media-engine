/**
 * TimelineContext - Shared timeline state for video components
 *
 * Provides centralized frame/time synchronization across:
 * - VideoPlayer / UnifiedVideoPlayer
 * - ChapterTimeline / ChapterSelector
 * - Timeline visualization
 * - Scene cards
 *
 * Usage:
 * ```tsx
 * <TimelineProvider fps={30} totalFrames={2679}>
 *   <UnifiedVideoPlayer />
 *   <ChapterTimeline />
 * </TimelineProvider>
 *
 * // In child components:
 * const { currentFrame, seekToFrame, fps } = useTimeline();
 * ```
 */

import React, { createContext, useContext, useState, useCallback, useMemo } from 'react';
import type { UnifiedScene } from '@/api/types/video';

// ============================================================================
// Types
// ============================================================================

interface TimelineState {
  /** Current frame position */
  currentFrame: number;
  /** Total frames in video */
  totalFrames: number;
  /** Frames per second */
  fps: number;
  /** Currently selected scene ID */
  selectedSceneId: string | null;
  /** All scenes with timing */
  scenes: UnifiedScene[];
  /** Is playing */
  isPlaying: boolean;
  /** Zoom level for timeline (1 = 100%) */
  zoom: number;
}

interface TimelineActions {
  /** Seek to a specific frame */
  seekToFrame: (frame: number) => void;
  /** Seek to a specific time in seconds */
  seekToTime: (seconds: number) => void;
  /** Select a scene by ID */
  selectScene: (sceneId: string | null) => void;
  /** Set playing state */
  setPlaying: (playing: boolean) => void;
  /** Set zoom level */
  setZoom: (zoom: number) => void;
  /** Update scenes */
  setScenes: (scenes: UnifiedScene[]) => void;
  /** Update total frames */
  setTotalFrames: (frames: number) => void;
  /** Update FPS */
  setFps: (fps: number) => void;
}

interface TimelineUtils {
  /** Convert frame to time in seconds */
  frameToTime: (frame: number) => number;
  /** Convert time in seconds to frame */
  timeToFrame: (seconds: number) => number;
  /** Format frame as time string (MM:SS.ms) */
  formatTime: (frame: number) => string;
  /** Get current scene based on frame position */
  getCurrentScene: () => UnifiedScene | null;
  /** Get scene at a specific frame */
  getSceneAtFrame: (frame: number) => UnifiedScene | null;
  /** Calculate progress (0-1) within current scene */
  getSceneProgress: () => number;
}

type TimelineContextValue = TimelineState & TimelineActions & TimelineUtils;

// ============================================================================
// Context
// ============================================================================

const TimelineContext = createContext<TimelineContextValue | null>(null);

// ============================================================================
// Provider Props
// ============================================================================

interface TimelineProviderProps {
  children: React.ReactNode;
  /** Initial FPS (default: 30) */
  fps?: number;
  /** Initial total frames (default: 300) */
  totalFrames?: number;
  /** Initial scenes */
  scenes?: UnifiedScene[];
}

// ============================================================================
// Provider Component
// ============================================================================

export function TimelineProvider({
  children,
  fps: initialFps = 30,
  totalFrames: initialTotalFrames = 300,
  scenes: initialScenes = [],
}: TimelineProviderProps) {
  // State
  const [currentFrame, setCurrentFrame] = useState(0);
  const [totalFrames, setTotalFrames] = useState(initialTotalFrames);
  const [fps, setFps] = useState(initialFps);
  const [selectedSceneId, setSelectedSceneId] = useState<string | null>(null);
  const [scenes, setScenes] = useState<UnifiedScene[]>(initialScenes);
  const [isPlaying, setPlaying] = useState(false);
  const [zoom, setZoom] = useState(1);

  // Actions
  const seekToFrame = useCallback((frame: number) => {
    setCurrentFrame(Math.max(0, Math.min(frame, totalFrames)));
  }, [totalFrames]);

  const seekToTime = useCallback((seconds: number) => {
    setCurrentFrame(Math.round(seconds * fps));
  }, [fps]);

  const selectScene = useCallback((sceneId: string | null) => {
    setSelectedSceneId(sceneId);
    // If selecting a scene, seek to its start
    if (sceneId) {
      const scene = scenes.find(s => s.id === sceneId);
      if (scene?.startFrame !== undefined) {
        setCurrentFrame(scene.startFrame);
      }
    }
  }, [scenes]);

  // Utility functions
  const frameToTime = useCallback((frame: number) => {
    return frame / fps;
  }, [fps]);

  const timeToFrame = useCallback((seconds: number) => {
    return Math.round(seconds * fps);
  }, [fps]);

  const formatTime = useCallback((frame: number) => {
    const totalSeconds = frame / fps;
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${seconds.toFixed(2).padStart(5, '0')}`;
  }, [fps]);

  const getSceneAtFrame = useCallback((frame: number): UnifiedScene | null => {
    return scenes.find(scene => {
      const start = scene.startFrame ?? 0;
      const end = scene.endFrame ?? (scene.startFrame ?? 0) + (scene.durationFrames ?? 0);
      return frame >= start && frame < end;
    }) || null;
  }, [scenes]);

  const getCurrentScene = useCallback(() => {
    return getSceneAtFrame(currentFrame);
  }, [currentFrame, getSceneAtFrame]);

  const getSceneProgress = useCallback(() => {
    const scene = getCurrentScene();
    if (!scene || scene.startFrame === undefined || scene.durationFrames === undefined) {
      return 0;
    }
    const sceneFrame = currentFrame - scene.startFrame;
    return Math.max(0, Math.min(1, sceneFrame / scene.durationFrames));
  }, [currentFrame, getCurrentScene]);

  // Memoized context value
  const value = useMemo<TimelineContextValue>(() => ({
    // State
    currentFrame,
    totalFrames,
    fps,
    selectedSceneId,
    scenes,
    isPlaying,
    zoom,
    // Actions
    seekToFrame,
    seekToTime,
    selectScene,
    setPlaying,
    setZoom,
    setScenes,
    setTotalFrames,
    setFps,
    // Utils
    frameToTime,
    timeToFrame,
    formatTime,
    getCurrentScene,
    getSceneAtFrame,
    getSceneProgress,
  }), [
    currentFrame, totalFrames, fps, selectedSceneId, scenes, isPlaying, zoom,
    seekToFrame, seekToTime, selectScene,
    frameToTime, timeToFrame, formatTime, getCurrentScene, getSceneAtFrame, getSceneProgress,
  ]);

  return (
    <TimelineContext.Provider value={value}>
      {children}
    </TimelineContext.Provider>
  );
}

// ============================================================================
// Hook
// ============================================================================

export function useTimeline(): TimelineContextValue {
  const context = useContext(TimelineContext);
  if (!context) {
    throw new Error('useTimeline must be used within a TimelineProvider');
  }
  return context;
}

// ============================================================================
// Optional Hook (doesn't throw if outside provider)
// ============================================================================

export function useTimelineOptional(): TimelineContextValue | null {
  return useContext(TimelineContext);
}

export default TimelineProvider;
