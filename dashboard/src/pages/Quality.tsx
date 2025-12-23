import { Routes, Route } from 'react-router-dom';
import {
  useInsights,
  useFreshness,
  useAdvancedInsights,
  useAuditLog,
} from '@/hooks/useApi';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { LoadingState } from '@/components/ui/Spinner';
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
    <Card className="module-unavailable">
      <CardContent className="empty-state">
        <Zap size={48} className="text-muted" />
        <h3>{name} Not Available</h3>
        <p className="text-muted">{reason || 'Install optional dependencies to enable this feature'}</p>
      </CardContent>
    </Card>
  );
}

// Helper component for module errors
function ModuleError({ name, error }: { name: string; error: string }) {
  return (
    <Card className="module-error">
      <CardContent className="empty-state">
        <AlertCircle size={48} className="text-error" />
        <h3>Error Loading {name}</h3>
        <p className="text-muted">{error}</p>
      </CardContent>
    </Card>
  );
}

// Quality Checks View
function QualityView() {
  const { data: insights, isLoading } = useInsights();

  if (isLoading) {
    return <LoadingState message="Loading quality checks..." />;
  }

  const health = insights?.health;
  const issues = health?.issues ?? [];
  const components = health?.components;

  const errorCount = issues.filter(i => i.severity === 'critical').length;
  const warningCount = issues.filter(i => i.severity === 'warning').length;

  return (
    <div className="quality-content">
      {/* Score Hero */}
      <Card variant="gradient" className="quality-hero">
        <CardContent>
          <div className="quality-score-display">
            <Shield size={40} className={health?.overall && health.overall >= 80 ? 'text-success' : 'text-warning'} />
            <div className="score-info">
              <span className="score-value">{Math.round(health?.overall ?? 0)}</span>
              <span className="score-label">
                Quality Score
                <InfoTooltip {...METRIC_EXPLANATIONS.qualityScore} />
              </span>
            </div>
            <Badge
              variant={health?.status === 'excellent' ? 'success' : health?.status === 'good' ? 'warning' : 'error'}
              size="lg"
            >
              {health?.status ?? 'unknown'}
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Issue Summary */}
      <div className="issue-summary">
        <Card className={errorCount > 0 ? 'card-error' : ''}>
          <CardContent>
            <AlertCircle size={20} className="text-error" />
            <span className="count">{errorCount}</span>
            <span className="label">Critical</span>
          </CardContent>
        </Card>
        <Card className={warningCount > 0 ? 'card-warning' : ''}>
          <CardContent>
            <AlertTriangle size={20} className="text-warning" />
            <span className="count">{warningCount}</span>
            <span className="label">Warnings</span>
          </CardContent>
        </Card>
        <Card className="card-success">
          <CardContent>
            <CheckCircle size={20} className="text-success" />
            <span className="count">{health?.document_count ?? 0}</span>
            <span className="label">Documents</span>
          </CardContent>
        </Card>
      </div>

      {/* Component Scores */}
      <Card>
        <CardHeader title="Component Scores" subtitle="Weighted health factors" />
        <CardContent>
          <div className="component-scores">
            {components && Object.entries(components).map(([key, value]) => {
              const explanation = METRIC_EXPLANATIONS[key as keyof typeof METRIC_EXPLANATIONS];
              return (
                <div key={key} className="component-row">
                  <span className="component-name">
                    {key}
                    {explanation && <InfoTooltip title={explanation.title} content={explanation.content} />}
                  </span>
                  <ProgressBar
                    value={value as number}
                    variant={(value as number) >= 90 ? 'success' : (value as number) >= 70 ? 'warning' : 'error'}
                    showLabel
                  />
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Issues */}
      {issues.length > 0 && (
        <Card>
          <CardHeader title="Issues" subtitle={`${issues.length} to address`} />
          <CardContent>
            <div className="issues-list">
              {issues.slice(0, 10).map((issue, idx) => (
                <div key={idx} className={`issue-item severity-${issue.severity}`}>
                  <AlertTriangle size={14} />
                  <div className="issue-content">
                    <Badge variant={issue.severity === 'critical' ? 'error' : 'warning'} size="sm">
                      {issue.category}
                    </Badge>
                    <span className="issue-doc">{issue.document}</span>
                    <p className="issue-message">{issue.message}</p>
                  </div>
                </div>
              ))}
              {issues.length > 10 && (
                <p className="text-muted">...and {issues.length - 10} more</p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {issues.length === 0 && (
        <Card>
          <CardContent className="empty-state">
            <CheckCircle size={48} className="text-success" />
            <h3>All Clear!</h3>
            <p className="text-muted">No quality issues found.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Semantic Analysis View
function SemanticView() {
  const { data: advanced, isLoading } = useAdvancedInsights();

  if (isLoading) {
    return <LoadingState message="Loading semantic analysis..." />;
  }

  const semantic = advanced?.semantic;

  if (!semantic?.available) {
    return <ModuleUnavailable name="Semantic Analysis" reason={semantic?.reason} />;
  }

  if (semantic?.error) {
    return <ModuleError name="Semantic Analysis" error={semantic.error} />;
  }

  return (
    <div className="semantic-content">
      {/* Summary Cards */}
      <div className="analysis-summary">
        <Card>
          <CardContent>
            <Copy size={24} className="text-warning" />
            <span className="count">{semantic.near_duplicate_count ?? 0}</span>
            <span className="label">
              Near Duplicates
              <InfoTooltip {...METRIC_EXPLANATIONS.semanticDuplicates} />
            </span>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <TrendingUp size={24} className="text-accent" />
            <span className="count">{semantic.drift_count ?? 0}</span>
            <span className="label">
              Terminology Drift
              <InfoTooltip {...METRIC_EXPLANATIONS.terminologyDrift} />
            </span>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Layers size={24} className="text-success" />
            <span className="count">{semantic.cluster_count ?? 0}</span>
            <span className="label">Content Clusters</span>
          </CardContent>
        </Card>
      </div>

      {/* Near Duplicates */}
      <Card>
        <CardHeader
          title="Near-Duplicate Content"
          subtitle="Semantically similar document pairs"
        />
        <CardContent>
          {semantic.near_duplicates && semantic.near_duplicates.length > 0 ? (
            <div className="duplicates-list">
              {semantic.near_duplicates.map((dup, idx) => (
                <div key={idx} className="duplicate-item">
                  <div className="duplicate-pair">
                    <FileText size={14} />
                    <span className="doc-path">{dup.doc1_path}</span>
                    <span className="similarity-arrow">~</span>
                    <span className="doc-path">{dup.doc2_path}</span>
                  </div>
                  <Badge variant="warning">{Math.round(dup.similarity * 100)}% similar</Badge>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state small">
              <CheckCircle size={24} className="text-success" />
              <p>No near-duplicate content found</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Terminology Drift */}
      <Card>
        <CardHeader
          title="Terminology Drift"
          subtitle="Inconsistent term usage across documents"
        />
        <CardContent>
          {semantic.terminology_drift && semantic.terminology_drift.length > 0 ? (
            <div className="drift-list">
              {semantic.terminology_drift.map((drift, idx) => (
                <div key={idx} className="drift-item">
                  <div className="drift-term">
                    <Badge variant="accent">{drift.term}</Badge>
                    <span className="drift-score">
                      Drift: {typeof drift.drift_score === 'number' && !isNaN(drift.drift_score)
                        ? `${Math.round(drift.drift_score * 100)}%`
                        : 'N/A'}
                    </span>
                  </div>
                  <div className="drift-usage">
                    <span className="old-usage">{drift.old_usage || 'N/A'}</span>
                    <span className="arrow">vs</span>
                    <span className="new-usage">{drift.new_usage || 'N/A'}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state small">
              <CheckCircle size={24} className="text-success" />
              <p>Terminology is consistent across documents</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Content Clusters */}
      <Card>
        <CardHeader
          title="Content Clusters"
          subtitle="Thematic groupings of related content"
        />
        <CardContent>
          {semantic.clusters && semantic.clusters.length > 0 ? (
            <div className="clusters-grid">
              {semantic.clusters.map((cluster, idx) => (
                <div key={idx} className="cluster-card">
                  <div className="cluster-header">
                    <Layers size={16} />
                    <span className="cluster-theme">{cluster.theme || `Cluster ${cluster.cluster_id}`}</span>
                  </div>
                  <div className="cluster-stats">
                    <span className="doc-count">{cluster.doc_count} documents</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state small">
              <Layers size={24} className="text-muted" />
              <p>Not enough content for clustering</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// Knowledge Graph View
function KnowledgeView() {
  const { data: advanced, isLoading } = useAdvancedInsights();

  if (isLoading) {
    return <LoadingState message="Loading knowledge graph..." />;
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
    <div className="knowledge-content">
      {/* Graph Metrics */}
      <div className="analysis-summary">
        <Card>
          <CardContent>
            <Network size={24} className="text-accent" />
            <span className="count">{metrics?.node_count ?? kg.node_count ?? 0}</span>
            <span className="label">Nodes</span>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Link2 size={24} className="text-success" />
            <span className="count">{metrics?.edge_count ?? kg.edge_count ?? 0}</span>
            <span className="label">Edges</span>
          </CardContent>
        </Card>
        <Card className={kg.orphan_count && kg.orphan_count > 0 ? 'card-warning' : ''}>
          <CardContent>
            <AlertTriangle size={24} className="text-warning" />
            <span className="count">{kg.orphan_count ?? 0}</span>
            <span className="label">
              Orphan Concepts
              <InfoTooltip {...METRIC_EXPLANATIONS.orphanConcepts} />
            </span>
          </CardContent>
        </Card>
        <Card className={kg.prereq_issue_count && kg.prereq_issue_count > 0 ? 'card-error' : ''}>
          <CardContent>
            <AlertCircle size={24} className="text-error" />
            <span className="count">{kg.prereq_issue_count ?? 0}</span>
            <span className="label">
              Prereq Issues
              <InfoTooltip {...METRIC_EXPLANATIONS.prerequisiteIssues} />
            </span>
          </CardContent>
        </Card>
      </div>

      {/* Graph Metrics Detail */}
      {metrics && (
        <Card>
          <CardHeader title="Graph Metrics" subtitle="Knowledge structure analysis" />
          <CardContent>
            <div className="metrics-grid">
              <div className="metric-item">
                <span className="metric-label">Density</span>
                <span className="metric-value">{(metrics.density * 100).toFixed(1)}%</span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Avg Connections</span>
                <span className="metric-value">{metrics.avg_connections?.toFixed(1) ?? 'N/A'}</span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Hub Documents</span>
                <span className="metric-value">{metrics.hub_count ?? 0}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Orphan Concepts */}
      <Card>
        <CardHeader
          title="Orphan Concepts"
          subtitle="Concepts without connections to other content"
        />
        <CardContent>
          {kg.orphan_concepts && kg.orphan_concepts.length > 0 ? (
            <div className="orphans-list">
              {kg.orphan_concepts.slice(0, 10).map((orphan, idx) => (
                <div key={idx} className="orphan-item">
                  <Brain size={14} className="text-warning" />
                  <span>{orphan}</span>
                </div>
              ))}
              {kg.orphan_concepts.length > 10 && (
                <p className="text-muted">...and {kg.orphan_concepts.length - 10} more</p>
              )}
            </div>
          ) : (
            <div className="empty-state small">
              <CheckCircle size={24} className="text-success" />
              <p>All concepts are well-connected</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Prerequisite Issues */}
      <Card>
        <CardHeader
          title="Prerequisite Issues"
          subtitle="Missing or circular prerequisites"
        />
        <CardContent>
          {kg.prerequisite_issues && kg.prerequisite_issues.length > 0 ? (
            <div className="prereq-list">
              {kg.prerequisite_issues.slice(0, 10).map((issue, idx) => (
                <div key={idx} className="prereq-item">
                  <AlertCircle size={14} className="text-error" />
                  <span className="doc-path">{issue.document}</span>
                  {issue.missing_prerequisites?.length > 0 && (
                    <Badge variant="warning" size="sm">
                      {issue.missing_prerequisites.length} missing
                    </Badge>
                  )}
                  {issue.circular_dependencies?.length > 0 && (
                    <Badge variant="error" size="sm">
                      circular
                    </Badge>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state small">
              <CheckCircle size={24} className="text-success" />
              <p>All prerequisites are properly defined</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// Readability View (Norwegian LIX + General)
function ReadabilityView() {
  const { data: advanced, isLoading } = useAdvancedInsights();
  const { data: insights } = useInsights();

  if (isLoading) {
    return <LoadingState message="Loading readability analysis..." />;
  }

  const norwegian = advanced?.norwegian_readability;
  const generalReadability = insights?.health?.components?.readability ?? 0;

  return (
    <div className="readability-content">
      {/* General Readability Score */}
      <Card variant="gradient">
        <CardHeader title="Overall Readability" />
        <CardContent>
          <div className="readability-hero">
            <BookOpen size={40} className={generalReadability >= 80 ? 'text-success' : 'text-warning'} />
            <div className="score-info">
              <span className="score-value">{Math.round(generalReadability)}</span>
              <span className="score-label">Readability Score</span>
            </div>
            <Badge variant={generalReadability >= 80 ? 'success' : generalReadability >= 60 ? 'warning' : 'error'}>
              {generalReadability >= 80 ? 'Excellent' : generalReadability >= 60 ? 'Good' : 'Needs Work'}
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Norwegian LIX */}
      {norwegian?.available ? (
        <>
          <Card>
            <CardHeader
              title="Norwegian LIX Analysis"
              subtitle="Scandinavian readability standard"
            />
            <CardContent>
              <div className="lix-summary">
                <div className="lix-score">
                  <span className="score-value">{norwegian.average_lix?.toFixed(1) ?? 'N/A'}</span>
                  <span className="score-label">Average LIX</span>
                </div>
                <div className="lix-info">
                  <p className="text-muted">
                    Analyzed {norwegian.documents_analyzed ?? 0} documents
                  </p>
                  <div className="lix-scale">
                    <span className="scale-item very-easy">&lt;25 Very Easy</span>
                    <span className="scale-item easy">25-34 Easy</span>
                    <span className="scale-item medium">35-44 Medium</span>
                    <span className="scale-item difficult">45-54 Difficult</span>
                    <span className="scale-item very-difficult">&gt;54 Very Difficult</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Difficult Documents */}
          {norwegian.difficult_documents && norwegian.difficult_documents.length > 0 && (
            <Card>
              <CardHeader
                title="Difficult Documents"
                subtitle={`${norwegian.difficult_count ?? norwegian.difficult_documents.length} documents need simplification`}
              />
              <CardContent>
                <div className="difficult-docs-list">
                  {norwegian.difficult_documents.map((doc, idx) => (
                    <div key={idx} className="difficult-doc-item">
                      <FileText size={14} />
                      <span className="doc-path">{doc.path}</span>
                      <Badge
                        variant={doc.difficulty_level === 'very_difficult' ? 'error' : 'warning'}
                        size="sm"
                      >
                        LIX: {doc.lix_score}
                      </Badge>
                      <span className="difficulty-level">{doc.difficulty_level}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      ) : norwegian?.reason ? (
        <ModuleUnavailable name="Norwegian LIX" reason={norwegian.reason} />
      ) : null}
    </div>
  );
}

// Freshness View (Current + Predictive)
function FreshnessView() {
  const { data: freshness, isLoading: freshnessLoading } = useFreshness();
  const { data: advanced, isLoading: advancedLoading } = useAdvancedInsights();

  if (freshnessLoading || advancedLoading) {
    return <LoadingState message="Loading freshness analysis..." />;
  }

  const predictive = advanced?.predictive_freshness;
  const totalItems = freshness?.total_items ?? 0;
  const freshCount = freshness?.fresh_count ?? 0;
  const staleCount = freshness?.stale_count ?? 0;
  const expiredCount = freshness?.expired_count ?? 0;
  const freshPercent = totalItems > 0 ? Math.round((freshCount / totalItems) * 100) : 0;

  return (
    <div className="freshness-content">
      {/* Summary Cards */}
      <div className="freshness-summary">
        <Card className="card-success">
          <CardContent>
            <CheckCircle size={24} className="text-success" />
            <span className="count">{freshCount}</span>
            <span className="label">Fresh</span>
          </CardContent>
        </Card>
        <Card className={staleCount > 0 ? 'card-warning' : ''}>
          <CardContent>
            <Clock size={24} className="text-warning" />
            <span className="count">{staleCount}</span>
            <span className="label">Stale</span>
          </CardContent>
        </Card>
        <Card className={expiredCount > 0 ? 'card-error' : ''}>
          <CardContent>
            <XCircle size={24} className="text-error" />
            <span className="count">{expiredCount}</span>
            <span className="label">Expired</span>
          </CardContent>
        </Card>
        {predictive?.available && (
          <Card className={(predictive.high_risk_count ?? 0) > 0 ? 'card-accent' : ''}>
            <CardContent>
              <RefreshCw size={24} className="text-accent" />
              <span className="count">{predictive.high_risk_count ?? 0}</span>
              <span className="label">High Risk</span>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Overall Progress */}
      <Card>
        <CardHeader title="Overall Freshness" subtitle={`${totalItems} tracked items`} />
        <CardContent>
          <div className="freshness-progress">
            <div className="progress-header">
              <span className="percent">{freshPercent}% Fresh</span>
              <Badge variant={freshPercent >= 90 ? 'success' : freshPercent >= 70 ? 'warning' : 'error'}>
                {freshPercent >= 90 ? 'Excellent' : freshPercent >= 70 ? 'Good' : 'Needs Attention'}
              </Badge>
            </div>
            <ProgressBar value={freshPercent} variant="success" size="lg" />
          </div>
        </CardContent>
      </Card>

      {/* Predictive Staleness */}
      {predictive?.available && (
        <Card>
          <CardHeader
            title="Predictive Staleness"
            subtitle="AI-powered freshness prediction"
          />
          <CardContent>
            <div className="predictive-summary">
              <div className="risk-distribution">
                <div className="risk-item low">
                  <span className="risk-label">Low Risk</span>
                  <span className="risk-count">{predictive.summary?.low_risk ?? 0}</span>
                </div>
                <div className="risk-item medium">
                  <span className="risk-label">Medium</span>
                  <span className="risk-count">{predictive.summary?.medium_risk ?? 0}</span>
                </div>
                <div className="risk-item high">
                  <span className="risk-label">High</span>
                  <span className="risk-count">{predictive.summary?.high_risk ?? 0}</span>
                </div>
                <div className="risk-item critical">
                  <span className="risk-label">Critical</span>
                  <span className="risk-count">{predictive.summary?.critical_risk ?? 0}</span>
                </div>
              </div>
            </div>

            {predictive.high_risk_documents && predictive.high_risk_documents.length > 0 && (
              <div className="high-risk-list">
                <h4>High Risk Documents</h4>
                {predictive.high_risk_documents.map((doc, idx) => (
                  <div key={idx} className="risk-doc-item">
                    <AlertTriangle size={14} className="text-warning" />
                    <span className="doc-path">{doc.path}</span>
                    <Badge
                      variant={doc.risk_level === 'critical' ? 'error' : 'warning'}
                      size="sm"
                    >
                      {Math.round(doc.staleness_probability * 100)}% likely stale
                    </Badge>
                    {doc.days_until_stale && (
                      <span className="days-until">~{doc.days_until_stale} days</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Stale Items */}
      {freshness?.stale_items && freshness.stale_items.length > 0 && (
        <Card className="stale-card">
          <CardHeader title="Stale Content" subtitle={`${freshness.stale_items.length} items need attention`} />
          <CardContent>
            <div className="stale-list">
              {freshness.stale_items.map((item, idx) => (
                <div key={idx} className="stale-item">
                  <Clock size={14} className="text-warning" />
                  <span className="item-path">{item.path}</span>
                  <Badge variant="default" size="sm">{item.content_type}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Code Sync View
function CodeSyncView() {
  const { data: advanced, isLoading } = useAdvancedInsights();

  if (isLoading) {
    return <LoadingState message="Loading code sync analysis..." />;
  }

  const codesync = advanced?.enhanced_codesync;

  if (!codesync?.available) {
    return <ModuleUnavailable name="Enhanced Code Sync" reason={codesync?.reason} />;
  }

  if (codesync?.error) {
    return <ModuleError name="Enhanced Code Sync" error={codesync.error} />;
  }

  return (
    <div className="codesync-content">
      {/* Summary Cards */}
      <div className="analysis-summary">
        <Card className={(codesync.syntax_error_count ?? 0) > 0 ? 'card-error' : ''}>
          <CardContent>
            <AlertCircle size={24} className="text-error" />
            <span className="count">{codesync.syntax_error_count ?? 0}</span>
            <span className="label">
              Syntax Errors
              <InfoTooltip {...METRIC_EXPLANATIONS.syntaxErrors} />
            </span>
          </CardContent>
        </Card>
        <Card className={(codesync.deprecated_count ?? 0) > 0 ? 'card-warning' : ''}>
          <CardContent>
            <AlertTriangle size={24} className="text-warning" />
            <span className="count">{codesync.deprecated_count ?? 0}</span>
            <span className="label">
              Deprecated
              <InfoTooltip {...METRIC_EXPLANATIONS.deprecatedPatterns} />
            </span>
          </CardContent>
        </Card>
        <Card className={(codesync.api_issue_count ?? 0) > 0 ? 'card-accent' : ''}>
          <CardContent>
            <Code size={24} className="text-accent" />
            <span className="count">{codesync.api_issue_count ?? 0}</span>
            <span className="label">
              API Issues
              <InfoTooltip {...METRIC_EXPLANATIONS.apiIssues} />
            </span>
          </CardContent>
        </Card>
      </div>

      {/* Syntax Errors */}
      <Card>
        <CardHeader title="Syntax Errors" subtitle="Invalid code blocks in documentation" />
        <CardContent>
          {codesync.syntax_errors && codesync.syntax_errors.length > 0 ? (
            <div className="issues-list">
              {codesync.syntax_errors.slice(0, 10).map((issue, idx) => (
                <div key={idx} className="code-issue-item">
                  <AlertCircle size={14} className="text-error" />
                  <span className="doc-path">{issue.document}</span>
                  <Badge variant="error" size="sm">Line {issue.line}</Badge>
                  <p className="issue-message">{issue.message}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state small">
              <CheckCircle size={24} className="text-success" />
              <p>All code blocks have valid syntax</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Deprecated Patterns */}
      <Card>
        <CardHeader title="Deprecated Patterns" subtitle="Outdated code patterns in examples" />
        <CardContent>
          {codesync.deprecated_patterns && codesync.deprecated_patterns.length > 0 ? (
            <div className="issues-list">
              {codesync.deprecated_patterns.slice(0, 10).map((issue, idx) => (
                <div key={idx} className="code-issue-item">
                  <AlertTriangle size={14} className="text-warning" />
                  <span className="doc-path">{issue.document}</span>
                  <p className="issue-message">{issue.message}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state small">
              <CheckCircle size={24} className="text-success" />
              <p>No deprecated patterns found</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* API Issues */}
      <Card>
        <CardHeader title="API Reference Issues" subtitle="Invalid or outdated API references" />
        <CardContent>
          {codesync.api_issues && codesync.api_issues.length > 0 ? (
            <div className="issues-list">
              {codesync.api_issues.slice(0, 10).map((issue, idx) => (
                <div key={idx} className="code-issue-item">
                  <Code size={14} className="text-accent" />
                  <span className="doc-path">{issue.document}</span>
                  <p className="issue-message">{issue.message}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state small">
              <CheckCircle size={24} className="text-success" />
              <p>All API references are valid</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// Advanced Analysis View
function AdvancedView() {
  const { data: advanced, isLoading } = useAdvancedInsights();

  if (isLoading) {
    return <LoadingState message="Loading advanced analysis..." />;
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
    <div className="advanced-content">
      {/* Summary Cards */}
      <div className="analysis-summary">
        {audienceDrift && (
          <Card className={audienceDrift.drift_score > 0.3 ? 'card-warning' : ''}>
            <CardContent>
              <Target size={24} className="text-accent" />
              <span className="count">{audienceDrift.trend}</span>
              <span className="label">Audience Drift</span>
            </CardContent>
          </Card>
        )}
        {questionCoverage && (
          <Card>
            <CardContent>
              <HelpCircle size={24} className="text-success" />
              <span className="count">{questionCoverage.coverage_percent?.toFixed(0) ?? 0}%</span>
              <span className="label">Questions Covered</span>
            </CardContent>
          </Card>
        )}
        {crossRefs && (
          <Card>
            <CardContent>
              <Link2 size={24} className="text-info" />
              <span className="count">{crossRefs.total_references ?? 0}</span>
              <span className="label">Cross-References</span>
            </CardContent>
          </Card>
        )}
        {style && (
          <Card className={style.style_score < 70 ? 'card-warning' : ''}>
            <CardContent>
              <BarChart3 size={24} className="text-warning" />
              <span className="count">{style.style_score?.toFixed(0) ?? 0}</span>
              <span className="label">Style Score</span>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Audience Drift */}
      {audienceDrift && (
        <Card>
          <CardHeader
            title="Audience Drift Analysis"
            subtitle="Content complexity trends over time"
          />
          <CardContent>
            <div className="drift-analysis">
              <div className="drift-trend">
                <span className="label">Complexity Trend:</span>
                <Badge
                  variant={audienceDrift.trend === 'stable' ? 'success' : 'warning'}
                >
                  {audienceDrift.trend}
                </Badge>
              </div>
              {audienceDrift.documents_with_drift?.length > 0 && (
                <div className="drift-docs">
                  <h4>Documents with Drift</h4>
                  {audienceDrift.documents_with_drift.slice(0, 5).map((doc, idx) => (
                    <div key={idx} className="drift-doc-item">
                      <FileText size={14} />
                      <span>{doc}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Question Coverage */}
      {questionCoverage && (
        <Card>
          <CardHeader
            title="Question Coverage"
            subtitle="How well your content answers reader questions"
          />
          <CardContent>
            <div className="question-coverage">
              <div className="coverage-stats">
                <div className="stat">
                  <span className="value">{questionCoverage.total_questions ?? 0}</span>
                  <span className="label">Total Questions</span>
                </div>
                <div className="stat">
                  <span className="value">{questionCoverage.answered_questions ?? 0}</span>
                  <span className="label">Answered</span>
                </div>
              </div>
              <ProgressBar
                value={questionCoverage.coverage_percent ?? 0}
                variant="success"
                showLabel
              />
              {questionCoverage.unanswered_questions?.length > 0 && (
                <div className="unanswered-list">
                  <h4>Unanswered Questions</h4>
                  {questionCoverage.unanswered_questions.slice(0, 5).map((q, idx) => (
                    <div key={idx} className="question-item">
                      <HelpCircle size={14} className="text-warning" />
                      <span>{q}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Cross-Reference Density */}
      {crossRefs && (
        <Card>
          <CardHeader
            title="Cross-Reference Analysis"
            subtitle="Internal and external linking"
          />
          <CardContent>
            <div className="crossref-stats">
              <div className="stat-row">
                <span>Internal References</span>
                <strong>{crossRefs.internal_references ?? 0}</strong>
              </div>
              <div className="stat-row">
                <span>External References</span>
                <strong>{crossRefs.external_references ?? 0}</strong>
              </div>
              <div className="stat-row">
                <span>Density Score</span>
                <strong>{crossRefs.density_score?.toFixed(1) ?? 'N/A'}</strong>
              </div>
            </div>
            {crossRefs.orphan_references?.length > 0 && (
              <div className="orphan-refs">
                <h4>Orphan References ({crossRefs.orphan_references.length})</h4>
                {crossRefs.orphan_references.slice(0, 5).map((ref, idx) => (
                  <div key={idx} className="orphan-item">
                    <Link2 size={14} className="text-warning" />
                    <span>{ref}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Style Consistency */}
      {style && (
        <Card>
          <CardHeader
            title="Style Consistency"
            subtitle="Writing style uniformity across documents"
          />
          <CardContent>
            <div className="style-score-display">
              <ProgressBar
                value={style.style_score ?? 0}
                variant={style.style_score >= 80 ? 'success' : style.style_score >= 60 ? 'warning' : 'error'}
                showLabel
                size="lg"
              />
            </div>
            {style.inconsistencies?.length > 0 && (
              <div className="inconsistencies-list">
                <h4>Style Inconsistencies</h4>
                {style.inconsistencies.slice(0, 5).map((item, idx) => (
                  <div key={idx} className="inconsistency-item">
                    <AlertTriangle size={14} className="text-warning" />
                    <span className="doc-path">{item.document}</span>
                    <span className="issue">{item.issue}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Activity View
function ActivityView() {
  const { data: auditLog, isLoading: auditLoading } = useAuditLog();
  const { data: insights, isLoading: insightsLoading } = useInsights();

  if (auditLoading || insightsLoading) {
    return <LoadingState message="Loading activity..." />;
  }

  const recentChanges = insights?.statistics?.activity?.recent_changes ?? [];
  const entries = auditLog?.entries ?? [];

  return (
    <div className="activity-content">
      {/* Recent Commits */}
      <Card>
        <CardHeader title="Recent Commits" subtitle="Git activity" />
        <CardContent>
          <div className="commits-list">
            {recentChanges.slice(0, 5).map((change, idx) => (
              <div key={idx} className="commit-item">
                <GitCommit size={16} className="text-accent" />
                <div className="commit-content">
                  <div className="commit-header">
                    <span className="commit-message">{change.message}</span>
                    <Badge variant="default" size="sm">{change.hash.substring(0, 7)}</Badge>
                  </div>
                  <div className="commit-meta">
                    <span><User size={10} /> {change.author}</span>
                    <span><Clock size={10} /> {new Date(change.date).toLocaleDateString()}</span>
                    <span><FileText size={10} /> {change.files.length} files</span>
                  </div>
                </div>
              </div>
            ))}
            {recentChanges.length === 0 && (
              <div className="empty-state small">
                <GitCommit size={24} className="text-muted" />
                <p>No recent commits</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Audit Log */}
      <Card>
        <CardHeader title="Audit Log" subtitle="System activity" />
        <CardContent>
          <div className="audit-list">
            {entries.slice(0, 10).map((entry, idx) => (
              <div key={idx} className="audit-item">
                <ActivityIcon size={14} className="text-muted" />
                <div className="audit-content">
                  <span className="audit-action">{entry.action}</span>
                  {entry.details && <span className="audit-details">{entry.details}</span>}
                </div>
                <span className="audit-time">{new Date(entry.timestamp).toLocaleString()}</span>
              </div>
            ))}
            {entries.length === 0 && (
              <div className="empty-state small">
                <ActivityIcon size={24} className="text-muted" />
                <p>No audit log entries</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Main Quality Page
export function Quality() {
  return (
    <div className="page quality-page">
      <div className="page-header">
        <h1>Quality</h1>
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
