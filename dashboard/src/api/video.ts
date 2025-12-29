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
