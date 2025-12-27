import { http, HttpResponse } from 'msw';

// Mock data
export const mockProject = {
  name: 'Test Project',
  description: 'A test project',
  root: '/test/project',
  languages: {
    en: { name: 'English', locale: 'en-US' },
    no: { name: 'Norwegian', locale: 'nb-NO' },
  },
  source_language: 'en',
  paths: {
    content: '/test/project/content',
    assets: '/test/project/assets',
    output: '/test/project/output',
    publish: '/test/project/dist',
  },
};

export const mockStatus = {
  project: {
    name: 'Test Project',
    root: '/test/project',
  },
  languages: ['en', 'no'],
  source_language: 'en',
  content: {
    en: { chapter: 5, script: 2, slides: 1 },
    no: { chapter: 3, script: 1 },
  },
  cache: {
    voiceover_items: 10,
    builds_tracked: 5,
  },
};

export const mockDocuments = {
  documents: [
    { path: 'content/en/chapters/intro.md', filename: 'intro.md', title: 'Introduction', type: 'chapter', language: 'en' },
    { path: 'content/en/chapters/setup.md', filename: 'setup.md', title: 'Setup Guide', type: 'chapter', language: 'en' },
    { path: 'content/en/scripts/demo.yaml', filename: 'demo.yaml', title: 'Demo Video', type: 'script', language: 'en' },
  ],
};

export const mockQualitySummary = {
  health_score: 85,
  grade: 'B',
  status: 'Good',
  core_metrics: {
    freshness: 90,
    translation: 75,
    consistency: 88,
    links: 95,
    readability: 82,
    dependencies: 85,
    metadata: 80,
  },
  critical_issues_count: 1,
  warning_count: 2,
  recommendations: ['Update stale documents', 'Complete translations'],
  advanced_available: {
    semantic: true,
    knowledge_graph: true,
    predictive_freshness: false,
    enhanced_codesync: true,
    norwegian_readability: false,
    advanced_analysis: false,
  },
  advanced_highlights: {},
};

export const mockInsights = {
  health: {
    overall: 85,
    grade: 'B',
    status: 'good',
    components: {
      freshness: 90,
      translation: 75,
      consistency: 88,
      links: 95,
      readability: 82,
      dependencies: 85,
      metadata: 80,
    },
    document_count: 10,
    critical_count: 1,
    issues: [
      { severity: 'warning', category: 'links', message: 'Broken link found', document: 'intro.md' },
      { severity: 'warning', category: 'readability', message: 'Consider simplifying sentence', document: 'setup.md' },
    ],
    recommendations: ['Update stale documents', 'Complete translations'],
  },
  statistics: {
    content: {
      total_documents: 10,
      documents_by_language: { en: 6, no: 4 },
      documents_by_type: { chapter: 5, script: 3, slides: 2 },
      total_words: 5000,
      words_by_language: { en: 3000, no: 2000 },
    },
    status: {
      by_status: { published: 8, draft: 2 },
      approval_queue_size: 1,
    },
    activity: {
      documents_modified_week: 3,
      documents_modified_month: 8,
      contributors: ['author1', 'author2'],
      commit_count_week: 5,
      recent_changes: [],
    },
  },
  incomplete: { total: 2, debt_score: 15, items: [] },
  consistency: [],
  parity: {
    matrix: {},
    missing: {},
    coverage: { en: 100, no: 67 },
    primary_language: 'en',
    languages: ['en', 'no'],
  },
  velocity: {
    period: '7d',
    commits: 5,
    lines_added: 200,
    lines_removed: 50,
    documents_modified: 3,
    documents_created: 1,
    top_contributors: [],
  },
  graph: { nodes: [], links: [], hubs: 2, orphans: 1 },
};

export const mockQuality = {
  issues: [
    { severity: 'warning', category: 'links', message: 'Broken link found', document: 'intro.md', line: 42 },
    { severity: 'warning', category: 'readability', message: 'Consider simplifying sentence', document: 'setup.md', line: 15 },
  ],
};

