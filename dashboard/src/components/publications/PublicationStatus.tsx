import { CheckCircle, AlertCircle, Clock, AlertTriangle, Archive } from 'lucide-react';
import clsx from 'clsx';

type PublicationStatusType = 'draft' | 'in_review' | 'approved' | 'published' | 'archived';

interface StatusBadgeProps {
  status: PublicationStatusType | string;
  size?: 'sm' | 'md' | 'lg';
}

export function StatusBadge({ status, size = 'sm' }: StatusBadgeProps) {
  const colors: Record<string, string> = {
    draft: 'badge-warning',
    in_review: 'badge-info',
    approved: 'badge-primary',
    published: 'badge-success',
    archived: 'badge-ghost',
  };

  const icons: Record<string, React.ComponentType<{ size?: number }>> = {
    draft: Clock,
    in_review: AlertTriangle,
    approved: CheckCircle,
    published: CheckCircle,
    archived: Archive,
  };

  const Icon = icons[status];
  const iconSize = size === 'sm' ? 12 : size === 'md' ? 14 : 16;

  return (
    <span className={clsx('badge gap-1', colors[status] || 'badge-ghost', {
      'badge-sm': size === 'sm',
      'badge-md': size === 'md',
      'badge-lg': size === 'lg',
    })}>
      {Icon && <Icon size={iconSize} />}
      {status.replace('_', ' ')}
    </span>
  );
}

interface ValidationBadgeProps {
  isValid: boolean;
  issueCount?: number;
  size?: 'sm' | 'md';
}

export function ValidationBadge({ isValid, issueCount = 0, size = 'sm' }: ValidationBadgeProps) {
  const iconSize = size === 'sm' ? 12 : 14;

  if (isValid) {
    return (
      <span className={clsx('badge badge-success gap-1', { 'badge-sm': size === 'sm' })}>
        <CheckCircle size={iconSize} />
        Valid
      </span>
    );
  }

  return (
    <span className={clsx('badge badge-error gap-1', { 'badge-sm': size === 'sm' })}>
      <AlertCircle size={iconSize} />
      {issueCount} issue{issueCount !== 1 ? 's' : ''}
    </span>
  );
}

interface SyncBadgeProps {
  isCurrent: boolean;
  sourceChanged?: boolean;
  size?: 'sm' | 'md';
}

export function SyncBadge({ isCurrent, sourceChanged = false, size = 'sm' }: SyncBadgeProps) {
  const iconSize = size === 'sm' ? 12 : 14;

  if (isCurrent) {
    return (
      <span className={clsx('badge badge-success gap-1', { 'badge-sm': size === 'sm' })}>
        <CheckCircle size={iconSize} />
        Synced
      </span>
    );
  }

  if (sourceChanged) {
    return (
      <span className={clsx('badge badge-warning gap-1', { 'badge-sm': size === 'sm' })}>
        <Clock size={iconSize} />
        Needs Update
      </span>
    );
  }

  return (
    <span className={clsx('badge badge-error gap-1', { 'badge-sm': size === 'sm' })}>
      <AlertCircle size={iconSize} />
      Missing
    </span>
  );
}

interface PublicationStatusProps {
  status: PublicationStatusType | string;
  isValid: boolean;
  issueCount?: number;
  isTranslation?: boolean;
  isCurrent?: boolean;
  sourceChanged?: boolean;
  showAll?: boolean;
}

export function PublicationStatus({
  status,
  isValid,
  issueCount = 0,
  isTranslation = false,
  isCurrent = true,
  sourceChanged = false,
  showAll = true,
}: PublicationStatusProps) {
  return (
    <div className="flex flex-wrap gap-2">
      <StatusBadge status={status} />
      {showAll && <ValidationBadge isValid={isValid} issueCount={issueCount} />}
      {showAll && isTranslation && (
        <SyncBadge isCurrent={isCurrent} sourceChanged={sourceChanged} />
      )}
    </div>
  );
}
