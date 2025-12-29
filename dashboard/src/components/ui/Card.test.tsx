import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from './Card';

describe('Card', () => {
  it('renders children correctly', () => {
    render(<Card>Card content</Card>);
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  it('renders with default styling', () => {
    render(<Card data-testid="card">Default Card</Card>);
    const card = screen.getByTestId('card');
    // Check for DaisyUI classes
    expect(card).toHaveClass('card', 'bg-base-200', 'border');
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
    render(
      <CardHeader>
        <CardTitle>Card Title</CardTitle>
      </CardHeader>
    );
    expect(screen.getByText('Card Title')).toBeInTheDocument();
  });

  it('renders description when provided', () => {
    render(
      <CardHeader>
        <CardTitle>Title</CardTitle>
        <CardDescription>Description text</CardDescription>
      </CardHeader>
    );
    expect(screen.getByText('Description text')).toBeInTheDocument();
  });

  it('renders title only without description', () => {
    render(
      <CardHeader>
        <CardTitle>Title Only</CardTitle>
      </CardHeader>
    );
    expect(screen.getByText('Title Only')).toBeInTheDocument();
    expect(screen.queryByText('undefined')).not.toBeInTheDocument();
  });

  it('renders action when provided alongside title', () => {
    render(
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>Title</CardTitle>
        <button>Action</button>
      </CardHeader>
    );
    expect(screen.getByRole('button', { name: 'Action' })).toBeInTheDocument();
  });

  it('renders title with proper styling', () => {
    render(
      <CardHeader>
        <CardTitle>Test</CardTitle>
      </CardHeader>
    );
    const title = screen.getByText('Test');
    expect(title).toHaveClass('text-base', 'font-semibold');
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
    expect(content).toHaveClass('p-4', 'pt-0');
  });

  it('applies custom className', () => {
    render(<CardContent className="custom-content" data-testid="content">Content</CardContent>);
    const content = screen.getByTestId('content');
    expect(content).toHaveClass('custom-content');
  });
});
