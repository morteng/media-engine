/**
 * Tests for Skeleton components
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  Skeleton,
  SkeletonCard,
  SkeletonList,
  SkeletonStats,
  SkeletonText,
  SkeletonAvatar,
  SkeletonTable,
} from './Skeleton';

describe('Skeleton', () => {
  it('renders with default styling', () => {
    const { container } = render(<Skeleton />);
    expect(container.querySelector('.skeleton')).toBeInTheDocument();
    expect(container.querySelector('.bg-base-300')).toBeInTheDocument();
  });

  it('renders with text variant (default)', () => {
    const { container } = render(<Skeleton />);
    expect(container.querySelector('.rounded')).toBeInTheDocument();
  });

  it('renders with circular variant', () => {
    const { container } = render(<Skeleton variant="circular" />);
    expect(container.querySelector('.rounded-full')).toBeInTheDocument();
  });

  it('renders with rectangular variant', () => {
    render(<Skeleton variant="rectangular" data-testid="skeleton" />);
    const skeleton = screen.getByTestId('skeleton');
    expect(skeleton).toHaveClass('skeleton');
    expect(skeleton).not.toHaveClass('rounded', 'rounded-full', 'rounded-lg');
  });

  it('renders with rounded variant', () => {
    const { container } = render(<Skeleton variant="rounded" />);
    expect(container.querySelector('.rounded-lg')).toBeInTheDocument();
  });

  it('applies width and height as pixels when number', () => {
    render(<Skeleton width={100} height={50} data-testid="skeleton" />);
    const skeleton = screen.getByTestId('skeleton');
    expect(skeleton).toHaveStyle({ width: '100px', height: '50px' });
  });

  it('applies width and height as string when string', () => {
    render(<Skeleton width="50%" height="2rem" data-testid="skeleton" />);
    const skeleton = screen.getByTestId('skeleton');
    expect(skeleton).toHaveStyle({ width: '50%', height: '2rem' });
  });

  it('applies custom className', () => {
    const { container } = render(<Skeleton className="custom-class" />);
    expect(container.querySelector('.custom-class')).toBeInTheDocument();
  });
});

describe('SkeletonText', () => {
  it('renders default 3 lines', () => {
    const { container } = render(<SkeletonText />);
    const skeletons = container.querySelectorAll('.skeleton');
    expect(skeletons).toHaveLength(3);
  });

  it('renders custom number of lines', () => {
    const { container } = render(<SkeletonText lines={5} />);
    const skeletons = container.querySelectorAll('.skeleton');
    expect(skeletons).toHaveLength(5);
  });

  it('renders last line with shorter width by default', () => {
    render(<SkeletonText lines={3} data-testid="text" />);
    const container = screen.getByTestId('text');
    const skeletons = container.querySelectorAll('.skeleton');
    // Last line should have 75% width
    expect(skeletons[2]).toHaveStyle({ width: '75%' });
    // Other lines should have 100% width
    expect(skeletons[0]).toHaveStyle({ width: '100%' });
    expect(skeletons[1]).toHaveStyle({ width: '100%' });
  });

  it('applies custom lastLineWidth', () => {
    render(<SkeletonText lines={2} lastLineWidth="50%" data-testid="text" />);
    const container = screen.getByTestId('text');
    const skeletons = container.querySelectorAll('.skeleton');
    expect(skeletons[1]).toHaveStyle({ width: '50%' });
  });

  it('applies custom lineHeight', () => {
    render(<SkeletonText lineHeight={20} data-testid="text" />);
    const container = screen.getByTestId('text');
    const skeletons = container.querySelectorAll('.skeleton');
    skeletons.forEach((skeleton) => {
      expect(skeleton).toHaveStyle({ height: '20px' });
    });
  });

  it('applies custom className', () => {
    const { container } = render(<SkeletonText className="custom-text" />);
    expect(container.querySelector('.custom-text')).toBeInTheDocument();
  });
});

describe('SkeletonAvatar', () => {
  it('renders with default md size', () => {
    render(<SkeletonAvatar data-testid="avatar" />);
    const avatar = screen.getByTestId('avatar');
    expect(avatar).toHaveStyle({ width: '40px', height: '40px' });
  });

  it('renders with sm size', () => {
    render(<SkeletonAvatar size="sm" data-testid="avatar" />);
    const avatar = screen.getByTestId('avatar');
    expect(avatar).toHaveStyle({ width: '24px', height: '24px' });
  });

  it('renders with lg size', () => {
    render(<SkeletonAvatar size="lg" data-testid="avatar" />);
    const avatar = screen.getByTestId('avatar');
    expect(avatar).toHaveStyle({ width: '56px', height: '56px' });
  });

  it('renders with xl size', () => {
    render(<SkeletonAvatar size="xl" data-testid="avatar" />);
    const avatar = screen.getByTestId('avatar');
    expect(avatar).toHaveStyle({ width: '80px', height: '80px' });
  });

  it('renders as circular', () => {
    const { container } = render(<SkeletonAvatar />);
    expect(container.querySelector('.rounded-full')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<SkeletonAvatar className="custom-avatar" />);
    expect(container.querySelector('.custom-avatar')).toBeInTheDocument();
  });
});

describe('SkeletonTable', () => {
  it('renders default 5 rows and 4 columns', () => {
    render(<SkeletonTable data-testid="table" />);
    const table = screen.getByTestId('table');
    // Header row + 5 data rows = 6 rows total
    const rows = table.querySelectorAll('.flex.gap-4.py-3');
    expect(rows).toHaveLength(6); // 1 header + 5 rows
  });

  it('renders custom number of rows', () => {
    render(<SkeletonTable rows={3} data-testid="table" />);
    const table = screen.getByTestId('table');
    // Header row + 3 data rows = 4 rows total
    const rows = table.querySelectorAll('.flex.gap-4.py-3');
    expect(rows).toHaveLength(4);
  });

  it('renders custom number of columns', () => {
    render(<SkeletonTable columns={6} rows={1} data-testid="table" />);
    const table = screen.getByTestId('table');
    // Each row should have 6 cells (flex-1 divs)
    const cells = table.querySelectorAll('.flex-1');
    expect(cells).toHaveLength(12); // 6 header cells + 6 row cells
  });

  it('renders without header when showHeader is false', () => {
    render(<SkeletonTable showHeader={false} rows={3} data-testid="table" />);
    const table = screen.getByTestId('table');
    const rows = table.querySelectorAll('.flex.gap-4.py-3');
    expect(rows).toHaveLength(3); // Just 3 data rows, no header
  });

  it('applies custom className', () => {
    const { container } = render(<SkeletonTable className="custom-table" />);
    expect(container.querySelector('.custom-table')).toBeInTheDocument();
  });
});

describe('SkeletonCard', () => {
  it('renders with card styling', () => {
    const { container } = render(<SkeletonCard />);
    expect(container.querySelector('.card')).toBeInTheDocument();
    expect(container.querySelector('.bg-base-200')).toBeInTheDocument();
  });

  it('renders with avatar, title lines, and text lines', () => {
    const { container } = render(<SkeletonCard />);
    // Should have circular avatar
    expect(container.querySelector('.rounded-full')).toBeInTheDocument();
    // Should have multiple skeleton elements
    const skeletons = container.querySelectorAll('.skeleton');
    expect(skeletons.length).toBeGreaterThan(3);
  });
});

describe('SkeletonList', () => {
  it('renders default 5 items', () => {
    const { container } = render(<SkeletonList />);
    const items = container.querySelectorAll('.flex.items-center.gap-3');
    expect(items).toHaveLength(5);
  });

  it('renders custom count of items', () => {
    const { container } = render(<SkeletonList count={3} />);
    const items = container.querySelectorAll('.flex.items-center.gap-3');
    expect(items).toHaveLength(3);
  });

  it('renders with rounded icons and text lines', () => {
    const { container } = render(<SkeletonList count={1} />);
    // Should have rounded icon placeholder
    expect(container.querySelector('.rounded-lg')).toBeInTheDocument();
    // Should have skeleton elements
    const skeletons = container.querySelectorAll('.skeleton');
    expect(skeletons.length).toBeGreaterThan(1);
  });
});

describe('SkeletonStats', () => {
  it('renders 4 stat cards', () => {
    const { container } = render(<SkeletonStats />);
    const cards = container.querySelectorAll('.card');
    expect(cards).toHaveLength(4);
  });

  it('renders in a 4-column grid', () => {
    const { container } = render(<SkeletonStats />);
    expect(container.querySelector('.grid-cols-4')).toBeInTheDocument();
  });

  it('each card has skeleton elements', () => {
    const { container } = render(<SkeletonStats />);
    const skeletons = container.querySelectorAll('.skeleton');
    expect(skeletons).toHaveLength(8); // 2 per card * 4 cards
  });
});
