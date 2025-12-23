import * as React from 'react';
import clsx from 'clsx';

export interface ProgressBarProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number;
  max?: number;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'accent' | 'info';
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

const variantClasses: Record<string, string> = {
  default: 'progress-primary',
  success: 'progress-success',
  warning: 'progress-warning',
  error: 'progress-error',
  accent: 'progress-accent',
  info: 'progress-info',
};

const ProgressBar = React.forwardRef<HTMLDivElement, ProgressBarProps>(
  ({ className, variant = 'default', size = 'md', value, max = 100, showLabel = false, ...props }, ref) => {
    const percentage = Math.min(100, Math.max(0, (value / max) * 100));

    return (
      <div className={clsx('flex items-center gap-3', className)} ref={ref} {...props}>
        <progress
          className={clsx(
            'progress w-full',
            variantClasses[variant],
            {
              'h-1': size === 'sm',
              'h-2': size === 'md',
              'h-3': size === 'lg',
            }
          )}
          value={value}
          max={max}
        />
        {showLabel && (
          <span className="text-sm font-medium text-base-content/60 tabular-nums min-w-[3ch]">
            {Math.round(percentage)}%
          </span>
        )}
      </div>
    );
  }
);
ProgressBar.displayName = 'ProgressBar';

export { ProgressBar };
