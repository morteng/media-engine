import type { ReactNode, HTMLAttributes } from 'react';
import clsx from 'clsx';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  className?: string;
  variant?: 'default' | 'glow' | 'gradient';
}

export function Card({ children, className, variant = 'default', ...props }: CardProps) {
  return (
    <div className={clsx('card', `card-${variant}`, className)} {...props}>
      {children}
    </div>
  );
}

interface CardHeaderProps {
  title: string;
  subtitle?: ReactNode;
  action?: ReactNode;
}

export function CardHeader({ title, subtitle, action }: CardHeaderProps) {
  return (
    <div className="card-header">
      <div>
        <h3 className="card-title">{title}</h3>
        {subtitle && <div className="card-subtitle">{subtitle}</div>}
      </div>
      {action && <div className="card-action">{action}</div>}
    </div>
  );
}

export function CardContent({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={clsx('card-content', className)}>{children}</div>;
}
