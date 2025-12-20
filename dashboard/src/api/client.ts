import axios from 'axios';
import type {
  Project,
  ProjectStatus,
  Document,
  DocumentContent,
  TranslationMatrix,
  QualityIssue,
  FreshnessResponse,
  InsightsResponse,
  BuildStatus,
  AuditLogEntry,
  RecentProjectsResponse,
  OpenProjectResponse,
  BrowseProjectResponse,
  VideoInfo,
  VideoScript,
} from './types';

export interface FileResponse {
  path: string;
  filename: string;
  content: string;
  parsed?: VideoScript;
  video?: VideoInfo;
}

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Project
export const getProject = () => api.get<Project>('/project').then(r => r.data);
export const getStatus = () => api.get<ProjectStatus>('/status').then(r => r.data);

// Documents
export const getDocuments = (language: string) =>
  api.get<{ documents: Document[] }>(`/documents/${language}`).then(r => {
    // Transform flat document list into categories
    const categories: Record<string, Document[]> = {};
    for (const doc of r.data.documents || []) {
      const category = doc.type || 'other';
      if (!categories[category]) {
        categories[category] = [];
      }
      categories[category].push(doc);
    }
    return { categories };
  });

export const getDocument = (path: string) =>
  api.get<DocumentContent>('/document', { params: { path } }).then(r => r.data);

export const saveDocument = (path: string, content: string, metadata?: Record<string, unknown>) =>
  api.post<{ status: string; path: string }>('/document', { content, metadata }, { params: { path } }).then(r => r.data);

export const getFile = (path: string) =>
  api.get<FileResponse>('/file', { params: { path } }).then(r => r.data);

// Translations
export const getTranslations = () =>
  api.get<{ pairs: unknown[] }>('/translations').then(r => r.data);

export const getTranslationMatrix = () =>
  api.get<TranslationMatrix>('/translations/matrix').then(r => r.data);

// Quality
export const getQuality = () =>
  api.get<{ issues: QualityIssue[] }>('/quality').then(r => r.data);

// Freshness
export const getFreshness = () =>
  api.get<FreshnessResponse>('/freshness').then(r => r.data);

// Insights
export const getInsights = () =>
  api.get<InsightsResponse>('/insights').then(r => r.data);

export const getInsightsPath = (type: string) =>
  api.get<unknown>('/insights/path', { params: { type } }).then(r => r.data);

// Build
export const getBuildStatus = () =>
  api.get<BuildStatus>('/build/status').then(r => r.data);

export const triggerBuild = (options: {
  formats: string[];
  languages: string[];
}) => api.post<{ status: string; message: string }>('/build', options).then(r => r.data);

// Audit Log
export const getAuditLog = (limit = 50) =>
  api.get<{ entries: AuditLogEntry[] }>('/audit-log', { params: { limit } }).then(r => r.data);

// Media
export const getMedia = () =>
  api.get<{ files: unknown[] }>('/media').then(r => r.data);

// Search
export const search = (query: string) =>
  api.get<{ results: unknown[] }>('/search', { params: { q: query } }).then(r => r.data);

// Scene Notes
export const getSceneNotes = (scriptPath: string) =>
  api.get<{ notes: Record<string, { text: string; created: string }> }>(
    `/scene-notes/${encodeURIComponent(scriptPath)}`
  ).then(r => r.data);

export const saveSceneNote = (scriptPath: string, sceneId: string, note: string) =>
  api.post(`/scene-notes/${encodeURIComponent(scriptPath)}`, { scene_id: sceneId, note }).then(r => r.data);

// Project Switching
export const getRecentProjects = () =>
  api.get<RecentProjectsResponse>('/recent-projects').then(r => r.data);

export const openProject = (path: string) =>
  api.post<OpenProjectResponse>('/open-project', null, { params: { path } }).then(r => r.data);

export const browseProject = () =>
  api.post<BrowseProjectResponse>('/browse-project').then(r => r.data);

