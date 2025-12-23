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
    status: 'Good',
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
    issues: [],
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
    { type: 'warning', category: 'Links', message: 'Broken link found', file: 'intro.md', line: 42 },
    { type: 'info', category: 'Readability', message: 'Consider simplifying sentence', file: 'setup.md', line: 15 },
  ],
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
  isBuilding: false,
  lastBuild: '2025-01-15T10:30:00Z',
  lastBuildStatus: 'success',
  availableFormats: ['html', 'pdf', 'pptx'],
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

  // Quality
  http.get('/api/quality', () => HttpResponse.json(mockQuality)),

  // Freshness
  http.get('/api/freshness', () => HttpResponse.json(mockFreshness)),

  // Build
  http.get('/api/build/status', () => HttpResponse.json(mockBuildStatus)),
  http.post('/api/build', () => HttpResponse.json({ status: 'started', message: 'Build started' })),

  // Recent Projects
  http.get('/api/recent-projects', () => HttpResponse.json(mockRecentProjects)),

  // Scene Notes
  http.get('/api/scene-notes/:scriptPath', () => HttpResponse.json(mockSceneNotes)),
  http.post('/api/scene-notes/:scriptPath', () => HttpResponse.json({ status: 'saved', scene_id: 'intro' })),

  // Search
  http.get('/api/search', () => HttpResponse.json({ results: [] })),

  // Audit Log
  http.get('/api/audit-log', () => HttpResponse.json({ entries: [] })),

  // Media
  http.get('/api/media', () => HttpResponse.json({ files: [] })),
];
