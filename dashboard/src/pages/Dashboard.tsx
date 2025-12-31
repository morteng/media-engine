import { Link } from 'react-router-dom';
import { useStatus, useInsights, useFreshness, usePublicationsStatus, useApi } from '@/hooks/useApi';
import { StatCard } from '@/components/ui/StatCard';
import { Spinner } from '@/components/ui';
import { RecentPublications } from '@/components/publications';
import { AIWorkspaceSummary } from '@/components/ai';
import type {
  AISessionsResponse,
  AINotesResponse,
  AITaskQueueResponse,
  AIResearchResponse,
} from '@/api/types';
import {
  Book,
  FileText,
  Languages,
  AlertTriangle,
  Clock,
  TrendingUp,
  Award,
  ArrowRight,
  Sparkles,
  Hammer,
} from 'lucide-react';

export function Dashboard() {
  const { data: status, isLoading: statusLoading } = useStatus();
  const { data: insights, isLoading: insightsLoading } = useInsights();
  const { data: freshness } = useFreshness();

  // Publications data
  const { data: publicationsData } = usePublicationsStatus();

  // AI Workspace data (graceful fallback if not available)
  const { data: sessionsData } = useApi<AISessionsResponse>('/api/ai/sessions');
  const { data: notesData } = useApi<AINotesResponse>('/api/ai/notes');
  const { data: tasksData } = useApi<AITaskQueueResponse>('/api/ai/queue');
  const { data: researchData } = useApi<AIResearchResponse>('/api/ai/research');

  if (statusLoading || insightsLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Spinner size="lg" className="text-primary" />
          <p className="mt-4 text-base-content/60">Loading project overview...</p>
        </div>
      </div>
    );
  }

  const healthScore = Math.round(insights?.health?.overall ?? 0);
  const healthGrade = insights?.health?.grade ?? 'N/A';
  const healthVariant = healthScore >= 80 ? 'success' : healthScore >= 60 ? 'warning' : 'error';

  // Calculate stats
  const totalDocs = insights?.statistics?.content?.total_documents ?? 0;
  const languageCount = status?.languages?.length ?? 0;
  const issueCount = insights?.health?.issues?.length ?? 0;
  const staleCount = freshness?.stale_count ?? 0;

  // Publications stats
  const pubStats = publicationsData?.summary ?? {
    total: 0,
    valid: 0,
    invalid: 0,
    translations_current: 0,
    translations_outdated: 0,
    total_issues: 0,
  };

  // Component scores
  const components = insights?.health?.components;

  const getHealthColor = (variant: string) => {
    switch (variant) {
      case 'success': return '#10b981';
      case 'warning': return '#f59e0b';
      case 'error': return '#ef4444';
      default: return '#6366f1';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{status?.project?.name || 'Project'} Overview</h1>
          <p className="text-base-content/60 text-sm mt-1">
            {pubStats.total} publications • {totalDocs} documents • {languageCount} languages
          </p>
        </div>
        <div className="flex gap-2">
          <Link to="/build" className="btn btn-primary btn-sm gap-1">
            <Hammer size={14} />
            Build
          </Link>
        </div>
      </div>

      {/* Main Grid: Health + Publications Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Health Score Card */}
        <div className="card bg-gradient-to-br from-base-200 to-base-300 border border-base-300">
          <div className="card-body p-6">
            <div className="flex items-center gap-6">
              {/* Health Ring */}
              <div className="relative w-24 h-24 flex-shrink-0">
                <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
                  <circle
                    cx="50"
                    cy="50"
                    r="45"
                    fill="none"
                    stroke="currentColor"
                    className="text-base-300"
                    strokeWidth="8"
                  />
                  <circle
                    cx="50"
                    cy="50"
                    r="45"
                    fill="none"
                    stroke={getHealthColor(healthVariant)}
                    strokeWidth="8"
                    strokeDasharray={`${healthScore * 2.83} 283`}
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-2xl font-bold">{healthScore}</span>
                  <span className="text-xs text-base-content/60">Health</span>
                </div>
              </div>

              {/* Health Details */}
              <div className="flex-1 space-y-2">
                <div className="flex items-center gap-2">
                  <Award size={18} className={`text-${healthVariant}`} />
                  <span className="font-medium">Grade: {healthGrade}</span>
                </div>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-base-content/70">Freshness</span>
                    <span>{components?.freshness ?? 0}%</span>
                  </div>
                  <progress className="progress progress-primary w-full h-1" value={components?.freshness ?? 0} max="100" />
                  <div className="flex justify-between">
                    <span className="text-base-content/70">Translation</span>
                    <span>{components?.translation ?? 0}%</span>
                  </div>
                  <progress className="progress progress-success w-full h-1" value={components?.translation ?? 0} max="100" />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Publications Summary */}
        <div className="card bg-base-200">
          <div className="card-body p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold flex items-center gap-2">
                <Book size={18} className="text-primary" />
                Publications
              </h3>
              <Link to="/publications" className="btn btn-ghost btn-xs gap-1">
                View All <ArrowRight size={12} />
              </Link>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 bg-base-300 rounded-lg">
                <div className="text-2xl font-bold">{pubStats.total}</div>
                <div className="text-xs text-base-content/60">Total</div>
              </div>
              <div className="text-center p-3 bg-base-300 rounded-lg">
                <div className="text-2xl font-bold text-success">{pubStats.valid}</div>
                <div className="text-xs text-base-content/60">Valid</div>
              </div>
              <div className="text-center p-3 bg-base-300 rounded-lg">
                <div className="text-2xl font-bold text-info">{pubStats.translations_current}</div>
                <div className="text-xs text-base-content/60">Synced</div>
              </div>
              <div className="text-center p-3 bg-base-300 rounded-lg">
                <div className={`text-2xl font-bold ${pubStats.total_issues > 0 ? 'text-warning' : 'text-success'}`}>
                  {pubStats.total_issues}
                </div>
                <div className="text-xs text-base-content/60">Issues</div>
              </div>
            </div>
          </div>
        </div>

        {/* AI Workspace Summary */}
        <AIWorkspaceSummary
          sessions={sessionsData?.sessions ?? []}
          notes={notesData?.notes ?? []}
          tasks={tasksData?.tasks ?? []}
          research={researchData?.entries ?? []}
        />
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard
          label="Documents"
          value={totalDocs}
          icon={<FileText size={20} />}
          variant="default"
          href="/content"
        />
        <StatCard
          label="Languages"
          value={languageCount}
          icon={<Languages size={20} />}
          variant="accent"
          href="/content/translations"
        />
        <StatCard
          label="Issues"
          value={issueCount}
          icon={<AlertTriangle size={20} />}
          variant={issueCount > 0 ? 'warning' : 'success'}
          href="/quality"
        />
        <StatCard
          label="Stale"
          value={staleCount}
          icon={<Clock size={20} />}
          variant={staleCount > 0 ? 'error' : 'success'}
          href="/quality"
        />
      </div>

      {/* Recent Publications */}
      {publicationsData?.publications && publicationsData.publications.length > 0 && (
        <div className="card bg-base-200">
          <div className="card-body">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-lg font-bold flex items-center gap-2">
                <Book size={20} className="text-primary" />
                Recent Publications
              </h2>
              <Link to="/publications" className="btn btn-ghost btn-sm gap-1">
                View All <ArrowRight size={14} />
              </Link>
            </div>
            <RecentPublications
              publications={publicationsData.publications}
              maxItems={4}
            />
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Build & Publish */}
        <Link to="/build" className="card bg-base-200 hover:bg-base-300 transition-colors">
          <div className="card-body p-4 flex-row items-center gap-4">
            <div className="p-3 rounded-lg bg-primary/10">
              <Hammer size={24} className="text-primary" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold">Build & Publish</h3>
              <p className="text-sm text-base-content/60">Generate PDF, HTML, PPTX and publish</p>
            </div>
            <ArrowRight size={20} className="text-base-content/40" />
          </div>
        </Link>

        {/* AI Workspace */}
        <Link to="/ai-assist" className="card bg-base-200 hover:bg-base-300 transition-colors">
          <div className="card-body p-4 flex-row items-center gap-4">
            <div className="p-3 rounded-lg bg-info/10">
              <Sparkles size={24} className="text-info" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold">AI Workspace</h3>
              <p className="text-sm text-base-content/60">
                {(tasksData?.pending_count ?? 0) > 0
                  ? `${tasksData?.pending_count} tasks pending`
                  : 'Sessions, notes, research'}
              </p>
            </div>
            <ArrowRight size={20} className="text-base-content/40" />
          </div>
        </Link>
      </div>

      {/* Critical Issues */}
      {issueCount > 0 && (
        <div className="card bg-base-200 border border-warning/30">
          <div className="card-body">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-lg">{issueCount} Issues to Address</h3>
              <Link to="/quality" className="btn btn-ghost btn-sm gap-1">
                View All <ArrowRight size={14} />
              </Link>
            </div>
            <div className="space-y-2">
              {insights?.health?.issues?.slice(0, 4).map((issue, idx) => (
                <div key={idx} className="flex items-start gap-3 p-3 rounded-lg bg-base-300">
                  <div className={`badge ${issue.severity === 'critical' ? 'badge-error' : 'badge-warning'} badge-sm`}>
                    {issue.category}
                  </div>
                  <span className="flex-1 text-sm">{issue.message}</span>
                  <span className="text-sm text-base-content/50 truncate max-w-[120px]">
                    {issue.document.split('/').pop()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Activity Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Translation Coverage */}
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="font-semibold mb-3">Translation Coverage</h3>
            <div className="flex flex-wrap gap-3">
              {insights?.parity?.languages?.map(lang => (
                <div key={lang} className="flex items-center gap-2">
                  <div className={`badge ${insights.parity.coverage[lang] === 100 ? 'badge-success' : 'badge-warning'}`}>
                    {lang.toUpperCase()}
                  </div>
                  <span className="text-sm">{Math.round(insights.parity.coverage[lang] ?? 0)}%</span>
                </div>
              ))}
            </div>
            <div className="mt-4">
              <progress className="progress progress-success w-full" value={components?.translation ?? 0} max="100" />
            </div>
          </div>
        </div>

        {/* Activity */}
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="font-semibold mb-3">Recent Activity</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <TrendingUp className="text-primary mx-auto mb-1" size={20} />
                <div className="text-xl font-semibold">{insights?.velocity?.commits ?? 0}</div>
                <div className="text-xs text-base-content/60">commits</div>
              </div>
              <div className="text-center">
                <FileText className="text-success mx-auto mb-1" size={20} />
                <div className="text-xl font-semibold">{insights?.velocity?.documents_modified ?? 0}</div>
                <div className="text-xs text-base-content/60">modified</div>
              </div>
              <div className="text-center">
                <div className="flex flex-col items-center gap-0.5">
                  <span className="text-success text-sm">+{insights?.velocity?.lines_added ?? 0}</span>
                  <span className="text-error text-sm">-{insights?.velocity?.lines_removed ?? 0}</span>
                </div>
                <div className="text-xs text-base-content/60">lines</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
