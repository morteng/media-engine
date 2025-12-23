import { Card, CardContent } from './Card';
import { InfoTooltip } from './InfoTooltip';
import type { ReactNode } from 'react';
import clsx from 'clsx';

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
}

export function StatCard({ label, value, icon, trend, variant = 'default', tooltip }: StatCardProps) {
  return (
    <Card className={clsx('stat-card', `stat-card-${variant}`)}>
      <CardContent>
        <div className="stat-card-header">
          {icon && <div className="stat-card-icon">{icon}</div>}
          <span className="stat-card-label">
            {label}
            {tooltip && <InfoTooltip title={tooltip.title} content={tooltip.content} />}
          </span>
        </div>
        <div className="stat-card-value">{value}</div>
        {trend && (
          <div className={clsx('stat-card-trend', { positive: trend.value > 0, negative: trend.value < 0 })}>
            <span>{trend.value > 0 ? '+' : ''}{trend.value}%</span>
            <span className="trend-label">{trend.label}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
