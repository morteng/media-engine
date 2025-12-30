/**
 * Video API module - centralized API functions for video production
 * Extracted from VideoProduction.tsx for reusability
 */

import type {
  VideoScriptsResponse,
  VideoScriptDetail,
  RenderJob,
  RenderQueueResponse,
  VideoAssetsResponse,
  MotionComponentsResponse,
} from './types';
import type { VideoProps } from './types/video';

// Re-export types for convenience
export type {
  VideoScriptsResponse,
  VideoScriptDetail,
  RenderJob,
  RenderQueueResponse,
  VideoAssetsResponse,
  MotionComponentsResponse,
  VideoProps,
};

// API Functions

/**
 * Get list of all video scripts
 */
export async function getVideoScripts(): Promise<VideoScriptsResponse> {
  const res = await fetch('/api/video/scripts');
  if (!res.ok) throw new Error('Failed to fetch scripts');
  return res.json();
}

/**
 * Get a single video script by ID
 */
export async function getVideoScript(scriptId: string): Promise<VideoScriptDetail> {
  const res = await fetch(`/api/video/scripts/${scriptId}`);
  if (!res.ok) throw new Error('Failed to fetch script');
  return res.json();
}

/**
 * Update a video script's content
 */
export async function updateVideoScript(params: {
  scriptId: string;
  content: string;
}): Promise<VideoScriptDetail> {
  const res = await fetch(`/api/video/scripts/${params.scriptId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content: params.content }),
  });
  if (!res.ok) throw new Error('Failed to update script');
  return res.json();
}

/**
 * Create a new video script
 */
export async function createVideoScript(params: {
  name: string;
  content: string;
}): Promise<VideoScriptDetail> {
  const res = await fetch('/api/video/scripts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error('Failed to create script');
  return res.json();
}

/**
 * Delete a video script
 */
export async function deleteVideoScript(scriptId: string): Promise<void> {
  const res = await fetch(`/api/video/scripts/${scriptId}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete script');
}

/**
 * Duplicate a video script
 */
export async function duplicateVideoScript(params: {
  sourceId: string;
  newName: string;
}): Promise<VideoScriptDetail> {
  const res = await fetch(`/api/video/scripts/${params.sourceId}/duplicate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: params.newName }),
  });
  if (!res.ok) throw new Error('Failed to duplicate script');
  return res.json();
}

/**
 * Start a video render job
 */
export async function startRender(params: {
  scriptId: string;
  quality: string;
}): Promise<RenderJob> {
  const res = await fetch('/api/video/render', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ script_id: params.scriptId, quality: params.quality }),
  });
  if (!res.ok) throw new Error('Failed to start render');
  return res.json();
}

/**
 * Get the render queue
 */
export async function getRenderQueue(): Promise<RenderQueueResponse> {
  const res = await fetch('/api/video/queue');
  if (!res.ok) throw new Error('Failed to fetch queue');
  return res.json();
}

/**
 * Download a rendered video
 */
export async function downloadRender(jobId: string): Promise<{ download_url?: string }> {
  const res = await fetch(`/api/video/render/${jobId}/download`);
  if (!res.ok) throw new Error('Failed to get download URL');
  const data = await res.json();
  // Trigger download
  if (data.download_url) {
    window.open(data.download_url, '_blank');
  }
  return data;
}

/**
 * Get video assets (demos, audio, graphics)
 */
export async function getVideoAssets(): Promise<VideoAssetsResponse> {
  const res = await fetch('/api/video/assets');
  if (!res.ok) throw new Error('Failed to fetch assets');
  return res.json();
}

/**
 * Get motion components for Remotion
 */
export async function getMotionComponents(): Promise<MotionComponentsResponse> {
  const res = await fetch('/api/video/components');
  if (!res.ok) throw new Error('Failed to fetch components');
  return res.json();
}

/**
 * Get generated Remotion props for a script
 * Returns the props.json data with scene timing information
 */
export async function getVideoProps(scriptId: string): Promise<VideoProps> {
  const res = await fetch(`/api/video/scripts/${scriptId}/props`);
  if (!res.ok) throw new Error('Failed to fetch props');
  const data = await res.json();
  return data.props;
}

/**
 * Get captions file for a script
 */
export async function getVideoCaptions(scriptId: string): Promise<string> {
  const res = await fetch(`/api/video/scripts/${scriptId}/captions`);
  if (!res.ok) throw new Error('Failed to fetch captions');
  const data = await res.json();
  return data.content;
}

// ============================================================================
// Voiceover Generation
// ============================================================================

export type VoiceoverMode = 'mock' | 'macos' | 'elevenlabs';

export interface VoiceoverStatus {
  has_voiceover: boolean;
  has_props: boolean;
  audio_path: string | null;
  audio_size: number | null;
  audio_modified: string | null;
}

export interface VoiceoverGenerateResponse {
  status: 'generating' | 'exists';
  job_id?: string;
  audio_path: string;
  message?: string;
}

/**
 * Get voiceover status for a script
 */
export async function getVoiceoverStatus(scriptId: string): Promise<VoiceoverStatus> {
  const res = await fetch(`/api/video/scripts/${scriptId}/voiceover/status`);
  if (!res.ok) throw new Error('Failed to get voiceover status');
  return res.json();
}

/**
 * Generate voiceover for a script
 */
export async function generateVoiceover(params: {
  scriptId: string;
  mode?: VoiceoverMode;
  force?: boolean;
}): Promise<VoiceoverGenerateResponse> {
  const res = await fetch(`/api/video/scripts/${params.scriptId}/voiceover`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      mode: params.mode || 'mock',
      force: params.force || false,
    }),
  });
  if (!res.ok) throw new Error('Failed to generate voiceover');
  return res.json();
}

// ============================================================================
// Camera Presets & Effects
// ============================================================================

export interface CameraPreset {
  id: string;
  name: string;
  description: string;
  pattern: string;
  default_zoom: number;
  default_duration: number;
  default_hold: number;
  default_easing: string;
  start_zoom: number;
  end_zoom: number;
}

export interface CameraPresetsResponse {
  presets: CameraPreset[];
  count: number;
}

export interface CameraEasing {
  name: string;
  recommended: boolean;
}

export interface CameraEasingsResponse {
  easings: CameraEasing[];
  count: number;
  recommended: string;
}

export interface EffectsPreset {
  id: string;
  name: string;
  description: string;
  vignette_enabled: boolean;
  shake_enabled: boolean;
  perspective_enabled: boolean;
  depth_of_field_enabled: boolean;
  motion_blur_enabled: boolean;
}

export interface EffectsPresetsResponse {
  presets: EffectsPreset[];
  count: number;
}

/**
 * Get available camera animation presets
 */
export async function getCameraPresets(): Promise<CameraPresetsResponse> {
  const res = await fetch('/api/video/camera/presets');
  if (!res.ok) throw new Error('Failed to fetch camera presets');
  return res.json();
}

/**
 * Get available camera easing functions
 */
export async function getCameraEasings(): Promise<CameraEasingsResponse> {
  const res = await fetch('/api/video/camera/easings');
  if (!res.ok) throw new Error('Failed to fetch camera easings');
  return res.json();
}

/**
 * Get available visual effects presets
 */
export async function getEffectsPresets(): Promise<EffectsPresetsResponse> {
  const res = await fetch('/api/video/effects/presets');
  if (!res.ok) throw new Error('Failed to fetch effects presets');
  return res.json();
}

// ============================================================================
// Demo Recordings (for Demo Recorder page)
// ============================================================================

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
    keyframes?: Array<{
      frame: number;
      centerX: number;
      centerY: number;
      zoom: number;
      easing?: string;
      holdFrames?: number;
    }>;
  };
}

export interface DemoRecordingSequence {
  id: string;
  description?: string;
  states: string[];
  transition_delay?: number;
}

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

export interface DemoRecordingsResponse {
  demos: DemoRecording[];
  count: number;
}

export interface DemoRecordingContentResponse {
  id: string;
  content: string;
  path: string;
  error?: string;
}

/**
 * Get list of all demo recordings
 */
export async function getDemoRecordings(): Promise<DemoRecordingsResponse> {
  const res = await fetch('/api/video/demos');
  if (!res.ok) throw new Error('Failed to fetch demo recordings');
  return res.json();
}

/**
 * Get a single demo recording with full details
 */
export async function getDemoRecording(
  demoId: string,
  language = 'en'
): Promise<DemoRecordingDetail> {
  const res = await fetch(`/api/video/demos/${demoId}?language=${language}`);
  if (!res.ok) throw new Error('Failed to fetch demo recording');
  return res.json();
}

/**
 * Get raw YAML content for a demo recording
 */
export async function getDemoRecordingContent(
  demoId: string,
  language = 'en'
): Promise<DemoRecordingContentResponse> {
  const res = await fetch(`/api/video/demos/${demoId}/content?language=${language}`);
  if (!res.ok) throw new Error('Failed to fetch demo recording content');
  return res.json();
}

/**
 * Capture screenshots for demo states
 */
export async function captureDemoScreenshots(
  demoId: string,
  options?: {
    language?: string;
    states?: string[];
  }
): Promise<{
  demo_id: string;
  captured: Array<{
    state_id: string;
    path: string;
    url: string;
    has_camera_data?: boolean;
    keyframes?: number;
  }>;
  errors: Array<{ state_id: string; error: string }>;
  total_captured: number;
}> {
  const params = new URLSearchParams();
  if (options?.language) params.set('language', options.language);

  const res = await fetch(`/api/video/demos/${demoId}/capture-screenshots?${params}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: options?.states ? JSON.stringify({ states: options.states }) : undefined,
  });
  if (!res.ok) throw new Error('Failed to capture screenshots');
  return res.json();
}

