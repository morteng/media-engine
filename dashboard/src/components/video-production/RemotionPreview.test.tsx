import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { server } from '../../test/mocks/server';
import { RemotionPreview } from './RemotionPreview';

// Create a wrapper with QueryClient for tests
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('RemotionPreview', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    server.resetHandlers();
  });

  it('shows loading state initially', () => {
    render(<RemotionPreview />, { wrapper: createWrapper() });

    // Should show loading spinner (Loader2 icon has animate-spin class)
    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('shows disabled message when Remotion not configured', async () => {
    server.use(
      http.get('/api/video/preview/config', () => HttpResponse.json({
        enabled: false,
        studio_url: '',
        studio_port: 0,
        compositions: [],
        default_composition: '',
      }))
    );

    render(<RemotionPreview />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Remotion Not Configured')).toBeInTheDocument();
    });
  });

  it('renders preview header when enabled', async () => {
    render(<RemotionPreview />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Preview')).toBeInTheDocument();
    });
  });

  it('shows composition selector with options', async () => {
    render(<RemotionPreview />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    const select = screen.getByRole('combobox');
    expect(select).toHaveValue('Main');
  });

  it('shows offline status when server not running', async () => {
    render(<RemotionPreview />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Offline')).toBeInTheDocument();
    });
  });

  it('shows start server button when offline', async () => {
    render(<RemotionPreview />, { wrapper: createWrapper() });

    await waitFor(() => {
      // There are two start buttons - one in controls and one in the main area
      const buttons = screen.getAllByText(/Start/);
      expect(buttons.length).toBeGreaterThan(0);
    });
  });

  it('renders refresh button', async () => {
    render(<RemotionPreview />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTitle('Refresh')).toBeInTheDocument();
    });
  });

  it('renders open in new tab button', async () => {
    render(<RemotionPreview />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTitle('Open in new tab')).toBeInTheDocument();
    });
  });

  it('renders fullscreen button', async () => {
    render(<RemotionPreview />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTitle('Fullscreen')).toBeInTheDocument();
    });
  });

  it('changes composition when selected', async () => {
    render(<RemotionPreview />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'Intro' } });
    expect(select).toHaveValue('Intro');
  });

  it('displays script ID when provided', async () => {
    render(<RemotionPreview scriptId="test-script-123" />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('test-script-123')).toBeInTheDocument();
    });
  });

  it('shows preview server message when offline', async () => {
    render(<RemotionPreview />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Preview Server Not Running')).toBeInTheDocument();
    });
  });

  it('can click start server button', async () => {
    render(<RemotionPreview />, { wrapper: createWrapper() });

    await waitFor(() => {
      const startButton = screen.getByRole('button', { name: /start preview server/i });
      expect(startButton).toBeInTheDocument();
    });

    const startButton = screen.getByRole('button', { name: /start preview server/i });
    // Just verify the button can be clicked without error
    fireEvent.click(startButton);

    // The button should still be in the DOM (may be in loading state)
    expect(startButton).toBeInTheDocument();
  });

  it('has all composition options', async () => {
    render(<RemotionPreview />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    const options = screen.getAllByRole('option');
    expect(options).toHaveLength(3);
    expect(options[0]).toHaveValue('Main');
    expect(options[1]).toHaveValue('Intro');
    expect(options[2]).toHaveValue('Outro');
  });
});
