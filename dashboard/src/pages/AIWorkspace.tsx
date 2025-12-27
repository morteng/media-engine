import { Routes, Route, NavLink } from 'react-router-dom';
import { useApi } from '@/hooks/useApi';
import {
  AIContextPanel,
  AISessionList,
  AINoteList,
  AITaskQueue,
  AIResearchCard,
} from '@/components/ai';
import {
  Sparkles,
  History,
  StickyNote,
  ListTodo,
  BookOpen,
  Brain,
} from 'lucide-react';
import type {
  AIContextResponse,
  AISessionsResponse,
  AINotesResponse,
  AITaskQueueResponse,
  AIResearchResponse,
  AIDecisionsResponse,
} from '@/api/types';
import clsx from 'clsx';

// Tab configuration
const tabs = [
  { path: '', icon: Sparkles, label: 'Overview' },
  { path: 'sessions', icon: History, label: 'Sessions' },
  { path: 'notes', icon: StickyNote, label: 'Notes' },
  { path: 'queue', icon: ListTodo, label: 'Queue' },
  { path: 'research', icon: BookOpen, label: 'Research' },
  { path: 'decisions', icon: Brain, label: 'Decisions' },
];

function AIOverview() {
  const { data: contextData, isLoading, refetch } = useApi<AIContextResponse>('/api/ai/context');
  const { data: sessionsData } = useApi<AISessionsResponse>('/api/ai/sessions');
  const { data: notesData } = useApi<AINotesResponse>('/api/ai/notes');
  const { data: tasksData } = useApi<AITaskQueueResponse>('/api/ai/queue');
  const { data: researchData } = useApi<AIResearchResponse>('/api/ai/research');

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <span className="loading loading-spinner loading-lg text-primary" />
      </div>
    );
  }

  const context = contextData?.context;

  return (
    <div className="space-y-6">
      {/* Context panel */}
      {context && (
        <AIContextPanel
          context={context}
          onRefresh={refetch}
        />
      )}

      {/* Quick summaries */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active sessions */}
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="font-semibold flex items-center gap-2 mb-4">
              <History size={18} className="text-primary" />
              Recent Sessions
            </h3>
            <AISessionList
              sessions={sessionsData?.sessions ?? []}
              compact
              maxItems={3}
            />
          </div>
        </div>

        {/* Pending notes */}
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="font-semibold flex items-center gap-2 mb-4">
              <StickyNote size={18} className="text-warning" />
              Notes Needing Attention
            </h3>
            <AINoteList
              notes={notesData?.notes?.filter((n) => !n.resolved && n.type === 'human_review') ?? []}
              compact
              maxItems={3}
              showFilter={false}
            />
          </div>
        </div>

        {/* Task queue */}
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="font-semibold flex items-center gap-2 mb-4">
              <ListTodo size={18} className="text-info" />
              Task Queue
            </h3>
            <AITaskQueue
              tasks={tasksData?.tasks ?? []}
              maxItems={3}
            />
          </div>
        </div>

        {/* Stale research */}
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="font-semibold flex items-center gap-2 mb-4">
              <BookOpen size={18} className="text-success" />
              Research Store
            </h3>
            {researchData?.entries && researchData.entries.length > 0 ? (
              <div className="space-y-2">
                {researchData.entries.slice(0, 3).map((entry) => (
                  <AIResearchCard key={entry.key} entry={entry} compact />
                ))}
              </div>
            ) : (
              <p className="text-center py-6 text-base-content/60 text-sm">
                No research entries yet
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function AISessions() {
  const { data, isLoading } = useApi<AISessionsResponse>('/api/ai/sessions');

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <span className="loading loading-spinner loading-lg text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">AI Sessions</h2>
        <div className="text-sm text-base-content/60">
          {data?.active_count ?? 0} active • {data?.total_count ?? 0} total
        </div>
      </div>
      <AISessionList sessions={data?.sessions ?? []} />
    </div>
  );
}

function AINotes() {
  const { data, isLoading } = useApi<AINotesResponse>('/api/ai/notes');

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <span className="loading loading-spinner loading-lg text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">AI Notes</h2>
        <div className="text-sm text-base-content/60">
          {data?.unresolved_count ?? 0} unresolved • {data?.total_count ?? 0} total
        </div>
      </div>
      <AINoteList notes={data?.notes ?? []} />
    </div>
  );
}

function AIQueue() {
  const { data, isLoading } = useApi<AITaskQueueResponse>('/api/ai/queue');

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <span className="loading loading-spinner loading-lg text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">Task Queue</h2>
        <div className="text-sm text-base-content/60">
          {data?.pending_count ?? 0} pending • {data?.in_progress_count ?? 0} in progress
        </div>
      </div>
      <AITaskQueue tasks={data?.tasks ?? []} />
    </div>
  );
}

