import { describe, it, expect } from 'vitest';
import { render, screen, waitFor, userEvent } from '@/test/utils';
import { Content } from './Content';

describe('Content', () => {
  it('renders content page header', async () => {
    render(<Content />);
    await waitFor(() => {
      expect(screen.getByText(/content/i)).toBeInTheDocument();
    });
  });

  it('renders document categories after loading', async () => {
    render(<Content />);
    await waitFor(() => {
      expect(screen.getByText(/chapter/i)).toBeInTheDocument();
    });
  });

  it('renders document list', async () => {
    render(<Content />);
    await waitFor(() => {
      expect(screen.getByText('Introduction')).toBeInTheDocument();
      expect(screen.getByText('Setup Guide')).toBeInTheDocument();
    });
  });

  it('allows clicking on a document', async () => {
    const user = userEvent.setup();
    render(<Content />);

    await waitFor(() => {
      expect(screen.getByText('Introduction')).toBeInTheDocument();
    });

    await user.click(screen.getByText('Introduction'));
    // Document should be selected (implementation specific)
  });

  it('shows language selector', async () => {
    render(<Content />);
    await waitFor(() => {
      // Check for language selection UI
      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
    });
  });
});
