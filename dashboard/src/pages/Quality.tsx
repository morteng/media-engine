import { Routes, Route } from 'react-router-dom';
import {
  useInsights,
  useFreshness,
  useAdvancedInsights,
  useAuditLog,
} from '@/hooks/useApi';
import { SubTabs } from '@/components/ui/SubTabs';
import { InfoTooltip, METRIC_EXPLANATIONS } from '@/components/ui/InfoTooltip';
import {
  Shield,
  AlertTriangle,
  AlertCircle,
  CheckCircle,
  Clock,
  XCircle,
  Brain,
  Network,
  BookOpen,
  Code,
  TrendingUp,
  GitCommit,
  FileText,
  Layers,
  Target,
  Zap,
  Activity as ActivityIcon,
  User,
  Copy,
  Link2,
  HelpCircle,
  BarChart3,
  RefreshCw,
} from 'lucide-react';

const tabs = [
  { path: '', label: 'Quality' },
  { path: 'semantic', label: 'Semantic' },
  { path: 'knowledge', label: 'Knowledge' },
  { path: 'readability', label: 'Readability' },
  { path: 'freshness', label: 'Freshness' },
  { path: 'codesync', label: 'Code Sync' },
  { path: 'advanced', label: 'Advanced' },
  { path: 'activity', label: 'Activity' },
];

// Helper component for unavailable modules
function ModuleUnavailable({ name, reason }: { name: string; reason?: string }) {
  return (
    <div className="card bg-base-200">
      <div className="card-body items-center text-center py-12">
        <Zap size={48} className="text-base-content/30 mb-4" />
        <h3 className="text-lg font-semibold">{name} Not Available</h3>
        <p className="text-base-content/60">{reason || 'Install optional dependencies to enable this feature'}</p>
      </div>
    </div>
  );
}

// Helper component for module errors
function ModuleError({ name, error }: { name: string; error: string }) {
  return (
    <div className="card bg-base-200 border border-error/30">
      <div className="card-body items-center text-center py-12">
        <AlertCircle size={48} className="text-error mb-4" />
        <h3 className="text-lg font-semibold">Error Loading {name}</h3>
        <p className="text-base-content/60">{error}</p>
      </div>
    </div>
  );
}

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