/**
 * Camera keyframe with resolved pixel coordinates
 */
export interface CameraKeyframe {
  frame: number;
  centerX: number;
  centerY: number;
  zoom: number;
  easing?: string;
  holdFrames?: number;
}

/**
 * Pre-computed camera data for a demo state
 */
export interface DemoStateCameraData {
  state_id: string;
  has_data: boolean;
  mode?: string;
  capture_scale?: number;
  background?: string;
  shadow?: boolean;
  viewport_width?: number;
  viewport_height?: number;
  fps?: number;
  total_frames?: number;
  keyframes?: CameraKeyframe[];
  element_bounds?: Record<string, {
    x: number;
    y: number;
    width: number;
    height: number;
    centerX: number;
    centerY: number;
  }>;
  effects?: Record<string, unknown>;
}

/**
 * Get pre-computed camera data for a demo state
 *
 * Returns keyframes with resolved pixel coordinates for camera animation.
 * This data is generated during screenshot capture and includes element
 * bounds extracted via Playwright.
 */
export async function getDemoStateCameraData(
  demoId: string,
  stateId: string,
  language = 'en'
): Promise<DemoStateCameraData> {
  const res = await fetch(
    `/api/video/demos/${demoId}/states/${stateId}/camera?language=${language}`
  );
  if (!res.ok) throw new Error('Failed to fetch camera data');
  return res.json();
}

