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
    // Check for DaisyUI badge classes
    expect(badge).toHaveClass('badge', 'badge-ghost');
  });

  it('renders with success variant', () => {
    render(<Badge variant="success">Success</Badge>);
    const badge = screen.getByText('Success');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('badge', 'badge-success');
  });

  it('renders with warning variant', () => {
    render(<Badge variant="warning">Warning</Badge>);
    const badge = screen.getByText('Warning');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('badge', 'badge-warning');
  });

  it('renders with error variant', () => {
    render(<Badge variant="error">Error</Badge>);
    const badge = screen.getByText('Error');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('badge', 'badge-error');
  });

  it('renders with info variant', () => {
    render(<Badge variant="info">Info</Badge>);
    const badge = screen.getByText('Info');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('badge', 'badge-info');
  });

  it('renders with small size', () => {
    render(<Badge size="sm">Small</Badge>);
    const badge = screen.getByText('Small');
    expect(badge).toBeInTheDocument();
    // sm maps to badge-xs in the component
    expect(badge).toHaveClass('badge', 'badge-xs');
  });

  it('renders with large size', () => {
    render(<Badge size="lg">Large</Badge>);
    const badge = screen.getByText('Large');
    expect(badge).toBeInTheDocument();
    // lg maps to badge-md in the component
    expect(badge).toHaveClass('badge', 'badge-md');
  });

  it('renders with both variant and size', () => {
    render(<Badge variant="success" size="sm">Combined</Badge>);
    const badge = screen.getByText('Combined');
    expect(badge).toBeInTheDocument();
    // sm maps to badge-xs
    expect(badge).toHaveClass('badge', 'badge-success', 'badge-xs');
  });
});
