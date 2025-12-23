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

// ============== ADVANCED ANALYSIS TYPES ==============

// Semantic Analysis
export interface SemanticMatch {
  doc1_path: string;
  doc2_path: string;
  similarity: number;
  matching_sections: string[];
}

export interface TerminologyDrift {
  term: string;
  old_usage: string;
  new_usage: string;
  documents: string[];
  drift_score: number;
}

export interface ContentCluster {
  id: number;
  cluster_id: number;
  theme: string;
  documents: string[];
  doc_count: number;
}

export interface SemanticAnalysisResponse {
  available: boolean;
  near_duplicates?: SemanticMatch[];
  near_duplicate_count?: number;
  terminology_drift?: TerminologyDrift[];
  drift_count?: number;
  clusters?: ContentCluster[];
  cluster_count?: number;
  error?: string;
  reason?: string;
}

// Knowledge Graph (Enhanced)
export interface KnowledgeGraphMetrics {
  node_count: number;
  edge_count: number;
  density: number;
  avg_connections: number;
  hub_count: number;
  orphan_count: number;
}

export interface PrerequisiteIssue {
  document: string;
  missing_prerequisites: string[];
  circular_dependencies: string[];
}

export interface KnowledgeGraphResponse {
  available: boolean;
  metrics?: KnowledgeGraphMetrics;
  orphan_concepts?: string[];
  orphan_count?: number;
  prerequisite_issues?: PrerequisiteIssue[];
  prereq_issue_count?: number;
  node_count?: number;
  edge_count?: number;
  error?: string;
  reason?: string;
}

// Norwegian Readability
export interface NorwegianReadabilityDoc {
  path: string;
  lix: number;
  lix_score: number;
  level: 'very_easy' | 'easy' | 'medium' | 'difficult' | 'very_difficult';
  difficulty_level: 'very_easy' | 'easy' | 'medium' | 'difficult' | 'very_difficult';
  word_count: number;
}

export interface NorwegianReadabilityResponse {
  available: boolean;
  documents_analyzed?: number;
  average_lix?: number;
  difficulty_distribution?: Record<string, number>;
  difficult_documents?: NorwegianReadabilityDoc[];
  difficult_count?: number;
  error?: string;
  reason?: string;
}

// Predictive Freshness
export interface StalenessPrediction {
  path: string;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  staleness_probability: number;
  days_until_stale: number;
  contributing_factors?: string[];
}

export interface ReviewQueueItem {
  path: string;
  priority: number;
  reason: string;
}

export interface PredictiveFreshnessResponse {
  available: boolean;
  predictions_count?: number;
  high_risk_count?: number;
  high_risk_documents?: StalenessPrediction[];
  review_queue?: ReviewQueueItem[];
  summary?: {
    total: number;
    low_risk: number;
    medium_risk: number;
    high_risk: number;
    critical_risk: number;
  };
  error?: string;
  reason?: string;
}

// Enhanced CodeSync
export interface CodeSyncIssue {
  document: string;
  line: number;
  issue_type: string;
  code_block: string;
  message: string;
}

export interface EnhancedCodeSyncResponse {
  available: boolean;
  syntax_errors?: CodeSyncIssue[];
  syntax_error_count?: number;
  deprecated_patterns?: CodeSyncIssue[];
  deprecated_count?: number;
  api_issues?: CodeSyncIssue[];
  api_issue_count?: number;
  total_issues?: number;
  error?: string;
  reason?: string;
}

// Advanced Analysis
export interface AudienceDriftData {
  trend: 'stable' | 'increasing' | 'decreasing';
  complexity_over_time: Array<{ date: string; complexity: number }>;
  documents_with_drift: string[];
  drift_score: number;
}

export interface QuestionCoverageData {
  total_questions: number;
  answered_questions: number;
  unanswered_questions: string[];
  coverage_percent: number;
}

export interface CrossReferenceData {
  total_references: number;
  internal_references: number;
  external_references: number;
  orphan_references: string[];
  density_score: number;
}

export interface StructureAnalysisData {
  avg_heading_depth: number;
  documents_with_issues: string[];
  heading_consistency_score: number;
}

export interface StyleConsistencyData {
  style_score: number;
  inconsistencies: Array<{
    document: string;
    issue: string;
    expected: string;
    found: string;
  }>;
}

