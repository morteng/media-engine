import { describe, it, expect, vi } from 'vitest';
import { render, screen, userEvent } from '@/test/utils';
import { Button } from './Button';

describe('Button', () => {
  it('renders children correctly', () => {
    render(<Button>Click Me</Button>);
    expect(screen.getByRole('button', { name: 'Click Me' })).toBeInTheDocument();
  });

  it('renders with default styling', () => {
    render(<Button>Default</Button>);
    const button = screen.getByRole('button');
    // Check for DaisyUI btn classes
    expect(button).toHaveClass('btn', 'btn-primary');
  });

  it('renders with secondary variant', () => {
    render(<Button variant="secondary">Secondary</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('btn', 'btn-secondary');
  });

  it('renders with ghost variant', () => {
    render(<Button variant="ghost">Ghost</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('btn', 'btn-ghost');
  });

  it('renders with danger variant', () => {
    render(<Button variant="danger">Danger</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('btn', 'btn-error');
  });

  it('renders with different sizes', () => {
    const { rerender } = render(<Button size="sm">Small</Button>);
    expect(screen.getByRole('button')).toHaveClass('btn', 'btn-sm');

    rerender(<Button size="lg">Large</Button>);
    expect(screen.getByRole('button')).toHaveClass('btn', 'btn-lg');
  });

  it('handles click events', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();

    render(<Button onClick={handleClick}>Clickable</Button>);
    await user.click(screen.getByRole('button'));

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('is disabled when loading', () => {
    render(<Button loading>Loading</Button>);
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });

  it('shows spinner when loading', () => {
    render(<Button loading>Loading</Button>);
    const button = screen.getByRole('button');
    // Check for DaisyUI loading spinner
    const spinner = button.querySelector('.loading');
    expect(spinner).toBeInTheDocument();
  });

  it('does not trigger click when disabled', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();

    render(<Button disabled onClick={handleClick}>Disabled</Button>);
    await user.click(screen.getByRole('button'));

    expect(handleClick).not.toHaveBeenCalled();
  });

  it('applies custom className', () => {
    render(<Button className="custom-class">Custom</Button>);
    expect(screen.getByRole('button')).toHaveClass('custom-class');
  });

  it('passes through additional props', () => {
    render(<Button type="submit" data-testid="submit-btn">Submit</Button>);
    const button = screen.getByTestId('submit-btn');
    expect(button).toHaveAttribute('type', 'submit');
  });

  it('applies touch-target class when touchFriendly is true', () => {
    render(<Button touchFriendly>Touch Friendly</Button>);
    expect(screen.getByRole('button')).toHaveClass('touch-target');
  });

  it('does not apply touch-target class by default', () => {
    render(<Button>Normal</Button>);
    expect(screen.getByRole('button')).not.toHaveClass('touch-target');
  });
});
