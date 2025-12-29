/**
 * Video-related type definitions
 * Unified types for consistent video data handling across the dashboard
 */

// ============================================================================
// Scene Types (Unified)
// ============================================================================

/** Scene types used in video scripts */
export type SceneType = 'intro' | 'content' | 'feature' | 'demo' | 'section' | 'outro' | 'split' | 'transition';

/** Visual configuration for a scene */
export interface SceneVisual {
  background?: 'dark' | 'aurora' | 'grid' | 'particles' | 'pulse' | 'cyber' | 'waves';
  intensity?: 'low' | 'medium' | 'high';
  transition_in?: string;
  transition_out?: string;
  text_effect?: 'fade-up' | 'bounce' | 'elastic' | 'wave' | 'split' | 'scale-pop' | 'rotate' | 'glitch';
  show_logo?: boolean;
  glow?: boolean;
  gradient_text?: boolean;
  /** Split screen configuration */
  split_screen?: {
    demo_on_left?: boolean;
    split_angle?: number;
    demo_width?: number;
    bullets?: string[];
    highlight?: 'cyan' | 'purple' | 'hot' | 'neon';
  };
  /** Demo clip reference */
  demo?: {
    state: string;
    clipPath: string;
  };
  /** Additional visual options */
  [key: string]: unknown;
}

/** Unified scene interface with frame-accurate timing */
export interface UnifiedScene {
  id: string;
  name?: string;
  type: SceneType | string;
  title?: string;
  text?: string;

  // Duration in seconds (from YAML)
  duration?: number;

  // Frame-accurate timing (from props.json)
  startFrame?: number;
  endFrame?: number;
  durationFrames?: number;

  // Content
  voiceover?: string;
  visual?: SceneVisual;

  // Demo clip for scene
  demo?: {
    state: string;
    clipPath: string;
  };
}

/** Legacy scene interface (for backward compatibility) */
export interface VideoScene {
  id: string;
  name: string;
  type: string;
  duration: number;
  voiceover?: string;
  visual?: Record<string, unknown>;
}

// ============================================================================
// Script Types
// ============================================================================

export interface VideoScript {
  title: string;
  description?: string;
  language: string;
  scenes: VideoScene[];
  narrator?: {
    voice: string;
    speed: number;
  };
  output?: {
    resolution: { width: number; height: number };
    framerate: number;
    filename: string;
  };
  settings?: {
    fps?: number;
    width?: number;
    height?: number;
    background?: string;
  };
  metadata?: {
    version?: string;
    author?: string;
    description?: string;
  };
}

// ============================================================================
// Props Types (Remotion)
// ============================================================================

/** Props JSON structure generated for Remotion */
export interface VideoProps {
  title: string;
  name: string;
  language: string;
  duration: number;
  fps: number;
  width: number;
  height: number;
  quality: 'preview' | 'production';
  is_releasable: boolean;
  resolution: {
    width: number;
    height: number;
  };
  scenes: UnifiedScene[];
}

/** Quality presets for video rendering */
export type VideoQuality = 'preview' | 'production';

export interface QualityPreset {
  id: VideoQuality;
  name: string;
  description: string;
  width: number;
  height: number;
  fps: number;
  crf: number;
  estimatedTime: string;
}

export const QUALITY_PRESETS: Record<VideoQuality, QualityPreset> = {
  preview: {
    id: 'preview',
    name: 'Preview',
    description: 'Fast render for review (720p, 24fps)',
    width: 1280,
    height: 720,
    fps: 24,
    crf: 28,
    estimatedTime: '~30 seconds',
  },
  production: {
    id: 'production',
    name: 'Production',
    description: 'Full quality for release (1080p, 60fps)',
    width: 1920,
    height: 1080,
    fps: 60,
    crf: 18,
    estimatedTime: '~5 minutes',
  },
};

export interface VideoInfo {
  hasVideo: boolean;
  hasAudio: boolean;
  hasCaptions: boolean;
  hasProps: boolean;
  videoUrl?: string;
  audioUrl?: string;
  captionsUrl?: string;
  duration?: number;
  fps?: number;
  sceneTiming?: Array<{
    id: string;
    startTime: number;
    endTime: number;
  }>;
}

export interface SceneNote {
  text: string;
  created: string;
  scene_id: string;
}

export interface SceneNotesResponse {
  notes: Record<string, SceneNote[]>;
}

export interface VoiceoverStatus {
  scenes: Array<{
    id: string;
    name: string;
    status: 'pending' | 'generating' | 'complete' | 'error';
    audio_path?: string;
    duration?: number;
  }>;
  total: number;
  completed: number;
  in_progress: number;
}

export interface RenderStatus {
  status: 'idle' | 'rendering' | 'complete' | 'error';
  progress: number;
  currentScene?: string;
  outputPath?: string;
  error?: string;
}
