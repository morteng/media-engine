import { Link } from 'react-router-dom';
import {
  Book,
  ArrowRight,
  CheckCircle,
  AlertCircle,
  Clock,
} from 'lucide-react';
import type { PublicationStatusItem } from '@/api/types';
import { getPublicationTypeIcon } from '@/utils/iconMappings';

interface RecentPublicationsProps {
  publications: PublicationStatusItem[];
  maxItems?: number;
}

/**
 * Compact recent publications list for the dashboard home page.
 * Shows essential info only: icon, title, language, status indicator.
 */
export function RecentPublications({
  publications,
  maxItems = 4,
}: RecentPublicationsProps) {
  if (!publications || publications.length === 0) {
    return (
      <div className="text-center py-8 text-base-content/60">
        <Book size={32} className="mx-auto mb-2 opacity-50" />
        <p className="text-sm">No publications yet</p>
        <Link to="/publications" className="btn btn-ghost btn-sm mt-2">
          Create Publication
        </Link>
      </div>
    );
  }

  const displayPubs = publications.slice(0, maxItems);

  return (
    <div className="space-y-2">
      {displayPubs.map((pub) => {
        const TypeIcon = getPublicationTypeIcon(pub.pub_type);
        const statusIcon = pub.is_valid ? (
          <CheckCircle size={14} className="text-success" />
        ) : pub.issues_count > 0 ? (
          <AlertCircle size={14} className="text-error" />
        ) : (
          <Clock size={14} className="text-warning" />
        );

        return (
          <Link
            key={pub.key}
            to={`/publications/${pub.key}`}
            className="flex items-center gap-3 p-3 rounded-lg bg-base-300/50 hover:bg-base-300 transition-colors group"
          >
            <div className="p-2 rounded-md bg-primary/10 flex-shrink-0">
              <TypeIcon size={16} className="text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="font-medium text-sm truncate">{pub.title}</h4>
              <span className="text-xs text-base-content/50">
                {pub.language.toUpperCase()} • {pub.item_count} {pub.item_label}
              </span>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              {statusIcon}
              <ArrowRight
                size={14}
                className="text-base-content/30 group-hover:text-base-content/60 transition-colors"
              />
            </div>
          </Link>
        );
      })}

      {publications.length > maxItems && (
        <Link
          to="/publications"
          className="flex items-center justify-center gap-1 text-sm text-primary hover:underline py-2"
        >
          View all {publications.length} publications
          <ArrowRight size={14} />
        </Link>
      )}
    </div>
  );
}
