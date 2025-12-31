import { useState, useMemo, useCallback, useRef, useEffect } from 'react';

export interface UseSearchOptions {
  /**
   * Debounce delay in milliseconds
   * @default 300
   */
  debounceMs?: number;
}

export interface UseSearchResult<T> {
  /**
   * Current search query
   */
  query: string;
  /**
   * Set the search query (will be debounced internally)
   */
  setQuery: (query: string) => void;
  /**
   * Filtered results based on current query
   */
  results: T[];
  /**
   * Whether search is currently in progress (during debounce)
   */
  isSearching: boolean;
  /**
   * Number of results found
   */
  resultCount: number;
  /**
   * Clear the search query
   */
  clearQuery: () => void;
  /**
   * Whether there's an active search (query is not empty)
   */
  hasQuery: boolean;
}

/**
 * Generic search hook for filtering items with debouncing
 *
 * @param items - Array of items to search through
 * @param searchFn - Function that determines if an item matches the query
 * @param options - Optional configuration
 *
 * @example
 * ```tsx
 * const { query, setQuery, results, resultCount } = useSearch(
 *   documents,
 *   (doc, q) => doc.title.toLowerCase().includes(q.toLowerCase())
 * );
 * ```
 */
export function useSearch<T>(
  items: T[],
  searchFn: (item: T, query: string) => boolean,
  options: UseSearchOptions = {}
): UseSearchResult<T> {
  const { debounceMs = 300 } = options;

  const [query, setQueryInternal] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout>>();

  // Handle query changes with debouncing
  const setQuery = useCallback(
    (newQuery: string) => {
      setQueryInternal(newQuery);

      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }

      if (newQuery !== debouncedQuery) {
        setIsSearching(true);

        if (debounceMs > 0) {
          debounceTimerRef.current = setTimeout(() => {
            setDebouncedQuery(newQuery);
            setIsSearching(false);
          }, debounceMs);
        } else {
          setDebouncedQuery(newQuery);
          setIsSearching(false);
        }
      } else {
        setIsSearching(false);
      }
    },
    [debounceMs, debouncedQuery]
  );

  // Clear query
  const clearQuery = useCallback(() => {
    setQueryInternal('');
    setDebouncedQuery('');
    setIsSearching(false);
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
  }, []);

  // Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  // Memoized filtered results
  const results = useMemo(() => {
    if (!debouncedQuery.trim()) {
      return items;
    }
    return items.filter((item) => searchFn(item, debouncedQuery));
  }, [items, debouncedQuery, searchFn]);

  return {
    query,
    setQuery,
    results,
    isSearching,
    resultCount: results.length,
    clearQuery,
    hasQuery: query.trim().length > 0,
  };
}

/**
 * Multi-field search helper that creates a search function for common use cases
 *
 * @param fields - Array of field accessor functions
 * @returns A search function compatible with useSearch
 *
 * @example
 * ```tsx
 * const search = useSearch(
 *   items,
 *   createMultiFieldSearch([
 *     (item) => item.title,
 *     (item) => item.description,
 *     (item) => item.tags.join(' ')
 *   ])
 * );
 * ```
 */
export function createMultiFieldSearch<T>(
  fields: ((item: T) => string | undefined | null)[]
): (item: T, query: string) => boolean {
  return (item: T, query: string) => {
    const normalizedQuery = query.toLowerCase().trim();
    if (!normalizedQuery) return true;

    // Support multiple search terms separated by spaces
    const searchTerms = normalizedQuery.split(/\s+/).filter(Boolean);

    return searchTerms.every((term) =>
      fields.some((getField) => {
        const fieldValue = getField(item);
        return fieldValue?.toLowerCase().includes(term);
      })
    );
  };
}

/**
 * Simple text search helper for single field matching
 *
 * @example
 * ```tsx
 * const search = useSearch(items, createTextSearch((item) => item.name));
 * ```
 */
export function createTextSearch<T>(
  getField: (item: T) => string | undefined | null
): (item: T, query: string) => boolean {
  return (item: T, query: string) => {
    const normalizedQuery = query.toLowerCase().trim();
    if (!normalizedQuery) return true;
    const fieldValue = getField(item);
    return fieldValue?.toLowerCase().includes(normalizedQuery) ?? false;
  };
}

export default useSearch;
