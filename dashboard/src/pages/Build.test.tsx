import { describe, it, expect } from 'vitest';
import { render, screen, waitFor, userEvent } from '@/test/utils';
import { Build } from './Build';

describe('Build', () => {
  it('renders build page header', async () => {
    render(<Build />);
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /build & publish/i })).toBeInTheDocument();
    });
  });

  it('shows publications section', async () => {
    render(<Build />);
    await waitFor(() => {
      expect(screen.getByText(/publications/i)).toBeInTheDocument();
    });
  });

  it('shows available publications', async () => {
    render(<Build />);
    await waitFor(() => {
      // Check for publication titles from mock data
      expect(screen.getByText(/documentation/i)).toBeInTheDocument();
    });
  });

  it('shows output options section', async () => {
    render(<Build />);
    await waitFor(() => {
      expect(screen.getByText(/output options/i)).toBeInTheDocument();
    });
  });

  it('has build & publish button', async () => {
    render(<Build />);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /build & publish/i })).toBeInTheDocument();
    });
  });

  it('has build only button', async () => {
    render(<Build />);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /build only/i })).toBeInTheDocument();
    });
  });

  it('shows last build time when available', async () => {
    render(<Build />);
    await waitFor(() => {
      expect(screen.getByText(/last build/i)).toBeInTheDocument();
    });
  });

  it('shows format options for publications', async () => {
    render(<Build />);
    await waitFor(() => {
      // Publications have format badges
      const htmlBadges = screen.getAllByText(/html/i);
      expect(htmlBadges.length).toBeGreaterThan(0);
    });
  });

  it('can toggle publication selection', async () => {
    const user = userEvent.setup();
    render(<Build />);

    await waitFor(() => {
      expect(screen.getByText(/documentation/i)).toBeInTheDocument();
    });

    // Find and click a checkbox
    const checkboxes = screen.getAllByRole('checkbox');
    expect(checkboxes.length).toBeGreaterThan(0);

    // Click to toggle
    await user.click(checkboxes[0]);
  });
});
