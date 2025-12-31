import { useMemo, useState, useEffect, useCallback, useRef } from 'react';
import {
  useInsights,
  useFreshness,
  useAdvancedInsights,
  useAuditLog,
} from '@/hooks/useApi';
import { useSettings } from '@/contexts';
import { ExpandableSection, Skeleton } from '@/components/ui';
import { InfoTooltip, METRIC_EXPLANATIONS } from '@/components/ui/InfoTooltip';
import {
  GraphCanvas,
  GraphErrorBoundary,
  toReagraphNodesFromKnowledgeGraph,
  toReagraphEdgesFromKnowledgeGraph,
  knowledgeGraphLegend,
} from '@/components/graphs';
import {
  Shield,
  AlertTriangle,
  AlertCircle,
  CheckCircle,
  Clock,
  Brain,
  Network,
  BookOpen,
  Code,
  TrendingUp,
  GitCommit,
  FileText,
  Target,
  Zap,
  Activity as ActivityIcon,
  User,
  Copy,
  Link2,
  HelpCircle,
  BarChart3,
  ListChecks,
  ChevronRight,
  ArrowDown,
} from 'lucide-react';

// Section IDs for "Jump to" navigation
const SECTION_IDS = {
  componentScores: 'section-component-scores',
  issues: 'section-issues',
  semantic: 'section-semantic',
  knowledgeGraph: 'section-knowledge-graph',
  readability: 'section-readability',
  freshness: 'section-freshness',
  codeSync: 'section-code-sync',
  advanced: 'section-advanced',
  activity: 'section-activity',
} as const;

type SectionId = keyof typeof SECTION_IDS;

// localStorage key for expanded sections
const EXPANDED_SECTIONS_KEY = 'media-engine-quality-expanded';

// Default expanded sections
const DEFAULT_EXPANDED: Record<SectionId, boolean> = {
  componentScores: true,
  issues: true,
  semantic: false,
  knowledgeGraph: false,
  readability: false,
  freshness: false,
  codeSync: false,
  advanced: false,
  activity: false,
};

// Load expanded state from localStorage
function loadExpandedState(): Record<SectionId, boolean> {
  try {
    const stored = localStorage.getItem(EXPANDED_SECTIONS_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      return { ...DEFAULT_EXPANDED, ...parsed };
    }
  } catch (error) {
    console.error('Failed to load expanded state:', error);
  }
  return DEFAULT_EXPANDED;
}

// Save expanded state to localStorage
function saveExpandedState(state: Record<SectionId, boolean>): void {
  try {
    localStorage.setItem(EXPANDED_SECTIONS_KEY, JSON.stringify(state));
  } catch (error) {
    console.error('Failed to save expanded state:', error);
  }
}

// Quick summary metric item component
interface QuickMetricProps {
  label: string;
  value: number;
  icon: React.ReactNode;
  status: 'success' | 'warning' | 'error';
  sectionId?: SectionId;
  onJumpTo?: (id: SectionId) => void;
}

function QuickMetric({ label, value, icon, status, sectionId, onJumpTo }: QuickMetricProps) {
  const statusColors = {
    success: 'bg-success/10 border-success/20 hover:bg-success/20',
    warning: 'bg-warning/10 border-warning/20 hover:bg-warning/20',
    error: 'bg-error/10 border-error/20 hover:bg-error/20',
  };
  const textColors = {
    success: 'text-success',
    warning: 'text-warning',
    error: 'text-error',
  };

  const content = (
    <>
      <div className={`${textColors[status]} mb-1`}>{icon}</div>
      <div className={`text-2xl font-bold ${textColors[status]}`}>{value}</div>
      <div className="text-xs text-base-content/60">{label}</div>
      {sectionId && onJumpTo && (
        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <ArrowDown size={12} className="text-base-content/40" />
        </div>
      )}
    </>
  );

  if (sectionId && onJumpTo) {
    return (
      <button
        onClick={() => onJumpTo(sectionId)}
        className={`group relative text-center p-3 rounded-lg border transition-colors cursor-pointer ${statusColors[status]}`}
      >
        {content}
      </button>
    );
  }

  return (
    <div className={`text-center p-3 rounded-lg border ${statusColors[status]}`}>
      {content}
    </div>
  );
}

// Top issue component for quick summary
interface TopIssueProps {
  issue: {
    severity: string;
    category: string;
    document: string;
    message: string;
  };
  index: number;
}

