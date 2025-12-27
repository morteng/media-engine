import { Link } from 'react-router-dom';
import { InfoTooltip } from './InfoTooltip';
import type { ReactNode } from 'react';

interface StatCardProps {
  label: string;
  value: string | number;
  icon?: ReactNode;
  trend?: {
    value: number;
    label: string;
  };
  variant?: 'default' | 'success' | 'warning' | 'error' | 'accent';
  tooltip?: {
    title: string;
    content: string;
  };
  href?: string;
}

const variantStyles: Record<string, { border: string; icon: string; accent: string }> = {
  default: {
    border: 'border-base-300',
    icon: 'text-base-content/60',
    accent: 'text-primary',
  },
  success: {
    border: 'border-success/30',
    icon: 'text-success',
    accent: 'text-success',
  },
  warning: {
    border: 'border-warning/30',
    icon: 'text-warning',
    accent: 'text-warning',
  },
  error: {
    border: 'border-error/30',
    icon: 'text-error',
    accent: 'text-error',
  },
  accent: {
    border: 'border-primary/30',
    icon: 'text-primary',
    accent: 'text-primary',
  },
};

export function StatCard({ label, value, icon, trend, variant = 'default', tooltip, href }: StatCardProps) {
  const styles = variantStyles[variant];

  const content = (
    <div className="card-body p-4">
      <div className="flex items-center gap-3 mb-2">
        {icon && <div className={`${styles.icon}`}>{icon}</div>}
        <span className="text-sm text-base-content/70 flex items-center gap-1.5">
          {label}
          {tooltip && <InfoTooltip title={tooltip.title} content={tooltip.content} />}
        </span>
      </div>
      <div className={`text-3xl font-semibold ${styles.accent}`}>{value}</div>
      {trend && (
        <div className={`flex items-center gap-2 text-sm mt-2 ${trend.value > 0 ? 'text-success' : trend.value < 0 ? 'text-error' : 'text-base-content/60'}`}>
          <span>{trend.value > 0 ? '+' : ''}{trend.value}%</span>
          <span className="text-base-content/50">{trend.label}</span>
        </div>
      )}
    </div>
  );

  const cardClasses = `card bg-base-200 border ${styles.border} ${href ? 'hover:bg-base-300 transition-colors cursor-pointer' : ''}`;

  if (href) {
    return (
      <Link to={href} className={cardClasses}>
        {content}
      </Link>
    );
  }

  return <div className={cardClasses}>{content}</div>;
}
