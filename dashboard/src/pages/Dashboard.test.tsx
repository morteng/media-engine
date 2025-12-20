import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import { Dashboard } from './Dashboard';

describe('Dashboard', () => {
  it('renders loading state initially', () => {
    render(<Dashboard />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('renders health score after loading', async () => {
    render(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText('85')).toBeInTheDocument();
    });
  });

  it('renders statistics cards', async () => {
    render(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText(/documents/i)).toBeInTheDocument();
    });
  });

  it('renders health status', async () => {
    render(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText(/good/i)).toBeInTheDocument();
    });
  });
});
