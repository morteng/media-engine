import axios from 'axios';
import type {
  Project,
  ProjectStatus,
  Document,
  DocumentContent,
  PublicationRef,
  PublicationsStatusResponse,
  PublicationTranslationsResponse,
  TranslationMatrix,
  QualityIssue,
  FreshnessResponse,
  InsightsResponse,
  BuildStatus,
  BuildStartResponse,
  BuildOutputsResponse,
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
  api.get<{ documents: Document[]; publications: PublicationRef[] }>(`/documents/${language}`).then(r => {
    // Group documents by publication first, then by type for orphans
    const categories: Record<string, Document[]> = {};
    const publications = r.data.publications || [];

    // First pass: group chapters by publication
    const publicationDocs: Record<string, Document[]> = {};
    const orphanChapters: Document[] = [];
    const otherDocs: Document[] = [];

    for (const doc of r.data.documents || []) {
      if (doc.type === 'chapter' && doc.publication) {
        // Chapter belongs to a publication
        const pubKey = doc.publication.key;
        if (!publicationDocs[pubKey]) {
          publicationDocs[pubKey] = [];
        }
        publicationDocs[pubKey].push(doc);
      } else if (doc.type === 'chapter') {
        // Orphan chapter (not in any publication)
        orphanChapters.push(doc);
      } else {
        // Non-chapter document
        otherDocs.push(doc);
      }
    }

    // Add publications as categories (with their chapters)
    for (const pub of publications) {
      const docs = publicationDocs[pub.key] || [];
      if (docs.length > 0) {
        // Use publication title as category name with icon hint
        const categoryName = `📚 ${pub.title}`;
        categories[categoryName] = docs;
      }
    }

    // Add orphan chapters as separate category
    if (orphanChapters.length > 0) {
      categories['Standalone Chapters'] = orphanChapters;
    }

    // Group remaining documents by type
    for (const doc of otherDocs) {
      const category = doc.type || 'other';
      if (!categories[category]) {
        categories[category] = [];
      }
      categories[category].push(doc);
    }

    return { categories, publications };
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

// Publications
export const getPublicationsStatus = (language?: string) =>
  api.get<PublicationsStatusResponse>('/publications/status', {
    params: language ? { language } : undefined
  }).then(r => r.data);

export const getPublicationTranslations = () =>
  api.get<PublicationTranslationsResponse>('/publications/translations').then(r => r.data);

// Insights
export const getInsights = () =>
  api.get<InsightsResponse>('/insights').then(r => r.data);

export const getInsightsPath = (type: string) =>
  api.get<unknown>('/insights/path', { params: { type } }).then(r => r.data);

// Build
export const getBuildStatus = () =>
  api.get<BuildStatus>('/build/status').then(r => r.data);

export const startBuild = (options: {
  formats: string[];
  languages: string[];
  force?: boolean;
}) => api.post<BuildStartResponse>('/build/start', null, {
  params: {
    formats: options.formats.join(','),
    languages: options.languages.join(','),
    force: options.force || false,
  }
}).then(r => r.data);

export const cancelBuild = () =>
  api.post<{ status: string; message?: string }>('/build/cancel').then(r => r.data);

export const getBuildOutputs = () =>
  api.get<BuildOutputsResponse>('/build/outputs').then(r => r.data);

// Legacy alias for backward compatibility
export const triggerBuild = (options: {
  formats: string[];
  languages: string[];
}) => startBuild(options);

// Publish configuration
export interface PublishConfig {
  publish_path: string;
  desktop_deliverables: boolean;
  default_path: string;
  desktop_path: string;
  project_name: string;
}

export interface PublishStartResponse {
  status: string;
  output_dir: string;
  include_fonts: boolean;
  include_diagrams: boolean;
  include_videos: boolean;
}

export const getPublishConfig = () =>
  api.get<PublishConfig>('/build/publish-config').then(r => r.data);

export const startPublish = (options?: {
  output_dir?: string;
  include_fonts?: boolean;
  include_diagrams?: boolean;
  include_videos?: boolean;
}) => api.post<PublishStartResponse>('/build/publish', null, {
  params: options
}).then(r => r.data);

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

// ============== ADVANCED ANALYSIS API ==============

import type {
  AdvancedInsightsResponse,
  QualitySummaryResponse,
  SemanticAnalysisResponse,
  KnowledgeGraphResponse,
  NorwegianReadabilityResponse,
  PredictiveFreshnessResponse,
  EnhancedCodeSyncResponse,
  AdvancedAnalysisResponse,
  HierarchyTreeResponse,
  HierarchyNodeDetail,
  BreadcrumbsResponse,
  DerivationGraphResponse,
  FlowGraphResponse,
} from './types';

// Comprehensive advanced insights
export const getAdvancedInsights = () =>
  api.get<AdvancedInsightsResponse>('/insights/advanced').then(r => r.data);

// Quality summary for dashboard
export const getQualitySummary = () =>
  api.get<QualitySummaryResponse>('/insights/quality-summary').then(r => r.data);

// Semantic analysis
export const getSemanticAnalysis = (options?: {
  duplicates?: boolean;
  drift?: boolean;
  clusters?: boolean;
  contradictions?: boolean;
  threshold?: number;
}) =>
  api.get<SemanticAnalysisResponse>('/insights/semantic', { params: options }).then(r => r.data);

// Knowledge graph
export const getKnowledgeGraph = (options?: {
  build?: boolean;
  orphans?: boolean;
  prerequisites?: boolean;
  metrics?: boolean;
  path_from?: string;
}) =>
  api.get<KnowledgeGraphResponse>('/insights/knowledge-graph', { params: options }).then(r => r.data);

// Norwegian readability
export const getNorwegianReadability = (options?: {
  document?: string;
  target?: string;
}) =>
  api.get<NorwegianReadabilityResponse>('/insights/norwegian-readability', { params: options }).then(r => r.data);

// Predictive freshness
export const getPredictiveFreshness = (options?: {
  train?: boolean;
  days?: number;
}) =>
  api.get<PredictiveFreshnessResponse>('/insights/predictive-freshness', { params: options }).then(r => r.data);

// Enhanced codesync
export const getEnhancedCodeSync = (options?: {
  syntax?: boolean;
  deprecated?: boolean;
  api_refs?: boolean;
  document?: string;
}) =>
  api.get<EnhancedCodeSyncResponse>('/insights/enhanced-codesync', { params: options }).then(r => r.data);

// Advanced analysis
export const getAdvancedAnalysis = (options?: {
  audience_drift?: boolean;
  questions?: boolean;
  crossrefs?: boolean;
  structure?: boolean;
  style?: boolean;
  full?: boolean;
  document?: string;
}) =>
  api.get<AdvancedAnalysisResponse>('/insights/advanced-analysis', { params: options }).then(r => r.data);

// ============== HIERARCHY API ==============

// Get hierarchy tree structure
export const getHierarchyTree = (language?: string) =>
  api.get<HierarchyTreeResponse>('/hierarchy/tree', { params: { language } }).then(r => r.data);

// Get detailed node information
export const getHierarchyNode = (path: string) =>
  api.get<HierarchyNodeDetail>(`/hierarchy/node/${encodeURIComponent(path)}`).then(r => r.data);

// Get breadcrumbs for a document
export const getBreadcrumbs = (path: string) =>
  api.get<BreadcrumbsResponse>(`/hierarchy/breadcrumbs/${encodeURIComponent(path)}`).then(r => r.data);

// Get derivation graph for visualization
export const getDerivationGraph = () =>
  api.get<DerivationGraphResponse>('/hierarchy/derivation-graph').then(r => r.data);

// Get flow graph with positions for visualization
export const getFlowGraph = (options?: {
  focus_path?: string;
  direction?: 'upstream' | 'downstream' | 'both';
  max_depth?: number;
  language?: string;
}) =>
  api.get<FlowGraphResponse>('/hierarchy/flow-graph', { params: options }).then(r => r.data);

// Unified graph response type
export interface UnifiedGraphNode {
  id: string;
  label: string;
  type: string;
  doc_type: string;
  lifecycle: string;
  is_stale: boolean;
  language: string;
}

export interface UnifiedGraphEdge {
  source: string;
  target: string;
  type: string;
  label: string;
  is_stale: boolean;
}

export interface UnifiedGraphResponse {
  nodes: UnifiedGraphNode[];
  edges: UnifiedGraphEdge[];
  summary: {
    node_count: number;
    edge_count: number;
    edge_types: Record<string, number>;
  };
}

// Get unified graph with all relationship types
export const getUnifiedGraph = (language?: string) =>
  api.get<UnifiedGraphResponse>('/hierarchy/unified-graph', { params: { language } }).then(r => r.data);

// ============== BRAND VOICE API ==============

export interface VoiceStyle {
  active_voice_target: number;
  sentence_length_target: number;
  paragraph_length_max: number;
  use_contractions: boolean;
  use_first_person: boolean;
  use_second_person: boolean;
}

export interface TermPreference {
  prefer: string;
  avoid: string[];
}

export interface VoiceProfile {
  has_voice: boolean;
  personality: string[];
  tone: string;
  formality_level: number;
  style: VoiceStyle;
  available_doc_types?: string[];
  available_audiences?: string[];
  preferred_terms?: TermPreference[];
  avoid_phrases?: string[];
  applied_doc_type?: string;
  applied_audience?: string;
  warning?: string;
}

export interface VoiceIssue {
  type: string;
  severity: string;
  message: string;
  suggestion?: string;
}

export interface VoiceCheckResult {
  document: string;
  document_name: string;
  passed: boolean;
  issues: VoiceIssue[];
  metrics: {
    active_voice_percentage?: number;
    avg_sentence_length?: number;
    detected_formality?: string;
    first_person_count?: number;
    second_person_count?: number;
  };
}

export interface VoiceCheckResponse {
  summary: {
    documents_checked: number;
    documents_passed: number;
    total_issues: number;
    pass_rate: number;
  };
  results: VoiceCheckResult[];
}

export interface TerminologyCheckResponse {
  preferred_terms: TermPreference[];
  avoid_phrases: string[];
  issues: Record<string, string[]>;
  summary: {
    total_issues: number;
    unique_issues: number;
  };
  warning?: string;
}

export interface VoiceContextResponse {
  document: string | null;
  resolution_chain: Array<{
    source: string;
    path: string | null;
    overrides: Record<string, unknown>;
  }>;
  effective_voice: {
    tone: string;
    formality_level: number;
    personality: string[];
    style: Record<string, unknown>;
  };
}

// Get brand voice profile
export const getBrandVoice = (options?: {
  doc_type?: string;
  audience?: string;
}) =>
  api.get<VoiceProfile>('/brand/voice', { params: options }).then(r => r.data);

// Check all documents against voice guidelines
export const checkVoiceAll = () =>
  api.get<VoiceCheckResponse>('/brand/voice/check').then(r => r.data);

// Check specific document against voice guidelines
export const checkVoiceDocument = (documentPath: string) =>
  api.get<VoiceCheckResult>(`/brand/voice/check/${encodeURIComponent(documentPath)}`).then(r => r.data);

// Check terminology consistency
export const checkTerminology = () =>
  api.get<TerminologyCheckResponse>('/brand/voice/terminology').then(r => r.data);

// Get voice context for a document
export const getVoiceContext = (documentPath: string) =>
  api.get<VoiceContextResponse>(`/brand/voice/context/${encodeURIComponent(documentPath)}`).then(r => r.data);

// ============== BRAND ASSETS API ==============

export interface BrandAssetsResponse {
  name: string;
  version: string;
  identity: {
    taglines?: { primary?: string; short?: string; technical?: string };
    legal?: { copyright?: string; license?: string };
  };
  colors: {
    brand: { primary: string; secondary: string; accent: string; muted?: string };
    semantic: { success: string; warning: string; error: string; info: string };
    text?: { primary: string; secondary: string; muted: string };
    background?: { primary: string; secondary: string };
    dark?: Record<string, unknown>;
  };
  typography: {
    fonts: {
      heading: { family: string; fallback?: string; weights: number[]; source: string };
      body: { family: string; fallback?: string; weights: number[]; source: string };
      code: { family: string; fallback?: string; weights: number[]; source: string };
    };
    scale?: Record<string, number>;
  };
  logos: Record<string, { path: string; alt: string; exists: boolean; url: string }>;
  spacing?: Record<string, unknown>;
  borders?: Record<string, unknown>;
  shadows?: Record<string, string>;
}

export interface BrandFile {
  path: string;
  type: string;
  category: string;
  size: number;
  modified: string;
  legacy?: boolean;
}

export interface BrandFilesResponse {
  files: BrandFile[];
  total: number;
  categories: Record<string, number>;
}

export interface BrandFileContent {
  path: string;
  name: string;
  type: string;
  mime_type: string;
  size: number;
  modified: string;
  content: string;
  encoding: 'text' | 'base64';
}

export interface BrandNote {
  id: string;
  category: string;
  target?: string;
  text: string;
  priority: string;
  status: string;
  created: string;
  updated: string;
}

export interface BrandNotesResponse {
  notes: BrandNote[];
  categories: string[];
}

export interface BrandGuideResponse {
  project: string;
  generated: string;
  identity: Record<string, unknown>;
  visual_identity: Record<string, unknown>;
  voice_guidelines: Record<string, unknown> | null;
  notes: BrandNote[];
}

// Get comprehensive brand assets
export const getBrandAssets = () =>
  api.get<BrandAssetsResponse>('/brand/assets').then(r => r.data);

// List all brand files
export const getBrandFiles = () =>
  api.get<BrandFilesResponse>('/brand/files').then(r => r.data);

// Get specific brand file content
export const getBrandFile = (path: string) =>
  api.get<BrandFileContent>(`/brand/file/${encodeURIComponent(path)}`).then(r => r.data);

// Get brand notes
export const getBrandNotes = () =>
  api.get<BrandNotesResponse>('/brand/notes').then(r => r.data);

// Add brand note
export const addBrandNote = (params: {
  category: string;
  text: string;
  target?: string;
  priority?: string;
}) =>
  api.post<{ status: string; note: BrandNote }>('/brand/notes', null, { params }).then(r => r.data);

// Update brand note
export const updateBrandNote = (noteId: string, params: {
  text?: string;
  status?: string;
  priority?: string;
}) =>
  api.put<{ status: string; note: BrandNote }>(`/brand/notes/${noteId}`, null, { params }).then(r => r.data);

// Delete brand note
export const deleteBrandNote = (noteId: string) =>
  api.delete<{ status: string; note_id: string }>(`/brand/notes/${noteId}`).then(r => r.data);

// Get complete brand guide
export const getBrandGuide = () =>
  api.get<BrandGuideResponse>('/brand/guide').then(r => r.data);

// ============== SETTINGS API ==============

import type {
  SettingsResponse,
  SettingsDefaultsResponse,
  SettingsProjectResponse,
  SettingsUpdateRequest,
  SettingsUpdateResponse,
  SettingsValidationResponse,
  EnvSettings,
} from './types';

// Get all settings with source annotations
export const getSettings = () =>
  api.get<SettingsResponse>('/settings').then(r => r.data);

// Get frozen default values
export const getSettingsDefaults = () =>
  api.get<SettingsDefaultsResponse>('/settings/defaults').then(r => r.data);

// Get project.yaml settings only
export const getSettingsProject = () =>
  api.get<SettingsProjectResponse>('/settings/project').then(r => r.data);

// Get environment variables status
export const getSettingsEnv = () =>
  api.get<EnvSettings>('/settings/env').then(r => r.data);

// Update project.yaml section
export const updateSettings = (request: SettingsUpdateRequest) =>
  api.put<SettingsUpdateResponse>('/settings/project', request).then(r => r.data);

// Validate settings before saving
export const validateSettings = (request: SettingsUpdateRequest) =>
  api.post<SettingsValidationResponse>('/settings/validate', request).then(r => r.data);

// ============== UNIFIED BUILD API ==============

import type {
  BuildPublicationsResponse,
  UnifiedBuildRequest,
  UnifiedBuildResponse,
  PublishConfig as PublishConfigType,
} from './types';

// Get publications available for building
export const getBuildPublications = () =>
  api.get<BuildPublicationsResponse>('/build/publications').then(r => r.data);

// Get available layout presets
export interface LayoutPreset {
  name: string;
  description: string;
  template: string;
  formats: string[];
  features: Record<string, boolean>;
  maxWidth: string;
  fontScale: number;
  lineHeight: number;
}

export interface BuildPresetsResponse {
  presets: LayoutPreset[];
  default: string;
}

export const getBuildPresets = () =>
  api.get<BuildPresetsResponse>('/build/presets').then(r => r.data);

// Start unified build (optionally with publish)
export const startUnifiedBuild = (request: UnifiedBuildRequest) =>
  api.post<UnifiedBuildResponse>('/build/unified', request).then(r => r.data);

// Get publish configuration
export const getPublishConfiguration = () =>
  api.get<PublishConfigType>('/build/publish-config').then(r => r.data);

export default api;