export interface AdvancedAnalysisResponse {
  available: boolean;
  audience_drift?: AudienceDriftData;
  question_coverage?: QuestionCoverageData;
  cross_references?: CrossReferenceData;
  structure_analysis?: StructureAnalysisData;
  style_consistency?: StyleConsistencyData;
  error?: string;
  reason?: string;
}

// Comprehensive Advanced Insights Response
export interface AdvancedInsightsResponse {
  semantic: SemanticAnalysisResponse | null;
  llm_quality: unknown | null;
  knowledge_graph: KnowledgeGraphResponse | null;
  norwegian_readability: NorwegianReadabilityResponse | null;
  predictive_freshness: PredictiveFreshnessResponse | null;
  enhanced_codesync: EnhancedCodeSyncResponse | null;
  advanced_analysis: AdvancedAnalysisResponse | null;
}

// Quality Summary for Dashboard
export interface QualitySummaryResponse {
  overall_score: number;
  grade: string;
  status: string;
  key_metrics: Array<{
    name: string;
    score: number;
    weight: number;
  }>;
  critical_issues: HealthIssue[];
  recommendations: string[];
  advanced_available: {
    semantic: boolean;
    knowledge_graph: boolean;
    norwegian_readability: boolean;
    predictive_freshness: boolean;
    enhanced_codesync: boolean;
    advanced_analysis: boolean;
  };
  advanced_highlights: Record<string, {
    message: string;
    [key: string]: unknown;
  }>;
}

// ============== HIERARCHY TYPES ==============

export interface HierarchyTreeNode {
  path: string;
  title: string;
  doc_type: 'chapter' | 'operations' | 'reference' | 'tutorial' | 'concept' | 'guide';
  lifecycle: 'living' | 'snapshot' | 'deprecated' | 'archived';
  is_stale: boolean;
  level: number;
  sequence_order: number;
  has_anchors: boolean;
  derived_from_count: number;
  children: HierarchyTreeNode[];
}

export interface HierarchyTreeResponse {
  nodes: HierarchyTreeNode[];
  total_count: number;
  root_count: number;
  error?: string;
}

export interface HierarchyNodeDetail {
  path: string;
  title: string;
  doc_type: string;
  lifecycle: string;
  is_stale: boolean;
  level: number;
  sequence_order: number;
  parent: string | null;
  children: string[];
  ancestors: string[];
  siblings: string[];
  derived_from: Array<{
    path: string;
    version: string | null;
    relationship: string;
  }>;
  derivatives: string[];
  defined_anchors: Array<{
    id: string;
    value: unknown;
  }>;
  anchor_refs: Array<{
    source: string;
    anchor: string;
  }>;
  owner: string | null;
  approvers: string[];
  error?: string;
}

export interface BreadcrumbItem {
  path: string;
  title: string;
  doc_type: string;
}

export interface BreadcrumbsResponse {
  breadcrumbs: BreadcrumbItem[];
  error?: string;
}

export interface DerivationGraphNode {
  id: string;
  title: string;
  doc_type: string;
  lifecycle: string;
  is_stale: boolean;
}

export interface DerivationGraphEdge {
  source: string;
  target: string;
  relationship: string;
  version: string | null;
}

export interface DerivationGraphResponse {
  nodes: DerivationGraphNode[];
  edges: DerivationGraphEdge[];
  node_count: number;
  edge_count: number;
  error?: string;
}

// Flow Graph Types
export interface FlowGraphNode {
  id: string;
  title: string;
  doc_type: string;
  lifecycle: string;
  is_stale: boolean;
  level: number;
  sequence_order: number;
  position: {
    x: number;
    y: number;
  };
}

export interface FlowGraphEdge {
  source: string;
  target: string;
  type: string;
  is_stale: boolean;
  version: string | null;
}

export interface FlowGraphLevel {
  level: number;
  count: number;
}

export interface StalenessSummary {
  total_nodes: number;
  stale_nodes: number;
  stale_percentage: number;
  stale_edges: number;
}

export interface FlowGraphResponse {
  nodes: FlowGraphNode[];
  edges: FlowGraphEdge[];
  levels: FlowGraphLevel[];
  staleness_summary: StalenessSummary;
  error?: string;
}
