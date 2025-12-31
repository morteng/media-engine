import type { ReactNode } from 'react';
import {
  FileQuestion,
  Search,
  FolderOpen,
  Inbox,
  ListTodo,
  MessageSquare,
  Package,
  History,
  StickyNote,
  BookOpen,
  Brain,
  Film,
  FileVideo,
  FileJson,
  Image,
  Layers,
} from 'lucide-react';

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

export function NoTasksState({ onAdd }: { onAdd?: () => void }) {
  return (
    <EmptyState
      icon={<ListTodo size={48} strokeWidth={1.5} />}
      title="No tasks in queue"
      description="Tasks are added when Claude identifies work to be done"
      action={onAdd ? { label: 'Add Task', onClick: onAdd } : undefined}
    />
  );
}

export function NoCommentsState() {
  return (
    <EmptyState
      icon={<MessageSquare size={48} strokeWidth={1.5} />}
      title="No comments yet"
      description="Add comments to provide feedback on this content"
      variant="compact"
    />
  );
}

export function NoPublicationsState({ onAdd }: { onAdd?: () => void }) {
  return (
    <EmptyState
      icon={<Package size={48} strokeWidth={1.5} />}
      title="No publications found"
      description="Create publications in your project.yaml to get started"
      action={onAdd ? { label: 'Create Publication', onClick: onAdd } : undefined}
    />
  );
}

export function NoDeliverablesState() {
  return (
    <EmptyState
      icon={<Package size={48} strokeWidth={1.5} />}
      title="No deliverables yet"
      description="Build a publication to generate outputs"
    />
  );
}

export function NoSessionsState() {
  return (
    <EmptyState
      icon={<History size={48} strokeWidth={1.5} />}
      title="No AI sessions"
      description="Sessions appear when Claude starts working on tasks"
    />
  );
}

export function NoNotesState() {
  return (
    <EmptyState
      icon={<StickyNote size={48} strokeWidth={1.5} />}
      title="No AI notes"
      description="Notes appear when Claude has questions or suggestions"
    />
  );
}

export function NoResearchState() {
  return (
    <EmptyState
      icon={<BookOpen size={48} strokeWidth={1.5} />}
      title="No research entries"
      description="Research is stored when Claude learns about your project"
    />
  );
}

export function NoDecisionsState() {
  return (
    <EmptyState
      icon={<Brain size={48} strokeWidth={1.5} />}
      title="No decisions recorded"
      description="Decisions are logged when Claude makes significant choices"
    />
  );
}

export function NoMediaState() {
  return (
    <EmptyState
      icon={<Image size={48} strokeWidth={1.5} />}
      title="No media files found"
      description="Media files will appear here after building videos"
    />
  );
}

export function NoScriptsState({ onAdd }: { onAdd?: () => void }) {
  return (
    <EmptyState
      icon={<FileVideo size={48} strokeWidth={1.5} />}
      title="No scripts yet"
      description="Create a video script to get started"
      action={onAdd ? { label: 'Create Script', onClick: onAdd } : undefined}
      variant="compact"
    />
  );
}

export function NoPropsState() {
  return (
    <EmptyState
      icon={<FileJson size={48} strokeWidth={1.5} />}
      title="No props available"
      description="Generate voiceover for a script to create props.json"
    />
  );
}

export function NoScenesState() {
  return (
    <EmptyState
      icon={<Film size={48} strokeWidth={1.5} />}
      title="No scenes"
      description="Scenes will appear after props are generated"
      variant="compact"
    />
  );
}

export function NoComponentsState() {
  return (
    <EmptyState
      icon={<Layers size={48} strokeWidth={1.5} />}
      title="No components defined"
      description="Add components to this publication in project.yaml"
      variant="compact"
    />
  );
}
