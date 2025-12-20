import type { ReactNode } from 'react';
import { FileQuestion, Search, FolderOpen, Inbox } from 'lucide-react';
import { Button } from './Button';
import './EmptyState.css';

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

export function EmptyState({
  icon,
  title,
  description,
  action,
  variant = 'default',
  className = '',
}: EmptyStateProps) {
  return (
    <div className={`empty-state empty-state-${variant} ${className}`}>
      <div className="empty-state-icon">
        {icon || <Inbox size={48} strokeWidth={1.5} />}
      </div>
      <h3 className="empty-state-title">{title}</h3>
      {description && <p className="empty-state-description">{description}</p>}
      {action && (
        <Button variant="secondary" onClick={action.onClick}>
          {action.label}
        </Button>
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
