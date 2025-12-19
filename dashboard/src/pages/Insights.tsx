import { useInsights } from '@/hooks/useApi';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { LoadingState } from '@/components/ui/Spinner';
import {
  TrendingUp,
  Users,
  GitCommit,
  FileText,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';

export function Insights() {
  const { data: insights, isLoading } = useInsights();

  if (isLoading) {
    return <LoadingState message="Loading insights..." />;
  }

  const stats = insights?.statistics;
  const velocity = insights?.velocity;
  const incomplete = insights?.incomplete;
  const consistency = insights?.consistency ?? [];

  return (
    <div className="page insights-page">
      <div className="page-header">
        <h1>Insights</h1>
        <p className="text-muted">Analytics and metrics for your content</p>
      </div>

      {/* Statistics Overview */}
      <div className="insights-grid">
        <Card>
          <CardHeader title="Content Statistics" />
          <CardContent>
            <div className="stat-rows">
              <div className="stat-row">
                <span>Total Documents</span>
                <strong>{stats?.content?.total_documents ?? 0}</strong>
              </div>
              <div className="stat-row">
                <span>Total Words</span>
                <strong>{(stats?.content?.total_words ?? 0).toLocaleString()}</strong>
              </div>
              {stats?.content?.documents_by_language && (
                <div className="language-breakdown">
                  <h4>By Language</h4>
                  {Object.entries(stats.content.documents_by_language).map(([lang, count]) => (
                    <div key={lang} className="stat-row">
                      <Badge variant="accent">{lang.toUpperCase()}</Badge>
                      <span>{count} docs</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader title="Velocity" subtitle={`Last ${velocity?.period ?? 'month'}`} />
          <CardContent>
            <div className="velocity-stats">
              <div className="velocity-stat">
                <GitCommit size={24} className="text-accent" />
                <div>
                  <span className="stat-value">{velocity?.commits ?? 0}</span>
                  <span className="stat-label">Commits</span>
                </div>
              </div>
              <div className="velocity-stat">
                <FileText size={24} className="text-success" />
                <div>
                  <span className="stat-value">{velocity?.documents_modified ?? 0}</span>
                  <span className="stat-label">Docs Modified</span>
                </div>
              </div>
              <div className="velocity-stat">
                <TrendingUp size={24} className="text-warning" />
                <div>
                  <span className="lines-added">+{velocity?.lines_added ?? 0}</span>
                  <span className="lines-removed">-{velocity?.lines_removed ?? 0}</span>
                </div>
              </div>
            </div>

            {velocity?.top_contributors && velocity.top_contributors.length > 0 && (
              <div className="contributors">
                <h4>Contributors</h4>
                {velocity.top_contributors.map(contributor => (
                  <div key={contributor.email} className="contributor">
                    <Users size={16} />
                    <span>{contributor.name}</span>
                    <Badge variant="default" size="sm">{contributor.commits} commits</Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader
            title="Incomplete Content"
            subtitle={`${incomplete?.total ?? 0} markers found`}
          />
          <CardContent>
            <div className="debt-score">
              <span className="label">Technical Debt Score</span>
              <ProgressBar
                value={100 - (incomplete?.debt_score ?? 0)}
                variant={incomplete?.debt_score ?? 0 > 50 ? 'error' : 'warning'}
                showLabel
              />
            </div>
            <div className="incomplete-list">
              {incomplete?.items?.slice(0, 5).map((item, idx) => (
                <div key={idx} className="incomplete-item">
                  <Badge variant="warning" size="sm">{item.marker_type}</Badge>
                  <span className="item-doc">{item.document}</span>
                  <span className="item-line">L{item.line_number}</span>
                </div>
              ))}
              {(incomplete?.total ?? 0) > 5 && (
                <p className="text-muted">...and {(incomplete?.total ?? 0) - 5} more</p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader
            title="Consistency Issues"
            subtitle={`${consistency.length} issues found`}
          />
          <CardContent>
            <div className="consistency-list">
              {consistency.slice(0, 5).map((issue, idx) => (
                <div key={idx} className="consistency-item">
                  <AlertTriangle size={16} className="text-warning" />
                  <div className="issue-details">
                    <span className="issue-doc">{issue.document}</span>
                    <span className="issue-type">{issue.issue_type.replace('_', ' ')}</span>
                  </div>
                  <div className="issue-status">
                    <Badge variant="error" size="sm">{issue.declared}</Badge>
                    <span>→</span>
                    <Badge variant="success" size="sm">{issue.detected}</Badge>
                  </div>
                </div>
              ))}
              {consistency.length > 5 && (
                <p className="text-muted">...and {consistency.length - 5} more</p>
              )}
              {consistency.length === 0 && (
                <div className="empty-state">
                  <CheckCircle size={32} className="text-success" />
                  <p>No consistency issues found</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
