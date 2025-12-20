// API Response Types for Media Engine Dashboard - Matching actual API responses

export interface Project {
  name: string;
  path: string;
  languages: string[];
  defaultLanguage: string;
  theme?: ThemeConfig;
}

export interface ThemeConfig {
  name: string;
  colors: {
    primary: string;
    secondary: string;
    accent: string;
  };
}

// Actual /api/status response
export interface ProjectStatus {
  project: {
    name: string;
    root: string;
  };
  languages: string[];
  source_language: string;
  content: Record<string, Record<string, number>>;
  cache: {
    voiceover_items: number;
    builds_tracked: number;
  };
}

export interface Document {
  path: string;
  filename: string;
  title: string;
  type: 'chapter' | 'deliverable' | 'script' | 'slides' | 'diagram' | 'data' | 'demo';
  language: string;
  frontmatter?: Record<string, unknown>;
}

export interface DocumentContent {
  path: string;
  filename: string;
  title: string;
  content: string;
  html?: string;
  metadata?: Record<string, unknown>;
}

export interface Translation {
  source: string;
  target: string;
  sourceLanguage: string;
  targetLanguage: string;
  status: 'synced' | 'outdated' | 'missing';
  sourceVersion?: string;
  targetVersion?: string;
}

export interface TranslationMatrix {
  documents: string[];
  languages: string[];
  matrix: Record<string, Record<string, Translation | null>>;
}

export interface QualityIssue {
  type: 'error' | 'warning' | 'info';
  category: string;
  message: string;
  file?: string;
  line?: number;
}

// Actual /api/freshness response
export interface FreshnessResponse {
  total_items: number;
  fresh_count: number;
  stale_count: number;
  expired_count: number;
  missing_count: number;
  untracked_count: number;
  items: FreshnessEntry[];
  stale_items: Array<{ path: string; content_type: string }>;
}

export interface FreshnessEntry {
  path: string;
  content_type: string;
  status: 'fresh' | 'stale' | 'expired';
  last_modified: string;
  content_hash: string;
}

// Actual /api/insights response
export interface InsightsResponse {
  health: HealthData;
  statistics: StatisticsData;
  incomplete: IncompleteData;
  consistency: ConsistencyIssue[];
  parity: ParityData;
  velocity: VelocityData;
  graph: GraphData;
}

export interface HealthData {
  overall: number;
  grade: string;
  status: string;
  components: {
    freshness: number;
    translation: number;
    consistency: number;
    links: number;
    readability: number;
    dependencies: number;
    metadata: number;
  };
  document_count: number;
  critical_count: number;
  issues: HealthIssue[];
  recommendations: string[];
}

export interface HealthIssue {
  category: string;
  severity: string;
  message: string;
  impact: number;
  document: string;
  recommendation: string;
}

export interface StatisticsData {
  content: {
    total_documents: number;
    documents_by_language: Record<string, number>;
    documents_by_type: Record<string, number>;
    total_words: number;
    words_by_language: Record<string, number>;
  };
  status: {
    by_status: Record<string, number>;
    approval_queue_size: number;
  };
  activity: {
    documents_modified_week: number;
    documents_modified_month: number;
    contributors: string[];
    commit_count_week: number;
    recent_changes: RecentChange[];
  };
}

export interface RecentChange {
  hash: string;
  author: string;
  message: string;
  date: string;
  files: string[];
}

export interface IncompleteData {
  total: number;
  debt_score: number;
  items: IncompleteItem[];
}

export interface IncompleteItem {
  document: string;
  line_number: number;
  marker_type: string;
  content: string;
  priority: string;
}

export interface ConsistencyIssue {
  document: string;
  issue_type: string;
  declared: string;
  detected: string;
  confidence: number;
  recommendation: string;
}

export interface ParityData {
  matrix: Record<string, Record<string, number>>;
  missing: Record<string, string[]>;
  coverage: Record<string, number>;
  primary_language: string;
  languages: string[];
}

export interface VelocityData {
  period: string;
  commits: number;
  lines_added: number;
  lines_removed: number;
  documents_modified: number;
  documents_created: number;
  top_contributors: Contributor[];
}

export interface Contributor {
  name: string;
  email: string;
  commits: number;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
  hubs: number;
  orphans: number;
}

export interface GraphNode {
  id: string;
  document: string;
  title: string;
  type: string;
  status: string;
  word_count: number;
  language: string;
}

export interface GraphLink {
  source: string;
  target: string;
  type: string;
  weight: number;
}

export interface BuildStatus {
  isBuilding: boolean;
  lastBuild?: string;
  lastBuildStatus?: 'success' | 'failed';
  availableFormats: string[];
}

export interface AuditLogEntry {
  timestamp: string;
  action: string;
  details?: string;
  user?: string;
}

export interface VideoScript {
  title: string;
  description: string;
  language: string;
  scenes: VideoScene[];
  narrator?: {
    voice: string;
    speed: number;
  };
  output?: {
    resolution: { width: number; height: number };
    framerate: number;
    filename: string;
  };
}

export interface VideoScene {
  id: string;
  name: string;
  type: string;
  duration: number;
  voiceover?: string;
  visual?: Record<string, unknown>;
}

export interface VideoInfo {
  hasVideo: boolean;
  hasAudio: boolean;
  hasCaptions: boolean;
  hasProps: boolean;
  videoUrl?: string;
  audioUrl?: string;
  captionsUrl?: string;
  duration?: number;
  fps?: number;
  sceneTiming?: Array<{
    id: string;
    startTime: number;
    endTime: number;
  }>;
}

// Project Switching
export interface RecentProject {
  path: string;
  name: string;
  last_accessed: string;
  exists: boolean;
}

export interface RecentProjectsResponse {
  current: {
    path: string;
    name: string;
  } | null;
  recent: RecentProject[];
}

export interface OpenProjectResponse {
  status: 'switched' | 'error';
  project?: {
    path: string;
    name: string;
  };
  error?: string;
}

export interface BrowseProjectResponse {
  status: 'selected' | 'prompt' | 'invalid';
  path: string | null;
  message?: string;
  error?: string;
}

// Scene Notes
export interface SceneNote {
  text: string;
  created: string;
  scene_id: string;
}

export interface SceneNotesResponse {
  notes: Record<string, SceneNote>;
}
