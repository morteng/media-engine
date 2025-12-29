/**
 * Video API hooks - React Query hooks for video production
 * Provides reusable data fetching and mutations for video features
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as videoApi from '@/api/video';
import type { VideoQuality } from '@/api/types/video';

// Query Keys for video-related data
export const videoQueryKeys = {
  scripts: ['videoScripts'] as const,
  script: (id: string) => ['videoScript', id] as const,
  props: (id: string) => ['videoProps', id] as const,
  captions: (id: string) => ['videoCaptions', id] as const,
  renderQueue: ['renderQueue'] as const,
  assets: ['videoAssets'] as const,
  motionComponents: ['motionComponents'] as const,
};

// ============================================================================
// Query Hooks
// ============================================================================

/**
 * Fetch all video scripts
 * Used in: Overview, Scripts, Render, Preview tabs
 */
export function useVideoScripts() {
  return useQuery({
    queryKey: videoQueryKeys.scripts,
    queryFn: videoApi.getVideoScripts,
  });
}

/**
 * Fetch a single video script by ID
 * Only fetches when scriptId is provided
 */
export function useVideoScript(scriptId: string | null) {
  return useQuery({
    queryKey: videoQueryKeys.script(scriptId || ''),
    queryFn: () => videoApi.getVideoScript(scriptId!),
    enabled: !!scriptId,
  });
}

/**
 * Fetch the render queue
 * @param options.polling - Enable automatic polling every 2 seconds
 */
export function useRenderQueue(options?: { polling?: boolean }) {
  return useQuery({
    queryKey: videoQueryKeys.renderQueue,
    queryFn: videoApi.getRenderQueue,
    refetchInterval: options?.polling ? 2000 : false,
  });
}

/**
 * Fetch video assets (demos, audio, graphics)
 */
export function useVideoAssets() {
  return useQuery({
    queryKey: videoQueryKeys.assets,
    queryFn: videoApi.getVideoAssets,
  });
}

/**
 * Fetch motion components for Remotion
 */
export function useMotionComponents() {
  return useQuery({
    queryKey: videoQueryKeys.motionComponents,
    queryFn: videoApi.getMotionComponents,
  });
}

/**
 * Fetch Remotion props for a script
 * Returns scene timing and configuration data
 */
export function useVideoProps(scriptId: string | null) {
  return useQuery({
    queryKey: videoQueryKeys.props(scriptId || ''),
    queryFn: () => videoApi.getVideoProps(scriptId!),
    enabled: !!scriptId,
  });
}

/**
 * Fetch captions (VTT) for a script
 */
export function useVideoCaptions(scriptId: string | null) {
  return useQuery({
    queryKey: videoQueryKeys.captions(scriptId || ''),
    queryFn: () => videoApi.getVideoCaptions(scriptId!),
    enabled: !!scriptId,
  });
}

// ============================================================================
// Mutation Hooks
// ============================================================================

/**
 * Hook providing all script-related mutations with automatic cache invalidation
 */
export function useScriptMutations() {
  const queryClient = useQueryClient();

  const invalidateScripts = () => {
    queryClient.invalidateQueries({ queryKey: videoQueryKeys.scripts });
  };

  const create = useMutation({
    mutationFn: videoApi.createVideoScript,
    onSuccess: invalidateScripts,
  });

  const update = useMutation({
    mutationFn: videoApi.updateVideoScript,
    onSuccess: (_data, variables) => {
      invalidateScripts();
      // Also invalidate the specific script
      queryClient.invalidateQueries({
        queryKey: videoQueryKeys.script(variables.scriptId)
      });
    },
  });

  const remove = useMutation({
    mutationFn: videoApi.deleteVideoScript,
    onSuccess: invalidateScripts,
  });

  const duplicate = useMutation({
    mutationFn: videoApi.duplicateVideoScript,
    onSuccess: invalidateScripts,
  });

  return { create, update, remove, duplicate };
}

/**
 * Hook for starting render jobs
 */
export function useRenderMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: videoApi.startRender,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: videoQueryKeys.renderQueue });
    },
  });
}

/**
 * Hook for downloading rendered videos
 */
export function useDownloadRender() {
  return useMutation({
    mutationFn: videoApi.downloadRender,
  });
}

// ============================================================================
// Combined hooks for common patterns
// ============================================================================

/**
 * Hook that provides all video data needed for the Overview tab
 */
export function useVideoOverviewData() {
  const scripts = useVideoScripts();
  const queue = useRenderQueue();
  const assets = useVideoAssets();

  return {
    scripts: scripts.data?.scripts || [],
    queue: queue.data?.jobs || [],
    assets: assets.data,
    isLoading: scripts.isLoading || queue.isLoading || assets.isLoading,
    error: scripts.error || queue.error || assets.error,
  };
}

/**
 * Hook that provides all video data needed for the Scripts tab
 */
export function useVideoScriptsData(selectedScriptId: string | null) {
  const scripts = useVideoScripts();
  const scriptDetail = useVideoScript(selectedScriptId);
  const mutations = useScriptMutations();

  return {
    scripts: scripts.data?.scripts || [],
    scriptsLoading: scripts.isLoading,
    scriptDetail: scriptDetail.data,
    detailLoading: scriptDetail.isLoading,
    ...mutations,
  };
}

/**
 * Hook that provides all video data needed for the Props tab
 */
export function useVideoPropsData(selectedScriptId: string | null) {
  const scripts = useVideoScripts();
  const props = useVideoProps(selectedScriptId);

  return {
    scripts: scripts.data?.scripts || [],
    scriptsLoading: scripts.isLoading,
    props: props.data,
    propsLoading: props.isLoading,
    propsError: props.error,
    refetchProps: props.refetch,
  };
}

/**
 * Hook that provides all video data needed for the Timeline tab
 */
export function useVideoTimelineData(selectedScriptId: string | null) {
  const scripts = useVideoScripts();
  const props = useVideoProps(selectedScriptId);
  const scriptDetail = useVideoScript(selectedScriptId);

  return {
    scripts: scripts.data?.scripts || [],
    scriptsLoading: scripts.isLoading,
    props: props.data,
    propsLoading: props.isLoading,
    scriptDetail: scriptDetail.data,
    detailLoading: scriptDetail.isLoading,
  };
}
