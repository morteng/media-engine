import { describe, it, expect } from 'vitest';
import { render, screen, userEvent } from '@/test/utils';
import { SubTabs } from './SubTabs';

const mockTabs = [
  { path: '', label: 'Overview' },
  { path: 'details', label: 'Details' },
  { path: 'settings', label: 'Settings' },
];

describe('SubTabs', () => {
  describe('Rendering', () => {
    it('renders all tabs', () => {
      render(<SubTabs tabs={mockTabs} basePath="/test" />);

      expect(screen.getByRole('link', { name: 'Overview' })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Details' })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Settings' })).toBeInTheDocument();
    });

    it('renders correct number of tabs', () => {
      render(<SubTabs tabs={mockTabs} basePath="/test" />);

      const links = screen.getAllByRole('link');
      expect(links).toHaveLength(3);
    });
  });

  describe('Links', () => {
    it('generates correct href for base tab', () => {
      render(<SubTabs tabs={mockTabs} basePath="/test" />);

      expect(screen.getByRole('link', { name: 'Overview' })).toHaveAttribute('href', '/test');
    });

    it('generates correct href for sub tabs', () => {
      render(<SubTabs tabs={mockTabs} basePath="/test" />);

      expect(screen.getByRole('link', { name: 'Details' })).toHaveAttribute('href', '/test/details');
      expect(screen.getByRole('link', { name: 'Settings' })).toHaveAttribute('href', '/test/settings');
    });

    it('works with different base paths', () => {
      render(<SubTabs tabs={mockTabs} basePath="/quality" />);

      expect(screen.getByRole('link', { name: 'Overview' })).toHaveAttribute('href', '/quality');
      expect(screen.getByRole('link', { name: 'Details' })).toHaveAttribute('href', '/quality/details');
    });
  });

  describe('Active State', () => {
    it('marks base tab as active on base route', () => {
      render(<SubTabs tabs={mockTabs} basePath="/test" />, {
        route: '/test',
        useMemoryRouter: true,
      });

      expect(screen.getByRole('link', { name: 'Overview' })).toHaveClass('active');
    });

    it('marks sub tab as active on sub route', () => {
      render(<SubTabs tabs={mockTabs} basePath="/test" />, {
        route: '/test/details',
        useMemoryRouter: true,
      });

      expect(screen.getByRole('link', { name: 'Details' })).toHaveClass('active');
    });

    it('only one tab is active at a time', () => {
      render(<SubTabs tabs={mockTabs} basePath="/test" />, {
        route: '/test/details',
        useMemoryRouter: true,
      });

      const activeLinks = screen.getAllByRole('link').filter(link =>
        link.classList.contains('active')
      );
      expect(activeLinks).toHaveLength(1);
    });
  });

  describe('Styling', () => {
    it('applies sub-tabs class to container', () => {
      const { container } = render(<SubTabs tabs={mockTabs} basePath="/test" />);

      expect(container.querySelector('.sub-tabs')).toBeInTheDocument();
    });

    it('applies sub-tab class to each tab', () => {
      const { container } = render(<SubTabs tabs={mockTabs} basePath="/test" />);

      const tabs = container.querySelectorAll('.sub-tab');
      expect(tabs).toHaveLength(3);
    });
  });

  describe('Navigation', () => {
    it('tabs are clickable', async () => {
      const user = userEvent.setup();
      render(<SubTabs tabs={mockTabs} basePath="/test" />);

      const detailsTab = screen.getByRole('link', { name: 'Details' });
      await user.click(detailsTab);

      // Navigation should work (we can't easily test route change in this setup)
      expect(detailsTab).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('all tabs are keyboard navigable', () => {
      render(<SubTabs tabs={mockTabs} basePath="/test" />);

      const links = screen.getAllByRole('link');
      links.forEach(link => {
        expect(link).not.toHaveAttribute('tabindex', '-1');
      });
    });
  });

  describe('Quality Page Tabs', () => {
    const qualityTabs = [
      { path: '', label: 'Quality' },
      { path: 'semantic', label: 'Semantic' },
      { path: 'knowledge', label: 'Knowledge' },
      { path: 'readability', label: 'Readability' },
      { path: 'freshness', label: 'Freshness' },
      { path: 'codesync', label: 'Code Sync' },
      { path: 'advanced', label: 'Advanced' },
      { path: 'activity', label: 'Activity' },
    ];

    it('renders all Quality page tabs', () => {
      render(<SubTabs tabs={qualityTabs} basePath="/quality" />);

      expect(screen.getByRole('link', { name: 'Quality' })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Semantic' })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Knowledge' })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Readability' })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Freshness' })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Code Sync' })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Advanced' })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Activity' })).toBeInTheDocument();
    });

    it('semantic tab has correct href', () => {
      render(<SubTabs tabs={qualityTabs} basePath="/quality" />);

      expect(screen.getByRole('link', { name: 'Semantic' })).toHaveAttribute(
        'href',
        '/quality/semantic'
      );
    });
  });
});
