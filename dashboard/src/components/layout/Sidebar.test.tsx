import { describe, it, expect, afterEach } from 'vitest';
import { render, screen } from '@/test/utils';
import { Sidebar } from './Sidebar';

// Mock window.innerWidth for responsive testing
const mockWindowWidth = (width: number) => {
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: width,
  });
  window.dispatchEvent(new Event('resize'));
};

describe('Sidebar', () => {
  const originalInnerWidth = window.innerWidth;

  afterEach(() => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: originalInnerWidth,
    });
  });

  describe('Navigation Items', () => {
    it('renders all navigation links', () => {
      mockWindowWidth(1024);
      render(<Sidebar />);

      expect(screen.getByRole('link', { name: /dashboard/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /content/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /quality/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /build/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /ai assist/i })).toBeInTheDocument();
    });

    it('Dashboard link points to root', () => {
      mockWindowWidth(1024);
      render(<Sidebar />);
      expect(screen.getByRole('link', { name: /dashboard/i })).toHaveAttribute('href', '/');
    });

    it('Content link points to /content', () => {
      mockWindowWidth(1024);
      render(<Sidebar />);
      expect(screen.getByRole('link', { name: /content/i })).toHaveAttribute('href', '/content');
    });

    it('Quality link points to /quality', () => {
      mockWindowWidth(1024);
      render(<Sidebar />);
      expect(screen.getByRole('link', { name: /quality/i })).toHaveAttribute('href', '/quality');
    });

    it('Build link points to /build', () => {
      mockWindowWidth(1024);
      render(<Sidebar />);
      expect(screen.getByRole('link', { name: /build/i })).toHaveAttribute('href', '/build');
    });

    it('AI Assist link points to /ai-assist', () => {
      mockWindowWidth(1024);
      render(<Sidebar />);
      expect(screen.getByRole('link', { name: /ai assist/i })).toHaveAttribute('href', '/ai-assist');
    });
  });

  describe('Desktop Behavior', () => {
    it('renders sidebar on desktop', () => {
      mockWindowWidth(1024);
      render(<Sidebar />);
      expect(screen.getByRole('complementary')).toBeInTheDocument();
    });

    it('has navigation element', () => {
      mockWindowWidth(1024);
      render(<Sidebar />);
      expect(screen.getByRole('navigation')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('uses complementary landmark for sidebar', () => {
      mockWindowWidth(1024);
      render(<Sidebar />);
      expect(screen.getByRole('complementary')).toBeInTheDocument();
    });

    it('uses navigation landmark', () => {
      mockWindowWidth(1024);
      render(<Sidebar />);
      expect(screen.getByRole('navigation')).toBeInTheDocument();
    });

    it('navigation links are keyboard accessible', () => {
      mockWindowWidth(1024);
      render(<Sidebar />);
      const links = screen.getAllByRole('link');
      links.forEach(link => {
        expect(link).not.toHaveAttribute('tabindex', '-1');
      });
    });
  });

  describe('Active State', () => {
    it('applies active class to current route', () => {
      mockWindowWidth(1024);
      render(<Sidebar />, { route: '/', useMemoryRouter: true });

      const dashboardLink = screen.getByRole('link', { name: /dashboard/i });
      expect(dashboardLink).toHaveClass('active');
    });

    it('Quality link is active on /quality route', () => {
      mockWindowWidth(1024);
      render(<Sidebar />, { route: '/quality', useMemoryRouter: true });

      const qualityLink = screen.getByRole('link', { name: /quality/i });
      expect(qualityLink).toHaveClass('active');
    });
  });
});
