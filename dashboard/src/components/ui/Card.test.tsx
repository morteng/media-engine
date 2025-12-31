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
    // Check for base card classes
    expect(card).toHaveClass('card', 'bg-base-200', 'border', 'rounded-lg');
  });

  it('applies custom className', () => {
    render(<Card className="custom-card" data-testid="card">Custom</Card>);
    const card = screen.getByTestId('card');
    expect(card).toHaveClass('custom-card');
  });

  describe('variants', () => {
    it('renders default variant with shadow-sm', () => {
      render(<Card variant="default" data-testid="card">Default</Card>);
      const card = screen.getByTestId('card');
      expect(card).toHaveClass('shadow-sm', 'bg-base-200', 'border');
    });

    it('renders elevated variant with shadow-lg', () => {
      render(<Card variant="elevated" data-testid="card">Elevated</Card>);
      const card = screen.getByTestId('card');
      expect(card).toHaveClass('shadow-lg', 'hover:shadow-xl', 'transition-shadow');
    });

    it('renders gradient variant with gradient background', () => {
      render(<Card variant="gradient" data-testid="card">Gradient</Card>);
      const card = screen.getByTestId('card');
      expect(card).toHaveClass('bg-gradient-to-br', 'from-base-200', 'to-base-300');
    });

    it('renders bordered variant with border-2', () => {
      render(<Card variant="bordered" data-testid="card">Bordered</Card>);
      const card = screen.getByTestId('card');
      expect(card).toHaveClass('border-2', 'border-base-300');
    });

    it('renders ghost variant with transparent background', () => {
      render(<Card variant="ghost" data-testid="card">Ghost</Card>);
      const card = screen.getByTestId('card');
      expect(card).toHaveClass('bg-transparent', 'hover:border-base-300', 'transition-colors');
    });

    it('renders interactive variant with hover effects', () => {
      render(<Card variant="interactive" data-testid="card">Interactive</Card>);
      const card = screen.getByTestId('card');
      expect(card).toHaveClass(
        'hover:shadow-md',
        'hover:border-primary/50',
        'transition-all',
        'cursor-pointer'
      );
    });

    it('renders glow variant (legacy) with primary glow', () => {
      render(<Card variant="glow" data-testid="card">Glow</Card>);
      const card = screen.getByTestId('card');
      expect(card).toHaveClass('border-primary/30', 'shadow-lg', 'shadow-primary/10');
    });
  });

  describe('padding', () => {
    it('renders without padding by default', () => {
      render(<Card data-testid="card">No padding</Card>);
      const card = screen.getByTestId('card');
      expect(card).not.toHaveClass('p-3', 'p-4', 'p-6');
    });

    it('renders with compact padding (p-3)', () => {
      render(<Card padding="compact" data-testid="card">Compact</Card>);
      const card = screen.getByTestId('card');
      expect(card).toHaveClass('p-3');
    });

    it('renders with default padding (p-4)', () => {
      render(<Card padding="default" data-testid="card">Default padding</Card>);
      const card = screen.getByTestId('card');
      expect(card).toHaveClass('p-4');
    });

    it('renders with spacious padding (p-6)', () => {
      render(<Card padding="spacious" data-testid="card">Spacious</Card>);
      const card = screen.getByTestId('card');
      expect(card).toHaveClass('p-6');
    });

    it('renders with none padding (no padding class)', () => {
      render(<Card padding="none" data-testid="card">None</Card>);
      const card = screen.getByTestId('card');
      expect(card).not.toHaveClass('p-3', 'p-4', 'p-6');
    });
  });

  describe('combined variant and padding', () => {
    it('renders elevated variant with spacious padding', () => {
      render(
        <Card variant="elevated" padding="spacious" data-testid="card">
          Combined
        </Card>
      );
      const card = screen.getByTestId('card');
      expect(card).toHaveClass('shadow-lg', 'p-6');
    });

    it('renders interactive variant with compact padding', () => {
      render(
        <Card variant="interactive" padding="compact" data-testid="card">
          Combined
        </Card>
      );
      const card = screen.getByTestId('card');
      expect(card).toHaveClass('cursor-pointer', 'p-3');
    });
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