// Default template for new scripts
export const DEFAULT_SCRIPT_TEMPLATE = `title: "New Video"
language: en

metadata:
  version: 1.0.0
  author: ""
  description: ""

settings:
  width: 1920
  height: 1080
  fps: 30

scenes:
  - id: intro
    type: title
    duration: 3
    content:
      title: "Welcome"
      subtitle: "Your video starts here"

  - id: main
    type: content
    duration: 10
    content:
      heading: "Main Content"
      body: "Add your content here"
`;

// ============================================================================
// Video Projects
// ============================================================================

export type ProjectStatus = 'draft' | 'in_review' | 'approved' | 'rendering' | 'published';
export type ComponentStatus = 'pending' | 'generating' | 'ready' | 'stale' | 'error';
export type ComponentType = 'script' | 'demo_definition' | 'demo_clip' | 'voiceover' | 'captions' | 'props' | 'render';

export interface VideoComponent {
  id: string;
  type: ComponentType;
  path: string;
  status: ComponentStatus;
  scene_id?: string;
  depends_on: string[];
  generated_at?: string;
  generated_by?: string;
  error_message?: string;
}

export interface VideoProject {
  id: string;
  name: string;
  language: string;
  status: ProjectStatus;
  script_path?: string;
  demo_definition_path?: string;
  source_documents: string[];
  components: Record<string, VideoComponent>;
  progress: number;
  is_complete: boolean;
  created_at: string;
  modified_at: string;
  metadata: Record<string, unknown>;
}

