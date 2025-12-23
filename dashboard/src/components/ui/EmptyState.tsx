import type { ReactNode } from 'react';
import { FileQuestion, Search, FolderOpen, Inbox } from 'lucide-react';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  variant?: 'default' | 'compact' | 'centered';
  className?: string;
}

const variantStyles = {
  default: 'py-12',
  compact: 'py-6',
  centered: 'py-16 min-h-[400px]',
};

export function EmptyState({
  icon,
  title,
  description,
  action,
  variant = 'default',
  className = '',
}: EmptyStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center text-center ${variantStyles[variant]} ${className}`}>
      <div className="text-base-content/30 mb-4">
        {icon || <Inbox size={48} strokeWidth={1.5} />}
      </div>
      <h3 className="text-lg font-semibold text-base-content">{title}</h3>
      {description && <p className="mt-2 text-sm text-base-content/60 max-w-sm">{description}</p>}
      {action && (
        <button
          className="btn btn-secondary btn-sm mt-4"
          onClick={action.onClick}
        >
          {action.label}
        </button>
      )}
    </div>
  );
}

// Pre-built empty states
export function NoResultsState({ query }: { query?: string }) {
  return (
    <EmptyState
      icon={<Search size={48} strokeWidth={1.5} />}
      title="No results found"
      description={query ? `No matches for "${query}"` : 'Try adjusting your search or filters'}
    />
  );
}

export function NoDocumentsState({ onAdd }: { onAdd?: () => void }) {
  return (
    <EmptyState
      icon={<FileQuestion size={48} strokeWidth={1.5} />}
      title="No documents yet"
      description="Get started by creating your first document"
      action={onAdd ? { label: 'Create Document', onClick: onAdd } : undefined}
    />
  );
}

export function NoFilesState() {
  return (
    <EmptyState
      icon={<FolderOpen size={48} strokeWidth={1.5} />}
      title="No files found"
      description="This folder is empty"
    />
  );
}
