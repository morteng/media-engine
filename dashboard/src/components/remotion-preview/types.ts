/**
 * Types for Remotion Preview Components
 *
 * Extended types for the @remotion/player integration.
 */

import type { CameraKeyframe, CameraState, CameraData } from '@/lib/camera';
import type { CameraEffectsConfig } from '@/lib/effects';

// Re-export for convenience
export type { CameraKeyframe, CameraState, CameraData, CameraEffectsConfig };

// ============================================================================
// Demo Recording Types (from API)
// ============================================================================

export interface DemoViewport {
  width: number;
  height: number;
}

export interface DemoCamera {
  preset?: string;
  keyframes?: CameraKeyframe[];
}

export interface DemoState {
  id: string;
  description?: string;
  duration?: number;
  camera?: DemoCamera;
  screenshot_path?: string;
  actions?: DemoAction[];
}

export interface DemoAction {
  type: string;
  selector?: string;
  value?: string;
  delay?: number;
}

export interface DemoRecordingDetail {
  id: string;
  name: string;
  path: string;
  language: string;
  url?: string;
  viewport?: DemoViewport;
  states: DemoState[];
  sequences?: DemoSequence[];
}

export interface DemoSequence {
  id: string;
  name: string;
  states: string[];
}

// ============================================================================
// Remotion Player Props
// ============================================================================

export interface RemotionDemoProps {
  /** URL or path to the screenshot image */
  screenshotUrl: string;
  /** Width of the captured screenshot in pixels */
  captureWidth: number;
  /** Height of the captured screenshot in pixels */
  captureHeight: number;
  /** Camera keyframes for animation */
  keyframes: CameraKeyframe[];
  /** Background color behind the screenshot */
  background: string;
  /** Whether to show shadow under the screenshot */
  shadow: boolean;
  /** Visual effects configuration */
  effects?: CameraEffectsConfig;
  /** Total frames for this demo state */
  totalFrames: number;
  /** Frames per second */
  fps: number;
}

export interface DemoCompositionProps extends RemotionDemoProps {
  /** Current frame passed by the Player */
  frame: number;
}

// ============================================================================
// Preview State
// ============================================================================

export interface PreviewState {
  /** Current playback frame */
  currentFrame: number;
  /** Is playback active */
  isPlaying: boolean;
  /** Playback speed multiplier (0.25, 0.5, 1, 1.5, 2) */
  playbackSpeed: number;
  /** Currently selected demo ID */
  selectedDemoId: string | null;
  /** Currently selected state within the demo */
  selectedStateId: string | null;
}

// ============================================================================
// Player Controls
// ============================================================================

export interface PlayerControlsProps {
  currentFrame: number;
  totalFrames: number;
  fps: number;
  isPlaying: boolean;
  playbackSpeed: number;
  onFrameChange: (frame: number) => void;
  onPlayPause: () => void;
  onSpeedChange: (speed: number) => void;
  onStepBackward?: () => void;
  onStepForward?: () => void;
  onJumpToStart?: () => void;
  onJumpToEnd?: () => void;
}

// ============================================================================
// Timeline Types
// ============================================================================

export interface TimelineKeyframe {
  frame: number;
  label?: string;
  zoom: number;
  centerX: number;
  centerY: number;
  easing?: string;
}

export interface TimelineProps {
  keyframes: TimelineKeyframe[];
  currentFrame: number;
  totalFrames: number;
  fps: number;
  onFrameClick: (frame: number) => void;
  onKeyframeClick?: (keyframe: TimelineKeyframe) => void;
}

// ============================================================================
// Demo Browser Types
// ============================================================================

export interface DemoBrowserItem {
  id: string;
  name: string;
  statesCount: number;
  language: string;
  viewport?: DemoViewport;
  hasScreenshots: boolean;
}

export interface DemoStateBrowserProps {
  demos: DemoBrowserItem[];
  selectedDemoId: string | null;
  selectedStateId: string | null;
  states: DemoState[];
  onSelectDemo: (demoId: string) => void;
  onSelectState: (stateId: string) => void;
  isLoading?: boolean;
}

// ============================================================================
// Preview API Response Types
// ============================================================================

export interface PreviewPropsResponse {
  demo_id: string;
  state_id: string;
  screenshot_url: string | null;
  capture_width: number;
  capture_height: number;
  keyframes: CameraKeyframe[];
  total_frames: number;
  fps: number;
  background: string;
  effects?: CameraEffectsConfig;
}

export interface DemoScreenshotsResponse {
  demo_id: string;
  screenshots: {
    state_id: string;
    path: string;
    url: string;
    width?: number;
    height?: number;
    exists: boolean;
  }[];
}
