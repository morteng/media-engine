import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from '@/components/layout';
import { Dashboard, Content, Quality, Build, AIAssist, Brand } from '@/pages';
import { WebSocketProvider, SidebarProvider } from '@/contexts';
import { ToastProvider } from '@/components/ui';

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
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <SidebarProvider>
          <WebSocketProvider>
            <BrowserRouter>
              <Routes>
                <Route path="/" element={<Layout />}>
                  <Route index element={<Dashboard />} />
                  <Route path="content/*" element={<Content />} />
                  <Route path="quality/*" element={<Quality />} />
                  <Route path="build/*" element={<Build />} />
                  <Route path="brand/*" element={<Brand />} />
                  <Route path="ai-assist/*" element={<AIAssist />} />
                </Route>
              </Routes>
            </BrowserRouter>
          </WebSocketProvider>
        </SidebarProvider>
      </ToastProvider>
    </QueryClientProvider>
  );
}
