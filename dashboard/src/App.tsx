import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from '@/components/layout';
import {
  Dashboard,
  Content,
  Quality,
  Build,
  Brand,
  Settings,
  AIWorkspace,
  VideoProduction,
} from '@/pages';
import { WebSocketProvider, SidebarProvider, SettingsProvider } from '@/contexts';
import { ToastProvider, ErrorBoundary, ConfirmProvider } from '@/components/ui';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60, // 1 minute
      retry: 1,
    },
  },
});

export default function App() {
  return (
    <ErrorBoundary showDetails={import.meta.env.DEV}>
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <ConfirmProvider>
            <SettingsProvider>
              <SidebarProvider>
                <WebSocketProvider>
                  <BrowserRouter>
                    <Routes>
                      <Route path="/" element={<Layout />}>
                        {/* Overview */}
                        <Route index element={<Dashboard />} />

                        {/* Build & Publish (primary workflow) */}
                        <Route path="build" element={<Build />} />
                        {/* Legacy redirects */}
                        <Route path="publications" element={<Navigate to="/build" replace />} />
                        <Route path="publications/*" element={<Navigate to="/build" replace />} />
                        <Route path="build/outputs" element={<Navigate to="/build" replace />} />
                        <Route path="build/deliverables" element={<Navigate to="/build" replace />} />
                        <Route path="deliverables" element={<Navigate to="/build" replace />} />

                        {/* Content section */}
                        <Route path="content/*" element={<Content />} />
                        <Route path="translations" element={<Navigate to="/content/translations" replace />} />
                        <Route path="quality/*" element={<Quality />} />

                        {/* Production section */}
                        <Route path="video/*" element={<VideoProduction />} />

                        {/* Tools section */}
                        <Route path="ai-assist/*" element={<AIWorkspace />} />
                        <Route path="brand/*" element={<Brand />} />
                        <Route path="settings/*" element={<Settings />} />

                        {/* Legacy redirect */}
                        <Route path="ai" element={<Navigate to="/ai-assist" replace />} />
                      </Route>
                    </Routes>
                  </BrowserRouter>
                </WebSocketProvider>
              </SidebarProvider>
            </SettingsProvider>
          </ConfirmProvider>
        </ToastProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