export const mockAdvancedInsights = {
  semantic: {
    available: true,
    near_duplicate_count: 2,
    drift_count: 1,
    cluster_count: 3,
    near_duplicates: [
      { doc1_path: 'intro.md', doc2_path: 'overview.md', similarity: 0.87 },
    ],
    terminology_drift: [
      { term: 'API', drift_score: 0.15, old_usage: 'Application Programming Interface', new_usage: 'API' },
    ],
    clusters: [
      { cluster_id: 1, theme: 'Getting Started', doc_count: 3 },
    ],
  },
  knowledge_graph: {
    available: true,
    node_count: 15,
    edge_count: 22,
    orphan_count: 2,
    prereq_issue_count: 1,
    metrics: {
      node_count: 15,
      edge_count: 22,
      density: 0.2,
      avg_connections: 2.9,
      hub_count: 3,
    },
    orphan_concepts: ['orphan-concept-1', 'orphan-concept-2'],
    prerequisite_issues: [
      { document: 'advanced.md', missing_prerequisites: ['basics.md'], circular_dependencies: [] },
    ],
  },
  predictive_freshness: {
    available: true,
    high_risk_count: 2,
    summary: {
      low_risk: 5,
      medium_risk: 3,
      high_risk: 2,
      critical_risk: 0,
    },
    high_risk_documents: [
      { path: 'old-doc.md', risk_level: 'high', staleness_probability: 0.75, days_until_stale: 10 },
    ],
  },
  enhanced_codesync: {
    available: true,
    syntax_error_count: 1,
    deprecated_count: 2,
    api_issue_count: 1,
    syntax_errors: [
      { document: 'code-example.md', line: 15, message: 'Syntax error in code block' },
    ],
    deprecated_patterns: [
      { document: 'old-api.md', message: 'Using deprecated componentDidMount' },
    ],
    api_issues: [
      { document: 'api-docs.md', message: 'Reference to removed endpoint' },
    ],
  },
  norwegian_readability: {
    available: true,
    average_lix: 42.5,
    documents_analyzed: 4,
    difficult_count: 1,
    difficult_documents: [
      { path: 'no/complex.md', lix_score: 52, difficulty_level: 'difficult' },
    ],
  },
  advanced_analysis: {
    available: true,
    audience_drift: {
      drift_score: 0.2,
      trend: 'stable',
      documents_with_drift: ['doc1.md'],
    },
    question_coverage: {
      coverage_percent: 75,
      total_questions: 20,
      answered_questions: 15,
      unanswered_questions: ['How to configure X?', 'What is Y?'],
    },
    cross_references: {
      total_references: 45,
      internal_references: 30,
      external_references: 15,
      density_score: 3.5,
      orphan_references: ['broken-link.md'],
    },
    style_consistency: {
      style_score: 82,
      inconsistencies: [
        { document: 'intro.md', issue: 'Inconsistent heading style' },
      ],
    },
  },
};

export const mockFreshness = {
  total_items: 10,
  fresh_count: 7,
  stale_count: 2,
  expired_count: 1,
  missing_count: 0,
  untracked_count: 0,
  items: [],
  stale_items: [
    { path: 'content/en/chapters/old.md', content_type: 'chapter' },
  ],
};

export const mockBuildStatus = {
  active: false,
  progress: 0,
  logs: [],
  last_build: '2025-01-15T10:30:00Z',
  freshness_warning: null,
  outputs: [
    { path: 'dist/main.html', name: 'main.html', format: 'html', language: 'en', modified: '2025-01-15T10:30:00Z', size: 1024 },
    { path: 'dist/main.pdf', name: 'main.pdf', format: 'pdf', language: 'en', modified: '2025-01-15T10:30:00Z', size: 2048 },
  ],
  // Legacy fields for backward compatibility
  isBuilding: false,
  lastBuild: '2025-01-15T10:30:00Z',
  lastBuildStatus: 'success',
  availableFormats: ['html', 'pdf', 'pptx'],
};

export const mockBuildPublications = {
  publications: [
    {
      key: 'documentation',
      title: 'Documentation',
      pub_type: 'book',
      formats: ['html', 'pdf'],
      languages: ['en', 'no'],
    },
    {
      key: 'pitch-deck',
      title: 'Pitch Deck',
      pub_type: 'deck',
      formats: ['pptx', 'pdf'],
      languages: ['en'],
    },
  ],
  projectLanguages: ['en', 'no'],
};

export const mockPublications = {
  publications: [
    {
      key: 'main',
      name: 'Main Publication',
      description: 'Primary publication',
      formats: ['html', 'pdf', 'pptx'],
      languages: ['en', 'no'],
    },
  ],
};

export const mockPublishConfig = {
  publishDir: '/test/project/dist/Test Project',
  defaultDir: '/test/project/dist/Test Project',
  desktopDir: '~/Desktop/Test Project',
  useDesktop: false,
  projectName: 'Test Project',
};

export const mockBuildOutputs = {
  outputs: [
    { path: 'dist/main.html', name: 'main.html', format: 'html', language: 'en', modified: '2025-01-15T10:30:00Z', size: 1024 },
    { path: 'dist/main.pdf', name: 'main.pdf', format: 'pdf', language: 'en', modified: '2025-01-15T10:30:00Z', size: 2048 },
  ],
};

