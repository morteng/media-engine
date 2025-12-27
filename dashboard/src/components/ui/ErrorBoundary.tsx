import { Component, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  showDetails?: boolean;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

/**
 * Global error boundary that catches React errors and displays a recovery UI.
 * Prevents the entire app from crashing due to component errors.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    this.setState({ errorInfo });

    // Log to console for debugging
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // Call optional error handler (for analytics/tracking)
    this.props.onError?.(error, errorInfo);
  }

  handleRetry = (): void => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  handleGoHome = (): void => {
    window.location.href = '/';
  };

  handleReload = (): void => {
    window.location.reload();
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div
          className="min-h-screen flex items-center justify-center bg-base-100 p-4"
          role="alert"
          aria-live="assertive"
        >
          <div className="card bg-base-200 shadow-xl max-w-lg w-full">
            <div className="card-body text-center">
              <div className="flex justify-center mb-4">
                <div className="p-4 rounded-full bg-error/10">
                  <AlertTriangle className="w-12 h-12 text-error" aria-hidden="true" />
                </div>
              </div>

              <h1 className="text-2xl font-bold text-base-content">
                Something went wrong
              </h1>

              <p className="text-base-content/70 mt-2">
                We encountered an unexpected error. You can try refreshing the page
                or going back to the dashboard.
              </p>

              {/* Error details (collapsible) */}
              {this.props.showDetails && this.state.error && (
                <details className="mt-4 text-left">
                  <summary className="cursor-pointer text-sm text-base-content/60 hover:text-base-content flex items-center gap-2">
                    <Bug size={14} aria-hidden="true" />
                    Technical details
                  </summary>
                  <div className="mt-2 p-3 bg-base-300 rounded-lg overflow-auto max-h-48">
                    <p className="text-sm font-mono text-error">
                      {this.state.error.message}
                    </p>
                    {this.state.errorInfo?.componentStack && (
                      <pre className="text-xs text-base-content/60 mt-2 whitespace-pre-wrap">
                        {this.state.errorInfo.componentStack}
                      </pre>
                    )}
                  </div>
                </details>
              )}

              <div className="card-actions justify-center mt-6 gap-3">
                <button
                  onClick={this.handleRetry}
                  className="btn btn-primary gap-2"
                  aria-label="Try again"
                >
                  <RefreshCw size={16} aria-hidden="true" />
                  Try Again
                </button>
                <button
                  onClick={this.handleGoHome}
                  className="btn btn-ghost gap-2"
                  aria-label="Go to dashboard"
                >
                  <Home size={16} aria-hidden="true" />
                  Dashboard
                </button>
              </div>

              <p className="text-xs text-base-content/50 mt-4">
                If this keeps happening, please check the browser console for details.
              </p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Smaller error boundary for individual page sections.
 * Shows inline error with retry option.
 */
export function PageErrorFallback({
  error,
  resetError,
  title = "Failed to load this section"
}: {
  error?: Error;
  resetError?: () => void;
  title?: string;
}) {
  return (
    <div
      className="flex flex-col items-center justify-center p-8 text-center"
      role="alert"
      aria-live="polite"
    >
      <AlertTriangle className="w-12 h-12 text-warning mb-4" aria-hidden="true" />
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="text-base-content/60 mt-1 max-w-md">
        {error?.message || "An unexpected error occurred. Please try again."}
      </p>
      {resetError && (
        <button
          onClick={resetError}
          className="btn btn-primary btn-sm mt-4 gap-2"
          aria-label="Retry loading"
        >
          <RefreshCw size={14} aria-hidden="true" />
          Retry
        </button>
      )}
    </div>
  );
}

/**
 * Higher-order component to wrap a component with an error boundary.
 */
export function withErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  fallback?: ReactNode
) {
  return function WithErrorBoundary(props: P) {
    return (
      <ErrorBoundary fallback={fallback}>
        <WrappedComponent {...props} />
      </ErrorBoundary>
    );
  };
}
