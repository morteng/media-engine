import { Routes, Route } from 'react-router-dom';
import { useInsights, useAuditLog } from '@/hooks/useApi';
import { SubTabs } from '@/components/ui/SubTabs';
import { Spinner } from '@/components/ui';
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
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Spinner size="lg" className="text-primary" />
          <p className="mt-4 text-base-content/60">Loading insights...</p>
        </div>
      </div>
    );
  }

  const stats = insights?.statistics;
  const velocity = insights?.velocity;
  const incomplete = insights?.incomplete;
  const consistency = insights?.consistency ?? [];
  const debtScore = incomplete?.debt_score ?? 0;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Content Statistics */}
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="card-title text-lg">Content Statistics</h3>
            <div className="space-y-3 mt-4">
              <div className="flex justify-between items-center p-3 rounded-lg bg-base-300">
                <span className="text-base-content/70">Total Documents</span>
                <strong className="text-lg">{stats?.content?.total_documents ?? 0}</strong>
              </div>
              <div className="flex justify-between items-center p-3 rounded-lg bg-base-300">
                <span className="text-base-content/70">Total Words</span>
                <strong className="text-lg">{(stats?.content?.total_words ?? 0).toLocaleString()}</strong>
              </div>
              {stats?.content?.documents_by_language && (
                <div className="pt-3 border-t border-base-300">
                  <h4 className="text-sm text-base-content/50 uppercase tracking-wider mb-2">By Language</h4>
                  <div className="space-y-2">
                    {Object.entries(stats.content.documents_by_language).map(([lang, count]) => (
                      <div key={lang} className="flex justify-between items-center">
                        <div className="badge badge-primary">{lang.toUpperCase()}</div>
                        <span className="text-sm">{count} docs</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Velocity */}
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="card-title text-lg">Velocity</h3>
            <p className="text-sm text-base-content/60">Last {velocity?.period ?? 'month'}</p>
            <div className="grid grid-cols-3 gap-4 mt-4">
              <div className="text-center p-3 rounded-lg bg-base-300">
                <GitCommit size={20} className="text-primary mx-auto mb-2" />
                <div className="text-2xl font-bold">{velocity?.commits ?? 0}</div>
                <div className="text-xs text-base-content/60">Commits</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-base-300">
                <FileText size={20} className="text-success mx-auto mb-2" />
                <div className="text-2xl font-bold">{velocity?.documents_modified ?? 0}</div>
                <div className="text-xs text-base-content/60">Modified</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-base-300">
                <TrendingUp size={20} className="text-warning mx-auto mb-2" />
                <div className="text-success text-sm font-semibold">+{velocity?.lines_added ?? 0}</div>
                <div className="text-error text-sm font-semibold">-{velocity?.lines_removed ?? 0}</div>
              </div>
            </div>

            {velocity?.top_contributors && velocity.top_contributors.length > 0 && (
              <div className="mt-4 pt-4 border-t border-base-300">
                <h4 className="text-sm text-base-content/50 uppercase tracking-wider mb-2">Top Contributors</h4>
                <div className="space-y-2">
                  {velocity.top_contributors.slice(0, 3).map(contributor => (
                    <div key={contributor.email} className="flex items-center gap-2">
                      <Users size={14} className="text-base-content/40" />
                      <span className="flex-1 text-sm">{contributor.name}</span>
                      <div className="badge badge-ghost badge-sm">{contributor.commits}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Incomplete Content */}
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="card-title text-lg">Incomplete Content</h3>
            <p className="text-sm text-base-content/60">{incomplete?.total ?? 0} markers</p>
            <div className="mt-4 space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Technical Debt</span>
                  <span>{100 - debtScore}%</span>
                </div>
                <progress
                  className={`progress w-full ${debtScore > 50 ? 'progress-error' : 'progress-warning'}`}
                  value={100 - debtScore}
                  max="100"
                ></progress>
              </div>
              <div className="space-y-2">
                {incomplete?.items?.slice(0, 4).map((item, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-sm">
                    <div className="badge badge-warning badge-sm">{item.marker_type}</div>
                    <span className="truncate text-base-content/70">{item.document}</span>
                  </div>
                ))}
                {(incomplete?.total ?? 0) > 4 && (
                  <p className="text-sm text-base-content/50">+{(incomplete?.total ?? 0) - 4} more</p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Consistency */}
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="card-title text-lg">Consistency</h3>
            <p className="text-sm text-base-content/60">{consistency.length} issues</p>
            <div className="mt-4 space-y-2">
              {consistency.slice(0, 4).map((issue, idx) => (
                <div key={idx} className="flex items-center gap-2 p-2 rounded bg-base-300">
                  <AlertTriangle size={14} className="text-warning flex-shrink-0" />
                  <span className="truncate text-sm flex-1">{issue.document}</span>
                  <div className="flex items-center gap-1 text-xs flex-shrink-0">
                    <div className="badge badge-error badge-xs">{issue.declared}</div>
                    <span className="text-base-content/50">-&gt;</span>
                    <div className="badge badge-success badge-xs">{issue.detected}</div>
                  </div>
                </div>
              ))}
              {consistency.length > 4 && (
                <p className="text-sm text-base-content/50">+{consistency.length - 4} more</p>
              )}
              {consistency.length === 0 && (
                <div className="flex flex-col items-center py-6 text-center">
                  <CheckCircle size={24} className="text-success mb-2" />
                  <p className="text-sm text-base-content/60">No issues</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Activity View - exported for use in Quality page
export function ActivityView() {
  const { data: auditLog, isLoading: auditLoading } = useAuditLog();
  const { data: insights, isLoading: insightsLoading } = useInsights();

  if (auditLoading || insightsLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Spinner size="lg" className="text-primary" />
          <p className="mt-4 text-base-content/60">Loading activity...</p>
        </div>
      </div>
    );
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
            <div className="flex flex-col items-center py-6 text-center">
              <GitCommit size={24} className="text-base-content/30 mb-2" />
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
            <div className="flex flex-col items-center py-6 text-center">
              <ActivityIcon size={24} className="text-base-content/30 mb-2" />
              <p className="text-sm text-base-content/60">No audit log entries</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Main Insights Page
export function Insights() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Insights</h1>
        <SubTabs tabs={tabs} basePath="/insights" />
      </div>

      <Routes>
        <Route index element={<AnalyticsView />} />
        <Route path="activity" element={<ActivityView />} />
      </Routes>
    </div>
  );
}
