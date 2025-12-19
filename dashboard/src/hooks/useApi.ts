import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from '@/api/client';

// Query Keys
export const queryKeys = {
  project: ['project'] as const,
  status: ['status'] as const,
  documents: (lang: string) => ['documents', lang] as const,
  document: (path: string) => ['document', path] as const,
  file: (path: string) => ['file', path] as const,
  translations: ['translations'] as const,
  translationMatrix: ['translationMatrix'] as const,
  quality: ['quality'] as const,
  freshness: ['freshness'] as const,
  insights: ['insights'] as const,
  insightsPath: (type: string) => ['insightsPath', type] as const,
  buildStatus: ['buildStatus'] as const,
  auditLog: ['auditLog'] as const,
  media: ['media'] as const,
  sceneNotes: (path: string) => ['sceneNotes', path] as const,
};

// Project Hooks
export const useProject = () =>
  useQuery({
    queryKey: queryKeys.project,
    queryFn: api.getProject,
  });

export const useStatus = () =>
  useQuery({
    queryKey: queryKeys.status,
    queryFn: api.getStatus,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

// Document Hooks
export const useDocuments = (language: string) =>
  useQuery({
    queryKey: queryKeys.documents(language),
    queryFn: () => api.getDocuments(language),
    enabled: !!language,
  });

export const useDocument = (path: string) =>
  useQuery({
    queryKey: queryKeys.document(path),
    queryFn: () => api.getDocument(path),
    enabled: !!path,
  });

export const useFile = (path: string) =>
  useQuery({
    queryKey: queryKeys.file(path),
    queryFn: () => api.getFile(path),
    enabled: !!path,
  });

// Translation Hooks
export const useTranslations = () =>
  useQuery({
    queryKey: queryKeys.translations,
    queryFn: api.getTranslations,
  });

export const useTranslationMatrix = () =>
  useQuery({
    queryKey: queryKeys.translationMatrix,
    queryFn: api.getTranslationMatrix,
  });

// Quality Hooks
export const useQuality = () =>
  useQuery({
    queryKey: queryKeys.quality,
    queryFn: api.getQuality,
  });

// Freshness Hooks
export const useFreshness = () =>
  useQuery({
    queryKey: queryKeys.freshness,
    queryFn: api.getFreshness,
  });

// Insights Hooks
export const useInsights = () =>
  useQuery({
    queryKey: queryKeys.insights,
    queryFn: api.getInsights,
  });

export const useInsightsPath = (type: string) =>
  useQuery({
    queryKey: queryKeys.insightsPath(type),
    queryFn: () => api.getInsightsPath(type),
    enabled: !!type,
  });

// Build Hooks
export const useBuildStatus = () =>
  useQuery({
    queryKey: queryKeys.buildStatus,
    queryFn: api.getBuildStatus,
  });

export const useBuild = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.triggerBuild,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.buildStatus });
    },
  });
};

// Audit Log Hook
export const useAuditLog = (limit = 50) =>
  useQuery({
    queryKey: queryKeys.auditLog,
    queryFn: () => api.getAuditLog(limit),
  });

// Media Hook
export const useMedia = () =>
  useQuery({
    queryKey: queryKeys.media,
    queryFn: api.getMedia,
  });

// Scene Notes Hooks
export const useSceneNotes = (scriptPath: string) =>
  useQuery({
    queryKey: queryKeys.sceneNotes(scriptPath),
    queryFn: () => api.getSceneNotes(scriptPath),
    enabled: !!scriptPath,
  });

export const useSaveSceneNote = (scriptPath: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ sceneId, note }: { sceneId: string; note: string }) =>
      api.saveSceneNote(scriptPath, sceneId, note),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.sceneNotes(scriptPath) });
    },
  });
};
