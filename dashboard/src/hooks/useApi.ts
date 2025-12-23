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

export const useSaveDocument = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ path, content, metadata }: { path: string; content: string; metadata?: Record<string, unknown> }) =>
      api.saveDocument(path, content, metadata),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.document(variables.path) });
      queryClient.invalidateQueries({ queryKey: queryKeys.file(variables.path) });
    },
  });
};

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

// Project Switching Hooks
export const useRecentProjects = () =>
  useQuery({
    queryKey: ['recentProjects'] as const,
    queryFn: api.getRecentProjects,
  });

export const useOpenProject = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.openProject,
    onSuccess: () => {
      // Invalidate all queries when project changes
      queryClient.invalidateQueries();
    },
  });
};

export const useBrowseProject = () => {
  return useMutation({
    mutationFn: api.browseProject,
  });
};

// ============== ADVANCED ANALYSIS HOOKS ==============

export const useAdvancedInsights = () =>
  useQuery({
    queryKey: ['advancedInsights'] as const,
    queryFn: api.getAdvancedInsights,
    staleTime: 1000 * 60 * 5, // 5 minutes - heavy computation
  });

export const useQualitySummary = () =>
  useQuery({
    queryKey: ['qualitySummary'] as const,
    queryFn: api.getQualitySummary,
    staleTime: 1000 * 60 * 2, // 2 minutes
  });

export const useSemanticAnalysis = (options?: Parameters<typeof api.getSemanticAnalysis>[0]) =>
  useQuery({
    queryKey: ['semanticAnalysis', options] as const,
    queryFn: () => api.getSemanticAnalysis(options),
    staleTime: 1000 * 60 * 5,
    enabled: true,
  });

export const useKnowledgeGraph = (options?: Parameters<typeof api.getKnowledgeGraph>[0]) =>
  useQuery({
    queryKey: ['knowledgeGraph', options] as const,
    queryFn: () => api.getKnowledgeGraph(options),
    staleTime: 1000 * 60 * 5,
    enabled: true,
  });

export const useNorwegianReadability = (options?: Parameters<typeof api.getNorwegianReadability>[0]) =>
  useQuery({
    queryKey: ['norwegianReadability', options] as const,
    queryFn: () => api.getNorwegianReadability(options),
    staleTime: 1000 * 60 * 5,
    enabled: true,
  });

export const usePredictiveFreshness = (options?: Parameters<typeof api.getPredictiveFreshness>[0]) =>
  useQuery({
    queryKey: ['predictiveFreshness', options] as const,
    queryFn: () => api.getPredictiveFreshness(options),
    staleTime: 1000 * 60 * 5,
    enabled: true,
  });

export const useEnhancedCodeSync = (options?: Parameters<typeof api.getEnhancedCodeSync>[0]) =>
  useQuery({
    queryKey: ['enhancedCodeSync', options] as const,
    queryFn: () => api.getEnhancedCodeSync(options),
    staleTime: 1000 * 60 * 5,
    enabled: true,
  });

export const useAdvancedAnalysis = (options?: Parameters<typeof api.getAdvancedAnalysis>[0]) =>
  useQuery({
    queryKey: ['advancedAnalysis', options] as const,
    queryFn: () => api.getAdvancedAnalysis(options),
    staleTime: 1000 * 60 * 5,
    enabled: true,
  });

// ============== HIERARCHY HOOKS ==============

export const useHierarchyTree = (language?: string) =>
  useQuery({
    queryKey: ['hierarchyTree', language] as const,
    queryFn: () => api.getHierarchyTree(language),
    staleTime: 1000 * 60 * 2,
  });

export const useHierarchyNode = (path: string) =>
  useQuery({
    queryKey: ['hierarchyNode', path] as const,
    queryFn: () => api.getHierarchyNode(path),
    enabled: !!path,
  });

export const useBreadcrumbs = (path: string) =>
  useQuery({
    queryKey: ['breadcrumbs', path] as const,
    queryFn: () => api.getBreadcrumbs(path),
    enabled: !!path,
  });

export const useDerivationGraph = () =>
  useQuery({
    queryKey: ['derivationGraph'] as const,
    queryFn: () => api.getDerivationGraph(),
    staleTime: 1000 * 60 * 2,
  });

export const useFlowGraph = (options?: Parameters<typeof api.getFlowGraph>[0]) =>
  useQuery({
    queryKey: ['flowGraph', options] as const,
    queryFn: () => api.getFlowGraph(options),
    staleTime: 1000 * 60 * 2,
  });

// ============== BRAND VOICE HOOKS ==============

export const useBrandVoice = (options?: Parameters<typeof api.getBrandVoice>[0]) =>
  useQuery({
    queryKey: ['brandVoice', options] as const,
    queryFn: () => api.getBrandVoice(options),
    staleTime: 1000 * 60 * 5,
  });

export const useVoiceCheck = () =>
  useQuery({
    queryKey: ['voiceCheck'] as const,
    queryFn: api.checkVoiceAll,
    staleTime: 1000 * 60 * 2,
  });

export const useVoiceCheckDocument = (documentPath: string) =>
  useQuery({
    queryKey: ['voiceCheckDocument', documentPath] as const,
    queryFn: () => api.checkVoiceDocument(documentPath),
    enabled: !!documentPath,
  });

export const useTerminologyCheck = () =>
  useQuery({
    queryKey: ['terminologyCheck'] as const,
    queryFn: api.checkTerminology,
    staleTime: 1000 * 60 * 2,
  });

export const useVoiceContext = (documentPath: string) =>
  useQuery({
    queryKey: ['voiceContext', documentPath] as const,
    queryFn: () => api.getVoiceContext(documentPath),
    enabled: !!documentPath,
  });

// ============== BRAND ASSETS HOOKS ==============

export const useBrandAssets = () =>
  useQuery({
    queryKey: ['brandAssets'] as const,
    queryFn: api.getBrandAssets,
    staleTime: 1000 * 60 * 5,
  });

export const useBrandFiles = () =>
  useQuery({
    queryKey: ['brandFiles'] as const,
    queryFn: api.getBrandFiles,
    staleTime: 1000 * 60 * 2,
  });

export const useBrandFile = (path: string) =>
  useQuery({
    queryKey: ['brandFile', path] as const,
    queryFn: () => api.getBrandFile(path),
    enabled: !!path,
  });

export const useBrandNotes = () =>
  useQuery({
    queryKey: ['brandNotes'] as const,
    queryFn: api.getBrandNotes,
    staleTime: 1000 * 60,
  });

export const useAddBrandNote = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.addBrandNote,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['brandNotes'] });
    },
  });
};

export const useUpdateBrandNote = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ noteId, ...params }: { noteId: string; text?: string; status?: string; priority?: string }) =>
      api.updateBrandNote(noteId, params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['brandNotes'] });
    },
  });
};

export const useDeleteBrandNote = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.deleteBrandNote,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['brandNotes'] });
    },
  });
};

export const useBrandGuide = () =>
  useQuery({
    queryKey: ['brandGuide'] as const,
    queryFn: api.getBrandGuide,
    staleTime: 1000 * 60 * 5,
  });
