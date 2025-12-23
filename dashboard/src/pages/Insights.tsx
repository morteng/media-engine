import { Routes, Route } from 'react-router-dom';
import { useInsights, useAuditLog } from '@/hooks/useApi';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { LoadingState } from '@/components/ui/Spinner';
import { SubTabs } from '@/components/ui/SubTabs';
import {
  TrendingUp,
  Users,
  GitCommit,
  FileText,
  AlertTriangle,
  CheckCircle,
  Clock,
  Activity as ActivityIcon,
  User
} from 'lucide-react';

const tabs = [
  { path: '', label: 'Analytics' },
  { path: 'activity', label: 'Activity' },
];

// Analytics View - exported for use in Quality page
export function AnalyticsView() {
  const { data: insights, isLoading } = useInsights();

  if (isLoading) {
    return <LoadingState message="Loading insights..." />;
  }

  const stats = insights?.statistics;
  const velocity = insights?.velocity;
  const incomplete = insights?.incomplete;
  const consistency = insights?.consistency ?? [];

  return (
    <div className="insights-content">
      <div className="insights-grid">
        {/* Content Statistics */}
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

        {/* Velocity */}
        <Card>
          <CardHeader title="Velocity" subtitle={`Last ${velocity?.period ?? 'month'}`} />
          <CardContent>
            <div className="velocity-stats">
              <div className="velocity-stat">
                <GitCommit size={20} className="text-accent" />
                <div>
                  <span className="stat-value">{velocity?.commits ?? 0}</span>
                  <span className="stat-label">Commits</span>
                </div>
              </div>
              <div className="velocity-stat">
                <FileText size={20} className="text-success" />
                <div>
                  <span className="stat-value">{velocity?.documents_modified ?? 0}</span>
                  <span className="stat-label">Modified</span>
                </div>
              </div>
              <div className="velocity-stat">
                <TrendingUp size={20} className="text-warning" />
                <div>
                  <span className="lines-added">+{velocity?.lines_added ?? 0}</span>
                  <span className="lines-removed">-{velocity?.lines_removed ?? 0}</span>
                </div>
              </div>
            </div>

            {velocity?.top_contributors && velocity.top_contributors.length > 0 && (
              <div className="contributors">
                <h4>Top Contributors</h4>
                {velocity.top_contributors.slice(0, 3).map(contributor => (
                  <div key={contributor.email} className="contributor">
                    <Users size={14} />
                    <span>{contributor.name}</span>
                    <Badge variant="default" size="sm">{contributor.commits}</Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Incomplete Content */}
        <Card>
          <CardHeader title="Incomplete Content" subtitle={`${incomplete?.total ?? 0} markers`} />
          <CardContent>
            <div className="debt-score">
              <span className="label">Technical Debt</span>
              <ProgressBar
                value={100 - (incomplete?.debt_score ?? 0)}
                variant={incomplete?.debt_score ?? 0 > 50 ? 'error' : 'warning'}
                showLabel
              />
            </div>
            <div className="incomplete-list">
              {incomplete?.items?.slice(0, 4).map((item, idx) => (
                <div key={idx} className="incomplete-item">
                  <Badge variant="warning" size="sm">{item.marker_type}</Badge>
                  <span className="item-doc">{item.document}</span>
                </div>
              ))}
              {(incomplete?.total ?? 0) > 4 && (
                <p className="text-muted">+{(incomplete?.total ?? 0) - 4} more</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Consistency */}
        <Card>
          <CardHeader title="Consistency" subtitle={`${consistency.length} issues`} />
          <CardContent>
            <div className="consistency-list">
              {consistency.slice(0, 4).map((issue, idx) => (
                <div key={idx} className="consistency-item">
                  <AlertTriangle size={14} className="text-warning" />
                  <span className="issue-doc">{issue.document}</span>
                  <div className="issue-status">
                    <Badge variant="error" size="sm">{issue.declared}</Badge>
                    <span>→</span>
                    <Badge variant="success" size="sm">{issue.detected}</Badge>
                  </div>
                </div>
              ))}
              {consistency.length > 4 && (
                <p className="text-muted">+{consistency.length - 4} more</p>
              )}
              {consistency.length === 0 && (
                <div className="empty-state small">
                  <CheckCircle size={24} className="text-success" />
                  <p>No issues</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// Activity View - exported for use in Quality page
export function ActivityView() {
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

// Main Insights Page
export function Insights() {
  return (
    <div className="page insights-page">
      <div className="page-header">
        <h1>Insights</h1>
        <SubTabs tabs={tabs} basePath="/insights" />
      </div>

      <Routes>
        <Route index element={<AnalyticsView />} />
        <Route path="activity" element={<ActivityView />} />
      </Routes>
    </div>
  );
}
