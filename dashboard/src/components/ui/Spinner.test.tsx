/**
 * Tests for Spinner components
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Spinner, LoadingState, PageLoading } from './Spinner';

describe('Spinner', () => {
  it('renders with default size', () => {
    const { container } = render(<Spinner />);
    expect(container.querySelector('.loading')).toBeInTheDocument();
    expect(container.querySelector('.loading-md')).toBeInTheDocument();
  });

  it('renders with different sizes', () => {
    const { rerender, container } = render(<Spinner size="sm" />);
    expect(container.querySelector('.loading-sm')).toBeInTheDocument();

    rerender(<Spinner size="md" />);
    expect(container.querySelector('.loading-md')).toBeInTheDocument();

    rerender(<Spinner size="lg" />);
    expect(container.querySelector('.loading-lg')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<Spinner className="text-primary" />);
    expect(container.querySelector('.text-primary')).toBeInTheDocument();
  });

  it('applies loading-spinner class', () => {
    const { container } = render(<Spinner />);
    expect(container.querySelector('.loading-spinner')).toBeInTheDocument();
  });
});

describe('LoadingState', () => {
  it('renders with default message', () => {
    render(<LoadingState />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders with custom message', () => {
    render(<LoadingState message="Custom loading" />);
    expect(screen.getByText('Custom loading')).toBeInTheDocument();
  });

  it('contains a Spinner', () => {
    const { container } = render(<LoadingState />);
    expect(container.querySelector('.loading-spinner')).toBeInTheDocument();
  });
});

describe('PageLoading', () => {
  it('renders with default message', () => {
    render(<PageLoading />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders with custom message', () => {
    render(<PageLoading message="Fetching data..." />);
    expect(screen.getByText('Fetching data...')).toBeInTheDocument();
  });

  it('applies default min-height', () => {
    const { container } = render(<PageLoading />);
    expect(container.querySelector('.min-h-\\[400px\\]')).toBeInTheDocument();
  });

  it('applies custom min-height', () => {
    const { container } = render(<PageLoading minHeight="min-h-screen" />);
    expect(container.querySelector('.min-h-screen')).toBeInTheDocument();
  });

  it('contains a centered Spinner', () => {
    const { container } = render(<PageLoading />);
    expect(container.querySelector('.loading-spinner')).toBeInTheDocument();
    expect(container.querySelector('.flex.items-center.justify-center')).toBeInTheDocument();
  });

  it('uses large spinner by default', () => {
    const { container } = render(<PageLoading />);
    expect(container.querySelector('.loading-lg')).toBeInTheDocument();
  });
});
