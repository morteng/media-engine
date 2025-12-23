import * as React from 'react';
import clsx from 'clsx';

export interface SpinnerProps extends React.HTMLAttributes<HTMLSpanElement> {
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

const sizeClasses: Record<string, string> = {
  sm: 'loading-sm',
  md: 'loading-md',
  lg: 'loading-lg',
  xl: 'loading-lg', // DaisyUI doesn't have xl, use lg
};

const Spinner = React.forwardRef<HTMLSpanElement, SpinnerProps>(
  ({ className, size = 'md', ...props }, ref) => (
    <span
      ref={ref}
      className={clsx(
        'loading loading-spinner',
        sizeClasses[size],
        className
      )}
      {...props}
    />
  )
);
Spinner.displayName = 'Spinner';

interface LoadingStateProps extends React.HTMLAttributes<HTMLDivElement> {
  message?: string;
}

function LoadingState({ message = 'Loading...', className, ...props }: LoadingStateProps) {
  return (
    <div
      className={clsx(
        'flex flex-col items-center justify-center gap-3 p-8 text-base-content/60',
        className
      )}
      {...props}
    >
      <Spinner size="lg" />
      <p className="text-sm">{message}</p>
    </div>
  );
}

export { Spinner, LoadingState };
