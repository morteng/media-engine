import { useAuditLog, useInsights } from '@/hooks/useApi';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { LoadingState } from '@/components/ui/Spinner';
import {
  Activity as ActivityIcon,
  GitCommit,
  FileText,
  Clock,
  User
} from 'lucide-react';

export function Activity() {
  const { data: auditLog, isLoading: auditLoading } = useAuditLog();
  const { data: insights, isLoading: insightsLoading } = useInsights();

  if (auditLoading || insightsLoading) {
    return <LoadingState message="Loading activity..." />;
  }

  const recentChanges = insights?.statistics?.activity?.recent_changes ?? [];
  const entries = auditLog?.entries ?? [];

  return (
    <div className="page activity-page">
      <div className="page-header">
        <h1>Activity</h1>
        <p className="text-muted">Recent changes and audit log</p>
      </div>

      {/* Recent Commits */}
      <Card>
        <CardHeader title="Recent Commits" subtitle="Git activity in content" />
        <CardContent>
          <div className="commits-list">
            {recentChanges.map((change, idx) => (
              <div key={idx} className="commit-item">
                <div className="commit-icon">
                  <GitCommit size={20} />
                </div>
                <div className="commit-content">
                  <div className="commit-header">
                    <span className="commit-message">{change.message}</span>
                    <Badge variant="default" size="sm">
                      {change.hash.substring(0, 7)}
                    </Badge>
                  </div>
                  <div className="commit-meta">
                    <span className="commit-author">
                      <User size={12} />
                      {change.author}
                    </span>
                    <span className="commit-date">
                      <Clock size={12} />
                      {new Date(change.date).toLocaleDateString()}
                    </span>
                    <span className="commit-files">
                      <FileText size={12} />
                      {change.files.length} files
                    </span>
                  </div>
                  {change.files.length > 0 && (
                    <div className="commit-files-list">
                      {change.files.slice(0, 3).map((file, fidx) => (
                        <span key={fidx} className="file-path">{file}</span>
                      ))}
                      {change.files.length > 3 && (
                        <span className="more-files">+{change.files.length - 3} more</span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {recentChanges.length === 0 && (
              <div className="empty-state">
                <GitCommit size={32} className="text-muted" />
                <p>No recent commits found</p>
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
            {entries.map((entry, idx) => (
              <div key={idx} className="audit-item">
                <div className="audit-icon">
                  <ActivityIcon size={16} />
                </div>
                <div className="audit-content">
                  <span className="audit-action">{entry.action}</span>
                  {entry.details && (
                    <span className="audit-details text-muted">{entry.details}</span>
                  )}
                </div>
                <div className="audit-meta">
                  {entry.user && (
                    <Badge variant="default" size="sm">{entry.user}</Badge>
                  )}
                  <span className="audit-time text-muted">
                    {new Date(entry.timestamp).toLocaleString()}
                  </span>
                </div>
              </div>
            ))}
            {entries.length === 0 && (
              <div className="empty-state">
                <ActivityIcon size={32} className="text-muted" />
                <p>No audit log entries</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
