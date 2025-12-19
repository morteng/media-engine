import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from '@/components/layout';
import {
  Overview,
  Content,
  Insights,
  Translations,
  Quality,
  Build,
  Freshness,
  Activity,
} from '@/pages';

// Placeholder pages for remaining features
function MediaPage() {
  return <div className="page"><h1>Media</h1><p className="text-muted">Coming soon...</p></div>;
}
function PacksPage() {
  return <div className="page"><h1>Packs</h1><p className="text-muted">Coming soon...</p></div>;
}
function SearchPage() {
  return <div className="page"><h1>Search</h1><p className="text-muted">Coming soon...</p></div>;
}
function DependenciesPage() {
  return <div className="page"><h1>Dependencies</h1><p className="text-muted">Coming soon...</p></div>;
}

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
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Overview />} />
            <Route path="content/*" element={<Content />} />
            <Route path="translations" element={<Translations />} />
            <Route path="insights" element={<Insights />} />
            <Route path="build" element={<Build />} />
            <Route path="quality" element={<Quality />} />
            <Route path="freshness" element={<Freshness />} />
            <Route path="activity" element={<Activity />} />
            <Route path="media" element={<MediaPage />} />
            <Route path="packs" element={<PacksPage />} />
            <Route path="search" element={<SearchPage />} />
            <Route path="dependencies" element={<DependenciesPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
