import { useStatus, useInsights, useFreshness, useQualitySummary } from '@/hooks/useApi';
import { StatCard } from '@/components/ui/StatCard';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { LoadingState } from '@/components/ui/Spinner';
import { Badge } from '@/components/ui/Badge';
import { InfoTooltip, METRIC_EXPLANATIONS } from '@/components/ui/InfoTooltip';
import { Link } from 'react-router-dom';
import {
  FileText,
  Languages,
  AlertTriangle,
  Clock,
  TrendingUp,
  CheckCircle,
  XCircle,
  Award,
  Brain,
  Network,
  Code,
  Target,
  RefreshCw,
  BookOpen,
  ArrowRight,
  Sparkles,
  Zap,
} from 'lucide-react';

export function Dashboard() {
  const { data: status, isLoading: statusLoading } = useStatus();
  const { data: insights, isLoading: insightsLoading } = useInsights();
  const { data: freshness } = useFreshness();
  const { data: qualitySummary } = useQualitySummary();

  if (statusLoading || insightsLoading) {
    return <LoadingState message="Loading project overview..." />;
  }

  const healthScore = Math.round(insights?.health?.overall ?? 0);
  const healthGrade = insights?.health?.grade ?? 'N/A';
  const healthVariant = healthScore >= 80 ? 'success' : healthScore >= 60 ? 'warning' : 'error';

  // Calculate document count from status
  const totalDocs = insights?.statistics?.content?.total_documents ?? 0;
  const languageCount = status?.languages?.length ?? 0;
  const issueCount = insights?.health?.issues?.length ?? 0;
  const staleCount = freshness?.stale_count ?? 0;
  const freshCount = freshness?.fresh_count ?? 0;
  const totalFreshness = freshness?.total_items ?? 0;

  // Component scores
  const components = insights?.health?.components;

  // Advanced analysis availability
  const advancedAvailable = qualitySummary?.advanced_available;
  const advancedHighlights = qualitySummary?.advanced_highlights;
  const hasAdvancedModules = advancedAvailable && Object.values(advancedAvailable).some(v => v);

  return (
    <div className="page overview-page">
      <div className="page-header">
        <h1>Project Overview</h1>
      </div>

      {/* Health Score Hero */}
      <Card variant="gradient" className="health-hero">
        <CardContent>
          <div className="health-score-display">
            <div className="health-score-ring">
              <svg viewBox="0 0 100 100" className="health-ring-svg">
                <circle
                  cx="50"
                  cy="50"
                  r="45"
                  fill="none"
                  stroke="var(--bg-tertiary)"
                  strokeWidth="8"
                />
                <circle
                  cx="50"
                  cy="50"
                  r="45"
                  fill="none"
                  stroke={`var(--color-${healthVariant})`}
                  strokeWidth="8"
                  strokeDasharray={`${healthScore * 2.83} 283`}
                  strokeLinecap="round"
                  transform="rotate(-90 50 50)"
                />
              </svg>
              <div className="health-score-value">
                <span className="score">{healthScore}</span>
                <span className="label">
                  Health
                  <InfoTooltip {...METRIC_EXPLANATIONS.healthScore} />
                </span>
              </div>
            </div>
            <div className="health-metrics">
              <div className="health-grade">
                <Award size={28} className={`text-${healthVariant}`} />
                <span className="grade-value">Grade: {healthGrade}</span>
                <Badge variant={healthVariant}>{insights?.health?.status ?? 'unknown'}</Badge>
              </div>
              <div className="metric">
                <span className="metric-label">
                  Freshness
                  <InfoTooltip {...METRIC_EXPLANATIONS.freshness} />
                </span>
                <ProgressBar value={components?.freshness ?? 0} variant="accent" />
              </div>
              <div className="metric">
                <span className="metric-label">
                  Translation
                  <InfoTooltip {...METRIC_EXPLANATIONS.translation} />
                </span>
                <ProgressBar value={components?.translation ?? 0} variant="success" />
              </div>
              <div className="metric">
                <span className="metric-label">
                  Consistency
                  <InfoTooltip {...METRIC_EXPLANATIONS.consistency} />
                </span>
                <ProgressBar value={components?.consistency ?? 0} variant="warning" />
              </div>
              <div className="metric">
                <span className="metric-label">
                  Readability
                  <InfoTooltip {...METRIC_EXPLANATIONS.readability} />
                </span>
                <ProgressBar value={components?.readability ?? 0} variant="info" />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats Grid */}
      <div className="stats-grid">
        <StatCard
          label="Documents"
          value={totalDocs}
          icon={<FileText size={24} />}
          variant="default"
          tooltip={METRIC_EXPLANATIONS.documentCount}
        />
        <StatCard
          label="Languages"
          value={languageCount}
          icon={<Languages size={24} />}
          variant="accent"
          tooltip={METRIC_EXPLANATIONS.languageCount}
        />
        <StatCard
          label="Issues"
          value={issueCount}
          icon={<AlertTriangle size={24} />}
          variant={issueCount > 0 ? 'warning' : 'success'}
          tooltip={METRIC_EXPLANATIONS.issueCount}
        />
        <StatCard
          label="Stale Content"
          value={staleCount}
          icon={<Clock size={24} />}
          variant={staleCount > 0 ? 'error' : 'success'}
          tooltip={METRIC_EXPLANATIONS.staleCount}
        />
      </div>

      {/* Advanced Analysis Summary */}
      {hasAdvancedModules && (
        <Card className="advanced-summary-card">
          <CardHeader
            title="Advanced Analysis"
            action={
              <Link to="/quality" className="see-all-link">
                View All <ArrowRight size={14} />
              </Link>
            }
          />
          <CardContent>
            <div className="advanced-modules-grid">
              {advancedAvailable?.semantic && (
                <Link to="/quality/semantic" className="module-card">
                  <Brain size={24} className="text-accent" />
                  <div className="module-info">
                    <span className="module-name">Semantic Analysis</span>
                    {advancedHighlights?.semantic ? (
                      <span className="module-highlight text-warning">
                        {advancedHighlights.semantic.message}
                      </span>
                    ) : (
                      <span className="module-status text-success">Active</span>
                    )}
                  </div>
                  <ArrowRight size={16} className="module-arrow" />
                </Link>
              )}

              {advancedAvailable?.knowledge_graph && (
                <Link to="/quality/knowledge" className="module-card">
                  <Network size={24} className="text-info" />
                  <div className="module-info">
                    <span className="module-name">Knowledge Graph</span>
                    {advancedHighlights?.knowledge_graph ? (
                      <span className="module-highlight text-warning">
                        {advancedHighlights.knowledge_graph.message}
                      </span>
                    ) : (
                      <span className="module-status text-success">Active</span>
                    )}
                  </div>
                  <ArrowRight size={16} className="module-arrow" />
                </Link>
              )}

              {advancedAvailable?.predictive_freshness && (
                <Link to="/quality/freshness" className="module-card">
                  <RefreshCw size={24} className="text-warning" />
                  <div className="module-info">
                    <span className="module-name">Predictive Freshness</span>
                    {advancedHighlights?.predictive_freshness ? (
                      <span className="module-highlight text-error">
                        {advancedHighlights.predictive_freshness.message}
                      </span>
                    ) : (
                      <span className="module-status text-success">Active</span>
                    )}
                  </div>
                  <ArrowRight size={16} className="module-arrow" />
                </Link>
              )}

              {advancedAvailable?.enhanced_codesync && (
                <Link to="/quality/codesync" className="module-card">
                  <Code size={24} className="text-success" />
                  <div className="module-info">
                    <span className="module-name">Code Sync</span>
                    {advancedHighlights?.enhanced_codesync ? (
                      <span className="module-highlight text-warning">
                        {advancedHighlights.enhanced_codesync.message}
                      </span>
                    ) : (
                      <span className="module-status text-success">Active</span>
                    )}
                  </div>
                  <ArrowRight size={16} className="module-arrow" />
                </Link>
              )}

              {advancedAvailable?.norwegian_readability && (
                <Link to="/quality/readability" className="module-card">
                  <BookOpen size={24} className="text-accent" />
                  <div className="module-info">
                    <span className="module-name">Norwegian LIX</span>
                    <span className="module-status text-success">Active</span>
                  </div>
                  <ArrowRight size={16} className="module-arrow" />
                </Link>
              )}

              {advancedAvailable?.advanced_analysis && (
                <Link to="/quality/advanced" className="module-card">
                  <Target size={24} className="text-error" />
                  <div className="module-info">
                    <span className="module-name">Advanced Analysis</span>
                    <span className="module-status text-success">Active</span>
                  </div>
                  <ArrowRight size={16} className="module-arrow" />
                </Link>
              )}
            </div>

            {/* Quick Highlights */}
            {Object.keys(advancedHighlights || {}).length > 0 && (
              <div className="analysis-highlights">
                <h4><Sparkles size={16} /> Key Findings</h4>
                <div className="highlights-list">
                  {Object.entries(advancedHighlights || {}).map(([key, highlight]) => (
                    <div key={key} className="highlight-item">
                      <Zap size={14} className="text-warning" />
                      <span>{highlight.message}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Quick Status Cards */}
      <div className="status-grid">
        <Card>
          <CardHeader title="Translation Coverage" subtitle="Multi-language parity" />
          <CardContent>
            <div className="translation-summary">
              {insights?.parity?.languages?.map(lang => (
                <div key={lang} className="translation-stat">
                  <Badge variant={insights.parity.coverage[lang] === 100 ? 'success' : 'warning'}>
                    {lang.toUpperCase()}
                  </Badge>
                  <span>{Math.round(insights.parity.coverage[lang] ?? 0)}%</span>
                </div>
              ))}
            </div>
            <ProgressBar
              value={components?.translation ?? 0}
              showLabel
              variant="success"
              size="lg"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader title="Content Freshness" subtitle={`${totalFreshness} tracked items`} />
          <CardContent>
            <div className="freshness-summary">
              <div className="freshness-stat">
                <CheckCircle className="text-success" size={18} />
                <Badge variant="success">Fresh</Badge>
                <span>{freshCount}</span>
              </div>
              <div className="freshness-stat">
                <XCircle className="text-warning" size={18} />
                <Badge variant="warning">Stale</Badge>
                <span>{staleCount}</span>
              </div>
            </div>
            <ProgressBar
              value={freshCount}
              max={totalFreshness || 100}
              showLabel
              variant="accent"
              size="lg"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader title="Activity" subtitle="This month" />
          <CardContent>
            <div className="activity-summary">
              <div className="activity-stat">
                <TrendingUp className="text-accent" size={24} />
                <div>
                  <span className="stat-value">{insights?.velocity?.commits ?? 0}</span>
                  <span className="stat-label">commits</span>
                </div>
              </div>
              <div className="activity-stat">
                <FileText className="text-success" size={24} />
                <div>
                  <span className="stat-value">{insights?.velocity?.documents_modified ?? 0}</span>
                  <span className="stat-label">docs modified</span>
                </div>
              </div>
              <div className="activity-stat">
                <span className="lines-added">+{insights?.velocity?.lines_added ?? 0}</span>
                <span className="lines-removed">-{insights?.velocity?.lines_removed ?? 0}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Critical Issues Section */}
      {issueCount > 0 && (
        <Card className="issues-card">
          <CardHeader
            title={`${issueCount} Issues to Address`}
            subtitle="Critical items affecting project health"
            action={
              <Link to="/quality" className="see-all-link">
                View All <ArrowRight size={14} />
              </Link>
            }
          />
          <CardContent>
            <div className="issues-list">
              {insights?.health?.issues?.slice(0, 5).map((issue, idx) => (
                <div key={idx} className="issue-item">
                  <Badge variant={issue.severity === 'critical' ? 'error' : 'warning'}>
                    {issue.category}
                  </Badge>
                  <span className="issue-message">{issue.message}</span>
                  <span className="issue-doc text-muted">{issue.document}</span>
                </div>
              ))}
              {issueCount > 5 && (
                <p className="text-muted">...and {issueCount - 5} more</p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recommendations */}
      {qualitySummary?.recommendations && qualitySummary.recommendations.length > 0 && (
        <Card className="recommendations-card">
          <CardHeader
            title="Recommendations"
            subtitle="Suggested improvements"
          />
          <CardContent>
            <div className="recommendations-list">
              {qualitySummary.recommendations.slice(0, 5).map((rec, idx) => (
                <div key={idx} className="recommendation-item">
                  <Sparkles size={14} className="text-accent" />
                  <span>{rec}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
