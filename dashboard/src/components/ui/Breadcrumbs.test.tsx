import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { Home } from 'lucide-react';
import { Breadcrumbs, type BreadcrumbItem } from './Breadcrumbs';

describe('Breadcrumbs', () => {
  it('renders items correctly', () => {
    const items: BreadcrumbItem[] = [
      { label: 'Home', href: '/' },
      { label: 'Projects', href: '/projects' },
      { label: 'Current Project' },
    ];
    render(<Breadcrumbs items={items} />);

    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Projects')).toBeInTheDocument();
    expect(screen.getByText('Current Project')).toBeInTheDocument();
  });

  it('renders nav element with proper aria-label', () => {
    const items: BreadcrumbItem[] = [{ label: 'Home' }];
    render(<Breadcrumbs items={items} />);

    const nav = screen.getByRole('navigation', { name: 'Breadcrumb' });
    expect(nav).toBeInTheDocument();
  });

  it('marks last item with aria-current="page"', () => {
    const items: BreadcrumbItem[] = [
      { label: 'Home', href: '/' },
      { label: 'Current Page' },
    ];
    render(<Breadcrumbs items={items} />);

    const lastItem = screen.getByText('Current Page');
    expect(lastItem).toHaveAttribute('aria-current', 'page');
  });

  it('renders links for items with href', () => {
    const items: BreadcrumbItem[] = [
      { label: 'Home', href: '/' },
      { label: 'Projects', href: '/projects' },
      { label: 'Detail' },
    ];
    render(<Breadcrumbs items={items} />);

    const homeLink = screen.getByRole('link', { name: 'Home' });
    expect(homeLink).toHaveAttribute('href', '/');

    const projectsLink = screen.getByRole('link', { name: 'Projects' });
    expect(projectsLink).toHaveAttribute('href', '/projects');

    // Last item should not be a link
    const detailText = screen.getByText('Detail');
    expect(detailText.tagName).toBe('SPAN');
  });

  it('renders last item with bold styling', () => {
    const items: BreadcrumbItem[] = [
      { label: 'Home', href: '/' },
      { label: 'Current' },
    ];
    render(<Breadcrumbs items={items} />);

    const lastItem = screen.getByText('Current');
    expect(lastItem).toHaveClass('font-medium');
  });

  it('renders separators between items', () => {
    const items: BreadcrumbItem[] = [
      { label: 'A' },
      { label: 'B' },
      { label: 'C' },
    ];
    render(<Breadcrumbs items={items} />);

    // Should have 2 separators for 3 items (span wrappers with aria-hidden)
    const separators = document.querySelectorAll('span[aria-hidden="true"]');
    expect(separators).toHaveLength(2);
  });

  it('renders custom separator', () => {
    const items: BreadcrumbItem[] = [
      { label: 'A' },
      { label: 'B' },
    ];
    render(<Breadcrumbs items={items} separator={<span data-testid="custom-sep">/</span>} />);

    expect(screen.getByTestId('custom-sep')).toBeInTheDocument();
  });

  it('renders icons when provided', () => {
    const items: BreadcrumbItem[] = [
      { label: 'Home', href: '/', icon: <Home data-testid="home-icon" size={14} /> },
      { label: 'Current' },
    ];
    render(<Breadcrumbs items={items} />);

    expect(screen.getByTestId('home-icon')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const items: BreadcrumbItem[] = [{ label: 'Test' }];
    render(<Breadcrumbs items={items} className="custom-class" />);

    const nav = screen.getByRole('navigation');
    expect(nav).toHaveClass('custom-class');
  });
});