export interface VideoProjectSummary {
  id: string;
  name: string;
  language: string;
  status: ProjectStatus;
  components_count: number;
  progress: number;
  created_at: string;
  modified_at: string;
}

export interface VideoProjectsResponse {
  projects: VideoProjectSummary[];
  count: number;
}

export interface VideoProjectComponentsResponse {
  project_id: string;
  by_type: Record<ComponentType, VideoComponent[]>;
  total: number;
  ready: number;
  stale: number;
  pending: number;
}

export interface VideoProjectDependenciesResponse {
  project_id: string;
  nodes: Array<{
    id: string;
    type: ComponentType;
    status: ComponentStatus;
    scene_id?: string;
  }>;
  edges: Array<{
    from: string;
    to: string;
  }>;
  type_dependencies: Record<ComponentType, ComponentType[]>;
}

/**
 * Get list of all video projects
 */
export async function getVideoProjects(status?: ProjectStatus): Promise<VideoProjectsResponse> {
  const url = status ? `/api/video/projects?status=${status}` : '/api/video/projects';
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch video projects');
  return res.json();
}

/**
 * Create a new video project
 */
export async function createVideoProject(params: {
  name: string;
  language?: string;
  source_documents?: string[];
}): Promise<{ id: string; name: string; status: ProjectStatus; created_at: string }> {
  const res = await fetch('/api/video/projects', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: params.name,
      language: params.language || 'en',
      source_documents: params.source_documents || [],
    }),
  });
  if (!res.ok) throw new Error('Failed to create video project');
  return res.json();
}

/**
 * Get a video project by ID
 */
export async function getVideoProject(projectId: string): Promise<VideoProject> {
  const res = await fetch(`/api/video/projects/${projectId}`);
  if (!res.ok) throw new Error('Failed to fetch video project');
  return res.json();
}

/**
 * Update a video project
 */
