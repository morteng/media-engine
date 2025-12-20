import { Routes, Route } from 'react-router-dom';
import { useInsights, useFreshness } from '@/hooks/useApi';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { LoadingState } from '@/components/ui/Spinner';
import { SubTabs } from '@/components/ui/SubTabs';
import {
  Shield,
  AlertTriangle,
  AlertCircle,
  CheckCircle,
  Clock,
  XCircle
} from 'lucide-react';

const tabs = [
  { path: '', label: 'Quality' },
  { path: 'freshness', label: 'Freshness' },
];

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
              <span className="score-label">Quality Score</span>
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
        <CardHeader title="Component Scores" />
        <CardContent>
          <div className="component-scores">
            {components && Object.entries(components).map(([key, value]) => (
              <div key={key} className="component-row">
                <span className="component-name">{key}</span>
                <ProgressBar
                  value={value as number}
                  variant={(value as number) >= 90 ? 'success' : (value as number) >= 70 ? 'warning' : 'error'}
                  showLabel
                />
              </div>
            ))}
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

// Freshness View
function FreshnessView() {
  const { data: freshness, isLoading } = useFreshness();

  if (isLoading) {
    return <LoadingState message="Loading freshness..." />;
  }

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
        <Route path="freshness" element={<FreshnessView />} />
      </Routes>
    </div>
  );
}
