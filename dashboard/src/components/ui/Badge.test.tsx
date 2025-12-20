import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { Badge } from './Badge';

describe('Badge', () => {
  it('renders children correctly', () => {
    render(<Badge>Test Badge</Badge>);
    expect(screen.getByText('Test Badge')).toBeInTheDocument();
  });

  it('applies default variant class', () => {
    render(<Badge>Default</Badge>);
    const badge = screen.getByText('Default');
    expect(badge).toHaveClass('badge', 'badge-default', 'badge-md');
  });

  it('applies success variant class', () => {
    render(<Badge variant="success">Success</Badge>);
    const badge = screen.getByText('Success');
    expect(badge).toHaveClass('badge-success');
  });

  it('applies warning variant class', () => {
    render(<Badge variant="warning">Warning</Badge>);
    const badge = screen.getByText('Warning');
    expect(badge).toHaveClass('badge-warning');
  });

  it('applies error variant class', () => {
    render(<Badge variant="error">Error</Badge>);
    const badge = screen.getByText('Error');
    expect(badge).toHaveClass('badge-error');
  });

  it('applies info variant class', () => {
    render(<Badge variant="info">Info</Badge>);
    const badge = screen.getByText('Info');
    expect(badge).toHaveClass('badge-info');
  });

  it('applies small size class', () => {
    render(<Badge size="sm">Small</Badge>);
    const badge = screen.getByText('Small');
    expect(badge).toHaveClass('badge-sm');
  });

  it('applies large size class', () => {
    render(<Badge size="lg">Large</Badge>);
    const badge = screen.getByText('Large');
    expect(badge).toHaveClass('badge-lg');
  });

  it('renders with both variant and size', () => {
    render(<Badge variant="success" size="sm">Combined</Badge>);
    const badge = screen.getByText('Combined');
    expect(badge).toHaveClass('badge', 'badge-success', 'badge-sm');
  });
});
