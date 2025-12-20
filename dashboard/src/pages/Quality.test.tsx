import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import { Quality } from './Quality';

describe('Quality', () => {
  it('renders quality page header', async () => {
    render(<Quality />);
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /quality/i })).toBeInTheDocument();
    });
  });

  it('displays quality issues after loading', async () => {
    render(<Quality />);
    await waitFor(() => {
      // Mock has warning and info issues
      expect(screen.getByText(/links/i)).toBeInTheDocument();
    });
  });

  it('shows issue count', async () => {
    render(<Quality />);
    await waitFor(() => {
      // Mock has 2 issues
      expect(screen.getByText(/2/)).toBeInTheDocument();
    });
  });

  it('displays issue categories', async () => {
    render(<Quality />);
    await waitFor(() => {
      expect(screen.getByText(/readability/i)).toBeInTheDocument();
    });
  });

  it('shows issue severity indicators', async () => {
    render(<Quality />);
    await waitFor(() => {
      expect(screen.getByText(/warning/i)).toBeInTheDocument();
    });
  });
});
