/**
 * Centralized Query Keys for React Query
 * Single source of truth for all query key definitions
 *
 * Benefits:
 * - Type-safe query keys
 * - Consistent invalidation patterns
 * - Easy refactoring
 * - Prevents typos in key strings
 */

// Project & Status
export const projectKeys = {
  all: ['project'] as const,
  status: ['projectStatus'] as const,
  settings: ['settings'] as const,
  recentProjects: ['recentProjects'] as const,
};

// Documents
export const documentKeys = {
  all: ['documents'] as const,
  list: (language: string) => ['documents', language] as const,
  detail: (path: string) => ['document', path] as const,
  chapters: (language: string) => ['chapters', language] as const,
};

// Translations
export const translationKeys = {
  all: ['translations'] as const,
  matrix: ['translationMatrix'] as const,
  status: (language: string) => ['translationStatus', language] as const,
};

// Quality & Insights
export const qualityKeys = {
  all: ['quality'] as const,
  summary: ['qualitySummary'] as const,
  insights: ['insights'] as const,
  freshness: ['freshness'] as const,
  advanced: ['advancedInsights'] as const,
};

// Build
export const buildKeys = {
  all: ['build'] as const,
  status: ['buildStatus'] as const,
  publications: ['buildPublications'] as const,
  outputs: ['buildOutputs'] as const,
  publishConfig: ['publishConfig'] as const,
};

// Publications
export const publicationKeys = {
  all: ['publications'] as const,
  list: ['publicationsList'] as const,
  status: ['publicationsStatus'] as const,
  detail: (key: string) => ['publication', key] as const,
  translations: ['publicationTranslations'] as const,
};

// Video Production
export const videoKeys = {
  all: ['video'] as const,
  scripts: ['videoScripts'] as const,
  script: (id: string) => ['videoScript', id] as const,
  renderQueue: ['renderQueue'] as const,
  assets: ['videoAssets'] as const,
  motionComponents: ['motionComponents'] as const,
  voices: ['videoVoices'] as const,
};

// AI Workspace
export const aiKeys = {
  all: ['ai'] as const,
  context: ['aiContext'] as const,
  sessions: ['aiSessions'] as const,
  session: (id: string) => ['aiSession', id] as const,
  notes: ['aiNotes'] as const,
  tasks: ['aiTasks'] as const,
  research: ['aiResearch'] as const,
  decisions: ['aiDecisions'] as const,
};

// Media & Assets
export const mediaKeys = {
  all: ['media'] as const,
  files: (folder: string) => ['mediaFiles', folder] as const,
  diagrams: ['diagrams'] as const,
};

// Search
export const searchKeys = {
  all: ['search'] as const,
  results: (query: string) => ['searchResults', query] as const,
};

// Hierarchy & Structure
export const hierarchyKeys = {
  all: ['hierarchy'] as const,
  tree: (language: string) => ['hierarchyTree', language] as const,
  node: (path: string) => ['hierarchyNode', path] as const,
  flow: (language: string) => ['flowGraph', language] as const,
};

// Combined query keys object for easy importing
export const queryKeys = {
  project: projectKeys,
  documents: documentKeys,
  translations: translationKeys,
  quality: qualityKeys,
  build: buildKeys,
  publications: publicationKeys,
  video: videoKeys,
  ai: aiKeys,
  media: mediaKeys,
  search: searchKeys,
  hierarchy: hierarchyKeys,
} as const;

// Type helper for extracting query key types
export type QueryKeys = typeof queryKeys;