function AIResearch() {
  const { data, isLoading } = useApi<AIResearchResponse>('/api/ai/research');

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <span className="loading loading-spinner loading-lg text-primary" />
      </div>
    );
  }

  const entries = data?.entries ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">Research Store</h2>
        <div className="text-sm text-base-content/60">
          {data?.stale_count ?? 0} stale • {data?.total_count ?? 0} total
        </div>
      </div>

      {entries.length === 0 ? (
        <div className="text-center py-12">
          <BookOpen size={48} className="mx-auto text-base-content/30 mb-4" />
          <p className="text-base-content/60">No research entries</p>
          <p className="text-sm text-base-content/40 mt-1">
            Research is stored when Claude learns about your project
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {entries.map((entry) => (
            <AIResearchCard key={entry.key} entry={entry} />
          ))}
        </div>
      )}
    </div>
  );
}

function AIDecisions() {
  const { data, isLoading } = useApi<AIDecisionsResponse>('/api/ai/decisions');

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <span className="loading loading-spinner loading-lg text-primary" />
      </div>
    );
  }

  const decisions = data?.decisions ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">Decisions</h2>
        <div className="text-sm text-base-content/60">
          {data?.total_count ?? 0} total
        </div>
      </div>

      {decisions.length === 0 ? (
        <div className="text-center py-12">
          <Brain size={48} className="mx-auto text-base-content/30 mb-4" />
          <p className="text-base-content/60">No decisions recorded</p>
          <p className="text-sm text-base-content/40 mt-1">
            Decisions are logged when Claude makes significant choices
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {decisions.map((decision) => (
            <div key={decision.id} className="card bg-base-200">
              <div className="card-body p-4">
                <div className="flex items-start gap-3">
                  <Brain size={18} className="text-primary flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="font-medium">{decision.decision}</p>
                    {decision.rationale && (
                      <p className="text-sm text-base-content/70 mt-1">
                        {decision.rationale}
                      </p>
                    )}
                    <div className="flex flex-wrap gap-2 mt-2 text-xs text-base-content/50">
                      {decision.document_path && (
                        <span>Document: {decision.document_path.split('/').pop()}</span>
                      )}
                      <span>
                        {new Date(decision.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function AIWorkspace() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Sparkles className="w-6 h-6 text-primary" />
          AI Workspace
        </h1>
        <p className="text-base-content/60 mt-1">
          Sessions, notes, research, and task management for AI collaboration
        </p>
      </div>

      {/* Tab navigation */}
      <div className="tabs tabs-boxed bg-base-200 p-1">
        {tabs.map((tab) => (
          <NavLink
            key={tab.path}
            to={tab.path || '.'}
            end={tab.path === ''}
            className={({ isActive }) =>
              clsx('tab gap-2', { 'tab-active': isActive })
            }
          >
            <tab.icon size={16} />
            {tab.label}
          </NavLink>
        ))}
      </div>

      {/* Tab content */}
      <Routes>
        <Route index element={<AIOverview />} />
        <Route path="sessions" element={<AISessions />} />
        <Route path="notes" element={<AINotes />} />
        <Route path="queue" element={<AIQueue />} />
        <Route path="research" element={<AIResearch />} />
        <Route path="decisions" element={<AIDecisions />} />
      </Routes>
    </div>
  );
}
