import clsx from 'clsx';
import type { ReactNode } from 'react';

interface BadgeProps {
  children: ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'accent';
  size?: 'sm' | 'md' | 'lg';
}

export function Badge({ children, variant = 'default', size = 'md' }: BadgeProps) {
  return (
    <span className={clsx('badge', `badge-${variant}`, `badge-${size}`)}>
      {children}
    </span>
  );
}
