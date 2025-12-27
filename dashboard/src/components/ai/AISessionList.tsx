import { AISessionCard, type AISession } from './AISessionCard';
import { History } from 'lucide-react';

interface AISessionListProps {
  sessions: AISession[];
  compact?: boolean;
  maxItems?: number;
  showEmpty?: boolean;
  onResume?: (sessionId: string) => void;
  onClick?: (sessionId: string) => void;
}

export function AISessionList({
  sessions,
  compact = false,
  maxItems,
  showEmpty = true,
  onResume,
  onClick,
}: AISessionListProps) {
  const displaySessions = maxItems ? sessions.slice(0, maxItems) : sessions;
  const hasMore = maxItems && sessions.length > maxItems;

  if (sessions.length === 0 && showEmpty) {
    return (
      <div className="text-center py-8">
        <History size={32} className="mx-auto text-base-content/30 mb-3" />
        <p className="text-base-content/60">No AI sessions</p>
        <p className="text-sm text-base-content/40 mt-1">
          Sessions appear when Claude starts working on tasks
        </p>
      </div>
    );
  }

  if (compact) {
    return (
      <div className="space-y-2">
        {displaySessions.map((session) => (
          <AISessionCard
            key={session.id}
            session={session}
            compact
            onResume={onResume}
            onClick={onClick}
          />
        ))}
        {hasMore && (
          <button className="btn btn-ghost btn-sm w-full">
            View all {sessions.length} sessions
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {displaySessions.map((session) => (
        <AISessionCard
          key={session.id}
          session={session}
          onResume={onResume}
          onClick={onClick}
        />
      ))}
      {hasMore && (
        <div className="col-span-full text-center">
          <button className="btn btn-ghost btn-sm">
            View all {sessions.length} sessions
          </button>
        </div>
      )}
    </div>
  );
}
