/**
 * Types for Demo Recorder components
 */

export interface CameraKeyframe {
  frame: number;
  centerX: number;
  centerY: number;
  zoom: number;
  easing?: string;
  holdFrames?: number;
}

export interface ElementBounds {
  x: number;
  y: number;
  width: number;
  height: number;
  centerX: number;
  centerY: number;
}

export interface CameraData {
  mode: string;
  capture_scale: number;
  background: string;
  shadow: boolean;
  viewport_width: number;
  viewport_height: number;
  fps: number;
  total_frames: number;
  keyframes: CameraKeyframe[];
  element_bounds: Record<string, ElementBounds>;
  image_path?: string;
}

export interface CameraEffects {
  vignette?: {
    enabled: boolean;
    intensity: number;
  };
  perspective_tilt?: {
    enabled: boolean;
    intensity: number;
  };
  camera_shake?: {
    enabled: boolean;
    intensity: number;
  };
  depth_of_field?: {
    enabled: boolean;
    blur_amount: number;
  };
  motion_blur?: {
    enabled: boolean;
    intensity: number;
  };
}

export interface DemoScene {
  id: string;
  type: string;
  name?: string;
  title?: string;
  duration?: number;
  startFrame?: number;
  endFrame?: number;
  durationFrames?: number;
  cameraData?: CameraData;
  effects?: CameraEffects;
}

export interface VideoScript {
  id: string;
  name: string;
  path: string;
  language: string;
  scenes?: number;
  duration?: number;
  has_output?: boolean;
}

// Demo Recording types (for actual demo definition files)
export interface DemoRecording {
  id: string;
  name: string;
  path: string;
  language: string;
  url?: string;
  viewport?: {
    width: number;
    height: number;
  };
  states_count?: number;
  sequences_count?: number;
  error?: string;
}

export interface DemoRecordingState {
  id: string;
  description?: string;
  duration?: number;
  wait_for?: string;
  has_setup: boolean;
  has_actions: boolean;
  camera?: {
    preset?: string;
    zoom?: number;
    focus?: string;
    keyframes?: CameraKeyframe[];
  };
}

export interface DemoRecordingSequence {
  id: string;
  description?: string;
  states: string[];
  transition_delay?: number;
}

export interface DemoRecordingDetail {
  id: string;
  name: string;
  path: string;
  url?: string;
  viewport?: {
    width: number;
    height: number;
  };
  states: DemoRecordingState[];
  sequences: DemoRecordingSequence[];
  error?: string;
}
