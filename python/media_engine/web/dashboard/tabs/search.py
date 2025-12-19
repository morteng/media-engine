"""
Dashboard Search Tab

Provides full-text search across all project documents.
"""


def get_search_tab() -> str:
    """Generate the search tab HTML with search controls and results."""
    return """
        <div id="tab-search" style="display: none;">
            <div class="card">
                <div class="card-header">
                    <div class="card-title">Search Documents</div>
                </div>

                <!-- Search Input -->
                <div style="margin-top: 1rem;">
                    <div style="display: flex; gap: 0.75rem;">
                        <div style="flex: 1; position: relative;">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="position: absolute; left: 0.75rem; top: 50%; transform: translateY(-50%); width: 1.1rem; height: 1.1rem; color: var(--text-muted);">
                                <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
                            </svg>
                            <input type="text" id="search-input" placeholder="Search for content, titles, or metadata..."
                                   style="width: 100%; padding: 0.75rem 0.75rem 0.75rem 2.5rem; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 0.5rem; color: var(--text); font-size: 0.95rem;"
                                   onkeyup="if(event.key==='Enter')performSearch()">
                        </div>
                        <button onclick="performSearch()" style="padding: 0.75rem 1.5rem; background: var(--primary); border: none; border-radius: 0.5rem; color: white; font-weight: 500; cursor: pointer; display: flex; align-items: center; gap: 0.5rem;">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 1rem; height: 1rem;"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
                            Search
                        </button>
                    </div>

                    <!-- Search Filters -->
                    <div style="display: flex; gap: 1rem; margin-top: 0.75rem; flex-wrap: wrap;">
                        <select id="search-lang-filter" style="padding: 0.4rem 0.75rem; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text); font-size: 0.85rem;">
                            <option value="">All Languages</option>
                        </select>
                        <select id="search-type-filter" style="padding: 0.4rem 0.75rem; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text); font-size: 0.85rem;">
                            <option value="">All Types</option>
                            <option value="chapter">Chapters</option>
                            <option value="script">Scripts</option>
                            <option value="data">Data Files</option>
                        </select>
                        <label style="display: flex; align-items: center; gap: 0.4rem; font-size: 0.85rem; color: var(--text-muted);">
                            <input type="checkbox" id="search-content-only"> Content only
                        </label>
                    </div>
                </div>
            </div>

            <!-- Search Results -->
            <div class="card" style="margin-top: 1rem;">
                <div class="card-header">
                    <div class="card-title">Results</div>
                    <span id="search-result-count" style="font-size: 0.8rem; color: var(--text-muted);"></span>
                </div>
                <div id="search-results" style="margin-top: 1rem;">
                    <div class="empty-state">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width: 3rem; height: 3rem; color: var(--text-muted); margin-bottom: 0.5rem;">
                            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
                        </svg>
                        <div>Enter a search query to find content</div>
                        <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.5rem;">
                            Tip: Use quotes for exact phrases, e.g. "user authentication"
                        </div>
                    </div>
                </div>
            </div>

            <!-- Recent Searches -->
            <div class="card" style="margin-top: 1rem;">
                <div class="card-header">
                    <div class="card-title">Recent Searches</div>
                    <button onclick="clearRecentSearches()" style="padding: 0.3rem 0.6rem; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text-muted); font-size: 0.75rem; cursor: pointer;">Clear</button>
                </div>
                <div id="recent-searches" style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 1rem;">
                    <span style="color: var(--text-muted); font-size: 0.85rem;">No recent searches</span>
                </div>
            </div>
        </div>

        <style>
            .search-result-item {
                padding: 1rem;
                border: 1px solid var(--border);
                border-radius: 0.5rem;
                margin-bottom: 0.75rem;
                cursor: pointer;
                transition: all 0.15s;
            }
            .search-result-item:hover {
                border-color: var(--primary);
                background: var(--bg-secondary);
            }
            .search-result-title {
                font-weight: 600;
                color: var(--text);
                margin-bottom: 0.25rem;
            }
            .search-result-path {
                font-size: 0.75rem;
                color: var(--text-muted);
                margin-bottom: 0.5rem;
            }
            .search-result-snippet {
                font-size: 0.85rem;
                color: var(--text);
                line-height: 1.5;
            }
            .search-result-snippet mark {
                background: #fef08a;
                color: #000;
                padding: 0.1rem 0.2rem;
                border-radius: 0.15rem;
            }
            .search-tag {
                display: inline-block;
                padding: 0.3rem 0.6rem;
                background: var(--bg-secondary);
                border: 1px solid var(--border);
                border-radius: 1rem;
                font-size: 0.8rem;
                color: var(--text);
                cursor: pointer;
                transition: all 0.15s;
            }
            .search-tag:hover {
                border-color: var(--primary);
                color: var(--primary);
            }
        </style>
"""
