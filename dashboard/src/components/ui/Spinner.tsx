import clsx from 'clsx';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function Spinner({ size = 'md', className }: SpinnerProps) {
  return (
    <div className={clsx('spinner', `spinner-${size}`, className)} />
  );
}

export function LoadingState({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="loading-state">
      <Spinner size="lg" />
      <p>{message}</p>
    </div>
  );
}
