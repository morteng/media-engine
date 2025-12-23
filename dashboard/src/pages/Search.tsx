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
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Search</h1>
      </div>

      {/* Search Form */}
      <Card>
        <CardContent className="pt-4">
          <form onSubmit={handleSearch} className="flex gap-3">
            <div className="flex items-center gap-2 flex-1 px-4 py-2 bg-base-300 border border-base-content/10 rounded-lg">
              <SearchIcon size={20} className="text-base-content/60" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search documents, content, metadata..."
                className="flex-1 bg-transparent outline-none"
                autoFocus
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={isSearching}>
              {isSearching ? (
                <>
                  <span className="loading loading-spinner loading-sm" />
                  Searching...
                </>
              ) : (
                'Search'
              )}
            </button>
          </form>
        </CardContent>
      </Card>

      {/* Results */}
      {hasSearched && (
        <div className="space-y-4">
          {results.length > 0 ? (
            <>
              <p className="text-sm text-base-content/60">{results.length} results found</p>
              {results.map((result, idx) => (
                <Card key={idx}>
                  <CardContent className="pt-4">
                    <div className="flex items-center gap-2 mb-2">
                      <FileText size={16} className="text-primary" />
                      <span className="font-medium">{result.title}</span>
                      <Badge size="sm">{result.type}</Badge>
                    </div>
                    <div className="text-sm text-base-content/60 mb-2">{result.path}</div>
                    {result.matches && result.matches.length > 0 && (
                      <div className="space-y-1">
                        {result.matches.slice(0, 2).map((match, midx) => (
                          <p key={midx} className="text-sm text-base-content/80 bg-base-300/50 px-2 py-1 rounded">
                            {match}
                          </p>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </>
          ) : (
            <div className="text-center py-12">
              <SearchIcon size={48} className="mx-auto text-base-content/30 mb-4" />
              <h3 className="text-lg font-medium mb-1">No results found</h3>
              <p className="text-base-content/60">Try different keywords or check your spelling.</p>
            </div>
          )}
        </div>
      )}

      {!hasSearched && (
        <Card>
          <CardContent className="pt-4">
            <h3 className="font-medium mb-3">Search Tips</h3>
            <ul className="space-y-2 text-sm text-base-content/60">
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                Search by document title or content
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                Use keywords from your documentation
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                Search by file type (chapter, script, slides)
              </li>
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
