import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { Card, CardHeader, CardContent } from './Card';

describe('Card', () => {
  it('renders children correctly', () => {
    render(<Card>Card content</Card>);
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  it('applies default variant class', () => {
    render(<Card data-testid="card">Default Card</Card>);
    const card = screen.getByTestId('card');
    expect(card).toHaveClass('card', 'card-default');
  });

  it('applies glow variant class', () => {
    render(<Card variant="glow" data-testid="card">Glow Card</Card>);
    const card = screen.getByTestId('card');
    expect(card).toHaveClass('card-glow');
  });

  it('applies gradient variant class', () => {
    render(<Card variant="gradient" data-testid="card">Gradient Card</Card>);
    const card = screen.getByTestId('card');
    expect(card).toHaveClass('card-gradient');
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

  it('applies correct classes', () => {
    render(<CardHeader title="Test" />);
    expect(screen.getByText('Test').closest('.card-header')).toBeInTheDocument();
    expect(screen.getByText('Test')).toHaveClass('card-title');
  });
});

describe('CardContent', () => {
  it('renders children', () => {
    render(<CardContent>Content here</CardContent>);
    expect(screen.getByText('Content here')).toBeInTheDocument();
  });

  it('applies card-content class', () => {
    render(<CardContent>Content</CardContent>);
    expect(screen.getByText('Content')).toHaveClass('card-content');
  });

  it('applies custom className', () => {
    render(<CardContent className="custom-content">Content</CardContent>);
    expect(screen.getByText('Content')).toHaveClass('card-content', 'custom-content');
  });
});