export async function updateVideoProject(params: {
  projectId: string;
  name?: string;
  status?: ProjectStatus;
  metadata?: Record<string, unknown>;
}): Promise<{ status: string; message: string }> {
  const res = await fetch(`/api/video/projects/${params.projectId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: params.name,
      status: params.status,
      metadata: params.metadata,
    }),
  });
  if (!res.ok) throw new Error('Failed to update video project');
  return res.json();
}

/**
 * Delete a video project
 */
export async function deleteVideoProject(projectId: string): Promise<void> {
  const res = await fetch(`/api/video/projects/${projectId}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete video project');
}

/**
 * Get all components for a video project
 */
export async function getVideoProjectComponents(
  projectId: string
): Promise<VideoProjectComponentsResponse> {
  const res = await fetch(`/api/video/projects/${projectId}/components`);
  if (!res.ok) throw new Error('Failed to fetch project components');
  return res.json();
}

/**
 * Get the dependency graph for a video project
 */
export async function getVideoProjectDependencies(
  projectId: string
): Promise<VideoProjectDependenciesResponse> {
  const res = await fetch(`/api/video/projects/${projectId}/dependencies`);
  if (!res.ok) throw new Error('Failed to fetch project dependencies');
  return res.json();
}

/**
 * Mark a component for regeneration
 */
export async function regenerateVideoComponent(params: {
  projectId: string;
  componentId: string;
  cascade?: boolean;
}): Promise<{ status: string; affected_components: string[] }> {
  const url = `/api/video/projects/${params.projectId}/components/${params.componentId}/regenerate?cascade=${params.cascade ?? true}`;
  const res = await fetch(url, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to regenerate component');
  return res.json();
}

// ============================================================================
// Video Review Comments
// ============================================================================

export type CommentStatus = 'pending' | 'queued' | 'processing' | 'resolved' | 'rejected';
export type CommentPriority = 'low' | 'normal' | 'high' | 'urgent';

export interface VideoReviewComment {
  id: string;
  project_id: string;
  component_id: string;
  text: string;
  author: string;
  timestamp?: number;
  frame?: number;
  status: CommentStatus;
  priority: CommentPriority;
  ai_task_id?: string;
  resolution?: string;
  created_at: string;
  resolved_at?: string;
  resolved_by?: string;
  metadata: Record<string, unknown>;
}

export interface VideoCommentsResponse {
  comments: VideoReviewComment[];
  count: number;
  stats: {
    total: number;
    pending: number;
    queued: number;
    processing: number;
    resolved: number;
    rejected: number;
  };
}

/**
 * Get review comments for a video project
 */
export async function getVideoComments(
  projectId: string,
  options?: {
    status?: CommentStatus;
    include_resolved?: boolean;
  }
): Promise<VideoCommentsResponse> {
  const params = new URLSearchParams();
  if (options?.status) params.set('status', options.status);
  if (options?.include_resolved) params.set('include_resolved', 'true');

  const url = `/api/video/projects/${projectId}/comments${params.toString() ? `?${params}` : ''}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch comments');
  return res.json();
}

/**
 * Add a review comment to a video project component
 */
export async function addVideoComment(params: {
  projectId: string;
  componentId: string;
  text: string;
  author?: string;
  timestamp?: number;
  frame?: number;
  priority?: CommentPriority;
}): Promise<{ id: string; status: CommentStatus; created_at: string }> {
  const res = await fetch(`/api/video/projects/${params.projectId}/comments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      component_id: params.componentId,
      text: params.text,
      author: params.author || 'user',
      timestamp: params.timestamp,
      frame: params.frame,
      priority: params.priority || 'normal',
    }),
  });
  if (!res.ok) throw new Error('Failed to add comment');
  return res.json();
}

/**
 * Get a specific review comment
 */
export async function getVideoComment(
  projectId: string,
  commentId: string
): Promise<VideoReviewComment> {
  const res = await fetch(`/api/video/projects/${projectId}/comments/${commentId}`);
  if (!res.ok) throw new Error('Failed to fetch comment');
  return res.json();
}

/**
 * Delete a review comment
 */
export async function deleteVideoComment(projectId: string, commentId: string): Promise<void> {
  const res = await fetch(`/api/video/projects/${projectId}/comments/${commentId}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete comment');
}

/**
 * Queue a review comment for AI processing
 */
export async function queueVideoCommentForAI(
  projectId: string,
  commentId: string
): Promise<{ status: string; task_id: string }> {
  const res = await fetch(`/api/video/projects/${projectId}/comments/${commentId}/queue`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to queue comment');
  return res.json();
}

/**
 * Resolve a review comment
 */
export async function resolveVideoComment(params: {
  projectId: string;
  commentId: string;
  resolution: string;
  resolvedBy?: string;
}): Promise<{ status: string; resolved_at: string }> {
  const res = await fetch(
    `/api/video/projects/${params.projectId}/comments/${params.commentId}/resolve`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        resolution: params.resolution,
        resolved_by: params.resolvedBy || 'user',
      }),
    }
  );
  if (!res.ok) throw new Error('Failed to resolve comment');
  return res.json();
}

/**
 * Get all pending comments across all projects
 */
export async function getPendingVideoComments(): Promise<{
  comments: VideoReviewComment[];
  count: number;
}> {
  const res = await fetch('/api/video/comments/pending');
  if (!res.ok) throw new Error('Failed to fetch pending comments');
  return res.json();
}
