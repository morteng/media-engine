import type { ReactNode } from 'react';
import { AlertCircle, RefreshCw, AlertTriangle, XCircle } from 'lucide-react';
import clsx from 'clsx';
import { Button } from './Button';

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
  suggestion?: string;
  variant?: 'inline' | 'card' | 'fullPage';
  severity?: 'error' | 'warning' | 'info';
  icon?: ReactNode;
  className?: string;
  retryLabel?: string;
}

const variantStyles = {
  inline: 'py-4',
  card: 'p-6 card bg-base-200 border border-base-300 rounded-lg',
  fullPage: 'py-16 min-h-[400px]',
};

const severityStyles = {
  error: {
    iconColor: 'text-error',
    bgColor: 'bg-error/5',
    borderColor: 'border-error/20',
  },
  warning: {
    iconColor: 'text-warning',
    bgColor: 'bg-warning/5',
    borderColor: 'border-warning/20',
  },
  info: {
    iconColor: 'text-info',
    bgColor: 'bg-info/5',
    borderColor: 'border-info/20',
  },
};

const severityIcons = {
  error: XCircle,
  warning: AlertTriangle,
  info: AlertCircle,
};

export function ErrorState({
  message,
  onRetry,
  suggestion,
  variant = 'inline',
  severity = 'error',
  icon,
  className = '',
  retryLabel = 'Try Again',
}: ErrorStateProps) {
  const styles = severityStyles[severity];
  const DefaultIcon = severityIcons[severity];

  const content = (
    <>
      <div className={clsx('mb-4', styles.iconColor)}>
        {icon || <DefaultIcon size={variant === 'fullPage' ? 48 : 32} strokeWidth={1.5} />}
      </div>
      <h3 className="text-lg font-semibold text-base-content">{message}</h3>
      {suggestion && (
        <p className="mt-2 text-sm text-base-content/60 max-w-md">{suggestion}</p>
      )}
      {onRetry && (
        <Button
          variant="secondary"
          size="sm"
          onClick={onRetry}
          className="mt-4 gap-2"
        >
          <RefreshCw size={14} />
          {retryLabel}
        </Button>
      )}
    </>
  );

  if (variant === 'card') {
    return (
      <div
        className={clsx(
          'flex flex-col items-center justify-center text-center',
          variantStyles[variant],
          styles.bgColor,
          styles.borderColor,
          className
        )}
      >
        {content}
      </div>
    );
  }

  return (
    <div
      className={clsx(
        'flex flex-col items-center justify-center text-center',
        variantStyles[variant],
        className
      )}
    >
      {content}
    </div>
  );
}

// Pre-built error states for common scenarios
interface NetworkErrorStateProps {
  onRetry?: () => void;
  className?: string;
}

export function NetworkErrorState({ onRetry, className }: NetworkErrorStateProps) {
  return (
    <ErrorState
      message="Connection Error"
      suggestion="Unable to connect to the server. Please check your internet connection and try again."
      onRetry={onRetry}
      variant="card"
      className={className}
    />
  );
}

interface LoadErrorStateProps {
  resource?: string;
  onRetry?: () => void;
  className?: string;
}

export function LoadErrorState({ resource = 'data', onRetry, className }: LoadErrorStateProps) {
  return (
    <ErrorState
      message={`Failed to load ${resource}`}
      suggestion="Something went wrong while loading. Please try again."
      onRetry={onRetry}
      variant="inline"
      className={className}
    />
  );
}

interface PageErrorStateProps {
  message?: string;
  onRetry?: () => void;
  onGoBack?: () => void;
  className?: string;
}

export function PageErrorState({
  message = 'Something went wrong',
  onRetry,
  onGoBack,
  className,
}: PageErrorStateProps) {
  return (
    <div
      className={clsx(
        'flex flex-col items-center justify-center text-center py-16 min-h-[400px]',
        className
      )}
    >
      <div className="text-error mb-4">
        <XCircle size={48} strokeWidth={1.5} />
      </div>
      <h3 className="text-lg font-semibold text-base-content">{message}</h3>
      <p className="mt-2 text-sm text-base-content/60 max-w-md">
        An unexpected error occurred. Please try again or go back to the previous page.
      </p>
      <div className="flex gap-3 mt-4">
        {onGoBack && (
          <Button variant="ghost" size="sm" onClick={onGoBack}>
            Go Back
          </Button>
        )}
        {onRetry && (
          <Button variant="secondary" size="sm" onClick={onRetry} className="gap-2">
            <RefreshCw size={14} />
            Try Again
          </Button>
        )}
      </div>
    </div>
  );
}
