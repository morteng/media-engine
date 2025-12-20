import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Search as SearchIcon, FileText } from 'lucide-react';
import * as api from '@/api/client';

interface SearchResult {
  path: string;
  title: string;
  type: string;
  matches: string[];
  score: number;
}

export function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    setHasSearched(true);

    try {
      const data = await api.search(query);
      setResults((data.results as SearchResult[]) ?? []);
    } catch (error) {
      console.error('Search failed:', error);
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="page search-page">
      <div className="page-header">
        <h1>Search</h1>
      </div>

      {/* Search Form */}
      <Card className="search-card">
        <CardContent>
          <form onSubmit={handleSearch} className="search-form">
            <div className="search-input-wrapper">
              <SearchIcon size={20} />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search documents, content, metadata..."
                className="search-input-large"
                autoFocus
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={isSearching}>
              {isSearching ? 'Searching...' : 'Search'}
            </button>
          </form>
        </CardContent>
      </Card>

      {/* Results */}
      {hasSearched && (
        <div className="search-results">
          {results.length > 0 ? (
            <>
              <p className="results-count">{results.length} results found</p>
              {results.map((result, idx) => (
                <Card key={idx} className="result-card">
                  <CardContent>
                    <div className="result-header">
                      <FileText size={16} />
                      <span className="result-title">{result.title}</span>
                      <Badge variant="default" size="sm">{result.type}</Badge>
                    </div>
                    <div className="result-path">{result.path}</div>
                    {result.matches && result.matches.length > 0 && (
                      <div className="result-matches">
                        {result.matches.slice(0, 2).map((match, midx) => (
                          <p key={midx} className="match-text">{match}</p>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </>
          ) : (
            <div className="empty-state">
              <SearchIcon size={48} className="text-muted" />
              <h3>No results found</h3>
              <p className="text-muted">Try different keywords or check your spelling.</p>
            </div>
          )}
        </div>
      )}

      {!hasSearched && (
        <div className="search-tips">
          <h3>Search Tips</h3>
          <ul>
            <li>Search by document title or content</li>
            <li>Use keywords from your documentation</li>
            <li>Search by file type (chapter, script, slides)</li>
          </ul>
        </div>
      )}
    </div>
  );
}