function TopIssue({ issue, index }: TopIssueProps) {
  const isCritical = issue.severity === 'critical';
  return (
    <div
      className={`flex items-start gap-3 p-3 rounded-lg ${
        isCritical ? 'bg-error/10 border border-error/20' : 'bg-warning/10 border border-warning/20'
      }`}
    >
      <div className="flex-shrink-0 mt-0.5">
        <span className={`badge badge-sm ${isCritical ? 'badge-error' : 'badge-warning'}`}>
          #{index + 1}
        </span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          {isCritical ? (
            <AlertCircle size={14} className="text-error flex-shrink-0" />
          ) : (
            <AlertTriangle size={14} className="text-warning flex-shrink-0" />
          )}
          <span className={`badge badge-xs ${isCritical ? 'badge-error' : 'badge-warning'}`}>
            {issue.category}
          </span>
          <span className="text-xs text-base-content/50 truncate">{issue.document}</span>
        </div>
        <p className="text-sm">{issue.message}</p>
      </div>
    </div>
  );
}

// Skeleton for quick summary while loading
function QuickSummarySkeleton() {
  return (
    <div className="card bg-base-200 border border-base-300">
      <div className="card-body">
        <div className="flex items-center gap-2 mb-4">
          <Skeleton width={20} height={20} variant="circular" />
          <Skeleton width={150} height={18} />
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="text-center p-3 rounded-lg bg-base-300">
              <Skeleton width={24} height={24} variant="circular" className="mx-auto mb-1" />
              <Skeleton width={40} height={28} className="mx-auto mb-1" />
              <Skeleton width={60} height={12} className="mx-auto" />
            </div>
          ))}
        </div>
        <Skeleton width={120} height={14} className="mb-3" />
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="p-3 rounded-lg bg-base-300">
              <div className="flex items-center gap-2 mb-2">
                <Skeleton width={24} height={16} variant="rounded" />
                <Skeleton width={60} height={14} variant="rounded" />
                <Skeleton width={100} height={12} />
              </div>
              <Skeleton width="90%" height={14} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============== MAIN QUALITY PAGE (Single Page View) ==============
