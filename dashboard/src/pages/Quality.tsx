import { Routes, Route } from 'react-router-dom';
import { useMemo } from 'react';
import {
  useInsights,
  useFreshness,
  useAdvancedInsights,
  useAuditLog,
} from '@/hooks/useApi';
import { useSettings } from '@/contexts';
import { SubTabs, ExpandableSection } from '@/components/ui';
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
} from 'lucide-react';

// Simplified to 3 tabs
const tabs = [
  { path: '', label: 'Overview' },
  { path: 'analysis', label: 'Analysis' },
  { path: 'activity', label: 'Activity' },
];

// Loading component
function Loading({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="text-center">
        <span className="loading loading-spinner loading-lg text-primary"></span>
        <p className="mt-4 text-base-content/60">{message}</p>
      </div>
    </div>
  );
}

// ============== OVERVIEW TAB ==============
function OverviewView() {
  const { data: insights, isLoading } = useInsights();

  if (isLoading) {
    return <Loading message="Loading quality overview..." />;
  }

  const health = insights?.health;
  const issues = health?.issues ?? [];
  const components = health?.components;

  const errorCount = issues.filter(i => i.severity === 'critical').length;
  const warningCount = issues.filter(i => i.severity === 'warning').length;

  return (
    <div className="space-y-6">
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

      {/* Issue Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className={`card bg-base-200 ${errorCount > 0 ? 'border border-error/30' : ''}`}>
          <div className="card-body p-4 flex-row items-center gap-4">
            <AlertCircle size={20} className="text-error" />
            <span className="text-2xl font-bold">{errorCount}</span>
            <span className="text-base-content/60 flex items-center gap-1">
              Critical
              <InfoTooltip
                title="Critical Issues"
                content="Blocking issues that must be resolved before publishing. Includes broken links, missing required content, and validation errors."
              />
            </span>
          </div>
        </div>
        <div className={`card bg-base-200 ${warningCount > 0 ? 'border border-warning/30' : ''}`}>
          <div className="card-body p-4 flex-row items-center gap-4">
            <AlertTriangle size={20} className="text-warning" />
            <span className="text-2xl font-bold">{warningCount}</span>
            <span className="text-base-content/60">Warnings</span>
          </div>
        </div>
        <div className="card bg-base-200 border border-success/30">
          <div className="card-body p-4 flex-row items-center gap-4">
            <CheckCircle size={20} className="text-success" />
            <span className="text-2xl font-bold">{health?.document_count ?? 0}</span>
            <span className="text-base-content/60 flex items-center gap-1">
              Documents
              <InfoTooltip {...METRIC_EXPLANATIONS.documentCount} />
            </span>
          </div>
        </div>
      </div>

      {/* Component Scores */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="card-title text-lg">Component Scores</h3>
          <p className="text-sm text-base-content/60 mb-4">Weighted health factors</p>
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
        </div>
      </div>

      {/* Issues */}
      {issues.length > 0 && (
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="card-title text-lg">Issues</h3>
            <p className="text-sm text-base-content/60 mb-4">{issues.length} to address</p>
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
          </div>
        </div>
      )}

      {issues.length === 0 && (
        <div className="card bg-base-200">
          <div className="card-body items-center text-center py-12">
            <CheckCircle size={48} className="text-success mb-4" />
            <h3 className="text-lg font-semibold">All Clear!</h3>
            <p className="text-base-content/60">No quality issues found.</p>
          </div>
        </div>
      )}
    </div>
  );
}

// ============== ANALYSIS TAB (Consolidated from 6 tabs) ==============
function AnalysisView() {
  const { data: advanced, isLoading: advancedLoading } = useAdvancedInsights();
  const { data: insights, isLoading: insightsLoading } = useInsights();
  const { data: freshness, isLoading: freshnessLoading } = useFreshness();
  const { isDark } = useSettings();

  const isLoading = advancedLoading || insightsLoading || freshnessLoading;

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

  if (isLoading) {
    return <Loading message="Loading analysis modules..." />;
  }

  const semantic = advanced?.semantic;
  const kg = advanced?.knowledge_graph;
  const norwegian = advanced?.norwegian_readability;
  const predictive = advanced?.predictive_freshness;
  const codesync = advanced?.enhanced_codesync;
  const analysis = advanced?.advanced_analysis;

  // Calculate summary metrics
  const totalItems = freshness?.total_items ?? 0;
  const freshCount = freshness?.fresh_count ?? 0;
  const freshPercent = totalItems > 0 ? Math.round((freshCount / totalItems) * 100) : 0;

  return (
    <div className="space-y-4">
      <p className="text-base-content/60 mb-2">
        Expand each section to view detailed analysis. Modules with issues show warning badges.
      </p>

      {/* Semantic Analysis */}
      <ExpandableSection
        title="Semantic Analysis"
        description="Content similarity, duplicates, and terminology consistency"
        icon={<Copy size={20} />}
        tooltip={METRIC_EXPLANATIONS.semanticDuplicates}
        statusBadge={(semantic?.near_duplicate_count ?? 0) > 0 ? 'warning' : undefined}
        statusCount={semantic?.near_duplicate_count}
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
            {/* Metrics */}
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

            {/* Near Duplicates */}
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

      {/* Knowledge Graph */}
      <ExpandableSection
        title="Knowledge Graph"
        description="Document relationships, concepts, and prerequisites"
        icon={<Network size={20} />}
        tooltip={METRIC_EXPLANATIONS.orphanConcepts}
        statusBadge={(kg?.orphan_count ?? 0) > 0 ? 'warning' : undefined}
        statusCount={kg?.orphan_count}
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
            {/* Metrics */}
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

            {/* Graph Visualization */}
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

            {/* Orphan Concepts */}
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

      {/* Readability */}
      <ExpandableSection
        title="Readability"
        description="Content accessibility and Norwegian LIX analysis"
        icon={<BookOpen size={20} />}
        tooltip={METRIC_EXPLANATIONS.readability}
        statusBadge={norwegian?.difficult_count && norwegian.difficult_count > 0 ? 'warning' : undefined}
        statusCount={norwegian?.difficult_count}
      >
        <div className="space-y-4">
          {/* General Score */}
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

          {/* Norwegian LIX */}
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

      {/* Freshness & Predictive */}
      <ExpandableSection
        title="Freshness & Staleness"
        description="Content freshness tracking and predictive analysis"
        icon={<Clock size={20} />}
        tooltip={METRIC_EXPLANATIONS.freshness}
        statusBadge={(freshness?.stale_count ?? 0) > 0 ? 'warning' : undefined}
        statusCount={freshness?.stale_count}
      >
        <div className="space-y-4">
          {/* Freshness Summary */}
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

          {/* Predictive Staleness */}
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

      {/* Code Sync */}
      <ExpandableSection
        title="Code Synchronization"
        description="Code example validation and API reference checks"
        icon={<Code size={20} />}
        tooltip={METRIC_EXPLANATIONS.syntaxErrors}
        statusBadge={(codesync?.syntax_error_count ?? 0) > 0 ? 'error' : (codesync?.deprecated_count ?? 0) > 0 ? 'warning' : undefined}
        statusCount={(codesync?.syntax_error_count ?? 0) + (codesync?.deprecated_count ?? 0)}
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

            {/* Syntax Errors List */}
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

      {/* Advanced Analysis */}
      <ExpandableSection
        title="Advanced Analysis"
        description="Audience drift, question coverage, cross-references, and style"
        icon={<TrendingUp size={20} />}
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

            {/* Unanswered Questions */}
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
  );
}

// ============== ACTIVITY TAB ==============
function ActivityView() {
  const { data: auditLog, isLoading: auditLoading } = useAuditLog();
  const { data: insights, isLoading: insightsLoading } = useInsights();

  if (auditLoading || insightsLoading) {
    return <Loading message="Loading activity..." />;
  }

  const recentChanges = insights?.statistics?.activity?.recent_changes ?? [];
  const entries = auditLog?.entries ?? [];

  return (
    <div className="space-y-6">
      {/* Recent Commits */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="card-title text-lg flex items-center gap-2">
            Recent Commits
            <InfoTooltip {...METRIC_EXPLANATIONS.recentCommits} />
          </h3>
          <p className="text-sm text-base-content/60 mb-4">Git activity affecting content files</p>
          {recentChanges.length > 0 ? (
            <div className="space-y-3">
              {recentChanges.slice(0, 8).map((change, idx) => (
                <div key={idx} className="p-3 rounded-lg bg-base-300">
                  <div className="flex items-start gap-3">
                    <GitCommit size={16} className="text-primary flex-shrink-0 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium truncate">{change.message}</span>
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
            <div className="text-center py-6">
              <GitCommit size={24} className="text-base-content/30 mx-auto mb-2" />
              <p className="text-sm text-base-content/60">No recent commits</p>
            </div>
          )}
        </div>
      </div>

      {/* Audit Log */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="card-title text-lg">Audit Log</h3>
          <p className="text-sm text-base-content/60 mb-4">System activity and actions</p>
          {entries.length > 0 ? (
            <div className="space-y-2">
              {entries.slice(0, 15).map((entry, idx) => (
                <div key={idx} className="flex items-center gap-3 p-3 rounded-lg bg-base-300">
                  <ActivityIcon size={14} className="text-base-content/40 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <span className="font-medium">{entry.action}</span>
                    {entry.details && <span className="text-sm text-base-content/60 ml-2">{entry.details}</span>}
                  </div>
                  <span className="text-xs text-base-content/50">{new Date(entry.timestamp).toLocaleString()}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-6">
              <ActivityIcon size={24} className="text-base-content/30 mx-auto mb-2" />
              <p className="text-sm text-base-content/60">No audit log entries</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ============== MAIN QUALITY PAGE ==============
export function Quality() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Quality</h1>
        <SubTabs tabs={tabs} basePath="/quality" />
      </div>

      <Routes>
        <Route index element={<OverviewView />} />
        <Route path="analysis" element={<AnalysisView />} />
        <Route path="activity" element={<ActivityView />} />
      </Routes>
    </div>
  );
}