// Quality Checks View
function QualityView() {
  const { data: insights, isLoading } = useInsights();

  if (isLoading) {
    return <Loading message="Loading quality checks..." />;
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
            <span className="text-base-content/60">Critical</span>
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
            <span className="text-base-content/60">Documents</span>
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

// Semantic Analysis View
function SemanticView() {
  const { data: advanced, isLoading } = useAdvancedInsights();

  if (isLoading) {
    return <Loading message="Loading semantic analysis..." />;
  }

  const semantic = advanced?.semantic;

  if (!semantic?.available) {
    return <ModuleUnavailable name="Semantic Analysis" reason={semantic?.reason} />;
  }

  if (semantic?.error) {
    return <ModuleError name="Semantic Analysis" error={semantic.error} />;
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="card bg-base-200">
          <div className="card-body p-4 items-center text-center">
            <Copy size={24} className="text-warning" />
            <span className="text-2xl font-bold">{semantic.near_duplicate_count ?? 0}</span>
            <span className="text-sm text-base-content/60 flex items-center gap-1">
              Near Duplicates
              <InfoTooltip {...METRIC_EXPLANATIONS.semanticDuplicates} />
            </span>
          </div>
        </div>
        <div className="card bg-base-200">
          <div className="card-body p-4 items-center text-center">
            <TrendingUp size={24} className="text-primary" />
            <span className="text-2xl font-bold">{semantic.drift_count ?? 0}</span>
            <span className="text-sm text-base-content/60 flex items-center gap-1">
              Terminology Drift
              <InfoTooltip {...METRIC_EXPLANATIONS.terminologyDrift} />
            </span>
          </div>
        </div>
        <div className="card bg-base-200">
          <div className="card-body p-4 items-center text-center">
            <Layers size={24} className="text-success" />
            <span className="text-2xl font-bold">{semantic.cluster_count ?? 0}</span>
            <span className="text-sm text-base-content/60">Content Clusters</span>
          </div>
        </div>
      </div>

      {/* Near Duplicates */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="card-title text-lg">Near-Duplicate Content</h3>
          <p className="text-sm text-base-content/60 mb-4">Semantically similar document pairs</p>
          {semantic.near_duplicates && semantic.near_duplicates.length > 0 ? (
            <div className="space-y-3">
              {semantic.near_duplicates.map((dup, idx) => (
                <div key={idx} className="flex items-center gap-3 p-3 rounded-lg bg-base-300">
                  <FileText size={14} className="text-base-content/60 flex-shrink-0" />
                  <span className="text-sm truncate">{dup.doc1_path}</span>
                  <span className="text-base-content/50">~</span>
                  <span className="text-sm truncate">{dup.doc2_path}</span>
                  <div className="badge badge-warning badge-sm ml-auto">{Math.round(dup.similarity * 100)}%</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-6">
              <CheckCircle size={24} className="text-success mx-auto mb-2" />
              <p className="text-sm text-base-content/60">No near-duplicate content found</p>
            </div>
          )}
        </div>
      </div>

      {/* Terminology Drift */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="card-title text-lg">Terminology Drift</h3>
          <p className="text-sm text-base-content/60 mb-4">Inconsistent term usage across documents</p>
          {semantic.terminology_drift && semantic.terminology_drift.length > 0 ? (
            <div className="space-y-3">
              {semantic.terminology_drift.map((drift, idx) => (
                <div key={idx} className="p-3 rounded-lg bg-base-300 space-y-2">
                  <div className="flex items-center gap-2">
                    <div className="badge badge-primary">{drift.term}</div>
                    <span className="text-sm text-base-content/60">
                      Drift: {typeof drift.drift_score === 'number' && !isNaN(drift.drift_score)
                        ? `${Math.round(drift.drift_score * 100)}%`
                        : 'N/A'}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-base-content/70">{drift.old_usage || 'N/A'}</span>
                    <span className="text-base-content/50">vs</span>
                    <span className="text-base-content/70">{drift.new_usage || 'N/A'}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-6">
              <CheckCircle size={24} className="text-success mx-auto mb-2" />
              <p className="text-sm text-base-content/60">Terminology is consistent across documents</p>
            </div>
          )}
        </div>
      </div>

      {/* Content Clusters */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="card-title text-lg">Content Clusters</h3>
          <p className="text-sm text-base-content/60 mb-4">Thematic groupings of related content</p>
          {semantic.clusters && semantic.clusters.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {semantic.clusters.map((cluster, idx) => (
                <div key={idx} className="p-4 rounded-lg bg-base-300">
                  <div className="flex items-center gap-2 mb-2">
                    <Layers size={16} className="text-primary" />
                    <span className="font-medium">{cluster.theme || `Cluster ${cluster.cluster_id}`}</span>
                  </div>
                  <span className="text-sm text-base-content/60">{cluster.doc_count} documents</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-6">
              <Layers size={24} className="text-base-content/30 mx-auto mb-2" />
              <p className="text-sm text-base-content/60">Not enough content for clustering</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Knowledge Graph View
function KnowledgeView() {
  const { data: advanced, isLoading } = useAdvancedInsights();

  if (isLoading) {
    return <Loading message="Loading knowledge graph..." />;
  }

  const kg = advanced?.knowledge_graph;

  if (!kg?.available) {
    return <ModuleUnavailable name="Knowledge Graph" reason={kg?.reason} />;
  }

  if (kg?.error) {
    return <ModuleError name="Knowledge Graph" error={kg.error} />;
  }

  const metrics = kg.metrics;

  return (
    <div className="space-y-6">
      {/* Graph Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card bg-base-200">
          <div className="card-body p-4 items-center text-center">
            <Network size={24} className="text-primary" />
            <span className="text-2xl font-bold">{metrics?.node_count ?? kg.node_count ?? 0}</span>
            <span className="text-sm text-base-content/60">Nodes</span>
          </div>
        </div>
        <div className="card bg-base-200">
          <div className="card-body p-4 items-center text-center">
            <Link2 size={24} className="text-success" />
            <span className="text-2xl font-bold">{metrics?.edge_count ?? kg.edge_count ?? 0}</span>
            <span className="text-sm text-base-content/60">Edges</span>
          </div>
        </div>
        <div className={`card bg-base-200 ${kg.orphan_count && kg.orphan_count > 0 ? 'border border-warning/30' : ''}`}>
          <div className="card-body p-4 items-center text-center">
            <AlertTriangle size={24} className="text-warning" />
            <span className="text-2xl font-bold">{kg.orphan_count ?? 0}</span>
            <span className="text-sm text-base-content/60 flex items-center gap-1">
              Orphans
              <InfoTooltip {...METRIC_EXPLANATIONS.orphanConcepts} />
            </span>
          </div>
        </div>
        <div className={`card bg-base-200 ${kg.prereq_issue_count && kg.prereq_issue_count > 0 ? 'border border-error/30' : ''}`}>
          <div className="card-body p-4 items-center text-center">
            <AlertCircle size={24} className="text-error" />
            <span className="text-2xl font-bold">{kg.prereq_issue_count ?? 0}</span>
            <span className="text-sm text-base-content/60 flex items-center gap-1">
              Prereq Issues
              <InfoTooltip {...METRIC_EXPLANATIONS.prerequisiteIssues} />
            </span>
          </div>
        </div>
      </div>

      {/* Graph Metrics Detail */}
      {metrics && (
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="card-title text-lg">Graph Metrics</h3>
            <p className="text-sm text-base-content/60 mb-4">Knowledge structure analysis</p>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold">{(metrics.density * 100).toFixed(1)}%</div>
                <div className="text-sm text-base-content/60">Density</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">{metrics.avg_connections?.toFixed(1) ?? 'N/A'}</div>
                <div className="text-sm text-base-content/60">Avg Connections</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">{metrics.hub_count ?? 0}</div>
                <div className="text-sm text-base-content/60">Hub Documents</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Orphan Concepts */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="card-title text-lg">Orphan Concepts</h3>
          <p className="text-sm text-base-content/60 mb-4">Concepts without connections to other content</p>
          {kg.orphan_concepts && kg.orphan_concepts.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {kg.orphan_concepts.slice(0, 10).map((orphan, idx) => (
                <div key={idx} className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-base-300 text-sm">
                  <Brain size={14} className="text-warning" />
                  <span>{orphan}</span>
                </div>
              ))}
              {kg.orphan_concepts.length > 10 && (
                <span className="text-sm text-base-content/60 self-center">+{kg.orphan_concepts.length - 10} more</span>
              )}
            </div>
          ) : (
            <div className="text-center py-6">
              <CheckCircle size={24} className="text-success mx-auto mb-2" />
              <p className="text-sm text-base-content/60">All concepts are well-connected</p>
            </div>
          )}
        </div>
      </div>

      {/* Prerequisite Issues */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="card-title text-lg">Prerequisite Issues</h3>
          <p className="text-sm text-base-content/60 mb-4">Missing or circular prerequisites</p>
          {kg.prerequisite_issues && kg.prerequisite_issues.length > 0 ? (
            <div className="space-y-2">
              {kg.prerequisite_issues.slice(0, 10).map((issue, idx) => (
                <div key={idx} className="flex items-center gap-3 p-3 rounded-lg bg-base-300">
                  <AlertCircle size={14} className="text-error flex-shrink-0" />
                  <span className="text-sm truncate flex-1">{issue.document}</span>
                  {issue.missing_prerequisites?.length > 0 && (
                    <div className="badge badge-warning badge-sm">{issue.missing_prerequisites.length} missing</div>
                  )}
                  {issue.circular_dependencies?.length > 0 && (
                    <div className="badge badge-error badge-sm">circular</div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-6">
              <CheckCircle size={24} className="text-success mx-auto mb-2" />
              <p className="text-sm text-base-content/60">All prerequisites are properly defined</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Readability View
function ReadabilityView() {
  const { data: advanced, isLoading } = useAdvancedInsights();
  const { data: insights } = useInsights();

  if (isLoading) {
    return <Loading message="Loading readability analysis..." />;
  }

  const norwegian = advanced?.norwegian_readability;
  const generalReadability = insights?.health?.components?.readability ?? 0;

  return (
    <div className="space-y-6">
      {/* General Readability Score */}
      <div className="card bg-gradient-to-br from-base-200 to-base-300 border border-base-300">
        <div className="card-body">
          <h3 className="card-title text-lg mb-4">Overall Readability</h3>
          <div className="flex items-center gap-6">
            <BookOpen size={40} className={generalReadability >= 80 ? 'text-success' : 'text-warning'} />
            <div className="flex-1">
              <div className="text-4xl font-bold">{Math.round(generalReadability)}</div>
              <div className="text-base-content/60">Readability Score</div>
            </div>
            <div className={`badge badge-lg ${generalReadability >= 80 ? 'badge-success' : generalReadability >= 60 ? 'badge-warning' : 'badge-error'}`}>
              {generalReadability >= 80 ? 'Excellent' : generalReadability >= 60 ? 'Good' : 'Needs Work'}
            </div>
          </div>
        </div>
      </div>

      {/* Norwegian LIX */}
      {norwegian?.available ? (
        <>
          <div className="card bg-base-200">
            <div className="card-body">
              <h3 className="card-title text-lg">Norwegian LIX Analysis</h3>
              <p className="text-sm text-base-content/60 mb-4">Scandinavian readability standard</p>
              <div className="flex items-center gap-6 mb-4">
                <div className="text-center">
                  <div className="text-4xl font-bold">{norwegian.average_lix?.toFixed(1) ?? 'N/A'}</div>
                  <div className="text-sm text-base-content/60">Average LIX</div>
                </div>
                <div className="flex-1">
                  <p className="text-sm text-base-content/60 mb-2">Analyzed {norwegian.documents_analyzed ?? 0} documents</p>
                  <div className="flex flex-wrap gap-2 text-xs">
                    <span className="px-2 py-1 rounded bg-success/20 text-success">&lt;25 Very Easy</span>
                    <span className="px-2 py-1 rounded bg-success/10 text-success/80">25-34 Easy</span>
                    <span className="px-2 py-1 rounded bg-warning/20 text-warning">35-44 Medium</span>
                    <span className="px-2 py-1 rounded bg-error/20 text-error">45-54 Difficult</span>
                    <span className="px-2 py-1 rounded bg-error/30 text-error">&gt;54 Very Difficult</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Difficult Documents */}
          {norwegian.difficult_documents && norwegian.difficult_documents.length > 0 && (
            <div className="card bg-base-200">
              <div className="card-body">
                <h3 className="card-title text-lg">Difficult Documents</h3>
                <p className="text-sm text-base-content/60 mb-4">
                  {norwegian.difficult_count ?? norwegian.difficult_documents.length} documents need simplification
                </p>
                <div className="space-y-2">
                  {norwegian.difficult_documents.map((doc, idx) => (
                    <div key={idx} className="flex items-center gap-3 p-3 rounded-lg bg-base-300">
                      <FileText size={14} className="text-base-content/60 flex-shrink-0" />
                      <span className="text-sm truncate flex-1">{doc.path}</span>
                      <div className={`badge badge-sm ${doc.difficulty_level === 'very_difficult' ? 'badge-error' : 'badge-warning'}`}>
                        LIX: {doc.lix_score}
                      </div>
                      <span className="text-xs text-base-content/60">{doc.difficulty_level}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      ) : norwegian?.reason ? (
        <ModuleUnavailable name="Norwegian LIX" reason={norwegian.reason} />
      ) : null}
    </div>
  );
}

// Freshness View
function FreshnessView() {
  const { data: freshness, isLoading: freshnessLoading } = useFreshness();
  const { data: advanced, isLoading: advancedLoading } = useAdvancedInsights();

  if (freshnessLoading || advancedLoading) {
    return <Loading message="Loading freshness analysis..." />;
  }

  const predictive = advanced?.predictive_freshness;
  const totalItems = freshness?.total_items ?? 0;
  const freshCount = freshness?.fresh_count ?? 0;
  const staleCount = freshness?.stale_count ?? 0;
  const expiredCount = freshness?.expired_count ?? 0;
  const freshPercent = totalItems > 0 ? Math.round((freshCount / totalItems) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card bg-base-200 border border-success/30">
          <div className="card-body p-4 items-center text-center">
            <CheckCircle size={24} className="text-success" />
            <span className="text-2xl font-bold">{freshCount}</span>
            <span className="text-sm text-base-content/60">Fresh</span>
          </div>
        </div>
        <div className={`card bg-base-200 ${staleCount > 0 ? 'border border-warning/30' : ''}`}>
          <div className="card-body p-4 items-center text-center">
            <Clock size={24} className="text-warning" />
            <span className="text-2xl font-bold">{staleCount}</span>
            <span className="text-sm text-base-content/60">Stale</span>
          </div>
        </div>
        <div className={`card bg-base-200 ${expiredCount > 0 ? 'border border-error/30' : ''}`}>
          <div className="card-body p-4 items-center text-center">
            <XCircle size={24} className="text-error" />
            <span className="text-2xl font-bold">{expiredCount}</span>
            <span className="text-sm text-base-content/60">Expired</span>
          </div>
        </div>
        {predictive?.available && (
          <div className={`card bg-base-200 ${(predictive.high_risk_count ?? 0) > 0 ? 'border border-primary/30' : ''}`}>
            <div className="card-body p-4 items-center text-center">
              <RefreshCw size={24} className="text-primary" />
              <span className="text-2xl font-bold">{predictive.high_risk_count ?? 0}</span>
              <span className="text-sm text-base-content/60">High Risk</span>
            </div>
          </div>
        )}
      </div>

      {/* Overall Progress */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="card-title text-lg">Overall Freshness</h3>
          <p className="text-sm text-base-content/60 mb-4">{totalItems} tracked items</p>
          <div className="flex items-center justify-between mb-2">
            <span className="text-lg font-semibold">{freshPercent}% Fresh</span>
            <div className={`badge ${freshPercent >= 90 ? 'badge-success' : freshPercent >= 70 ? 'badge-warning' : 'badge-error'}`}>
              {freshPercent >= 90 ? 'Excellent' : freshPercent >= 70 ? 'Good' : 'Needs Attention'}
            </div>
          </div>
          <progress className="progress progress-success w-full h-3" value={freshPercent} max="100"></progress>
        </div>
      </div>

      {/* Predictive Staleness */}
      {predictive?.available && (
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="card-title text-lg">Predictive Staleness</h3>
            <p className="text-sm text-base-content/60 mb-4">AI-powered freshness prediction</p>
            <div className="grid grid-cols-4 gap-4 mb-4">
              <div className="text-center p-3 rounded-lg bg-success/10">
                <div className="text-lg font-bold text-success">{predictive.summary?.low_risk ?? 0}</div>
                <div className="text-xs text-base-content/60">Low Risk</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-warning/10">
                <div className="text-lg font-bold text-warning">{predictive.summary?.medium_risk ?? 0}</div>
                <div className="text-xs text-base-content/60">Medium</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-error/10">
                <div className="text-lg font-bold text-error">{predictive.summary?.high_risk ?? 0}</div>
                <div className="text-xs text-base-content/60">High</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-error/20">
                <div className="text-lg font-bold text-error">{predictive.summary?.critical_risk ?? 0}</div>
                <div className="text-xs text-base-content/60">Critical</div>
              </div>
            </div>

            {predictive.high_risk_documents && predictive.high_risk_documents.length > 0 && (
              <div className="space-y-2 pt-4 border-t border-base-300">
                <h4 className="font-medium">High Risk Documents</h4>
                {predictive.high_risk_documents.map((doc, idx) => (
                  <div key={idx} className="flex items-center gap-3 p-3 rounded-lg bg-base-300">
                    <AlertTriangle size={14} className="text-warning flex-shrink-0" />
                    <span className="text-sm truncate flex-1">{doc.path}</span>
                    <div className={`badge badge-sm ${doc.risk_level === 'critical' ? 'badge-error' : 'badge-warning'}`}>
                      {Math.round(doc.staleness_probability * 100)}% likely stale
                    </div>
                    {doc.days_until_stale && (
                      <span className="text-xs text-base-content/60">~{doc.days_until_stale} days</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Stale Items */}
      {freshness?.stale_items && freshness.stale_items.length > 0 && (
        <div className="card bg-base-200 border border-warning/30">
          <div className="card-body">
            <h3 className="card-title text-lg">Stale Content</h3>
            <p className="text-sm text-base-content/60 mb-4">{freshness.stale_items.length} items need attention</p>
            <div className="space-y-2">
              {freshness.stale_items.map((item, idx) => (
                <div key={idx} className="flex items-center gap-3 p-3 rounded-lg bg-base-300">
                  <Clock size={14} className="text-warning flex-shrink-0" />
                  <span className="text-sm truncate flex-1">{item.path}</span>
                  <div className="badge badge-ghost badge-sm">{item.content_type}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Code Sync View
function CodeSyncView() {
  const { data: advanced, isLoading } = useAdvancedInsights();

  if (isLoading) {
    return <Loading message="Loading code sync analysis..." />;
  }

  const codesync = advanced?.enhanced_codesync;

  if (!codesync?.available) {
    return <ModuleUnavailable name="Enhanced Code Sync" reason={codesync?.reason} />;
  }

  if (codesync?.error) {
    return <ModuleError name="Enhanced Code Sync" error={codesync.error} />;
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className={`card bg-base-200 ${(codesync.syntax_error_count ?? 0) > 0 ? 'border border-error/30' : ''}`}>
          <div className="card-body p-4 items-center text-center">
            <AlertCircle size={24} className="text-error" />
            <span className="text-2xl font-bold">{codesync.syntax_error_count ?? 0}</span>
            <span className="text-sm text-base-content/60 flex items-center gap-1">
              Syntax Errors
              <InfoTooltip {...METRIC_EXPLANATIONS.syntaxErrors} />
            </span>
          </div>
        </div>
        <div className={`card bg-base-200 ${(codesync.deprecated_count ?? 0) > 0 ? 'border border-warning/30' : ''}`}>
          <div className="card-body p-4 items-center text-center">
            <AlertTriangle size={24} className="text-warning" />
            <span className="text-2xl font-bold">{codesync.deprecated_count ?? 0}</span>
            <span className="text-sm text-base-content/60 flex items-center gap-1">
              Deprecated
              <InfoTooltip {...METRIC_EXPLANATIONS.deprecatedPatterns} />
            </span>
          </div>
        </div>
        <div className={`card bg-base-200 ${(codesync.api_issue_count ?? 0) > 0 ? 'border border-primary/30' : ''}`}>
          <div className="card-body p-4 items-center text-center">
            <Code size={24} className="text-primary" />
            <span className="text-2xl font-bold">{codesync.api_issue_count ?? 0}</span>
            <span className="text-sm text-base-content/60 flex items-center gap-1">
              API Issues
              <InfoTooltip {...METRIC_EXPLANATIONS.apiIssues} />
            </span>
          </div>
        </div>
      </div>

      {/* Syntax Errors */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="card-title text-lg">Syntax Errors</h3>
          <p className="text-sm text-base-content/60 mb-4">Invalid code blocks in documentation</p>
          {codesync.syntax_errors && codesync.syntax_errors.length > 0 ? (
            <div className="space-y-3">
              {codesync.syntax_errors.slice(0, 10).map((issue, idx) => (
                <div key={idx} className="p-3 rounded-lg bg-base-300 space-y-1">
                  <div className="flex items-center gap-2">
                    <AlertCircle size={14} className="text-error" />
                    <span className="text-sm truncate flex-1">{issue.document}</span>
                    <div className="badge badge-error badge-sm">Line {issue.line}</div>
                  </div>
                  <p className="text-sm text-base-content/70 pl-5">{issue.message}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-6">
              <CheckCircle size={24} className="text-success mx-auto mb-2" />
              <p className="text-sm text-base-content/60">All code blocks have valid syntax</p>
            </div>
          )}
        </div>
      </div>

      {/* Deprecated Patterns */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="card-title text-lg">Deprecated Patterns</h3>
          <p className="text-sm text-base-content/60 mb-4">Outdated code patterns in examples</p>
          {codesync.deprecated_patterns && codesync.deprecated_patterns.length > 0 ? (
            <div className="space-y-3">
              {codesync.deprecated_patterns.slice(0, 10).map((issue, idx) => (
                <div key={idx} className="p-3 rounded-lg bg-base-300 space-y-1">
                  <div className="flex items-center gap-2">
                    <AlertTriangle size={14} className="text-warning" />
                    <span className="text-sm truncate">{issue.document}</span>
                  </div>
                  <p className="text-sm text-base-content/70 pl-5">{issue.message}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-6">
              <CheckCircle size={24} className="text-success mx-auto mb-2" />
              <p className="text-sm text-base-content/60">No deprecated patterns found</p>
            </div>
          )}
        </div>
      </div>

      {/* API Issues */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="card-title text-lg">API Reference Issues</h3>
          <p className="text-sm text-base-content/60 mb-4">Invalid or outdated API references</p>
          {codesync.api_issues && codesync.api_issues.length > 0 ? (
            <div className="space-y-3">
              {codesync.api_issues.slice(0, 10).map((issue, idx) => (
                <div key={idx} className="p-3 rounded-lg bg-base-300 space-y-1">
                  <div className="flex items-center gap-2">
                    <Code size={14} className="text-primary" />
                    <span className="text-sm truncate">{issue.document}</span>
                  </div>
                  <p className="text-sm text-base-content/70 pl-5">{issue.message}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-6">
              <CheckCircle size={24} className="text-success mx-auto mb-2" />
              <p className="text-sm text-base-content/60">All API references are valid</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Advanced Analysis View
function AdvancedView() {
  const { data: advanced, isLoading } = useAdvancedInsights();

  if (isLoading) {
    return <Loading message="Loading advanced analysis..." />;
  }

  const analysis = advanced?.advanced_analysis;

  if (!analysis?.available) {
    return <ModuleUnavailable name="Advanced Analysis" reason={analysis?.reason} />;
  }

  if (analysis?.error) {
    return <ModuleError name="Advanced Analysis" error={analysis.error} />;
  }

  const audienceDrift = analysis.audience_drift;
  const questionCoverage = analysis.question_coverage;
  const crossRefs = analysis.cross_references;
  const style = analysis.style_consistency;

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {audienceDrift && (
          <div className={`card bg-base-200 ${audienceDrift.drift_score > 0.3 ? 'border border-warning/30' : ''}`}>
            <div className="card-body p-4 items-center text-center">
              <Target size={24} className="text-primary" />
              <span className="text-lg font-bold">{audienceDrift.trend}</span>
              <span className="text-sm text-base-content/60">Audience Drift</span>
            </div>
          </div>
        )}
        {questionCoverage && (
          <div className="card bg-base-200">
            <div className="card-body p-4 items-center text-center">
              <HelpCircle size={24} className="text-success" />
              <span className="text-2xl font-bold">{questionCoverage.coverage_percent?.toFixed(0) ?? 0}%</span>
              <span className="text-sm text-base-content/60">Questions Covered</span>
            </div>
          </div>
        )}
        {crossRefs && (
          <div className="card bg-base-200">
            <div className="card-body p-4 items-center text-center">
              <Link2 size={24} className="text-info" />
              <span className="text-2xl font-bold">{crossRefs.total_references ?? 0}</span>
              <span className="text-sm text-base-content/60">Cross-References</span>
            </div>
          </div>
        )}
        {style && (
          <div className={`card bg-base-200 ${style.style_score < 70 ? 'border border-warning/30' : ''}`}>
            <div className="card-body p-4 items-center text-center">
              <BarChart3 size={24} className="text-warning" />
              <span className="text-2xl font-bold">{style.style_score?.toFixed(0) ?? 0}</span>
              <span className="text-sm text-base-content/60">Style Score</span>
            </div>
          </div>
        )}
      </div>

      {/* Audience Drift */}
      {audienceDrift && (
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="card-title text-lg">Audience Drift Analysis</h3>
            <p className="text-sm text-base-content/60 mb-4">Content complexity trends over time</p>
            <div className="flex items-center gap-3 mb-4">
              <span className="text-sm text-base-content/60">Complexity Trend:</span>
              <div className={`badge ${audienceDrift.trend === 'stable' ? 'badge-success' : 'badge-warning'}`}>
                {audienceDrift.trend}
              </div>
            </div>
            {audienceDrift.documents_with_drift?.length > 0 && (
              <div className="space-y-2 pt-4 border-t border-base-300">
                <h4 className="font-medium">Documents with Drift</h4>
                {audienceDrift.documents_with_drift.slice(0, 5).map((doc, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-sm">
                    <FileText size={14} className="text-base-content/60" />
                    <span>{doc}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Question Coverage */}
      {questionCoverage && (
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="card-title text-lg">Question Coverage</h3>
            <p className="text-sm text-base-content/60 mb-4">How well your content answers reader questions</p>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="text-center p-4 rounded-lg bg-base-300">
                <div className="text-2xl font-bold">{questionCoverage.total_questions ?? 0}</div>
                <div className="text-sm text-base-content/60">Total Questions</div>
              </div>
              <div className="text-center p-4 rounded-lg bg-base-300">
                <div className="text-2xl font-bold text-success">{questionCoverage.answered_questions ?? 0}</div>
                <div className="text-sm text-base-content/60">Answered</div>
              </div>
            </div>
            <div className="space-y-1 mb-4">
              <div className="flex justify-between text-sm">
                <span>Coverage</span>
                <span>{questionCoverage.coverage_percent ?? 0}%</span>
              </div>
              <progress className="progress progress-success w-full" value={questionCoverage.coverage_percent ?? 0} max="100"></progress>
            </div>
            {questionCoverage.unanswered_questions?.length > 0 && (
              <div className="space-y-2 pt-4 border-t border-base-300">
                <h4 className="font-medium">Unanswered Questions</h4>
                {questionCoverage.unanswered_questions.slice(0, 5).map((q, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-sm">
                    <HelpCircle size={14} className="text-warning flex-shrink-0" />
                    <span>{q}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Cross-Reference Density */}
      {crossRefs && (
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="card-title text-lg">Cross-Reference Analysis</h3>
            <p className="text-sm text-base-content/60 mb-4">Internal and external linking</p>
            <div className="space-y-3 mb-4">
              <div className="flex justify-between items-center p-3 rounded-lg bg-base-300">
                <span>Internal References</span>
                <strong>{crossRefs.internal_references ?? 0}</strong>
              </div>
              <div className="flex justify-between items-center p-3 rounded-lg bg-base-300">
                <span>External References</span>
                <strong>{crossRefs.external_references ?? 0}</strong>
              </div>
              <div className="flex justify-between items-center p-3 rounded-lg bg-base-300">
                <span>Density Score</span>
                <strong>{crossRefs.density_score?.toFixed(1) ?? 'N/A'}</strong>
              </div>
            </div>
            {crossRefs.orphan_references?.length > 0 && (
              <div className="space-y-2 pt-4 border-t border-base-300">
                <h4 className="font-medium">Orphan References ({crossRefs.orphan_references.length})</h4>
                {crossRefs.orphan_references.slice(0, 5).map((ref, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-sm">
                    <Link2 size={14} className="text-warning flex-shrink-0" />
                    <span>{ref}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Style Consistency */}
      {style && (
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="card-title text-lg">Style Consistency</h3>
            <p className="text-sm text-base-content/60 mb-4">Writing style uniformity across documents</p>
            <div className="space-y-1 mb-4">
              <div className="flex justify-between text-sm">
                <span>Style Score</span>
                <span>{style.style_score ?? 0}%</span>
              </div>
              <progress
                className={`progress w-full h-3 ${style.style_score >= 80 ? 'progress-success' : style.style_score >= 60 ? 'progress-warning' : 'progress-error'}`}
                value={style.style_score ?? 0}
                max="100"
              ></progress>
            </div>
            {style.inconsistencies?.length > 0 && (
              <div className="space-y-2 pt-4 border-t border-base-300">
                <h4 className="font-medium">Style Inconsistencies</h4>
                {style.inconsistencies.slice(0, 5).map((item, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-sm p-3 rounded-lg bg-base-300">
                    <AlertTriangle size={14} className="text-warning flex-shrink-0 mt-0.5" />
                    <div>
                      <span className="text-base-content/60">{item.document}</span>
                      <span className="mx-2">-</span>
                      <span>{item.issue}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// Activity View
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
          <h3 className="card-title text-lg">Recent Commits</h3>
          <p className="text-sm text-base-content/60 mb-4">Git activity</p>
          {recentChanges.length > 0 ? (
            <div className="space-y-3">
              {recentChanges.slice(0, 5).map((change, idx) => (
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
          <p className="text-sm text-base-content/60 mb-4">System activity</p>
          {entries.length > 0 ? (
            <div className="space-y-2">
              {entries.slice(0, 10).map((entry, idx) => (
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

// Main Quality Page
export function Quality() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Quality</h1>
        <SubTabs tabs={tabs} basePath="/quality" />
      </div>

      <Routes>
        <Route index element={<QualityView />} />
        <Route path="semantic" element={<SemanticView />} />
        <Route path="knowledge" element={<KnowledgeView />} />
        <Route path="readability" element={<ReadabilityView />} />
        <Route path="freshness" element={<FreshnessView />} />
        <Route path="codesync" element={<CodeSyncView />} />
        <Route path="advanced" element={<AdvancedView />} />
        <Route path="activity" element={<ActivityView />} />
      </Routes>
    </div>
  );
}
