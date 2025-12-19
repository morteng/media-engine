import clsx from 'clsx';

interface ProgressBarProps {
  value: number;
  max?: number;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'accent';
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export function ProgressBar({
  value,
  max = 100,
  variant = 'default',
  size = 'md',
  showLabel = false
}: ProgressBarProps) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));

  return (
    <div className={clsx('progress-bar', `progress-${size}`)}>
      <div className="progress-track">
        <div
          className={clsx('progress-fill', `progress-${variant}`)}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <span className="progress-label">{Math.round(percentage)}%</span>
      )}
    </div>
  );
}
