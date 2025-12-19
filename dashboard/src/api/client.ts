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
} from './types';

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
  api.get<{ categories: Record<string, Document[]> }>(`/documents/${language}`).then(r => r.data);

export const getDocument = (path: string) =>
  api.get<DocumentContent>('/document', { params: { path } }).then(r => r.data);

export const getFile = (path: string) =>
  api.get<{ path: string; filename: string; content: string; parsed?: unknown; video?: unknown }>(
    '/file',
    { params: { path } }
  ).then(r => r.data);

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

export default api;
