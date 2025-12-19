import { useFreshness } from '@/hooks/useApi';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { LoadingState } from '@/components/ui/Spinner';
import {
  Clock,
  CheckCircle,
  AlertTriangle,
  XCircle,
  FileText,
  RefreshCw
} from 'lucide-react';

export function Freshness() {
  const { data: freshness, isLoading } = useFreshness();

  if (isLoading) {
    return <LoadingState message="Loading freshness data..." />;
  }

  const totalItems = freshness?.total_items ?? 0;
  const freshCount = freshness?.fresh_count ?? 0;
  const staleCount = freshness?.stale_count ?? 0;
  const expiredCount = freshness?.expired_count ?? 0;
  const untrackedCount = freshness?.untracked_count ?? 0;

  const freshPercent = totalItems > 0 ? Math.round((freshCount / totalItems) * 100) : 0;

  return (
    <div className="page freshness-page">
      <div className="page-header">
        <h1>Freshness</h1>
        <p className="text-muted">Track content freshness and staleness</p>
      </div>

      {/* Summary Cards */}
      <div className="freshness-summary">
        <Card className="summary-card card-success">
          <CardContent>
            <CheckCircle size={32} className="text-success" />
            <span className="count">{freshCount}</span>
            <span className="label">Fresh</span>
          </CardContent>
        </Card>
        <Card className={`summary-card ${staleCount > 0 ? 'card-warning' : ''}`}>
          <CardContent>
            <AlertTriangle size={32} className="text-warning" />
            <span className="count">{staleCount}</span>
            <span className="label">Stale</span>
          </CardContent>
        </Card>
        <Card className={`summary-card ${expiredCount > 0 ? 'card-error' : ''}`}>
          <CardContent>
            <XCircle size={32} className="text-error" />
            <span className="count">{expiredCount}</span>
            <span className="label">Expired</span>
          </CardContent>
        </Card>
        <Card className="summary-card">
          <CardContent>
            <RefreshCw size={32} className="text-muted" />
            <span className="count">{untrackedCount}</span>
            <span className="label">Untracked</span>
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
          <CardHeader
            title="Stale Content"
            subtitle={`${freshness.stale_items.length} items need attention`}
          />
          <CardContent>
            <div className="stale-list">
              {freshness.stale_items.map((item, idx) => (
                <div key={idx} className="stale-item">
                  <Clock size={16} className="text-warning" />
                  <FileText size={16} />
                  <span className="item-path">{item.path}</span>
                  <Badge variant="default" size="sm">{item.content_type}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* All Items */}
      <Card>
        <CardHeader title="All Tracked Items" subtitle="Content freshness status" />
        <CardContent>
          <div className="items-list">
            {freshness?.items?.slice(0, 20).map((item, idx) => (
              <div key={idx} className={`item-row status-${item.status}`}>
                {item.status === 'fresh' ? (
                  <CheckCircle size={16} className="text-success" />
                ) : item.status === 'stale' ? (
                  <AlertTriangle size={16} className="text-warning" />
                ) : (
                  <XCircle size={16} className="text-error" />
                )}
                <span className="item-path">{item.path}</span>
                <Badge
                  variant={item.status === 'fresh' ? 'success' : item.status === 'stale' ? 'warning' : 'error'}
                  size="sm"
                >
                  {item.status}
                </Badge>
                <span className="item-type text-muted">{item.content_type}</span>
              </div>
            ))}
            {(freshness?.items?.length ?? 0) > 20 && (
              <p className="text-muted">...and {(freshness?.items?.length ?? 0) - 20} more items</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
