import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { Card, CardHeader, CardContent } from './Card';

describe('Card', () => {
  it('renders children correctly', () => {
    render(<Card>Card content</Card>);
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  it('renders with default styling', () => {
    render(<Card data-testid="card">Default Card</Card>);
    const card = screen.getByTestId('card');
    // Check for essential Tailwind classes
    expect(card).toHaveClass('rounded-lg', 'border', 'bg-card');
  });

  it('renders with glow variant', () => {
    render(<Card variant="glow" data-testid="card">Glow Card</Card>);
    const card = screen.getByTestId('card');
    expect(card).toHaveClass('border-primary/30', 'shadow-lg');
  });

  it('renders with gradient variant', () => {
    render(<Card variant="gradient" data-testid="card">Gradient Card</Card>);
    const card = screen.getByTestId('card');
    expect(card).toHaveClass('bg-gradient-to-br');
  });

  it('applies custom className', () => {
    render(<Card className="custom-card" data-testid="card">Custom</Card>);
    const card = screen.getByTestId('card');
    expect(card).toHaveClass('custom-card');
  });
});

describe('CardHeader', () => {
  it('renders title', () => {
    render(<CardHeader title="Card Title" />);
    expect(screen.getByText('Card Title')).toBeInTheDocument();
  });

  it('renders subtitle when provided', () => {
    render(<CardHeader title="Title" subtitle="Subtitle text" />);
    expect(screen.getByText('Subtitle text')).toBeInTheDocument();
  });

  it('does not render subtitle when not provided', () => {
    render(<CardHeader title="Title Only" />);
    expect(screen.queryByText('undefined')).not.toBeInTheDocument();
  });

  it('renders action when provided', () => {
    render(<CardHeader title="Title" action={<button>Action</button>} />);
    expect(screen.getByRole('button', { name: 'Action' })).toBeInTheDocument();
  });

  it('renders title with proper styling', () => {
    render(<CardHeader title="Test" />);
    const title = screen.getByText('Test');
    expect(title).toHaveClass('text-lg', 'font-semibold');
  });
});

describe('CardContent', () => {
  it('renders children', () => {
    render(<CardContent>Content here</CardContent>);
    expect(screen.getByText('Content here')).toBeInTheDocument();
  });

  it('renders with proper padding', () => {
    render(<CardContent data-testid="content">Content</CardContent>);
    const content = screen.getByTestId('content');
    expect(content).toHaveClass('p-6', 'pt-0');
  });

  it('applies custom className', () => {
    render(<CardContent className="custom-content" data-testid="content">Content</CardContent>);
    const content = screen.getByTestId('content');
    expect(content).toHaveClass('custom-content');
  });
});
