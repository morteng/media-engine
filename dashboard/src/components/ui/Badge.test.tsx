import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { Badge } from './Badge';

describe('Badge', () => {
  it('renders children correctly', () => {
    render(<Badge>Test Badge</Badge>);
    expect(screen.getByText('Test Badge')).toBeInTheDocument();
  });

  it('renders with default styling', () => {
    render(<Badge>Default</Badge>);
    const badge = screen.getByText('Default');
    expect(badge).toBeInTheDocument();
    // Check that it has essential Tailwind classes
    expect(badge).toHaveClass('inline-flex', 'items-center', 'rounded-full');
  });

  it('renders with success variant', () => {
    render(<Badge variant="success">Success</Badge>);
    const badge = screen.getByText('Success');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('bg-success/15', 'text-success');
  });

  it('renders with warning variant', () => {
    render(<Badge variant="warning">Warning</Badge>);
    const badge = screen.getByText('Warning');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('bg-warning/15', 'text-warning');
  });

  it('renders with error variant', () => {
    render(<Badge variant="error">Error</Badge>);
    const badge = screen.getByText('Error');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('bg-destructive/15', 'text-destructive');
  });

  it('renders with info variant', () => {
    render(<Badge variant="info">Info</Badge>);
    const badge = screen.getByText('Info');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('bg-info/15', 'text-info');
  });

  it('renders with small size', () => {
    render(<Badge size="sm">Small</Badge>);
    const badge = screen.getByText('Small');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('text-[10px]', 'px-2', 'py-0');
  });

  it('renders with large size', () => {
    render(<Badge size="lg">Large</Badge>);
    const badge = screen.getByText('Large');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('text-sm', 'px-3', 'py-1');
  });

  it('renders with both variant and size', () => {
    render(<Badge variant="success" size="sm">Combined</Badge>);
    const badge = screen.getByText('Combined');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('bg-success/15', 'text-[10px]');
  });
});
