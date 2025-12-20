import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import { Insights } from './Insights';

describe('Insights', () => {
  it('renders insights page header', async () => {
    render(<Insights />);
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /insights/i })).toBeInTheDocument();
    });
  });

  it('displays content statistics card', async () => {
    render(<Insights />);
    await waitFor(() => {
      expect(screen.getByText(/content statistics/i)).toBeInTheDocument();
    });
  });

  it('shows total documents count', async () => {
    render(<Insights />);
    await waitFor(() => {
      expect(screen.getByText(/total documents/i)).toBeInTheDocument();
    });
  });

  it('has analytics and activity tabs', async () => {
    render(<Insights />);
    await waitFor(() => {
      expect(screen.getByText('Analytics')).toBeInTheDocument();
      expect(screen.getByText('Activity')).toBeInTheDocument();
    });
  });
});
