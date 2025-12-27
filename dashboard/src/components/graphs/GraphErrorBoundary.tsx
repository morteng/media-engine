/**
 * Error Boundary for Graph Components
 *
 * Catches React errors in graph rendering (especially Reagraph/React 19 compatibility issues)
 * and displays a fallback UI instead of crashing the entire page.
 */

import { Component, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallbackHeight?: string | number;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class GraphErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('GraphErrorBoundary caught error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined });
    this.props.onReset?.();
  };

  render() {
    if (this.state.hasError) {
      const height = this.props.fallbackHeight || 400;

      return (
        <div
          className="flex flex-col items-center justify-center bg-base-200 rounded-lg border border-error/20"
          style={{ height }}
        >
          <AlertTriangle size={48} className="text-warning mb-4" />
          <h3 className="text-lg font-semibold mb-2">Graph Visualization Error</h3>
          <p className="text-sm text-base-content/60 mb-4 text-center max-w-md px-4">
            The interactive graph could not be rendered. This may be due to a library compatibility issue.
          </p>
          <div className="flex gap-2">
            <button
              className="btn btn-sm btn-outline"
              onClick={this.handleReset}
            >
              <RefreshCw size={14} />
              Try Again
            </button>
          </div>
          {this.state.error && (
            <details className="mt-4 text-xs text-base-content/40 max-w-md">
              <summary className="cursor-pointer">Technical Details</summary>
              <pre className="mt-2 p-2 bg-base-300 rounded text-left overflow-auto max-h-32">
                {this.state.error.message}
              </pre>
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default GraphErrorBoundary;
