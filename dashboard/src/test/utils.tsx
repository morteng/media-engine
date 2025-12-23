import type { ReactElement, ReactNode } from 'react';
import { render, type RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { SidebarProvider } from '@/contexts/SidebarContext';

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

// All-in-one wrapper with QueryClient, Router, and SidebarProvider
function AllProviders({ children }: WrapperProps) {
  const queryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      <SidebarProvider>
        <BrowserRouter>{children}</BrowserRouter>
      </SidebarProvider>
    </QueryClientProvider>
  );
}

// Wrapper with MemoryRouter for testing specific routes
function createMemoryRouterWrapper(initialRoute: string) {
  return function MemoryRouterWrapper({ children }: WrapperProps) {
    const queryClient = createTestQueryClient();
    return (
      <QueryClientProvider client={queryClient}>
        <SidebarProvider>
          <MemoryRouter initialEntries={[initialRoute]}>{children}</MemoryRouter>
        </SidebarProvider>
      </QueryClientProvider>
    );
  };
}

// Custom render function
function customRender(
  ui: ReactElement,
  { route = '/', useMemoryRouter = false, ...options }: CustomRenderOptions = {}
) {
  const Wrapper = useMemoryRouter
    ? createMemoryRouterWrapper(route)
    : AllProviders;

  return render(ui, { wrapper: Wrapper, ...options });
}

// Re-export everything from testing-library
export * from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';

// Override render with our custom version
export { customRender as render };