export const mockBuildPresets = {
  presets: [
    { id: 'default', name: 'Default', description: 'Standard layout' },
    { id: 'minimal', name: 'Minimal', description: 'Minimal layout' },
  ],
  default: 'default',
};

export const mockAISessions = {
  sessions: [],
  active_session: null,
};

export const mockAINotes = {
  notes: [],
};

export const mockAIQueue = {
  queue: [],
  processing: null,
};

export const mockAIResearch = {
  research_items: [],
};

export const mockRecentProjects = {
  current: { path: '/test/project', name: 'Test Project' },
  recent: [
    { path: '/test/project', name: 'Test Project', last_accessed: '2025-01-15', exists: true },
    { path: '/other/project', name: 'Other Project', last_accessed: '2025-01-10', exists: true },
  ],
};

export const mockVideoScript = {
  path: 'content/en/scripts/demo.yaml',
  filename: 'demo.yaml',
  content: 'title: Demo Video\nscenes: ...',
  parsed: {
    title: 'Demo Video',
    description: 'A demo video script',
    language: 'en',
    scenes: [
      { id: 'intro', name: 'Introduction', type: 'intro', duration: 5, voiceover: 'Welcome to the demo' },
      { id: 'main', name: 'Main Content', type: 'feature', duration: 10, voiceover: 'Here is the main content' },
      { id: 'outro', name: 'Conclusion', type: 'outro', duration: 5, voiceover: 'Thanks for watching' },
    ],
    narrator: { voice: 'Professional', speed: 1.0 },
  },
};

export const mockSceneNotes = {
  notes: {
    intro: { text: 'Consider adding music', created: '2025-01-15T10:00:00Z', scene_id: 'intro' },
  },
};

// API Handlers
export const handlers = [
  // Project
  http.get('/api/project', () => HttpResponse.json(mockProject)),
  http.get('/api/status', () => HttpResponse.json(mockStatus)),

  // Documents
  http.get('/api/documents/:language', () => HttpResponse.json(mockDocuments)),
  http.get('/api/document', () => HttpResponse.json({ path: 'test.md', filename: 'test.md', title: 'Test', content: '# Test' })),
  http.get('/api/file', ({ request }) => {
    const url = new URL(request.url);
    const path = url.searchParams.get('path');
    if (path?.includes('script')) {
      return HttpResponse.json(mockVideoScript);
    }
    return HttpResponse.json({ path, filename: 'test.md', content: '# Test' });
  }),

  // Insights
  http.get('/api/insights', () => HttpResponse.json(mockInsights)),
  http.get('/api/insights/quality-summary', () => HttpResponse.json(mockQualitySummary)),
  http.get('/api/insights/advanced', () => HttpResponse.json(mockAdvancedInsights)),

  // Quality
  http.get('/api/quality', () => HttpResponse.json(mockQuality)),

  // Freshness
  http.get('/api/freshness', () => HttpResponse.json(mockFreshness)),

  // Build
  http.get('/api/build/status', () => HttpResponse.json(mockBuildStatus)),
  http.get('/api/build/publications', () => HttpResponse.json(mockBuildPublications)),
  http.get('/api/build/publish-config', () => HttpResponse.json(mockPublishConfig)),
  http.get('/api/build/outputs', () => HttpResponse.json(mockBuildOutputs)),
  http.get('/api/build/presets', () => HttpResponse.json(mockBuildPresets)),
  http.post('/api/build', () => HttpResponse.json({ status: 'started', message: 'Build started' })),
  http.post('/api/build/start', () => HttpResponse.json({ status: 'started', formats: ['html'], languages: ['en'] })),
  http.post('/api/build/unified', () => HttpResponse.json({ status: 'started', publications: [], publish: true })),

  // Recent Projects
  http.get('/api/recent-projects', () => HttpResponse.json(mockRecentProjects)),

  // Publications
  http.get('/api/publications/status', () => HttpResponse.json(mockPublications)),

  // Scene Notes
  http.get('/api/scene-notes/:scriptPath', () => HttpResponse.json(mockSceneNotes)),
  http.post('/api/scene-notes/:scriptPath', () => HttpResponse.json({ status: 'saved', scene_id: 'intro' })),

  // Search
  http.get('/api/search', () => HttpResponse.json({ results: [] })),

  // Audit Log
  http.get('/api/audit-log', () => HttpResponse.json({ entries: [] })),

  // Media
  http.get('/api/media', () => HttpResponse.json({ files: [] })),

  // AI
  http.get('/api/ai/sessions', () => HttpResponse.json(mockAISessions)),
  http.get('/api/ai/notes', () => HttpResponse.json(mockAINotes)),
  http.get('/api/ai/queue', () => HttpResponse.json(mockAIQueue)),
  http.get('/api/ai/research', () => HttpResponse.json(mockAIResearch)),
];
