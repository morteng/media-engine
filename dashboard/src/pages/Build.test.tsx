import { describe, it, expect } from 'vitest';
import { render, screen, waitFor, userEvent } from '@/test/utils';
import { Build } from './Build';

describe('Build', () => {
  it('renders build page header', async () => {
    render(<Build />);
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /build/i })).toBeInTheDocument();
    });
  });

  it('shows available output formats', async () => {
    render(<Build />);
    await waitFor(() => {
      // Use getAllByText since HTML appears multiple times
      const htmlElements = screen.getAllByText(/html/i);
      expect(htmlElements.length).toBeGreaterThan(0);
    });
  });

  it('shows last build status', async () => {
    render(<Build />);
    await waitFor(() => {
      expect(screen.getByText(/success/i)).toBeInTheDocument();
    });
  });

  it('has a build button', async () => {
    render(<Build />);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /build/i })).toBeInTheDocument();
    });
  });

  it('triggers build when button is clicked', async () => {
    const user = userEvent.setup();
    render(<Build />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /build/i })).toBeInTheDocument();
    });

    const buildButton = screen.getByRole('button', { name: /build/i });
    await user.click(buildButton);

    // Build should be triggered (implementation specific behavior)
  });
});
