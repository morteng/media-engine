import { useQuality, useInsights } from '@/hooks/useApi';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { LoadingState } from '@/components/ui/Spinner';
import {
  Shield,
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle,
  FileWarning
} from 'lucide-react';

export function Quality() {
  const { data: quality, isLoading: qualityLoading } = useQuality();
  const { data: insights, isLoading: insightsLoading } = useInsights();

  if (qualityLoading || insightsLoading) {
    return <LoadingState message="Loading quality checks..." />;
  }

  const health = insights?.health;
  const issues = health?.issues ?? [];
  const components = health?.components;

  const errorCount = issues.filter(i => i.severity === 'critical').length;
  const warningCount = issues.filter(i => i.severity === 'warning').length;
  const infoCount = issues.filter(i => i.severity === 'info').length;

  return (
    <div className="page quality-page">
      <div className="page-header">
        <h1>Quality</h1>
        <p className="text-muted">Content quality checks and validation</p>
      </div>

      {/* Quality Score */}
      <Card variant="gradient" className="quality-hero">
        <CardContent>
          <div className="quality-score-display">
            <Shield size={48} className={health?.overall && health.overall >= 80 ? 'text-success' : 'text-warning'} />
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
            <AlertCircle size={24} className="text-error" />
            <span className="count">{errorCount}</span>
            <span className="label">Critical</span>
          </CardContent>
        </Card>
        <Card className={warningCount > 0 ? 'card-warning' : ''}>
          <CardContent>
            <AlertTriangle size={24} className="text-warning" />
            <span className="count">{warningCount}</span>
            <span className="label">Warnings</span>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Info size={24} className="text-info" />
            <span className="count">{infoCount}</span>
            <span className="label">Info</span>
          </CardContent>
        </Card>
        <Card className="card-success">
          <CardContent>
            <CheckCircle size={24} className="text-success" />
            <span className="count">{health?.document_count ?? 0}</span>
            <span className="label">Documents</span>
          </CardContent>
        </Card>
      </div>

      {/* Component Scores */}
      <Card>
        <CardHeader title="Component Scores" subtitle="Quality breakdown by area" />
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

      {/* Issues List */}
      {issues.length > 0 && (
        <Card>
          <CardHeader
            title="Issues"
            subtitle={`${issues.length} issues to address`}
          />
          <CardContent>
            <div className="issues-list">
              {issues.map((issue, idx) => (
                <div key={idx} className={`issue-item severity-${issue.severity}`}>
                  <FileWarning size={18} />
                  <div className="issue-content">
                    <div className="issue-header">
                      <Badge
                        variant={issue.severity === 'critical' ? 'error' : 'warning'}
                        size="sm"
                      >
                        {issue.category}
                      </Badge>
                      <span className="issue-doc">{issue.document}</span>
                    </div>
                    <p className="issue-message">{issue.message}</p>
                    {issue.recommendation && (
                      <p className="issue-recommendation text-muted">{issue.recommendation}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {issues.length === 0 && (
        <Card className="empty-card">
          <CardContent className="empty-state">
            <CheckCircle size={48} className="text-success" />
            <h3>All Clear!</h3>
            <p className="text-muted">No quality issues found in your content.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
