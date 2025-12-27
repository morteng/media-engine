import { useState } from 'react';
import { AINoteCard, type AINote, type NoteType } from './AINoteCard';
import { StickyNote, Filter } from 'lucide-react';

interface AINoteListProps {
  notes: AINote[];
  compact?: boolean;
  maxItems?: number;
  showFilter?: boolean;
  showResolved?: boolean;
  onResolve?: (noteId: string, resolution: string) => void;
  onClick?: (noteId: string) => void;
}

export function AINoteList({
  notes,
  compact = false,
  maxItems,
  showFilter = true,
  showResolved = false,
  onResolve,
  onClick,
}: AINoteListProps) {
  const [filter, setFilter] = useState<NoteType | 'all'>('all');
  const [showResolvedNotes, setShowResolvedNotes] = useState(showResolved);

  // Filter notes
  let filteredNotes = notes;
  if (!showResolvedNotes) {
    filteredNotes = filteredNotes.filter((n) => !n.resolved);
  }
  if (filter !== 'all') {
    filteredNotes = filteredNotes.filter((n) => n.type === filter);
  }

  const displayNotes = maxItems ? filteredNotes.slice(0, maxItems) : filteredNotes;
  const hasMore = maxItems && filteredNotes.length > maxItems;

  // Count by type
  const typeCounts = notes.reduce((acc, note) => {
    if (!showResolvedNotes && note.resolved) return acc;
    acc[note.type] = (acc[note.type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  if (notes.length === 0) {
    return (
      <div className="text-center py-8">
        <StickyNote size={32} className="mx-auto text-base-content/30 mb-3" />
        <p className="text-base-content/60">No AI notes</p>
        <p className="text-sm text-base-content/40 mt-1">
          Notes appear when Claude has questions or suggestions
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filter bar */}
      {showFilter && (
        <div className="flex flex-wrap items-center gap-2">
          <Filter size={14} className="text-base-content/50" />
          <button
            className={`btn btn-xs ${filter === 'all' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setFilter('all')}
          >
            All ({filteredNotes.length})
          </button>
          {Object.entries(typeCounts).map(([type, count]) => (
            <button
              key={type}
              className={`btn btn-xs ${filter === type ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => setFilter(type as NoteType)}
            >
              {type.replace('_', ' ')} ({count})
            </button>
          ))}
          <div className="flex-1" />
          <label className="label cursor-pointer gap-2">
            <input
              type="checkbox"
              className="checkbox checkbox-xs"
              checked={showResolvedNotes}
              onChange={(e) => setShowResolvedNotes(e.target.checked)}
            />
            <span className="label-text text-xs">Show resolved</span>
          </label>
        </div>
      )}

      {/* Notes list */}
      {displayNotes.length === 0 ? (
        <div className="text-center py-6 text-base-content/60 text-sm">
          No {filter !== 'all' ? filter.replace('_', ' ') + ' ' : ''}notes
          {!showResolvedNotes && ' (excluding resolved)'}
        </div>
      ) : compact ? (
        <div className="space-y-2">
          {displayNotes.map((note) => (
            <AINoteCard
              key={note.id}
              note={note}
              compact
              onResolve={onResolve}
              onClick={onClick}
            />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {displayNotes.map((note) => (
            <AINoteCard
              key={note.id}
              note={note}
              onResolve={onResolve}
              onClick={onClick}
            />
          ))}
        </div>
      )}

      {hasMore && (
        <div className="text-center">
          <button className="btn btn-ghost btn-sm">
            View all {filteredNotes.length} notes
          </button>
        </div>
      )}
    </div>
  );
}
