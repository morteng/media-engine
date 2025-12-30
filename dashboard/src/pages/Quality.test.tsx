import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SidebarProvider } from '@/contexts/SidebarContext';
import { SettingsProvider } from '@/contexts/SettingsContext';
import { Quality } from './Quality';

// Custom render for Quality page
function renderQuality(initialRoute = '/quality') {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <SettingsProvider>
        <SidebarProvider>
          <MemoryRouter initialEntries={[initialRoute]}>
            <Routes>
              <Route path="/quality" element={<Quality />} />
            </Routes>
          </MemoryRouter>
        </SidebarProvider>
      </SettingsProvider>
    </QueryClientProvider>
  );
}

describe('Quality', () => {
  it('renders quality page header', async () => {
    renderQuality();
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /quality/i })).toBeInTheDocument();
    });
  });

  it('displays quality score after loading', async () => {
    renderQuality();
    await waitFor(() => {
      // Mock has health.overall = 85
      expect(screen.getByText('85')).toBeInTheDocument();
    }, { timeout: 5000 });
  });

  it('shows quality status badge', async () => {
    renderQuality();
    await waitFor(() => {
      // Mock has status: 'good'
      expect(screen.getByText(/good/i)).toBeInTheDocument();
    }, { timeout: 5000 });
  });

  it('displays component scores section', async () => {
    renderQuality();
    await waitFor(() => {
      expect(screen.getByText(/component scores/i)).toBeInTheDocument();
    }, { timeout: 5000 });
  });

  it('shows issue count summary', async () => {
    renderQuality();
    await waitFor(() => {
      // Look for Critical/Warnings labels
      expect(screen.getByText(/critical/i)).toBeInTheDocument();
      expect(screen.getByText(/warnings/i)).toBeInTheDocument();
    }, { timeout: 5000 });
  });

  it('displays document count', async () => {
    renderQuality();
    await waitFor(() => {
      // Mock has document_count: 10
      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText(/documents/i)).toBeInTheDocument();
    }, { timeout: 5000 });
  });

  it('displays expandable analysis sections', async () => {
    renderQuality();
    // Wait for Component Scores section to appear (first expandable section after data loads)
    await waitFor(() => {
      expect(screen.getByText(/component scores/i)).toBeInTheDocument();
    }, { timeout: 5000 });
    // The page is loaded, check for key sections using getByRole to find headings
    // These sections exist as h3 elements inside ExpandableSection buttons
    expect(screen.getByRole('heading', { name: /semantic analysis/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /knowledge graph/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /readability/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /freshness/i })).toBeInTheDocument();
  });

  it('displays activity section', async () => {
    renderQuality();
    await waitFor(() => {
      expect(screen.getByText(/recent activity/i)).toBeInTheDocument();
    }, { timeout: 5000 });
  });
});
