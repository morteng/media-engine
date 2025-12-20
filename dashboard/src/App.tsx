import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from '@/components/layout';
import { Dashboard, Content, Video, Media, Quality, Build, Insights, AIAssist, SearchPage } from '@/pages';
import { WebSocketProvider } from '@/contexts';
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
        <WebSocketProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<Layout />}>
                <Route index element={<Dashboard />} />
                <Route path="content/*" element={<Content />} />
                <Route path="video/*" element={<Video />} />
                <Route path="media" element={<Media />} />
                <Route path="quality/*" element={<Quality />} />
                <Route path="build/*" element={<Build />} />
                <Route path="insights/*" element={<Insights />} />
                <Route path="ai-assist/*" element={<AIAssist />} />
                <Route path="search" element={<SearchPage />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </WebSocketProvider>
      </ToastProvider>
    </QueryClientProvider>
  );
}