export function Quality() {
  const { data: insights, isLoading: insightsLoading } = useInsights();
  const { data: freshness, isLoading: freshnessLoading } = useFreshness();
  const { data: advanced, isLoading: advancedLoading } = useAdvancedInsights();
  const { data: auditLog, isLoading: auditLoading } = useAuditLog();
  const { isDark } = useSettings();

  // Expanded sections state with localStorage persistence
  const [expandedSections, setExpandedSections] = useState<Record<SectionId, boolean>>(loadExpandedState);

  // Section refs for scrolling
  const sectionRefs = useRef<Record<SectionId, HTMLDivElement | null>>({
    componentScores: null,
    issues: null,
    semantic: null,
    knowledgeGraph: null,
    readability: null,
    freshness: null,
    codeSync: null,
    advanced: null,
    activity: null,
  });

  // Save to localStorage when expanded state changes
  useEffect(() => {
    saveExpandedState(expandedSections);
  }, [expandedSections]);

  // Toggle section expansion
  const toggleSection = useCallback((sectionId: SectionId) => {
    setExpandedSections((prev) => ({
      ...prev,
      [sectionId]: !prev[sectionId],
    }));
  }, []);

  // Jump to section: expand and scroll into view
  const jumpToSection = useCallback((sectionId: SectionId) => {
    // Expand the section if not already expanded
    setExpandedSections((prev) => ({
      ...prev,
      [sectionId]: true,
    }));

    // Scroll to section after a brief delay to allow expansion
    setTimeout(() => {
      const ref = sectionRefs.current[sectionId];
      if (ref) {
        ref.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }, 100);
  }, []);

  // Check if primary data is loading (show skeleton for summary)
  const isPrimaryLoading = insightsLoading || freshnessLoading;

  // Memoize graph data conversion
  const graphData = insights?.graph;
  const reagraphNodes = useMemo(() => {
    if (!graphData?.nodes) return [];
    return toReagraphNodesFromKnowledgeGraph(graphData.nodes, isDark);
  }, [graphData?.nodes, isDark]);

  const reagraphEdges = useMemo(() => {
    if (!graphData?.links) return [];
    return toReagraphEdgesFromKnowledgeGraph(graphData.links);
  }, [graphData?.links]);

  const health = insights?.health;
  const issues = useMemo(() => health?.issues ?? [], [health?.issues]);
  const components = health?.components;
  const errorCount = useMemo(() => issues.filter(i => i.severity === 'critical').length, [issues]);
  const warningCount = useMemo(() => issues.filter(i => i.severity === 'warning').length, [issues]);

  const semantic = advanced?.semantic;
  const kg = advanced?.knowledge_graph;
  const norwegian = advanced?.norwegian_readability;
  const predictive = advanced?.predictive_freshness;
  const codesync = advanced?.enhanced_codesync;
  const analysis = advanced?.advanced_analysis;

  const totalItems = freshness?.total_items ?? 0;
  const freshCount = freshness?.fresh_count ?? 0;
  const freshPercent = totalItems > 0 ? Math.round((freshCount / totalItems) * 100) : 0;

  const recentChanges = insights?.statistics?.activity?.recent_changes ?? [];
  const entries = auditLog?.entries ?? [];

  // Compute summary metrics for quick view
  const duplicateCount = semantic?.near_duplicate_count ?? 0;
  const orphanCount = kg?.orphan_count ?? 0;
  const staleCount = freshness?.stale_count ?? 0;
  const syntaxErrorCount = codesync?.syntax_error_count ?? 0;

  // Get top 3 most critical issues (prioritize critical over warning)
  const topIssues = useMemo(() => {
    const sorted = [...issues].sort((a, b) => {
      if (a.severity === 'critical' && b.severity !== 'critical') return -1;
      if (a.severity !== 'critical' && b.severity === 'critical') return 1;
      return 0;
    });
    return sorted.slice(0, 3);
  }, [issues]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Quality</h1>

      {/* Score Hero */}
      <div className="card bg-gradient-to-br from-base-200 to-base-300 border border-base-300">
        <div className="card-body">
          <div className="flex items-center gap-6">
            <Shield size={40} className={health?.overall && health.overall >= 80 ? 'text-success' : 'text-warning'} />
            <div className="flex-1">
              <div className="flex items-center gap-3">
                <span className="text-4xl font-bold">{Math.round(health?.overall ?? 0)}</span>
                <span className="text-base-content/60 flex items-center gap-1">
                  Quality Score
                  <InfoTooltip {...METRIC_EXPLANATIONS.qualityScore} />
                </span>
              </div>
            </div>
            <div className={`badge badge-lg ${health?.status === 'excellent' ? 'badge-success' : health?.status === 'good' ? 'badge-warning' : 'badge-error'}`}>
              {health?.status ?? 'unknown'}
            </div>
          </div>
        </div>
      </div>

      {/* Quick Summary - At a Glance */}
      {isPrimaryLoading ? (
        <QuickSummarySkeleton />
      ) : (
        <div className="card bg-base-200 border border-base-300">
          <div className="card-body">
            {/* Header */}
            <div className="flex items-center gap-2 mb-4">
              <Zap size={20} className="text-primary" />
              <h2 className="font-semibold">At a Glance</h2>
              <span className="text-sm text-base-content/50">Click metrics to jump to details</span>
            </div>

            {/* Key Metrics Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
              <QuickMetric
                label="Duplicates"
                value={duplicateCount}
                icon={<Copy size={20} />}
                status={duplicateCount === 0 ? 'success' : duplicateCount <= 3 ? 'warning' : 'error'}
                sectionId="semantic"
                onJumpTo={jumpToSection}
              />
              <QuickMetric
                label="Orphan Concepts"
                value={orphanCount}
                icon={<Brain size={20} />}
                status={orphanCount === 0 ? 'success' : orphanCount <= 5 ? 'warning' : 'error'}
                sectionId="knowledgeGraph"
                onJumpTo={jumpToSection}
              />
              <QuickMetric
                label="Stale Docs"
                value={staleCount}
                icon={<Clock size={20} />}
                status={staleCount === 0 ? 'success' : staleCount <= 5 ? 'warning' : 'error'}
                sectionId="freshness"
                onJumpTo={jumpToSection}
              />
              <QuickMetric
                label="Syntax Errors"
                value={syntaxErrorCount}
                icon={<Code size={20} />}
                status={syntaxErrorCount === 0 ? 'success' : 'error'}
                sectionId="codeSync"
                onJumpTo={jumpToSection}
              />
            </div>

            {/* Top Issues Preview */}
            {topIssues.length > 0 ? (
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-medium text-base-content/70">Top Issues</h3>
                  {issues.length > 3 && (
                    <button
                      onClick={() => jumpToSection('issues')}
                      className="text-xs text-primary hover:underline flex items-center gap-1"
                    >
                      View all {issues.length} issues
                      <ChevronRight size={12} />
                    </button>
                  )}
                </div>
                <div className="space-y-2">
                  {topIssues.map((issue, idx) => (
                    <TopIssue key={idx} issue={issue} index={idx} />
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-3 p-4 rounded-lg bg-success/10 border border-success/20">
                <CheckCircle size={24} className="text-success" />
                <div>
                  <div className="font-medium text-success">No Issues Found</div>
                  <div className="text-sm text-base-content/60">Your content is in great shape!</div>
                </div>
              </div>
            )}

            {/* Issue Summary Row */}
            <div className="flex items-center gap-4 pt-4 mt-4 border-t border-base-300">
              <div className="flex items-center gap-2">
                <AlertCircle size={16} className="text-error" />
                <span className="text-sm">
                  <span className="font-bold">{errorCount}</span> critical
                </span>
              </div>
              <div className="flex items-center gap-2">
                <AlertTriangle size={16} className="text-warning" />
                <span className="text-sm">
                  <span className="font-bold">{warningCount}</span> warnings
                </span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle size={16} className="text-success" />
                <span className="text-sm">
                  <span className="font-bold">{health?.document_count ?? 0}</span> documents
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Component Scores */}
      <div ref={(el) => { sectionRefs.current.componentScores = el; }} id={SECTION_IDS.componentScores}>
        <ExpandableSection
          title="Component Scores"
          description="Weighted health factors across all quality dimensions"
          icon={<ListChecks size={20} />}
          isExpanded={expandedSections.componentScores}
          onToggle={() => toggleSection('componentScores')}
        >
        <div className="space-y-4">
          {components && Object.entries(components).map(([key, value]) => {
            const explanation = METRIC_EXPLANATIONS[key as keyof typeof METRIC_EXPLANATIONS];
            const numValue = value as number;
            return (
              <div key={key} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center gap-1 capitalize">
                    {key}
                    {explanation && <InfoTooltip title={explanation.title} content={explanation.content} />}
                  </span>
                  <span>{numValue}%</span>
                </div>
                <progress
                  className={`progress w-full ${numValue >= 90 ? 'progress-success' : numValue >= 70 ? 'progress-warning' : 'progress-error'}`}
                  value={numValue}
                  max="100"
                ></progress>
              </div>
            );
          })}
        </div>
        </ExpandableSection>
      </div>

      {/* Issues */}
      {issues.length > 0 && (
        <div ref={(el) => { sectionRefs.current.issues = el; }} id={SECTION_IDS.issues}>
          <ExpandableSection
            title="Issues"
            description={`${issues.length} issues to address`}
            icon={<AlertTriangle size={20} />}
            statusBadge={errorCount > 0 ? 'error' : 'warning'}
            statusCount={issues.length}
            isExpanded={expandedSections.issues}
            onToggle={() => toggleSection('issues')}
          >
          <div className="space-y-3">
            {issues.slice(0, 10).map((issue, idx) => (
              <div key={idx} className="flex items-start gap-3 p-3 rounded-lg bg-base-300">
                <AlertTriangle size={14} className={issue.severity === 'critical' ? 'text-error' : 'text-warning'} />
                <div className="flex-1 min-w-0 space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <div className={`badge badge-sm ${issue.severity === 'critical' ? 'badge-error' : 'badge-warning'}`}>
                      {issue.category}
                    </div>
                    <span className="text-sm text-base-content/60 truncate">{issue.document}</span>
                  </div>
                  <p className="text-sm">{issue.message}</p>
                </div>
              </div>
            ))}
            {issues.length > 10 && (
              <p className="text-sm text-base-content/60 text-center">...and {issues.length - 10} more</p>
            )}
          </div>
          </ExpandableSection>
        </div>
      )}

      {/* Semantic Analysis */}
      <div ref={(el) => { sectionRefs.current.semantic = el; }} id={SECTION_IDS.semantic}>
        <ExpandableSection
          title="Semantic Analysis"
          description="Content similarity, duplicates, and terminology consistency"
          icon={<Copy size={20} />}
          tooltip={METRIC_EXPLANATIONS.semanticDuplicates}
          statusBadge={(semantic?.near_duplicate_count ?? 0) > 0 ? 'warning' : undefined}
          statusCount={semantic?.near_duplicate_count}
          isExpanded={expandedSections.semantic}
          onToggle={() => toggleSection('semantic')}
          isLoading={advancedLoading}
        >
        {!semantic?.available ? (
          <div className="text-center py-6 text-base-content/60">
            <Zap size={24} className="mx-auto mb-2 opacity-30" />
            <p>{semantic?.reason || 'Semantic analysis not available'}</p>
          </div>
        ) : semantic?.error ? (
          <div className="text-center py-6 text-error">
            <AlertCircle size={24} className="mx-auto mb-2" />
            <p>{semantic.error}</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-3 rounded-lg bg-base-300">
                <div className="text-2xl font-bold text-warning">{semantic.near_duplicate_count ?? 0}</div>
                <div className="text-xs text-base-content/60 flex items-center justify-center gap-1">
                  Near Duplicates
                  <InfoTooltip {...METRIC_EXPLANATIONS.semanticDuplicates} />
                </div>
              </div>
              <div className="text-center p-3 rounded-lg bg-base-300">
                <div className="text-2xl font-bold text-primary">{semantic.drift_count ?? 0}</div>
                <div className="text-xs text-base-content/60 flex items-center justify-center gap-1">
                  Terminology Drift
                  <InfoTooltip {...METRIC_EXPLANATIONS.terminologyDrift} />
                </div>
              </div>
              <div className="text-center p-3 rounded-lg bg-base-300">
                <div className="text-2xl font-bold text-success">{semantic.cluster_count ?? 0}</div>
                <div className="text-xs text-base-content/60">Content Clusters</div>
              </div>
            </div>

            {semantic.near_duplicates && semantic.near_duplicates.length > 0 && (
              <div className="pt-4 border-t border-base-300">
                <h4 className="font-medium mb-2">Near-Duplicate Pairs</h4>
                <div className="space-y-2">
                  {semantic.near_duplicates.slice(0, 5).map((dup, idx) => (
                    <div key={idx} className="flex items-center gap-2 p-2 rounded bg-base-300 text-sm">
                      <FileText size={14} className="text-base-content/60 flex-shrink-0" />
                      <span className="truncate">{dup.doc1_path}</span>
                      <span className="text-base-content/50">~</span>
                      <span className="truncate">{dup.doc2_path}</span>
                      <span className="badge badge-warning badge-sm ml-auto">{Math.round(dup.similarity * 100)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        </ExpandableSection>
      </div>

      {/* Knowledge Graph */}
      <div ref={(el) => { sectionRefs.current.knowledgeGraph = el; }} id={SECTION_IDS.knowledgeGraph}>
        <ExpandableSection
          title="Knowledge Graph"
          description="Document relationships, concepts, and prerequisites"
          icon={<Network size={20} />}
          tooltip={METRIC_EXPLANATIONS.orphanConcepts}
          statusBadge={(kg?.orphan_count ?? 0) > 0 ? 'warning' : undefined}
          statusCount={kg?.orphan_count}
          isExpanded={expandedSections.knowledgeGraph}
          onToggle={() => toggleSection('knowledgeGraph')}
          isLoading={advancedLoading}
        >
        {!kg?.available ? (
          <div className="text-center py-6 text-base-content/60">
            <Zap size={24} className="mx-auto mb-2 opacity-30" />
            <p>{kg?.reason || 'Knowledge graph not available'}</p>
          </div>
        ) : kg?.error ? (
          <div className="text-center py-6 text-error">
            <AlertCircle size={24} className="mx-auto mb-2" />
            <p>{kg.error}</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-4 gap-4">
              <div className="text-center p-3 rounded-lg bg-base-300">
                <div className="text-2xl font-bold text-primary">{kg.metrics?.total_nodes ?? kg.node_count ?? 0}</div>
                <div className="text-xs text-base-content/60">Nodes</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-base-300">
                <div className="text-2xl font-bold text-success">{kg.metrics?.total_edges ?? kg.edge_count ?? 0}</div>
                <div className="text-xs text-base-content/60">Edges</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-base-300">
                <div className="text-2xl font-bold text-warning">{kg.orphan_count ?? 0}</div>
                <div className="text-xs text-base-content/60 flex items-center justify-center gap-1">
                  Orphans
                  <InfoTooltip {...METRIC_EXPLANATIONS.orphanConcepts} />
                </div>
              </div>
              <div className="text-center p-3 rounded-lg bg-base-300">
                <div className="text-2xl font-bold text-error">{kg.prereq_issue_count ?? 0}</div>
                <div className="text-xs text-base-content/60 flex items-center justify-center gap-1">
                  Prereq Issues
                  <InfoTooltip {...METRIC_EXPLANATIONS.prerequisiteIssues} />
                </div>
              </div>
            </div>

            {reagraphNodes.length > 0 && (
              <div className="pt-4 border-t border-base-300">
                <h4 className="font-medium mb-2">Interactive Graph</h4>
                <p className="text-sm text-base-content/60 mb-3">Drag to pan, scroll to zoom, click nodes for details.</p>
                <GraphErrorBoundary fallbackHeight={350}>
                  <GraphCanvas
                    nodes={reagraphNodes}
                    edges={reagraphEdges}
                    height={350}
                    showToolbar={true}
                    showLegend={true}
                    legendItems={knowledgeGraphLegend}
                    layoutType="forceDirected2d"
                  />
                </GraphErrorBoundary>
              </div>
            )}

            {kg.orphan_concepts && kg.orphan_concepts.length > 0 && (
              <div className="pt-4 border-t border-base-300">
                <h4 className="font-medium mb-2">Orphan Concepts</h4>
                <div className="flex flex-wrap gap-2">
                  {kg.orphan_concepts.slice(0, 8).map((orphan, idx) => {
                    const name = typeof orphan === 'string' ? orphan : orphan?.concept ?? 'Unknown';
                    return (
                      <span key={idx} className="badge badge-warning gap-1">
                        <Brain size={12} />
                        {name}
                      </span>
                    );
                  })}
                  {kg.orphan_concepts.length > 8 && (
                    <span className="badge badge-ghost">+{kg.orphan_concepts.length - 8} more</span>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
        </ExpandableSection>
      </div>

      {/* Readability */}
      <div ref={(el) => { sectionRefs.current.readability = el; }} id={SECTION_IDS.readability}>
        <ExpandableSection
          title="Readability"
          description="Content accessibility and Norwegian LIX analysis"
          icon={<BookOpen size={20} />}
          tooltip={METRIC_EXPLANATIONS.readability}
          statusBadge={norwegian?.difficult_count && norwegian.difficult_count > 0 ? 'warning' : undefined}
          statusCount={norwegian?.difficult_count}
          isExpanded={expandedSections.readability}
          onToggle={() => toggleSection('readability')}
          isLoading={advancedLoading}
        >
        <div className="space-y-4">
          <div className="flex items-center gap-4 p-4 rounded-lg bg-base-300">
            <BookOpen size={32} className={insights?.health?.components?.readability && insights.health.components.readability >= 80 ? 'text-success' : 'text-warning'} />
            <div>
              <div className="text-2xl font-bold">{Math.round(insights?.health?.components?.readability ?? 0)}%</div>
              <div className="text-sm text-base-content/60 flex items-center gap-1">
                Overall Readability
                <InfoTooltip {...METRIC_EXPLANATIONS.readability} />
              </div>
            </div>
          </div>

          {norwegian?.available ? (
            <div className="pt-4 border-t border-base-300">
              <h4 className="font-medium mb-2 flex items-center gap-2">
                Norwegian LIX Analysis
                <InfoTooltip {...METRIC_EXPLANATIONS.lixScore} />
              </h4>
              <div className="grid grid-cols-2 gap-4 mb-3">
                <div className="text-center p-3 rounded-lg bg-base-300">
                  <div className="text-2xl font-bold">{norwegian.average_lix?.toFixed(1) ?? 'N/A'}</div>
                  <div className="text-xs text-base-content/60">Average LIX</div>
                </div>
                <div className="text-center p-3 rounded-lg bg-base-300">
                  <div className="text-2xl font-bold">{norwegian.documents_analyzed ?? 0}</div>
                  <div className="text-xs text-base-content/60">Documents Analyzed</div>
                </div>
              </div>
              <div className="flex flex-wrap gap-2 text-xs">
                <span className="px-2 py-1 rounded bg-success/20 text-success">&lt;25 Very Easy</span>
                <span className="px-2 py-1 rounded bg-success/10 text-success/80">25-34 Easy</span>
                <span className="px-2 py-1 rounded bg-warning/20 text-warning">35-44 Medium</span>
                <span className="px-2 py-1 rounded bg-error/20 text-error">45-54 Difficult</span>
                <span className="px-2 py-1 rounded bg-error/30 text-error">&gt;54 Very Difficult</span>
              </div>
            </div>
          ) : norwegian?.reason ? (
            <p className="text-sm text-base-content/60 pt-4 border-t border-base-300">
              Norwegian LIX: {norwegian.reason}
            </p>
          ) : null}
        </div>
        </ExpandableSection>
      </div>

      {/* Freshness & Staleness */}
      <div ref={(el) => { sectionRefs.current.freshness = el; }} id={SECTION_IDS.freshness}>
        <ExpandableSection
          title="Freshness & Staleness"
          description="Content freshness tracking and predictive analysis"
          icon={<Clock size={20} />}
          tooltip={METRIC_EXPLANATIONS.freshness}
          statusBadge={(freshness?.stale_count ?? 0) > 0 ? 'warning' : undefined}
          statusCount={freshness?.stale_count}
          isExpanded={expandedSections.freshness}
          onToggle={() => toggleSection('freshness')}
        >
        <div className="space-y-4">
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center p-3 rounded-lg bg-success/10">
              <div className="text-2xl font-bold text-success">{freshCount}</div>
              <div className="text-xs text-base-content/60">Fresh</div>
            </div>
            <div className="text-center p-3 rounded-lg bg-warning/10">
              <div className="text-2xl font-bold text-warning">{freshness?.stale_count ?? 0}</div>
              <div className="text-xs text-base-content/60">Stale</div>
            </div>
            <div className="text-center p-3 rounded-lg bg-error/10">
              <div className="text-2xl font-bold text-error">{freshness?.expired_count ?? 0}</div>
              <div className="text-xs text-base-content/60">Expired</div>
            </div>
            <div className="text-center p-3 rounded-lg bg-primary/10">
              <div className="text-2xl font-bold text-primary">{freshPercent}%</div>
              <div className="text-xs text-base-content/60 flex items-center justify-center gap-1">
                Overall
                <InfoTooltip {...METRIC_EXPLANATIONS.freshnessProgress} />
              </div>
            </div>
          </div>

          {predictive?.available && (
            <div className="pt-4 border-t border-base-300">
              <h4 className="font-medium mb-2 flex items-center gap-2">
                Predictive Staleness
                <InfoTooltip {...METRIC_EXPLANATIONS.predictiveStaleness} />
              </h4>
              <div className="grid grid-cols-4 gap-3 mb-3">
                <div className="text-center p-2 rounded bg-success/10">
                  <div className="font-bold text-success">{predictive.summary?.low_risk ?? 0}</div>
                  <div className="text-xs">Low Risk</div>
                </div>
                <div className="text-center p-2 rounded bg-warning/10">
                  <div className="font-bold text-warning">{predictive.summary?.medium_risk ?? 0}</div>
                  <div className="text-xs">Medium</div>
                </div>
                <div className="text-center p-2 rounded bg-error/10">
                  <div className="font-bold text-error">{predictive.summary?.high_risk ?? 0}</div>
                  <div className="text-xs">High</div>
                </div>
                <div className="text-center p-2 rounded bg-error/20">
                  <div className="font-bold text-error">{predictive.summary?.critical_risk ?? 0}</div>
                  <div className="text-xs">Critical</div>
                </div>
              </div>
            </div>
          )}
        </div>
        </ExpandableSection>
      </div>

      {/* Code Sync */}
      <div ref={(el) => { sectionRefs.current.codeSync = el; }} id={SECTION_IDS.codeSync}>
        <ExpandableSection
          title="Code Synchronization"
          description="Code example validation and API reference checks"
          icon={<Code size={20} />}
          tooltip={METRIC_EXPLANATIONS.syntaxErrors}
          statusBadge={(codesync?.syntax_error_count ?? 0) > 0 ? 'error' : (codesync?.deprecated_count ?? 0) > 0 ? 'warning' : undefined}
          statusCount={(codesync?.syntax_error_count ?? 0) + (codesync?.deprecated_count ?? 0)}
          isExpanded={expandedSections.codeSync}
          onToggle={() => toggleSection('codeSync')}
          isLoading={advancedLoading}
        >
        {!codesync?.available ? (
          <div className="text-center py-6 text-base-content/60">
            <Zap size={24} className="mx-auto mb-2 opacity-30" />
            <p>{codesync?.reason || 'Code sync analysis not available'}</p>
          </div>
        ) : codesync?.error ? (
          <div className="text-center py-6 text-error">
            <AlertCircle size={24} className="mx-auto mb-2" />
            <p>{codesync.error}</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-3 rounded-lg bg-base-300">
                <div className="text-2xl font-bold text-error">{codesync.syntax_error_count ?? 0}</div>
                <div className="text-xs text-base-content/60 flex items-center justify-center gap-1">
                  Syntax Errors
                  <InfoTooltip {...METRIC_EXPLANATIONS.syntaxErrors} />
                </div>
              </div>
              <div className="text-center p-3 rounded-lg bg-base-300">
                <div className="text-2xl font-bold text-warning">{codesync.deprecated_count ?? 0}</div>
                <div className="text-xs text-base-content/60 flex items-center justify-center gap-1">
                  Deprecated
                  <InfoTooltip {...METRIC_EXPLANATIONS.deprecatedPatterns} />
                </div>
              </div>
              <div className="text-center p-3 rounded-lg bg-base-300">
                <div className="text-2xl font-bold text-primary">{codesync.api_issue_count ?? 0}</div>
                <div className="text-xs text-base-content/60 flex items-center justify-center gap-1">
                  API Issues
                  <InfoTooltip {...METRIC_EXPLANATIONS.apiIssues} />
                </div>
              </div>
            </div>

            {codesync.syntax_errors && codesync.syntax_errors.length > 0 && (
              <div className="pt-4 border-t border-base-300">
                <h4 className="font-medium mb-2">Syntax Errors</h4>
                <div className="space-y-2">
                  {codesync.syntax_errors.slice(0, 5).map((issue, idx) => (
                    <div key={idx} className="p-2 rounded bg-base-300 text-sm">
                      <div className="flex items-center gap-2">
                        <AlertCircle size={14} className="text-error" />
                        <span className="truncate">{issue.document}</span>
                        <span className="badge badge-error badge-sm">Line {issue.line}</span>
                      </div>
                      <p className="text-xs text-base-content/60 mt-1 pl-5">{issue.message}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        </ExpandableSection>
      </div>

      {/* Advanced Analysis */}
      <div ref={(el) => { sectionRefs.current.advanced = el; }} id={SECTION_IDS.advanced}>
        <ExpandableSection
          title="Advanced Analysis"
          description="Audience drift, question coverage, cross-references, and style"
          icon={<TrendingUp size={20} />}
          isExpanded={expandedSections.advanced}
          onToggle={() => toggleSection('advanced')}
          isLoading={advancedLoading}
        >
        {!analysis?.available ? (
          <div className="text-center py-6 text-base-content/60">
            <Zap size={24} className="mx-auto mb-2 opacity-30" />
            <p>{analysis?.reason || 'Advanced analysis not available'}</p>
          </div>
        ) : analysis?.error ? (
          <div className="text-center py-6 text-error">
            <AlertCircle size={24} className="mx-auto mb-2" />
            <p>{analysis.error}</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {analysis.audience_drift && (
                <div className="text-center p-3 rounded-lg bg-base-300">
                  <Target size={20} className="mx-auto mb-1 text-primary" />
                  <div className="font-bold">{analysis.audience_drift.trend}</div>
                  <div className="text-xs text-base-content/60">Audience Drift</div>
                </div>
              )}
              {analysis.question_coverage && (
                <div className="text-center p-3 rounded-lg bg-base-300">
                  <HelpCircle size={20} className="mx-auto mb-1 text-success" />
                  <div className="font-bold">{analysis.question_coverage.coverage_percent?.toFixed(0) ?? 0}%</div>
                  <div className="text-xs text-base-content/60">Question Coverage</div>
                </div>
              )}
              {analysis.cross_references && (
                <div className="text-center p-3 rounded-lg bg-base-300">
                  <Link2 size={20} className="mx-auto mb-1 text-info" />
                  <div className="font-bold">{analysis.cross_references.total_references ?? 0}</div>
                  <div className="text-xs text-base-content/60">Cross-References</div>
                </div>
              )}
              {analysis.style_consistency && (
                <div className="text-center p-3 rounded-lg bg-base-300">
                  <BarChart3 size={20} className="mx-auto mb-1 text-warning" />
                  <div className="font-bold">{analysis.style_consistency.style_score?.toFixed(0) ?? 0}</div>
                  <div className="text-xs text-base-content/60">Style Score</div>
                </div>
              )}
            </div>

            {(analysis.question_coverage?.unanswered_questions?.length ?? 0) > 0 && (
              <div className="pt-4 border-t border-base-300">
                <h4 className="font-medium mb-2">Unanswered Questions</h4>
                <div className="space-y-1">
                  {analysis.question_coverage?.unanswered_questions?.slice(0, 5).map((q, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-sm">
                      <HelpCircle size={14} className="text-warning flex-shrink-0" />
                      <span>{q}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        </ExpandableSection>
      </div>

      {/* Activity Section */}
      <div ref={(el) => { sectionRefs.current.activity = el; }} id={SECTION_IDS.activity}>
        <ExpandableSection
          title="Recent Activity"
          description="Git commits and system audit log"
          icon={<GitCommit size={20} />}
          isExpanded={expandedSections.activity}
          onToggle={() => toggleSection('activity')}
          isLoading={auditLoading}
        >
        <div className="space-y-6">
          {/* Recent Commits */}
          <div>
            <h4 className="font-medium mb-3 flex items-center gap-2">
              Recent Commits
              <InfoTooltip {...METRIC_EXPLANATIONS.recentCommits} />
            </h4>
            {recentChanges.length > 0 ? (
              <div className="space-y-2">
                {recentChanges.slice(0, 5).map((change, idx) => (
                  <div key={idx} className="p-3 rounded-lg bg-base-300">
                    <div className="flex items-start gap-3">
                      <GitCommit size={14} className="text-primary flex-shrink-0 mt-0.5" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium truncate text-sm">{change.message}</span>
                          <div className="badge badge-ghost badge-sm">{change.hash.substring(0, 7)}</div>
                        </div>
                        <div className="flex items-center gap-4 text-xs text-base-content/60">
                          <span className="flex items-center gap-1"><User size={10} /> {change.author}</span>
                          <span className="flex items-center gap-1"><Clock size={10} /> {new Date(change.date).toLocaleDateString()}</span>
                          <span className="flex items-center gap-1"><FileText size={10} /> {change.files.length} files</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-4">
                <GitCommit size={20} className="text-base-content/30 mx-auto mb-2" />
                <p className="text-sm text-base-content/60">No recent commits</p>
              </div>
            )}
          </div>

          {/* Audit Log */}
          <div className="pt-4 border-t border-base-300">
            <h4 className="font-medium mb-3">Audit Log</h4>
            {entries.length > 0 ? (
              <div className="space-y-2">
                {entries.slice(0, 8).map((entry, idx) => (
                  <div key={idx} className="flex items-center gap-3 p-2 rounded-lg bg-base-300 text-sm">
                    <ActivityIcon size={12} className="text-base-content/40 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <span className="font-medium">{entry.action}</span>
                      {entry.details && <span className="text-base-content/60 ml-2">{entry.details}</span>}
                    </div>
                    <span className="text-xs text-base-content/50">{new Date(entry.timestamp).toLocaleString()}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-4">
                <ActivityIcon size={20} className="text-base-content/30 mx-auto mb-2" />
                <p className="text-sm text-base-content/60">No audit log entries</p>
              </div>
            )}
          </div>
        </div>
        </ExpandableSection>
      </div>

      {/* All Clear Message */}
      {issues.length === 0 && (
        <div className="card bg-base-200">
          <div className="card-body items-center text-center py-8">
            <CheckCircle size={40} className="text-success mb-2" />
            <h3 className="font-semibold">All Clear!</h3>
            <p className="text-base-content/60 text-sm">No quality issues found.</p>
          </div>
        </div>
      )}
    </div>
  );
}
