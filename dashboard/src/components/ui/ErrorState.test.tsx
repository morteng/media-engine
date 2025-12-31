/**
 * Tests for ErrorState components
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import {
  ErrorState,
  NetworkErrorState,
  LoadErrorState,
  PageErrorState,
} from './ErrorState';

describe('ErrorState', () => {
  it('renders error message', () => {
    render(<ErrorState message="Something went wrong" />);
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('renders suggestion when provided', () => {
    render(
      <ErrorState
        message="Error occurred"
        suggestion="Try refreshing the page"
      />
    );
    expect(screen.getByText('Try refreshing the page')).toBeInTheDocument();
  });

  it('does not render suggestion when not provided', () => {
    render(<ErrorState message="Error occurred" />);
    expect(screen.queryByText('Try refreshing')).not.toBeInTheDocument();
  });

  it('renders retry button when onRetry is provided', () => {
    const onRetry = vi.fn();
    render(<ErrorState message="Error" onRetry={onRetry} />);
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });

  it('calls onRetry when retry button is clicked', () => {
    const onRetry = vi.fn();
    render(<ErrorState message="Error" onRetry={onRetry} />);
    fireEvent.click(screen.getByRole('button', { name: /try again/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('does not render retry button when onRetry is not provided', () => {
    render(<ErrorState message="Error" />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('renders custom retry label', () => {
    render(<ErrorState message="Error" onRetry={() => {}} retryLabel="Retry Now" />);
    expect(screen.getByRole('button', { name: /retry now/i })).toBeInTheDocument();
  });

  describe('variants', () => {
    it('renders inline variant with minimal padding', () => {
      const { container } = render(<ErrorState message="Error" variant="inline" />);
      expect(container.querySelector('.py-4')).toBeInTheDocument();
    });

    it('renders card variant with card styling', () => {
      const { container } = render(<ErrorState message="Error" variant="card" />);
      expect(container.querySelector('.card')).toBeInTheDocument();
      expect(container.querySelector('.bg-base-200')).toBeInTheDocument();
    });

    it('renders fullPage variant with large padding', () => {
      const { container } = render(<ErrorState message="Error" variant="fullPage" />);
      expect(container.querySelector('.py-16')).toBeInTheDocument();
      expect(container.querySelector('.min-h-\\[400px\\]')).toBeInTheDocument();
    });
  });

  describe('severity', () => {
    it('renders error severity with error color', () => {
      const { container } = render(<ErrorState message="Error" severity="error" />);
      expect(container.querySelector('.text-error')).toBeInTheDocument();
    });

    it('renders warning severity with warning color', () => {
      const { container } = render(<ErrorState message="Warning" severity="warning" />);
      expect(container.querySelector('.text-warning')).toBeInTheDocument();
    });

    it('renders info severity with info color', () => {
      const { container } = render(<ErrorState message="Info" severity="info" />);
      expect(container.querySelector('.text-info')).toBeInTheDocument();
    });

    it('applies severity background for card variant', () => {
      const { container } = render(
        <ErrorState message="Error" severity="error" variant="card" />
      );
      expect(container.querySelector('.bg-error\\/5')).toBeInTheDocument();
    });
  });

  it('renders custom icon when provided', () => {
    render(
      <ErrorState
        message="Error"
        icon={<span data-testid="custom-icon">Custom Icon</span>}
      />
    );
    expect(screen.getByTestId('custom-icon')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<ErrorState message="Error" className="custom-error" />);
    expect(container.querySelector('.custom-error')).toBeInTheDocument();
  });
});

describe('NetworkErrorState', () => {
  it('renders connection error message', () => {
    render(<NetworkErrorState />);
    expect(screen.getByText('Connection Error')).toBeInTheDocument();
  });

  it('renders suggestion about checking connection', () => {
    render(<NetworkErrorState />);
    expect(screen.getByText(/check your internet connection/i)).toBeInTheDocument();
  });

  it('renders with card variant', () => {
    const { container } = render(<NetworkErrorState />);
    expect(container.querySelector('.card')).toBeInTheDocument();
  });

  it('renders retry button when onRetry is provided', () => {
    const onRetry = vi.fn();
    render(<NetworkErrorState onRetry={onRetry} />);
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });

  it('calls onRetry when retry button is clicked', () => {
    const onRetry = vi.fn();
    render(<NetworkErrorState onRetry={onRetry} />);
    fireEvent.click(screen.getByRole('button', { name: /try again/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('applies custom className', () => {
    const { container } = render(<NetworkErrorState className="custom-network" />);
    expect(container.querySelector('.custom-network')).toBeInTheDocument();
  });
});

describe('LoadErrorState', () => {
  it('renders default data load error message', () => {
    render(<LoadErrorState />);
    expect(screen.getByText(/failed to load data/i)).toBeInTheDocument();
  });

  it('renders custom resource name in message', () => {
    render(<LoadErrorState resource="documents" />);
    expect(screen.getByText(/failed to load documents/i)).toBeInTheDocument();
  });

  it('renders suggestion to try again', () => {
    render(<LoadErrorState />);
    expect(screen.getByText(/something went wrong while loading/i)).toBeInTheDocument();
  });

  it('renders with inline variant', () => {
    const { container } = render(<LoadErrorState />);
    expect(container.querySelector('.py-4')).toBeInTheDocument();
  });

  it('renders retry button when onRetry is provided', () => {
    const onRetry = vi.fn();
    render(<LoadErrorState onRetry={onRetry} />);
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });

  it('calls onRetry when retry button is clicked', () => {
    const onRetry = vi.fn();
    render(<LoadErrorState onRetry={onRetry} />);
    fireEvent.click(screen.getByRole('button', { name: /try again/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('applies custom className', () => {
    const { container } = render(<LoadErrorState className="custom-load" />);
    expect(container.querySelector('.custom-load')).toBeInTheDocument();
  });
});

describe('PageErrorState', () => {
  it('renders default error message', () => {
    render(<PageErrorState />);
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('renders custom error message', () => {
    render(<PageErrorState message="Page not found" />);
    expect(screen.getByText('Page not found')).toBeInTheDocument();
  });

  it('renders suggestion to try again or go back', () => {
    render(<PageErrorState />);
    expect(screen.getByText(/try again or go back/i)).toBeInTheDocument();
  });

  it('renders with full page styling', () => {
    const { container } = render(<PageErrorState />);
    expect(container.querySelector('.py-16')).toBeInTheDocument();
    expect(container.querySelector('.min-h-\\[400px\\]')).toBeInTheDocument();
  });

  it('renders Go Back button when onGoBack is provided', () => {
    const onGoBack = vi.fn();
    render(<PageErrorState onGoBack={onGoBack} />);
    expect(screen.getByRole('button', { name: /go back/i })).toBeInTheDocument();
  });

  it('calls onGoBack when Go Back button is clicked', () => {
    const onGoBack = vi.fn();
    render(<PageErrorState onGoBack={onGoBack} />);
    fireEvent.click(screen.getByRole('button', { name: /go back/i }));
    expect(onGoBack).toHaveBeenCalledTimes(1);
  });

  it('renders Try Again button when onRetry is provided', () => {
    const onRetry = vi.fn();
    render(<PageErrorState onRetry={onRetry} />);
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });

  it('calls onRetry when Try Again button is clicked', () => {
    const onRetry = vi.fn();
    render(<PageErrorState onRetry={onRetry} />);
    fireEvent.click(screen.getByRole('button', { name: /try again/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('renders both buttons when both callbacks are provided', () => {
    const onGoBack = vi.fn();
    const onRetry = vi.fn();
    render(<PageErrorState onGoBack={onGoBack} onRetry={onRetry} />);
    expect(screen.getByRole('button', { name: /go back/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });

  it('does not render buttons when callbacks are not provided', () => {
    render(<PageErrorState />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<PageErrorState className="custom-page" />);
    expect(container.querySelector('.custom-page')).toBeInTheDocument();
  });
});
