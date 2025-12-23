import * as React from 'react';
import clsx from 'clsx';

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'accent' | 'outline';
  size?: 'sm' | 'md' | 'lg';
}

const variantClasses: Record<string, string> = {
  default: 'badge-ghost',
  success: 'badge-success',
  warning: 'badge-warning',
  error: 'badge-error',
  info: 'badge-info',
  accent: 'badge-primary',
  outline: 'badge-outline',
};

const sizeClasses: Record<string, string> = {
  sm: 'badge-xs',
  md: 'badge-sm',
  lg: 'badge-md',
};

function Badge({ className, variant = 'default', size = 'md', ...props }: BadgeProps) {
  return (
    <div
      className={clsx(
        'badge gap-1',
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      {...props}
    />
  );
}

export { Badge };
