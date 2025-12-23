import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { GraphToolbar } from './GraphToolbar';

describe('GraphToolbar', () => {
  it('renders zoom controls', () => {
    render(<GraphToolbar />);

    expect(screen.getByTitle('Zoom in')).toBeInTheDocument();
    expect(screen.getByTitle('Zoom out')).toBeInTheDocument();
    expect(screen.getByTitle('Reset view')).toBeInTheDocument();
  });

  it('renders layout selector buttons', () => {
    render(<GraphToolbar />);

    expect(screen.getByTitle('Force')).toBeInTheDocument();
    expect(screen.getByTitle('Circular')).toBeInTheDocument();
    expect(screen.getByTitle('Tree')).toBeInTheDocument();
    expect(screen.getByTitle('Radial')).toBeInTheDocument();
  });

  it('renders 3D toggle', () => {
    render(<GraphToolbar />);

    expect(screen.getByTitle(/Switch to (2D|3D)/)).toBeInTheDocument();
  });

  it('calls onZoomIn when zoom in clicked', async () => {
    const user = userEvent.setup();
    const onZoomIn = vi.fn();
    render(<GraphToolbar onZoomIn={onZoomIn} />);

    await user.click(screen.getByTitle('Zoom in'));
    expect(onZoomIn).toHaveBeenCalledTimes(1);
  });

  it('calls onZoomOut when zoom out clicked', async () => {
    const user = userEvent.setup();
    const onZoomOut = vi.fn();
    render(<GraphToolbar onZoomOut={onZoomOut} />);

    await user.click(screen.getByTitle('Zoom out'));
    expect(onZoomOut).toHaveBeenCalledTimes(1);
  });

  it('calls onResetView when reset clicked', async () => {
    const user = userEvent.setup();
    const onResetView = vi.fn();
    render(<GraphToolbar onResetView={onResetView} />);

    await user.click(screen.getByTitle('Reset view'));
    expect(onResetView).toHaveBeenCalledTimes(1);
  });

  it('calls onLayoutChange when layout button clicked', async () => {
    const user = userEvent.setup();
    const onLayoutChange = vi.fn();
    render(<GraphToolbar onLayoutChange={onLayoutChange} />);

    await user.click(screen.getByTitle('Circular'));
    expect(onLayoutChange).toHaveBeenCalledWith('circular2d');
  });

  it('highlights current layout', () => {
    render(<GraphToolbar currentLayout="hierarchicalTd" />);

    const treeButton = screen.getByTitle('Tree');
    expect(treeButton).toHaveClass('btn-primary');
  });

  it('calls onToggle3D when 3D button clicked', async () => {
    const user = userEvent.setup();
    const onToggle3D = vi.fn();
    render(<GraphToolbar onToggle3D={onToggle3D} />);

    await user.click(screen.getByTitle('Switch to 3D'));
    expect(onToggle3D).toHaveBeenCalledTimes(1);
  });

  it('shows correct 3D title based on state', () => {
    const { rerender } = render(<GraphToolbar is3D={false} />);
    expect(screen.getByTitle('Switch to 3D')).toBeInTheDocument();

    rerender(<GraphToolbar is3D={true} />);
    expect(screen.getByTitle('Switch to 2D')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<GraphToolbar className="custom-toolbar" />);

    const toolbar = container.firstChild as HTMLElement;
    expect(toolbar).toHaveClass('custom-toolbar');
  });
});
