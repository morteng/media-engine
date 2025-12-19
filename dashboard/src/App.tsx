import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from '@/components/layout';
import { Overview } from '@/pages';

// Placeholder pages - will be implemented
function ContentPage() {
  return <div className="page"><h1>Content</h1><p className="text-muted">Coming soon...</p></div>;
}
function TranslationsPage() {
  return <div className="page"><h1>Translations</h1><p className="text-muted">Coming soon...</p></div>;
}
function InsightsPage() {
  return <div className="page"><h1>Insights</h1><p className="text-muted">Coming soon...</p></div>;
}
function BuildPage() {
  return <div className="page"><h1>Build</h1><p className="text-muted">Coming soon...</p></div>;
}
function QualityPage() {
  return <div className="page"><h1>Quality</h1><p className="text-muted">Coming soon...</p></div>;
}
function FreshnessPage() {
  return <div className="page"><h1>Freshness</h1><p className="text-muted">Coming soon...</p></div>;
}
function ActivityPage() {
  return <div className="page"><h1>Activity</h1><p className="text-muted">Coming soon...</p></div>;
}
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
            <Route path="content/*" element={<ContentPage />} />
            <Route path="translations" element={<TranslationsPage />} />
            <Route path="insights" element={<InsightsPage />} />
            <Route path="build" element={<BuildPage />} />
            <Route path="quality" element={<QualityPage />} />
            <Route path="freshness" element={<FreshnessPage />} />
            <Route path="activity" element={<ActivityPage />} />
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
