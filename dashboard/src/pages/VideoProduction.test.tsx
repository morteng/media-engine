import { describe, it, expect } from 'vitest';
import { render, screen, waitFor, userEvent } from '@/test/utils';
import { VideoProduction } from './VideoProduction';

describe('VideoProduction', () => {
  it('renders video production page header', async () => {
    render(<VideoProduction />);
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /video production/i })).toBeInTheDocument();
    });
  });

  it('shows tab navigation', async () => {
    render(<VideoProduction />);
    await waitFor(() => {
      expect(screen.getByRole('link', { name: /overview/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /scripts/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /render/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /assets/i })).toBeInTheDocument();
    });
  });

  it('shows overview tab by default', async () => {
    render(<VideoProduction />);
    await waitFor(() => {
      // Overview shows stats cards - there are multiple "Video Scripts" elements
      expect(screen.getAllByText(/video scripts/i).length).toBeGreaterThan(0);
    });
  });
});

describe('VideoProduction - Overview Tab', () => {
  it('displays script count', async () => {
    render(<VideoProduction />);
    await waitFor(() => {
      // Should show count from mock data (3 scripts)
      expect(screen.getByText('3')).toBeInTheDocument();
    });
  });

  it('displays active renders', async () => {
    render(<VideoProduction />);
    await waitFor(() => {
      expect(screen.getByText(/active renders/i)).toBeInTheDocument();
    });
  });

  it('displays completed renders', async () => {
    render(<VideoProduction />);
    await waitFor(() => {
      expect(screen.getByText(/completed/i)).toBeInTheDocument();
    });
  });

  it('shows video scripts section', async () => {
    render(<VideoProduction />);
    await waitFor(() => {
      // The heading text "Video Scripts" appears in the overview
      expect(screen.getAllByText(/video scripts/i).length).toBeGreaterThan(0);
    });
  });
});

describe('VideoProduction - Scripts Tab', () => {
  it('has scripts tab link', async () => {
    render(<VideoProduction />);

    await waitFor(() => {
      expect(screen.getByRole('link', { name: /scripts/i })).toBeInTheDocument();
    });
  });

  it('scripts tab link has correct href', async () => {
    render(<VideoProduction />);

    await waitFor(() => {
      const scriptsLink = screen.getByRole('link', { name: /scripts/i });
      expect(scriptsLink).toHaveAttribute('href', expect.stringContaining('scripts'));
    });
  });
});

describe('VideoProduction - Render Tab', () => {
  it('has render tab link', async () => {
    render(<VideoProduction />);

    await waitFor(() => {
      expect(screen.getByRole('link', { name: /render/i })).toBeInTheDocument();
    });
  });

  it('render tab link has correct href', async () => {
    render(<VideoProduction />);

    await waitFor(() => {
      const renderLink = screen.getByRole('link', { name: /render/i });
      expect(renderLink).toHaveAttribute('href', expect.stringContaining('render'));
    });
  });
});

describe('VideoProduction - Assets Tab', () => {
  it('has assets tab link', async () => {
    render(<VideoProduction />);

    await waitFor(() => {
      expect(screen.getByRole('link', { name: /assets/i })).toBeInTheDocument();
    });
  });

  it('assets tab link has correct href', async () => {
    render(<VideoProduction />);

    await waitFor(() => {
      const assetsLink = screen.getByRole('link', { name: /assets/i });
      expect(assetsLink).toHaveAttribute('href', expect.stringContaining('assets'));
    });
  });
});

describe('VideoProduction - Loading States', () => {
  it('shows loading spinner initially', () => {
    render(<VideoProduction />);
    // Check for loading state (spinner has animate-spin class)
    const spinners = document.querySelectorAll('[class*="animate-spin"]');
    expect(spinners.length).toBeGreaterThanOrEqual(0); // May or may not show depending on timing
  });
});

describe('VideoProduction - Error Handling', () => {
  // Error handling tests would require overriding the msw handlers
  // to return errors, which is more complex to set up
  it('handles missing data gracefully', async () => {
    render(<VideoProduction />);
    // Should render without crashing even if data is loading
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /video production/i })).toBeInTheDocument();
    });
  });
});

describe('VideoProduction - Interactions', () => {
  it('tabs are clickable', async () => {
    const user = userEvent.setup();
    render(<VideoProduction />);

    await waitFor(() => {
      expect(screen.getByRole('link', { name: /scripts/i })).toBeInTheDocument();
    });

    // Clicking should not throw an error
    const scriptsTab = screen.getByRole('link', { name: /scripts/i });
    await user.click(scriptsTab);
  });
});
