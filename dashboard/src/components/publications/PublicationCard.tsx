import { Link } from 'react-router-dom';
import {
  Book,
  FileText,
  Globe,
  Presentation,
  Table2,
  FileCheck,
  AlertCircle,
  Clock,
  CheckCircle,
  ChevronRight,
  Layers,
  Database,
} from 'lucide-react';
import type { PublicationStatusItem } from '@/api/types';

// Icon map for publication types
const typeIcons: Record<string, React.ComponentType<{ className?: string; size?: number }>> = {
  book: Book,
  deck: Presentation,
  spreadsheet: Table2,
  report: FileText,
};

// Item icon based on type
const itemIcons: Record<string, React.ComponentType<{ className?: string; size?: number }>> = {
  chapters: FileText,
  slides: Layers,
  sources: Database,
};

// Status colors
const statusColors: Record<string, string> = {
  draft: 'badge-warning',
  in_review: 'badge-info',
  approved: 'badge-primary',
  published: 'badge-success',
  archived: 'badge-ghost',
};

interface PublicationCardProps {
  publication: PublicationStatusItem;
  compact?: boolean;
  showActions?: boolean;
  onBuild?: (pubId: string) => void;
}

export function PublicationCard({
  publication: pub,
  compact = false,
  showActions = false,
  onBuild,
}: PublicationCardProps) {
  const TypeIcon = typeIcons[pub.pub_type] || Book;
  const ItemIcon = itemIcons[pub.item_label] || FileText;

  if (compact) {
    return (
      <Link
        to={`/publications/${pub.key}`}
        className="flex items-center gap-3 p-3 rounded-lg bg-base-200 hover:bg-base-300 transition-colors group"
      >
        <TypeIcon size={20} className="text-primary flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-sm truncate">{pub.title}</h4>
          <div className="flex items-center gap-2 text-xs text-base-content/60">
            <span>{pub.language.toUpperCase()}</span>
            <span>&bull;</span>
            <span>{pub.item_count} {pub.item_label}</span>
          </div>
        </div>
        <span className={`badge badge-xs ${statusColors[pub.status] || 'badge-ghost'}`}>
          {pub.status.replace('_', ' ')}
        </span>
        <ChevronRight size={16} className="text-base-content/40 group-hover:text-base-content" />
      </Link>
    );
  }

  return (
    <div className="card bg-base-200 shadow-sm hover:shadow-md transition-shadow">
      <div className="card-body p-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <TypeIcon size={24} className="text-primary" />
            </div>
            <div>
              <h3 className="font-semibold">{pub.title}</h3>
              <p className="text-xs text-base-content/60">{pub.key}</p>
            </div>
          </div>
          <span className={`badge ${statusColors[pub.status] || 'badge-ghost'}`}>
            {(pub.status || 'draft').replace('_', ' ')}
          </span>
        </div>

        {/* Badges */}
        <div className="flex flex-wrap gap-2 mt-3">
          <span className="badge badge-sm badge-ghost gap-1">
            <Globe size={12} />
            {(pub.language || 'en').toUpperCase()}
          </span>
          <span className="badge badge-sm badge-ghost gap-1">
            <ItemIcon size={12} />
            {pub.item_count ?? 0} {pub.item_label || 'items'}
          </span>

          {/* Validation badge */}
          {pub.is_valid ? (
            <span className="badge badge-sm badge-success gap-1">
              <CheckCircle size={12} />
              Valid
            </span>
          ) : (
            <span className="badge badge-sm badge-error gap-1">
              <AlertCircle size={12} />
              {pub.issues_count} issues
            </span>
          )}

          {/* Translation badge */}
          {pub.is_translation && (
            pub.translation_current ? (
              <span className="badge badge-sm badge-success gap-1">
                <FileCheck size={12} />
                Synced
              </span>
            ) : (
              <span className="badge badge-sm badge-warning gap-1">
                <Clock size={12} />
                Needs Update
              </span>
            )
          )}
        </div>

        {/* Missing chapters warning */}
        {pub.missing_chapters > 0 && (
          <div className="alert alert-warning py-2 px-3 mt-3">
            <AlertCircle size={14} />
            <span className="text-xs">{pub.missing_chapters} missing chapter(s)</span>
          </div>
        )}

        {/* Actions */}
        {showActions && (
          <div className="card-actions justify-end mt-4">
            <Link to={`/publications/${pub.key}`} className="btn btn-ghost btn-sm">
              Details
            </Link>
            <button
              className="btn btn-primary btn-sm"
              onClick={() => onBuild?.(pub.key)}
              disabled={!pub.is_valid}
            >
              Build
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
