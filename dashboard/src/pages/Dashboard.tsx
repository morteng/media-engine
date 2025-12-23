import { useStatus, useInsights, useFreshness, useQualitySummary } from '@/hooks/useApi';
import { StatCard } from '@/components/ui/StatCard';
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
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <span className="loading loading-spinner loading-lg text-primary"></span>
          <p className="mt-4 text-base-content/60">Loading project overview...</p>
        </div>
      </div>
    );
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
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">Project Overview</h1>
      </div>

      {/* Health Score Hero */}
      <div className="card bg-gradient-to-br from-base-200 to-base-300 border border-base-300">
        <div className="card-body">
          <div className="flex flex-col lg:flex-row items-center gap-8">
            {/* Health Ring */}
            <div className="relative w-40 h-40 flex-shrink-0">
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
                <span className="text-4xl font-bold">{healthScore}</span>
                <span className="text-sm text-base-content/60 flex items-center gap-1">
                  Health
                  <InfoTooltip {...METRIC_EXPLANATIONS.healthScore} />
                </span>
              </div>
            </div>

            {/* Health Metrics */}
            <div className="flex-1 space-y-4">
              <div className="flex items-center gap-3 mb-4">
                <Award size={28} className={`text-${healthVariant}`} />
                <span className="text-lg">Grade: {healthGrade}</span>
                <div className={`badge badge-${healthVariant}`}>{insights?.health?.status ?? 'unknown'}</div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <span className="text-sm text-base-content/70 flex items-center gap-1">
                    Freshness
                    <InfoTooltip {...METRIC_EXPLANATIONS.freshness} />
                  </span>
                  <progress className="progress progress-primary w-full" value={components?.freshness ?? 0} max="100"></progress>
                </div>
                <div className="space-y-1">
                  <span className="text-sm text-base-content/70 flex items-center gap-1">
                    Translation
                    <InfoTooltip {...METRIC_EXPLANATIONS.translation} />
                  </span>
                  <progress className="progress progress-success w-full" value={components?.translation ?? 0} max="100"></progress>
                </div>
                <div className="space-y-1">
                  <span className="text-sm text-base-content/70 flex items-center gap-1">
                    Consistency
                    <InfoTooltip {...METRIC_EXPLANATIONS.consistency} />
                  </span>
                  <progress className="progress progress-warning w-full" value={components?.consistency ?? 0} max="100"></progress>
                </div>
                <div className="space-y-1">
                  <span className="text-sm text-base-content/70 flex items-center gap-1">
                    Readability
                    <InfoTooltip {...METRIC_EXPLANATIONS.readability} />
                  </span>
                  <progress className="progress progress-info w-full" value={components?.readability ?? 0} max="100"></progress>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
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
        <div className="card bg-base-200">
          <div className="card-body">
            <div className="flex items-center justify-between mb-4">
              <h3 className="card-title text-lg">Advanced Analysis</h3>
              <Link to="/quality" className="btn btn-ghost btn-sm gap-1">
                View All <ArrowRight size={14} />
              </Link>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {advancedAvailable?.semantic && (
                <Link to="/quality/semantic" className="flex items-center gap-3 p-4 rounded-lg bg-base-300 hover:bg-base-100 transition-colors group">
                  <Brain size={24} className="text-primary" />
                  <div className="flex-1 min-w-0">
                    <span className="font-medium block">Semantic Analysis</span>
                    {advancedHighlights?.semantic ? (
                      <span className="text-sm text-warning truncate block">{advancedHighlights.semantic.message}</span>
                    ) : (
                      <span className="text-sm text-success">Active</span>
                    )}
                  </div>
                  <ArrowRight size={16} className="text-base-content/40 group-hover:text-base-content transition-colors" />
                </Link>
              )}

              {advancedAvailable?.knowledge_graph && (
                <Link to="/quality/knowledge" className="flex items-center gap-3 p-4 rounded-lg bg-base-300 hover:bg-base-100 transition-colors group">
                  <Network size={24} className="text-info" />
                  <div className="flex-1 min-w-0">
                    <span className="font-medium block">Knowledge Graph</span>
                    {advancedHighlights?.knowledge_graph ? (
                      <span className="text-sm text-warning truncate block">{advancedHighlights.knowledge_graph.message}</span>
                    ) : (
                      <span className="text-sm text-success">Active</span>
                    )}
                  </div>
                  <ArrowRight size={16} className="text-base-content/40 group-hover:text-base-content transition-colors" />
                </Link>
              )}

              {advancedAvailable?.predictive_freshness && (
                <Link to="/quality/freshness" className="flex items-center gap-3 p-4 rounded-lg bg-base-300 hover:bg-base-100 transition-colors group">
                  <RefreshCw size={24} className="text-warning" />
                  <div className="flex-1 min-w-0">
                    <span className="font-medium block">Predictive Freshness</span>
                    {advancedHighlights?.predictive_freshness ? (
                      <span className="text-sm text-error truncate block">{advancedHighlights.predictive_freshness.message}</span>
                    ) : (
                      <span className="text-sm text-success">Active</span>
                    )}
                  </div>
                  <ArrowRight size={16} className="text-base-content/40 group-hover:text-base-content transition-colors" />
                </Link>
              )}

              {advancedAvailable?.enhanced_codesync && (
                <Link to="/quality/codesync" className="flex items-center gap-3 p-4 rounded-lg bg-base-300 hover:bg-base-100 transition-colors group">
                  <Code size={24} className="text-success" />
                  <div className="flex-1 min-w-0">
                    <span className="font-medium block">Code Sync</span>
                    {advancedHighlights?.enhanced_codesync ? (
                      <span className="text-sm text-warning truncate block">{advancedHighlights.enhanced_codesync.message}</span>
                    ) : (
                      <span className="text-sm text-success">Active</span>
                    )}
                  </div>
                  <ArrowRight size={16} className="text-base-content/40 group-hover:text-base-content transition-colors" />
                </Link>
              )}

              {advancedAvailable?.norwegian_readability && (
                <Link to="/quality/readability" className="flex items-center gap-3 p-4 rounded-lg bg-base-300 hover:bg-base-100 transition-colors group">
                  <BookOpen size={24} className="text-primary" />
                  <div className="flex-1 min-w-0">
                    <span className="font-medium block">Norwegian LIX</span>
                    <span className="text-sm text-success">Active</span>
                  </div>
                  <ArrowRight size={16} className="text-base-content/40 group-hover:text-base-content transition-colors" />
                </Link>
              )}

              {advancedAvailable?.advanced_analysis && (
                <Link to="/quality/advanced" className="flex items-center gap-3 p-4 rounded-lg bg-base-300 hover:bg-base-100 transition-colors group">
                  <Target size={24} className="text-error" />
                  <div className="flex-1 min-w-0">
                    <span className="font-medium block">Advanced Analysis</span>
                    <span className="text-sm text-success">Active</span>
                  </div>
                  <ArrowRight size={16} className="text-base-content/40 group-hover:text-base-content transition-colors" />
                </Link>
              )}
            </div>

            {/* Quick Highlights */}
            {Object.keys(advancedHighlights || {}).length > 0 && (
              <div className="mt-6 pt-4 border-t border-base-300">
                <h4 className="text-sm font-medium flex items-center gap-2 mb-3">
                  <Sparkles size={16} className="text-primary" /> Key Findings
                </h4>
                <div className="space-y-2">
                  {Object.entries(advancedHighlights || {}).map(([key, highlight]) => (
                    <div key={key} className="flex items-center gap-2 text-sm">
                      <Zap size={14} className="text-warning flex-shrink-0" />
                      <span className="text-base-content/80">{highlight.message}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Quick Status Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="card-title text-base">Translation Coverage</h3>
            <p className="text-sm text-base-content/60">Multi-language parity</p>
            <div className="flex flex-wrap gap-2 my-3">
              {insights?.parity?.languages?.map(lang => (
                <div key={lang} className="flex items-center gap-2">
                  <div className={`badge ${insights.parity.coverage[lang] === 100 ? 'badge-success' : 'badge-warning'}`}>
                    {lang.toUpperCase()}
                  </div>
                  <span className="text-sm">{Math.round(insights.parity.coverage[lang] ?? 0)}%</span>
                </div>
              ))}
            </div>
            <div className="mt-auto">
              <div className="flex justify-between text-sm mb-1">
                <span>Coverage</span>
                <span>{components?.translation ?? 0}%</span>
              </div>
              <progress className="progress progress-success w-full h-3" value={components?.translation ?? 0} max="100"></progress>
            </div>
          </div>
        </div>

        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="card-title text-base">Content Freshness</h3>
            <p className="text-sm text-base-content/60">{totalFreshness} tracked items</p>
            <div className="flex gap-4 my-3">
              <div className="flex items-center gap-2">
                <CheckCircle className="text-success" size={18} />
                <div className="badge badge-success badge-sm">Fresh</div>
                <span className="text-sm">{freshCount}</span>
              </div>
              <div className="flex items-center gap-2">
                <XCircle className="text-warning" size={18} />
                <div className="badge badge-warning badge-sm">Stale</div>
                <span className="text-sm">{staleCount}</span>
              </div>
            </div>
            <div className="mt-auto">
              <div className="flex justify-between text-sm mb-1">
                <span>Fresh</span>
                <span>{freshCount} / {totalFreshness || 0}</span>
              </div>
              <progress className="progress progress-primary w-full h-3" value={freshCount} max={totalFreshness || 100}></progress>
            </div>
          </div>
        </div>

        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="card-title text-base">Activity</h3>
            <p className="text-sm text-base-content/60">This month</p>
            <div className="grid grid-cols-3 gap-4 my-4">
              <div className="text-center">
                <TrendingUp className="text-primary mx-auto mb-1" size={24} />
                <div className="text-2xl font-semibold">{insights?.velocity?.commits ?? 0}</div>
                <div className="text-xs text-base-content/60">commits</div>
              </div>
              <div className="text-center">
                <FileText className="text-success mx-auto mb-1" size={24} />
                <div className="text-2xl font-semibold">{insights?.velocity?.documents_modified ?? 0}</div>
                <div className="text-xs text-base-content/60">docs modified</div>
              </div>
              <div className="text-center">
                <div className="flex flex-col items-center gap-1 mt-2">
                  <span className="text-success text-sm font-medium">+{insights?.velocity?.lines_added ?? 0}</span>
                  <span className="text-error text-sm font-medium">-{insights?.velocity?.lines_removed ?? 0}</span>
                </div>
                <div className="text-xs text-base-content/60">lines</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Critical Issues Section */}
      {issueCount > 0 && (
        <div className="card bg-base-200 border border-warning/30">
          <div className="card-body">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="card-title text-lg">{issueCount} Issues to Address</h3>
                <p className="text-sm text-base-content/60">Critical items affecting project health</p>
              </div>
              <Link to="/quality" className="btn btn-ghost btn-sm gap-1">
                View All <ArrowRight size={14} />
              </Link>
            </div>
            <div className="space-y-3">
              {insights?.health?.issues?.slice(0, 5).map((issue, idx) => (
                <div key={idx} className="flex items-start gap-3 p-3 rounded-lg bg-base-300">
                  <div className={`badge ${issue.severity === 'critical' ? 'badge-error' : 'badge-warning'} badge-sm`}>
                    {issue.category}
                  </div>
                  <span className="flex-1 text-sm">{issue.message}</span>
                  <span className="text-sm text-base-content/50 truncate max-w-[150px]">{issue.document}</span>
                </div>
              ))}
              {issueCount > 5 && (
                <p className="text-sm text-base-content/60 text-center">...and {issueCount - 5} more</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Recommendations */}
      {qualitySummary?.recommendations && qualitySummary.recommendations.length > 0 && (
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="card-title text-lg">Recommendations</h3>
            <p className="text-sm text-base-content/60 mb-4">Suggested improvements</p>
            <div className="space-y-2">
              {qualitySummary.recommendations.slice(0, 5).map((rec, idx) => (
                <div key={idx} className="flex items-center gap-3 p-3 rounded-lg bg-base-300">
                  <Sparkles size={14} className="text-primary flex-shrink-0" />
                  <span className="text-sm">{rec}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
