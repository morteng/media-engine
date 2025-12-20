import { useStatus, useInsights, useFreshness } from '@/hooks/useApi';
import { StatCard } from '@/components/ui/StatCard';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { LoadingState } from '@/components/ui/Spinner';
import { Badge } from '@/components/ui/Badge';
import {
  FileText,
  Languages,
  AlertTriangle,
  Clock,
  TrendingUp,
  CheckCircle,
  XCircle,
  Award
} from 'lucide-react';

export function Dashboard() {
  const { data: status, isLoading: statusLoading } = useStatus();
  const { data: insights, isLoading: insightsLoading } = useInsights();
  const { data: freshness } = useFreshness();

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

  return (
    <div className="page overview-page">
      <div className="page-header">
        <h1>Project Overview</h1>
        <p className="text-muted">Real-time status of your media engine project</p>
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
                <span className="label">Health</span>
              </div>
            </div>
            <div className="health-metrics">
              <div className="health-grade">
                <Award size={28} className={`text-${healthVariant}`} />
                <span className="grade-value">Grade: {healthGrade}</span>
                <Badge variant={healthVariant}>{insights?.health?.status ?? 'unknown'}</Badge>
              </div>
              <div className="metric">
                <span className="metric-label">Freshness</span>
                <ProgressBar value={components?.freshness ?? 0} variant="accent" />
              </div>
              <div className="metric">
                <span className="metric-label">Translation</span>
                <ProgressBar value={components?.translation ?? 0} variant="success" />
              </div>
              <div className="metric">
                <span className="metric-label">Consistency</span>
                <ProgressBar value={components?.consistency ?? 0} variant="warning" />
              </div>
              <div className="metric">
                <span className="metric-label">Readability</span>
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
        />
        <StatCard
          label="Languages"
          value={languageCount}
          icon={<Languages size={24} />}
          variant="accent"
        />
        <StatCard
          label="Issues"
          value={issueCount}
          icon={<AlertTriangle size={24} />}
          variant={issueCount > 0 ? 'warning' : 'success'}
        />
        <StatCard
          label="Stale Content"
          value={staleCount}
          icon={<Clock size={24} />}
          variant={staleCount > 0 ? 'error' : 'success'}
        />
      </div>

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

      {/* Issues Section */}
      {issueCount > 0 && (
        <Card className="issues-card">
          <CardHeader
            title={`${issueCount} Issues to Address`}
            subtitle="Critical items affecting project health"
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
    </div>
  );
}