export const removeRecentProject = (path: string) =>
  api.delete('/recent-projects', { params: { path } }).then(r => r.data);

// AI Processing
export interface AIContentSelection {
  path: string;
  content: string;
  title: string;
  content_type: string;
  target_id?: string;
  notes?: Array<{ text: string; priority: string }>;
  metadata?: Record<string, unknown>;
}

export interface AIProcessRequest {
  operation: string;
  selections: AIContentSelection[];
  instructions: string;
  target_language?: string;
  options?: Record<string, unknown>;
}

export interface AIProcessResponse {
  request_id: string;
  status: 'success' | 'error' | 'partial';
  results: Array<{
    path: string;
    original: string;
    processed: string;
    changes_summary: string;
  }>;
  usage?: { input_tokens: number; output_tokens: number };
  duration_ms: number;
  error?: string;
}

export interface AIConfig {
  configured: boolean;
  backend: 'anthropic' | 'claude_code';
  model: string;
  max_tokens: number;
  temperature: number;
  has_api_key: boolean;
}

export interface AIOperation {
  id: string;
  name: string;
  description: string;
}

export interface AIModel {
  id: string;
  name: string;
  description: string;
}

export interface AIBackend {
  id: string;
  name: string;
  description: string;
  requires_key: boolean;
}

export const getAIConfig = () =>
  api.get<AIConfig>('/ai/config').then(r => r.data);

export const updateAIConfig = (config: {
  api_key?: string;
  backend?: string;
  model?: string;
  max_tokens?: number;
  temperature?: number;
}) => api.post('/ai/config', config).then(r => r.data);

export const processAI = (request: AIProcessRequest) =>
  api.post<AIProcessResponse>('/ai/process', request).then(r => r.data);

export const getAIOperations = () =>
  api.get<{ operations: AIOperation[] }>('/ai/operations').then(r => r.data);

export const getAIModels = () =>
  api.get<{ models: AIModel[] }>('/ai/models').then(r => r.data);

export const getAIBackends = () =>
  api.get<{ backends: AIBackend[] }>('/ai/backends').then(r => r.data);

// AI Task Queue (Claude Code Integration)
export interface AITaskSelection {
  path: string;
  title: string;
  notes_count: number;
}

export interface AITask {
  id: string;
  operation: string;
  status: 'pending' | 'claimed' | 'processing' | 'completed' | 'failed';
  priority: 'low' | 'normal' | 'high' | 'urgent';
  instructions: string;
  selections: AITaskSelection[];
  created_at: string;
  completed_at?: string;
  summary?: string;
  files_modified?: string[];
  error?: string;
}

export interface AITaskSubmitRequest {
  operation: string;
  selections: AIContentSelection[];
  instructions: string;
  priority?: string;
  target_language?: string;
}

export interface AITaskSubmitResponse {
  task_id: string;
  status: string;
  operation: string;
  selections_count: number;
  priority: string;
  created_at: string;
}

export interface AITasksResponse {
  tasks: AITask[];
  total: number;
  stats: {
    total: number;
    pending: number;
    claimed: number;
    processing: number;
    completed: number;
    failed: number;
  };
}

export const submitAITask = (request: AITaskSubmitRequest) =>
  api.post<AITaskSubmitResponse>('/ai/tasks', request).then(r => r.data);

export const getAITasks = (status?: string, limit?: number) =>
  api.get<AITasksResponse>('/ai/tasks', { params: { status, limit } }).then(r => r.data);

export const getAITask = (taskId: string) =>
  api.get<AITask>('/ai/tasks/' + taskId).then(r => r.data);

export const cancelAITask = (taskId: string) =>
  api.post<{ status: string; task_id: string }>('/ai/tasks/' + taskId + '/cancel').then(r => r.data);

export const deleteAITask = (taskId: string) =>
  api.delete<{ status: string; task_id: string }>('/ai/tasks/' + taskId).then(r => r.data);

export const getAIQueueStats = () =>
  api.get<AITasksResponse['stats']>('/ai/queue/stats').then(r => r.data);

export default api;
