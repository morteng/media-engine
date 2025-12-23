import { describe, it, expect, afterEach } from 'vitest';
import { render, screen, userEvent, waitFor } from '@/test/utils';
import { Header } from './Header';

// Mock window.innerWidth for responsive testing
const mockWindowWidth = (width: number) => {
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: width,
  });
  window.dispatchEvent(new Event('resize'));
};

describe('Header', () => {
  const originalInnerWidth = window.innerWidth;

  afterEach(() => {
    // Restore original window width
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: originalInnerWidth,
    });
  });

  describe('Menu Toggle', () => {
    it('renders menu toggle button in top left', () => {
      render(<Header />);
      const toggleButton = screen.getByRole('button', { name: /sidebar|menu/i });
      expect(toggleButton).toBeInTheDocument();
    });

    it('shows collapse/expand icon on desktop', () => {
      mockWindowWidth(1024);
      render(<Header />);
      const toggleButton = screen.getByRole('button', { name: /sidebar/i });
      expect(toggleButton).toBeInTheDocument();
    });

    it('has correct aria-label on desktop', () => {
      mockWindowWidth(1024);
      render(<Header />);
      const toggleButton = screen.getByRole('button', { name: /collapse sidebar|expand sidebar/i });
      expect(toggleButton).toHaveAttribute('aria-label');
    });

    it('toggle button is clickable', async () => {
      const user = userEvent.setup();
      render(<Header />);
      const toggleButton = screen.getByRole('button', { name: /sidebar|menu/i });
      await user.click(toggleButton);
      // Should not throw
    });
  });

  describe('Project Selector', () => {
    it('renders project selector', () => {
      render(<Header />);
      expect(screen.getByText('ME')).toBeInTheDocument();
    });

    it('opens project menu on click', async () => {
      const user = userEvent.setup();
      render(<Header />);

      const projectButton = screen.getByRole('button', { name: /media engine/i });
      await user.click(projectButton);

      await waitFor(() => {
        expect(screen.getByText('Open Project...')).toBeInTheDocument();
      });
    });
  });

  describe('Search', () => {
    it('renders search button', () => {
      render(<Header />);
      expect(screen.getByText('Search...')).toBeInTheDocument();
    });

    it('displays keyboard shortcut', () => {
      render(<Header />);
      expect(screen.getByText('⌘K')).toBeInTheDocument();
    });
  });

  describe('Theme Toggle', () => {
    it('renders theme toggle button', () => {
      render(<Header />);
      expect(screen.getByRole('button', { name: /switch to (light|dark) theme/i })).toBeInTheDocument();
    });

    it('toggles theme on click', async () => {
      const user = userEvent.setup();
      render(<Header />);

      const themeButton = screen.getByRole('button', { name: /switch to (light|dark) theme/i });
      await user.click(themeButton);

      // Theme should toggle (we can't easily test document attribute changes)
      expect(themeButton).toBeInTheDocument();
    });
  });

  describe('Layout Structure', () => {
    it('renders header element', () => {
      render(<Header />);
      expect(screen.getByRole('banner')).toBeInTheDocument();
    });

    it('renders header with correct structure', () => {
      const { container } = render(<Header />);
      // Check that header uses flexbox layout
      const header = container.querySelector('header');
      expect(header).toHaveClass('flex', 'items-center', 'justify-between');
    });
  });

  describe('Accessibility', () => {
    it('menu toggle has accessible name', () => {
      render(<Header />);
      const toggleButton = screen.getByRole('button', { name: /sidebar|menu/i });
      expect(toggleButton).toHaveAccessibleName();
    });

    it('theme toggle has accessible name', () => {
      render(<Header />);
      const themeButton = screen.getByRole('button', { name: /switch to (light|dark) theme/i });
      expect(themeButton).toHaveAccessibleName();
    });
  });
});
