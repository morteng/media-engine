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

export interface PublicationRef {
  key: string;
  title: string;
  pub_type: 'book' | 'deck' | 'spreadsheet' | 'report';
  item_count: number;
  item_label: 'chapters' | 'slides' | 'sources';
}

export interface Document {
  path: string;
  filename: string;
  title: string;
  type: 'chapter' | 'deliverable' | 'script' | 'slides' | 'diagram' | 'data' | 'demo';
  language: string;
  frontmatter?: Record<string, unknown>;
  publication?: PublicationRef | null;  // Which publication this doc belongs to
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

export interface BuildLogEntry {
  timestamp: string;
  message: string;
  level: 'info' | 'success' | 'warning' | 'error';
}

export interface BuildOutput {
  path: string;
  name: string;
  format: string;
  language: string;
  size: number;
  modified: string;
}

export interface FreshnessWarning {
  stale: number;
  expired: number;
  message: string;
}

export interface BuildStatus {
  active: boolean;
  progress: number;
  logs: BuildLogEntry[];
  last_build: string | null;
  freshness_warning: FreshnessWarning | null;
  outputs: BuildOutput[];
  // Deprecated - keeping for backward compatibility
  isBuilding?: boolean;
  lastBuild?: string;
  lastBuildStatus?: 'success' | 'failed';
  availableFormats?: string[];
}

export interface BuildStartResponse {
  status: 'started' | 'error';
  formats: string[];
  languages: string[];
  force: boolean;
  message?: string;
}

export interface BuildOutputsResponse {
  outputs: BuildOutput[];
}

export interface DeliverableConfig {
  output_dir: string;
  package_name: string;
  include_source: boolean;
  create_zip: boolean;
  version_folders: boolean;
}

export interface AuditLogEntry {
  timestamp: string;
  action: string;
  details?: string;
  user?: string;
}

export interface VideoScript {
  title: string;
  description?: string;
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
  settings?: {
    fps?: number;
    width?: number;
    height?: number;
    background?: string;
  };
  metadata?: {
    version?: string;
    author?: string;
    description?: string;
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
  // API returns these field names
  total_nodes?: number;
  total_edges?: number;
  document_count?: number;
  concept_count?: number;
  avg_connections_per_doc?: number;
  orphan_concepts?: number;
  circular_dependencies?: number;
  clustering_coefficient?: number;
  connected_components?: number;
  // Legacy field names for compatibility
  node_count?: number;
  edge_count?: number;
  density?: number;
  avg_connections?: number;
  hub_count?: number;
  orphan_count?: number;
}

export interface OrphanConcept {
  concept: string;
  mentions: Array<{ doc: string; line: number }>;
  mention_count: number;
  importance: number;
}

export interface PrerequisiteIssue {
  document: string;
  // API returns single string
  missing_prereq?: string;
  explanation?: string;
  suggested_order?: string[];
  // Legacy format (array)
  missing_prerequisites?: string[];
  circular_dependencies?: string[];
}

export interface KnowledgeGraphResponse {
  available: boolean;
  metrics?: KnowledgeGraphMetrics;
  // API returns objects, not strings
  orphan_concepts?: Array<OrphanConcept | string>;
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

// ============== SETTINGS TYPES ==============

export type SettingSource = 'default' | 'project' | 'env';

export interface SettingValue<T = unknown> {
  value: T;
  source: SettingSource;
  default: T;
  editable: boolean;
  description: string;
  category: string;
  type?: string;
  is_set?: boolean;  // For env vars
  sensitive?: boolean;  // For env vars
}

export interface ProjectSettings {
  name: SettingValue<string>;
  description: SettingValue<string>;
  source_language: SettingValue<string>;
  languages: SettingValue<string[]>;
}

export interface VideoSettings {
  width: SettingValue<number>;
  height: SettingValue<number>;
  fps: SettingValue<number>;
}

export interface VoiceoverSettings {
  provider: SettingValue<string>;
  stability: SettingValue<number>;
  similarity_boost: SettingValue<number>;
}

export interface QualitySettings {
  freshness_default_days: SettingValue<number>;
  max_sentence_words: SettingValue<number>;
}

export interface PathsSettings {
  content: SettingValue<string>;
  assets: SettingValue<string>;
  output: SettingValue<string>;
  publish?: SettingValue<string>;
  desktop_deliverables?: SettingValue<boolean>;
}

export interface EnvSettings {
  [key: string]: SettingValue<string>;
}

export interface SettingsResponse {
  project: ProjectSettings;
  video: VideoSettings;
  voiceover: VoiceoverSettings;
  quality: QualitySettings;
  paths: PathsSettings;
  environment: EnvSettings;
}

export interface SettingsDefaultsResponse {
  video: Record<string, SettingValue>;
  voiceover: Record<string, SettingValue>;
  quality: Record<string, SettingValue>;
  web: Record<string, SettingValue>;
  network: Record<string, SettingValue>;
  cache: Record<string, SettingValue>;
  cli: Record<string, SettingValue>;
}

export interface SettingsProjectResponse {
  path: string;
  config: Record<string, unknown>;
  last_modified: string;
}

export interface SettingsUpdateRequest {
  section: 'project' | 'video' | 'voiceover' | 'quality' | 'paths' | 'localization';
  updates: Record<string, unknown>;
}

export interface SettingsUpdateResponse {
  status: 'success' | 'error';
  section: string;
  updated_fields: string[];
  backup_path?: string;
  requires_reload?: boolean;
}

export interface SettingsValidationResponse {
  valid: boolean;
  errors: Record<string, string>;
}

// ============== PUBLICATIONS TYPES ==============

export interface PublicationOutput {
  format: string;
  template: string;
  filename: string;
  single_file: boolean;
  toc: boolean;
}

export interface PublicationChapter {
  path: string;
  required: boolean;
  sections: string[];
}

export interface PublicationMetadata {
  version: string;
  status: string;
  author: string;
  copyright: string;
  license: string;
  isbn: string | null;
  edition: string;
  publication_date: string | null;
  target_audience: string;
  reading_time: string;
}

export interface PublicationValidation {
  is_valid: boolean;
  issues: string[];
  chapter_count: number;
  missing_chapters: number;
  translation_current: boolean;
  source_changed: boolean;
}

export interface Publication {
  key: string;
  title: string;
  subtitle: string;
  language: string;
  status: string;
  version: string;
  chapter_count: number;
  output_formats: string[];
  is_translation: boolean;
  source_document: string | null;
}

export interface PublicationDetail extends Publication {
  description: string;
  metadata: PublicationMetadata;
  chapters: PublicationChapter[];
  outputs: PublicationOutput[];
  source_hash: string | null;
  validation: PublicationValidation;
  assets: string[];
  related: string[];
}

export interface PublicationsResponse {
  publications: Publication[];
  total: number;
}

export interface PublicationStatusItem {
  key: string;
  title: string;
  language: string;
  pub_type: 'book' | 'deck' | 'spreadsheet' | 'report';
  status: string;
  is_valid: boolean;
  issues_count: number;
  item_count: number;
  item_label: 'chapters' | 'slides' | 'sources';
  chapter_count: number;
  slide_count: number;
  data_source_count: number;
  missing_chapters: number;
  is_translation: boolean;
  translation_current: boolean;
  source_changed: boolean;
}

export interface PublicationsStatusResponse {
  publications: PublicationStatusItem[];
  summary: {
    total: number;
    valid: number;
    invalid: number;
    translations_current: number;
    translations_outdated: number;
    total_issues: number;
  };
}

export interface PublicationTranslationPair {
  source: {
    key: string;
    title: string;
    language: string;
    content_hash: string;
  };
  translation: {
    key: string;
    title: string;
    language: string;
    source_hash: string | null;
  };
  sync_status: {
    is_current: boolean;
    source_changed: boolean;
    needs_update: boolean;
  };
}

export interface PublicationTranslationsResponse {
  pairs: PublicationTranslationPair[];
  total: number;
  outdated: number;
}

// ============== AI WORKSPACE TYPES ==============

export interface AISession {
  id: string;
  task_id: string;
  status: 'active' | 'paused' | 'completed' | 'failed';
  started_at: string;
  last_active?: string;
  completed_at?: string;
  progress: {
    total_steps: number;
    completed_steps: number;
    current_step?: string;
  };
  changes: Array<{
    type: string;
    path: string;
    description: string;
    timestamp: string;
  }>;
}

export interface AISessionsResponse {
  sessions: AISession[];
  active_count: number;
  total_count: number;
}

export type NoteType =
  | 'uncertainty'
  | 'suggestion'
  | 'human_review'
  | 'decision'
  | 'todo'
  | 'warning'
  | 'info';

export interface AINote {
  id: string;
  type: NoteType;
  content: string;
  context?: string;
  document_path?: string;
  created_at: string;
  resolved: boolean;
  resolved_at?: string;
  resolution?: string;
}

export interface AINotesResponse {
  notes: AINote[];
  unresolved_count: number;
  total_count: number;
}

export interface AITask {
  id: string;
  type: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'pending' | 'claimed' | 'in_progress' | 'completed' | 'failed';
  created_at: string;
  claimed_by?: string;
  claimed_at?: string;
  completed_at?: string;
  document_path?: string;
  context?: Record<string, unknown>;
}

export interface AITaskQueueResponse {
  tasks: AITask[];
  pending_count: number;
  in_progress_count: number;
}

export interface AIResearchEntry {
  key: string;
  value: unknown;
  context?: string;
  tags: string[];
  created_at: string;
  updated_at: string;
  is_stale: boolean;
  confidence?: number;
}

export interface AIResearchResponse {
  entries: AIResearchEntry[];
  stale_count: number;
  total_count: number;
}

export interface AIDecision {
  id: string;
  decision: string;
  rationale: string;
  context: string;
  document_path?: string;
  session_id?: string;
  created_at: string;
}

export interface AIDecisionsResponse {
  decisions: AIDecision[];
  total_count: number;
}

export interface AIContextData {
  project: {
    name: string;
    languages: string[];
    document_count: number;
  };
  publications: {
    total: number;
    valid: number;
    stale: number;
  };
  active_session?: {
    id: string;
    task_id: string;
    progress: number;
  };
  pending_tasks: number;
  unresolved_notes: number;
  stale_research: number;
  recent_decisions: number;
  health_score: number;
  last_refresh: string;
}

export interface AIContextResponse {
  context: AIContextData;
  success: boolean;
}

// ============== UNIFIED BUILD TYPES ==============

export interface PublicationBuildInfo {
  key: string;
  title: string;
  pub_type: 'book' | 'deck' | 'spreadsheet' | 'report';
  languages: string[];
  formats: string[];  // Available formats from publication config
  lastBuilt?: string;
  isStale?: boolean;
}

export interface BuildPublicationsResponse {
  publications: PublicationBuildInfo[];
  projectLanguages: string[];
}

export interface UnifiedBuildPublication {
  key: string;
  formats: string[];
  languages: string[];
}

export interface UnifiedBuildRequest {
  publications: UnifiedBuildPublication[];
  outputDir?: string;
  includeFonts?: boolean;
  includeDiagrams?: boolean;
  includeVideos?: boolean;
  includeNavigation?: boolean;
  publish?: boolean;  // If true, package after building
  preset?: string;    // Layout preset for HTML output (documentation, ebook, report, etc.)
}

export interface UnifiedBuildResponse {
  status: 'started' | 'error';
  publications: UnifiedBuildPublication[];
  publish: boolean;
  outputDir?: string;
  message?: string;
}

export interface PublishConfig {
  publishDir: string;
  defaultDir: string;
  desktopDir: string;
  useDesktop: boolean;
  projectName: string;
}

// ============== VIDEO PRODUCTION TYPES ==============

export interface VideoScriptItem {
  id: string;
  name: string;
  path: string;
  language: string;
  description?: string;
  version?: string;
  status?: string;
  scenes: number;
  duration?: number;
  has_output?: boolean;
  output_size?: number;
  output_modified?: string;
  error?: string;
}

export interface VideoScriptsResponse {
  scripts: VideoScriptItem[];
  count: number;
}

export interface VideoScriptDetail {
  id: string;
  path: string;
  content: string;
  parsed: VideoScript;
  modified: string;
}

export interface VideoPropsResponse {
  props: Record<string, unknown>;
}

export interface RenderRequest {
  script_id: string;
  quality: 'preview' | 'production';
  output_format?: string;
}

export interface RenderJob {
  id: string;
  script_id: string;
  quality: string;
  status: 'queued' | 'rendering' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  stage: string;
  started: string;
  completed?: string;
  error?: string;
  output_path?: string;
}

export interface RenderStartResponse {
  job_id: string;
  status: string;
}

export interface RenderQueueResponse {
  jobs: RenderJob[];
  active: number;
  completed: number;
  failed: number;
}

export interface VideoAssetItem {
  name: string;
  path: string;
  size: number;
  modified: string;
  language?: string;
}

export interface VideoAssetsResponse {
  demos: VideoAssetItem[];
  audio: VideoAssetItem[];
  graphics: VideoAssetItem[];
  outputs: VideoAssetItem[];
}

export interface MotionComponent {
  id: string;
  name: string;
  category: string;
  description: string;
  props: string[];
}

export interface MotionComponentsResponse {
  components: MotionComponent[];
  backgrounds: string[];
  transitions: string[];
  text_effects: string[];
}

export interface VideoVoice {
  language: string;
  voice_id: string;
  name: string;
}

export interface VideoVoicesResponse {
  voices: VideoVoice[];
}
