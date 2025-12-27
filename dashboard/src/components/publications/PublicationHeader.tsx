import { Link } from 'react-router-dom';
import { ChevronLeft, Book, Presentation, FileText, Video, Package, Globe } from 'lucide-react';
import { StatusBadge, ValidationBadge, SyncBadge } from './PublicationStatus';
import type { PublicationDetail } from '@/api/types';

// Icon map for publication types
const typeIcons: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
  book: Book,
  deck: Presentation,
  video: Video,
  report: FileText,
  website: Globe,
  package: Package,
};

interface PublicationHeaderProps {
  publication: PublicationDetail;
  backLink?: string;
  actions?: React.ReactNode;
}

export function PublicationHeader({
  publication,
  backLink = '/publications',
  actions,
}: PublicationHeaderProps) {
  const TypeIcon = typeIcons[publication.status] || Book;

  return (
    <div className="bg-base-200 rounded-lg p-6">
      {/* Breadcrumb */}
      <Link
        to={backLink}
        className="inline-flex items-center gap-1 text-sm text-base-content/60 hover:text-primary mb-4"
      >
        <ChevronLeft size={16} />
        Back to Publications
      </Link>

      {/* Header content */}
      <div className="flex flex-col lg:flex-row lg:items-start gap-6">
        {/* Icon and title */}
        <div className="flex items-start gap-4 flex-1">
          <div className="p-3 rounded-xl bg-primary/10">
            <TypeIcon size={32} className="text-primary" />
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold">{publication.title}</h1>
            {publication.subtitle && (
              <p className="text-lg text-base-content/70 mt-1">{publication.subtitle}</p>
            )}
            <p className="text-sm text-base-content/60 mt-2">{publication.key}</p>

            {/* Status badges */}
            <div className="flex flex-wrap gap-2 mt-4">
              <StatusBadge status={publication.status} size="md" />
              <ValidationBadge
                isValid={publication.validation.is_valid}
                issueCount={publication.validation.issues.length}
                size="md"
              />
              {publication.is_translation && (
                <SyncBadge
                  isCurrent={publication.validation.translation_current}
                  sourceChanged={publication.validation.source_changed}
                  size="md"
                />
              )}
              <span className="badge badge-md gap-1">
                <Globe size={14} />
                {publication.language.toUpperCase()}
              </span>
            </div>
          </div>
        </div>

        {/* Actions */}
        {actions && <div className="flex gap-2">{actions}</div>}
      </div>

      {/* Description */}
      {publication.description && (
        <p className="mt-6 text-base-content/80">{publication.description}</p>
      )}

      {/* Metadata */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-base-300">
        <div>
          <p className="text-xs text-base-content/60 uppercase tracking-wide">Version</p>
          <p className="font-medium">{publication.version}</p>
        </div>
        <div>
          <p className="text-xs text-base-content/60 uppercase tracking-wide">Chapters</p>
          <p className="font-medium">{publication.chapter_count}</p>
        </div>
        <div>
          <p className="text-xs text-base-content/60 uppercase tracking-wide">Formats</p>
          <div className="flex gap-1 mt-1">
            {publication.output_formats.map((fmt) => (
              <span key={fmt} className="badge badge-sm badge-ghost uppercase">
                {fmt}
              </span>
            ))}
          </div>
        </div>
        <div>
          <p className="text-xs text-base-content/60 uppercase tracking-wide">
            {publication.is_translation ? 'Source' : 'Type'}
          </p>
          <p className="font-medium capitalize">
            {publication.is_translation ? publication.source_document : publication.status}
          </p>
        </div>
      </div>
    </div>
  );
}
