import type { ReactElement, ReactNode } from 'react';
import { render, type RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { SidebarProvider } from '@/contexts/SidebarContext';
import { SettingsProvider } from '@/contexts/SettingsContext';
import { ConfirmProvider } from '@/components/ui/ConfirmDialog';

// Create a fresh QueryClient for each test
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });
}

interface WrapperProps {
  children: ReactNode;
}

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  route?: string;
  useMemoryRouter?: boolean;
}

// Providers wrapper without router (router is added separately)
function ProvidersWrapper({ children }: WrapperProps) {
  const queryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      <SettingsProvider>
        <ConfirmProvider>
          <SidebarProvider>
            {children}
          </SidebarProvider>
        </ConfirmProvider>
      </SettingsProvider>
    </QueryClientProvider>
  );
}

// Custom render function using data router (supports useBlocker)
function customRender(
  ui: ReactElement,
  { route = '/', ...options }: CustomRenderOptions = {}
) {
  const queryClient = createTestQueryClient();

  // Create a data router that supports useBlocker
  const router = createMemoryRouter(
    [
      {
        path: '*',
        element: (
          <QueryClientProvider client={queryClient}>
            <SettingsProvider>
              <ConfirmProvider>
                <SidebarProvider>
                  {ui}
                </SidebarProvider>
              </ConfirmProvider>
            </SettingsProvider>
          </QueryClientProvider>
        ),
      },
    ],
    {
      initialEntries: [route],
    }
  );

  return render(<RouterProvider router={router} />, options);
}

// Re-export everything from testing-library
export * from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';

// Override render with our custom version
export { customRender as render };

// Export ProvidersWrapper for use cases that don't need routing
export { ProvidersWrapper };
