/**
 * Video API hooks - React Query hooks for video production
 * Provides reusable data fetching and mutations for video features
 */

import { useMemo } from 'react';
import { useQuery, useMutation, useQueryClient, useQueries } from '@tanstack/react-query';
import type { VideoChapter, ChapterTimelineData } from '@/api/types/video';
import * as videoApi from '@/api/video';

// Query Keys for video-related data
export const videoQueryKeys = {
  scripts: ['videoScripts'] as const,
  script: (id: string) => ['videoScript', id] as const,
  props: (id: string) => ['videoProps', id] as const,
  captions: (id: string) => ['videoCaptions', id] as const,
  voiceoverStatus: (id: string) => ['voiceoverStatus', id] as const,
  renderQueue: ['renderQueue'] as const,
  assets: ['videoAssets'] as const,
  motionComponents: ['motionComponents'] as const,
  cameraPresets: ['cameraPresets'] as const,
  cameraEasings: ['cameraEasings'] as const,
  effectsPresets: ['effectsPresets'] as const,
  // Demo recordings
  demoRecordings: ['demoRecordings'] as const,
  demoRecording: (id: string) => ['demoRecording', id] as const,
  demoRecordingContent: (id: string) => ['demoRecordingContent', id] as const,
  // Video Projects
  projects: ['videoProjects'] as const,
  project: (id: string) => ['videoProject', id] as const,
  projectComponents: (id: string) => ['videoProjectComponents', id] as const,
  projectDependencies: (id: string) => ['videoProjectDependencies', id] as const,
  projectComments: (id: string) => ['videoProjectComments', id] as const,
  pendingComments: ['videoPendingComments'] as const,
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
 * Fetch camera animation presets
 */
export function useCameraPresets() {
  return useQuery({
    queryKey: videoQueryKeys.cameraPresets,
    queryFn: videoApi.getCameraPresets,
    staleTime: 1000 * 60 * 5, // 5 minutes - presets don't change often
  });
}

/**
 * Fetch camera easing functions
 */
export function useCameraEasings() {
  return useQuery({
    queryKey: videoQueryKeys.cameraEasings,
    queryFn: videoApi.getCameraEasings,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

/**
 * Fetch visual effects presets
 */
export function useEffectsPresets() {
  return useQuery({
    queryKey: videoQueryKeys.effectsPresets,
    queryFn: videoApi.getEffectsPresets,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

// ============================================================================
// Demo Recording Hooks
// ============================================================================

/**
 * Fetch all demo recordings
 * Used in: Demo Recorder page
 */
export function useDemoRecordings() {
  return useQuery({
    queryKey: videoQueryKeys.demoRecordings,
    queryFn: videoApi.getDemoRecordings,
  });
}

/**
 * Fetch a single demo recording with full details
 * Returns states, sequences, and camera configurations
 */
export function useDemoRecording(demoId: string | null) {
  return useQuery({
    queryKey: videoQueryKeys.demoRecording(demoId || ''),
    queryFn: () => videoApi.getDemoRecording(demoId!),
    enabled: !!demoId,
  });
}

/**
 * Fetch raw YAML content for a demo recording
 * For editing in the YAML editor
 */
export function useDemoRecordingContent(demoId: string | null) {
  return useQuery({
    queryKey: videoQueryKeys.demoRecordingContent(demoId || ''),
    queryFn: () => videoApi.getDemoRecordingContent(demoId!),
    enabled: !!demoId,
  });
}

/**
 * Hook that provides all data needed for the Demo Recorder page
 */
export function useDemoRecorderData(selectedDemoId: string | null) {
  const demos = useDemoRecordings();
  const demoDetail = useDemoRecording(selectedDemoId);
  const demoContent = useDemoRecordingContent(selectedDemoId);

  return {
    demos: demos.data?.demos || [],
    demosLoading: demos.isLoading,
    demosError: demos.error,
    demoDetail: demoDetail.data,
    detailLoading: demoDetail.isLoading,
    demoContent: demoContent.data?.content,
    contentLoading: demoContent.isLoading,
    refetchDemos: demos.refetch,
    refetchDetail: demoDetail.refetch,
  };
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
 * Fetch voiceover status for a script
 * Returns info about whether voiceover exists and its metadata
 */
export function useVoiceoverStatus(scriptId: string | null) {
  return useQuery({
    queryKey: videoQueryKeys.voiceoverStatus(scriptId || ''),
    queryFn: () => videoApi.getVoiceoverStatus(scriptId!),
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
 * Hook for generating voiceover for a script
 * Supports mock, macos, and elevenlabs modes
 */
export function useGenerateVoiceover() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: videoApi.generateVoiceover,
    onSuccess: (_data, variables) => {
      // Invalidate voiceover status for this script
      queryClient.invalidateQueries({
        queryKey: videoQueryKeys.voiceoverStatus(variables.scriptId),
      });
      // Also invalidate props since they're regenerated with voiceover
      queryClient.invalidateQueries({
        queryKey: videoQueryKeys.props(variables.scriptId),
      });
      // And assets since audio is added
      queryClient.invalidateQueries({
        queryKey: videoQueryKeys.assets,
      });
    },
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

// ============================================================================
// Video Project Hooks
// ============================================================================

/**
 * Fetch all video projects
 */
export function useVideoProjects(status?: videoApi.ProjectStatus) {
  return useQuery({
    queryKey: [...videoQueryKeys.projects, status],
    queryFn: () => videoApi.getVideoProjects(status),
  });
}

/**
 * Fetch a single video project by ID
 */
export function useVideoProject(projectId: string | null) {
  return useQuery({
    queryKey: videoQueryKeys.project(projectId || ''),
    queryFn: () => videoApi.getVideoProject(projectId!),
    enabled: !!projectId,
  });
}

/**
 * Fetch components for a video project
 */
export function useVideoProjectComponents(projectId: string | null) {
  return useQuery({
    queryKey: videoQueryKeys.projectComponents(projectId || ''),
    queryFn: () => videoApi.getVideoProjectComponents(projectId!),
    enabled: !!projectId,
  });
}

/**
 * Fetch dependency graph for a video project
 */
export function useVideoProjectDependencies(projectId: string | null) {
  return useQuery({
    queryKey: videoQueryKeys.projectDependencies(projectId || ''),
    queryFn: () => videoApi.getVideoProjectDependencies(projectId!),
    enabled: !!projectId,
  });
}

/**
 * Hook providing all project-related mutations
 */
export function useVideoProjectMutations() {
  const queryClient = useQueryClient();

  const invalidateProjects = () => {
    queryClient.invalidateQueries({ queryKey: videoQueryKeys.projects });
  };

  const create = useMutation({
    mutationFn: videoApi.createVideoProject,
    onSuccess: invalidateProjects,
  });

  const update = useMutation({
    mutationFn: videoApi.updateVideoProject,
    onSuccess: (_data, variables) => {
      invalidateProjects();
      queryClient.invalidateQueries({
        queryKey: videoQueryKeys.project(variables.projectId),
      });
    },
  });

  const remove = useMutation({
    mutationFn: videoApi.deleteVideoProject,
    onSuccess: invalidateProjects,
  });

  const regenerateComponent = useMutation({
    mutationFn: videoApi.regenerateVideoComponent,
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: videoQueryKeys.projectComponents(variables.projectId),
      });
      queryClient.invalidateQueries({
        queryKey: videoQueryKeys.project(variables.projectId),
      });
    },
  });

  return { create, update, remove, regenerateComponent };
}

/**
 * Combined hook for video project list view
 */
export function useVideoProjectsData(status?: videoApi.ProjectStatus) {
  const projects = useVideoProjects(status);
  const mutations = useVideoProjectMutations();

  return {
    projects: projects.data?.projects || [],
    count: projects.data?.count || 0,
    isLoading: projects.isLoading,
    error: projects.error,
    refetch: projects.refetch,
    ...mutations,
  };
}

/**
 * Combined hook for video project detail view
 */
export function useVideoProjectDetail(projectId: string | null) {
  const project = useVideoProject(projectId);
  const components = useVideoProjectComponents(projectId);
  const dependencies = useVideoProjectDependencies(projectId);
  const mutations = useVideoProjectMutations();

  return {
    project: project.data,
    projectLoading: project.isLoading,
    projectError: project.error,
    components: components.data,
    componentsLoading: components.isLoading,
    dependencies: dependencies.data,
    dependenciesLoading: dependencies.isLoading,
    refetchProject: project.refetch,
    refetchComponents: components.refetch,
    ...mutations,
  };
}

// ============================================================================
// Video Comment Hooks
// ============================================================================

/**
 * Fetch comments for a video project
 */
export function useVideoComments(
  projectId: string | null,
  options?: { status?: videoApi.CommentStatus; include_resolved?: boolean }
) {
  return useQuery({
    queryKey: [...videoQueryKeys.projectComments(projectId || ''), options],
    queryFn: () => videoApi.getVideoComments(projectId!, options),
    enabled: !!projectId,
  });
}

/**
 * Hook providing all comment-related mutations
 */
export function useVideoCommentMutations(projectId: string | null) {
  const queryClient = useQueryClient();

  const invalidateComments = () => {
    if (projectId) {
      queryClient.invalidateQueries({
        queryKey: videoQueryKeys.projectComments(projectId),
      });
    }
    queryClient.invalidateQueries({
      queryKey: videoQueryKeys.pendingComments,
    });
  };

  const addComment = useMutation({
    mutationFn: videoApi.addVideoComment,
    onSuccess: invalidateComments,
  });

  const deleteComment = useMutation({
    mutationFn: (params: { projectId: string; commentId: string }) =>
      videoApi.deleteVideoComment(params.projectId, params.commentId),
    onSuccess: invalidateComments,
  });

  const queueForAI = useMutation({
    mutationFn: (params: { projectId: string; commentId: string }) =>
      videoApi.queueVideoCommentForAI(params.projectId, params.commentId),
    onSuccess: invalidateComments,
  });

  const resolveComment = useMutation({
    mutationFn: videoApi.resolveVideoComment,
    onSuccess: invalidateComments,
  });

  return { addComment, deleteComment, queueForAI, resolveComment };
}

/**
 * Combined hook for project review panel
 */
export function useVideoReviewData(
  projectId: string | null,
  options?: { status?: videoApi.CommentStatus; include_resolved?: boolean }
) {
  const comments = useVideoComments(projectId, options);
  const mutations = useVideoCommentMutations(projectId);

  return {
    comments: comments.data?.comments || [],
    stats: comments.data?.stats,
    count: comments.data?.count || 0,
    isLoading: comments.isLoading,
    error: comments.error,
    refetch: comments.refetch,
    ...mutations,
  };
}

// ============================================================================
// Unified Video Review Hooks
// ============================================================================

/**
 * Hook for chapter-aggregated video data with comments
 * Combines all video scripts into chapters with global frame offsets
 */
export function useChapterVideoData(projectId: string | null): {
  chapters: VideoChapter[];
  timelineData: ChapterTimelineData | null;
  isLoading: boolean;
  error: Error | null;
} {
  const scripts = useVideoScripts();
  const { comments } = useVideoReviewData(projectId, { include_resolved: true });

  // Get script IDs to fetch props for each
  const scriptIds = useMemo(() =>
    scripts.data?.scripts?.map(s => s.id) || [],
    [scripts.data]
  );

  // Fetch props for all scripts to get frame timing
  const propsQueries = useQueries({
    queries: scriptIds.map(id => ({
      queryKey: videoQueryKeys.props(id),
      queryFn: () => videoApi.getVideoProps(id),
      enabled: !!id,
      staleTime: 1000 * 60 * 5, // 5 minutes
    })),
  });

  // Build chapter data from scripts + props
  const chaptersData = useMemo((): ChapterTimelineData | null => {
    if (!scripts.data?.scripts || scripts.data.scripts.length === 0) {
      return null;
    }

    let globalFrameOffset = 0;
    let maxFps = 30; // Default FPS

    const chapters: VideoChapter[] = scripts.data.scripts.map((script, index) => {
      // Get corresponding props query result
      const propsQuery = propsQueries[index];
      const props = propsQuery?.data;

      // Use props data if available, otherwise estimate
      const fps = props?.fps || 30;
      const duration = props?.duration || script.duration || 60;
      const totalFrames = Math.ceil(duration * fps);
      const scenes = props?.scenes || [];

      maxFps = Math.max(maxFps, fps);

      // Get comments for this script/chapter
      const chapterComments = comments.filter(
        c => c.component_id === script.id
      );

      // Build video URL if output exists
      const scriptName = script.id.includes('/')
        ? script.id.split('/').pop()
        : script.id;
      const videoUrl = script.has_output
        ? `/api/video/asset?path=output/${script.language}/videos/${scriptName}.mp4`
        : null;
      const audioUrl = script.has_output
        ? `/api/video/asset?path=output/${script.language}/videos/${scriptName}.mp3`
        : null;

      const chapter: VideoChapter = {
        id: script.id,
        name: script.name || scriptName || script.id,
        scriptPath: script.path || script.id,
        language: script.language || 'en',
        duration,
        totalFrames,
        fps,
        videoUrl,
        audioUrl,
        scenes,
        startGlobalFrame: globalFrameOffset,
        endGlobalFrame: globalFrameOffset + totalFrames,
        comments: chapterComments,
        hasVideo: script.has_output || false,
        hasAudio: script.has_output || false,
      };

      globalFrameOffset += totalFrames;
      return chapter;
    });

    return {
      chapters,
      totalDuration: chapters.reduce((sum, c) => sum + c.duration, 0),
      totalFrames: globalFrameOffset,
      globalFps: maxFps,
    };
  }, [scripts.data, propsQueries, comments]);

  const isLoading = scripts.isLoading || propsQueries.some(q => q.isLoading);
  const error = scripts.error || propsQueries.find(q => q.error)?.error || null;

  return {
    chapters: chaptersData?.chapters || [],
    timelineData: chaptersData,
    isLoading,
    error: error as Error | null,
  };
}

/**
 * Utility: Convert global frame to chapter + local frame
 */
export function globalToLocalFrame(
  globalFrame: number,
  chapters: VideoChapter[]
): { chapter: VideoChapter; localFrame: number } | null {
  for (const chapter of chapters) {
    if (globalFrame >= chapter.startGlobalFrame && globalFrame < chapter.endGlobalFrame) {
      return {
        chapter,
        localFrame: globalFrame - chapter.startGlobalFrame,
      };
    }
  }
  // Return last chapter if past end
  if (chapters.length > 0) {
    const last = chapters[chapters.length - 1];
    return {
      chapter: last,
      localFrame: last.totalFrames - 1,
    };
  }
  return null;
}

/**
 * Utility: Convert chapter + local frame to global frame
 */
export function localToGlobalFrame(
  chapter: VideoChapter,
  localFrame: number
): number {
  return chapter.startGlobalFrame + localFrame;
}

/**
 * Utility: Format time as M:SS or H:MM:SS
 */
export function formatTime(seconds: number): string {
  const s = Math.floor(seconds);
  const mins = Math.floor(s / 60);
  const secs = s % 60;

  if (mins >= 60) {
    const hours = Math.floor(mins / 60);
    const remainingMins = mins % 60;
    return `${hours}:${remainingMins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  return `${mins}:${secs.toString().padStart(2, '0')}`;
}
