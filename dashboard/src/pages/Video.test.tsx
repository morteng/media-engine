import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import { Video } from './Video';

describe('Video', () => {
  it('renders video scripts header', async () => {
    render(<Video />);
    await waitFor(() => {
      // Header shows "Scripts" with icon
      expect(screen.getByText('Scripts')).toBeInTheDocument();
    });
  });

  it('renders scripts list after loading', async () => {
    render(<Video />);
    await waitFor(() => {
      expect(screen.getByText(/scripts/i)).toBeInTheDocument();
    });
  });

  it('shows empty state when no script is selected', async () => {
    render(<Video />);
    await waitFor(() => {
      expect(screen.getByText(/select a script/i)).toBeInTheDocument();
    });
  });

  it('renders page with manage notes subtitle', async () => {
    render(<Video />);
    await waitFor(() => {
      // The page shows "manage notes" in the empty state description
      expect(screen.getByText(/manage notes/i)).toBeInTheDocument();
    });
  });
});
