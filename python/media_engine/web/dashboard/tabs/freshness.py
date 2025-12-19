"""
Dashboard Freshness Tab

Provides the freshness tab HTML for the Media Engine Dashboard.
Shows content freshness status, stale items, ignored files, and untracked files.
"""


def get_freshness_tab() -> str:
    """Generate the freshness tab HTML with freshness report and controls."""
    return """
        <div id="tab-freshness" style="display: none;">
            <div class="card">
                <div class="card-header">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div class="card-title">Content Freshness</div>
                        <span id="freshness-status" style="font-size: 0.75rem; color: var(--text-muted);"></span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <button onclick="toggleIgnorePatterns()" style="padding: 0.4rem 0.75rem; background: var(--bg); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text); font-size: 0.8rem; cursor: pointer; display: flex; align-items: center; gap: 0.4rem;" title="Show ignore patterns">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 0.9rem; height: 0.9rem;"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                            <span>Patterns</span>
                        </button>
                        <button onclick="exportReport('freshness')" style="padding: 0.4rem 0.75rem; background: var(--bg); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text); font-size: 0.8rem; cursor: pointer; display: flex; align-items: center; gap: 0.4rem;" title="Export report">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 0.9rem; height: 0.9rem;"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
                            <span>Export</span>
                        </button>
                        <button id="freshness-scan-btn" onclick="scanFreshness()" style="padding: 0.4rem 0.75rem; background: var(--bg); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text); font-size: 0.8rem; cursor: pointer; display: flex; align-items: center; gap: 0.4rem;">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 0.9rem; height: 0.9rem;"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
                            <span>Re-scan</span>
                        </button>
                        <button id="freshness-refresh-btn" onclick="refreshFreshness()" style="padding: 0.4rem 0.75rem; background: var(--primary); border: none; border-radius: 0.25rem; color: white; font-size: 0.8rem; cursor: pointer; display: flex; align-items: center; gap: 0.4rem;">
                            <svg id="freshness-refresh-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 0.9rem; height: 0.9rem;"><path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg>
                            <span id="freshness-refresh-text">Refresh</span>
                        </button>
                    </div>
                </div>

                <!-- Summary Cards -->
                <div id="freshness-summary" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 0.75rem; margin-bottom: 1rem;">
                    <div class="stat-card" onclick="filterFreshness('all')" style="background: var(--bg); padding: 0.75rem; border-radius: 0.5rem; text-align: center; cursor: pointer; border: 2px solid transparent; transition: all 0.2s;" data-stat="all">
                        <div style="font-size: 1.5rem; font-weight: 600; color: var(--primary);" id="freshness-total">-</div>
                        <div style="font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase;">Total</div>
                    </div>
                    <div class="stat-card" onclick="filterFreshness('fresh')" style="background: var(--bg); padding: 0.75rem; border-radius: 0.5rem; text-align: center; cursor: pointer; border: 2px solid transparent; transition: all 0.2s;" data-stat="fresh">
                        <div style="font-size: 1.5rem; font-weight: 600; color: #22c55e;" id="freshness-fresh">-</div>
                        <div style="font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase;">Fresh</div>
                    </div>
                    <div class="stat-card" onclick="filterFreshness('stale')" style="background: var(--bg); padding: 0.75rem; border-radius: 0.5rem; text-align: center; cursor: pointer; border: 2px solid transparent; transition: all 0.2s;" data-stat="stale">
                        <div style="font-size: 1.5rem; font-weight: 600; color: #eab308;" id="freshness-stale">-</div>
                        <div style="font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase;">Stale</div>
                    </div>
                    <div class="stat-card" onclick="filterFreshness('expired')" style="background: var(--bg); padding: 0.75rem; border-radius: 0.5rem; text-align: center; cursor: pointer; border: 2px solid transparent; transition: all 0.2s;" data-stat="expired">
                        <div style="font-size: 1.5rem; font-weight: 600; color: #ef4444;" id="freshness-expired">-</div>
                        <div style="font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase;">Expired</div>
                    </div>
                    <div class="stat-card" onclick="filterFreshness('untracked')" style="background: var(--bg); padding: 0.75rem; border-radius: 0.5rem; text-align: center; cursor: pointer; border: 2px solid transparent; transition: all 0.2s;" data-stat="untracked">
                        <div style="font-size: 1.5rem; font-weight: 600; color: #a855f7;" id="freshness-untracked">-</div>
                        <div style="font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase;">Untracked</div>
                    </div>
                    <div class="stat-card" onclick="filterFreshness('ignored')" style="background: var(--bg); padding: 0.75rem; border-radius: 0.5rem; text-align: center; cursor: pointer; border: 2px solid transparent; transition: all 0.2s;" data-stat="ignored">
                        <div style="font-size: 1.5rem; font-weight: 600; color: #6b7280;" id="freshness-ignored">-</div>
                        <div style="font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase;">Ignored</div>
                    </div>
                </div>

                <!-- Ignore Patterns Panel (hidden by default) -->
                <div id="ignore-patterns-panel" style="display: none; background: var(--bg); border: 1px solid var(--border); border-radius: 0.5rem; padding: 1rem; margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                        <div style="font-weight: 600; font-size: 0.9rem;">Active Ignore Patterns</div>
                        <button onclick="toggleIgnorePatterns()" style="background: none; border: none; color: var(--text-muted); cursor: pointer; padding: 0.25rem;">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 1rem; height: 1rem;"><path d="M18 6L6 18M6 6l12 12"/></svg>
                        </button>
                    </div>
                    <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.5rem;">
                        Files matching these patterns are excluded from untracked detection.
                        Add patterns to <code style="background: var(--bg-card); padding: 0.15rem 0.35rem; border-radius: 3px;">.mediaignore</code> or
                        <code style="background: var(--bg-card); padding: 0.15rem 0.35rem; border-radius: 3px;">project.yaml</code>
                    </div>
                    <div id="ignore-patterns-list" style="display: flex; flex-wrap: wrap; gap: 0.5rem; max-height: 150px; overflow-y: auto;"></div>
                </div>

                <!-- Filter Controls -->
                <div style="display: flex; gap: 0.5rem; margin-bottom: 1rem; align-items: center; flex-wrap: wrap;">
                    <div style="display: flex; gap: 0.25rem; background: var(--bg); padding: 0.25rem; border-radius: 0.375rem;">
                        <button class="freshness-filter active" data-filter="all" onclick="filterFreshness('all')" style="padding: 0.35rem 0.6rem; background: var(--primary); border: none; border-radius: 0.25rem; color: white; font-size: 0.75rem; cursor: pointer; transition: all 0.2s;">All</button>
                        <button class="freshness-filter" data-filter="fresh" onclick="filterFreshness('fresh')" style="padding: 0.35rem 0.6rem; background: transparent; border: none; border-radius: 0.25rem; color: var(--text-muted); font-size: 0.75rem; cursor: pointer; transition: all 0.2s;">Fresh</button>
                        <button class="freshness-filter" data-filter="stale" onclick="filterFreshness('stale')" style="padding: 0.35rem 0.6rem; background: transparent; border: none; border-radius: 0.25rem; color: var(--text-muted); font-size: 0.75rem; cursor: pointer; transition: all 0.2s;">Stale</button>
                        <button class="freshness-filter" data-filter="expired" onclick="filterFreshness('expired')" style="padding: 0.35rem 0.6rem; background: transparent; border: none; border-radius: 0.25rem; color: var(--text-muted); font-size: 0.75rem; cursor: pointer; transition: all 0.2s;">Expired</button>
                        <button class="freshness-filter" data-filter="untracked" onclick="filterFreshness('untracked')" style="padding: 0.35rem 0.6rem; background: transparent; border: none; border-radius: 0.25rem; color: var(--text-muted); font-size: 0.75rem; cursor: pointer; transition: all 0.2s;">Untracked</button>
                        <button class="freshness-filter" data-filter="ignored" onclick="filterFreshness('ignored')" style="padding: 0.35rem 0.6rem; background: transparent; border: none; border-radius: 0.25rem; color: var(--text-muted); font-size: 0.75rem; cursor: pointer; transition: all 0.2s;">Ignored</button>
                    </div>
                    <div style="flex: 1;"></div>
                    <select id="freshness-type-filter" onchange="loadFreshness()" style="padding: 0.4rem 0.5rem; background: var(--bg); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text); font-size: 0.75rem;">
                        <option value="">All Types</option>
                        <option value="source_document">Source Documents</option>
                        <option value="translated_document">Translated Documents</option>
                        <option value="video_script">Video Scripts</option>
                        <option value="video_render">Video Renders</option>
                        <option value="voiceover_audio">Voiceover Audio</option>
                        <option value="demo_html">Demo HTML</option>
                        <option value="demo_asset">Demo Assets</option>
                        <option value="deliverable">Deliverables</option>
                        <option value="diagram_source">Diagram Sources</option>
                        <option value="diagram_render">Diagram Renders</option>
                        <option value="theme">Theme</option>
                        <option value="config">Config</option>
                    </select>
                </div>

                <!-- Content List -->
                <div id="freshness-content" style="max-height: 500px; overflow-y: auto;">
                    <div class="loading">Loading freshness data...</div>
                </div>
            </div>

            <!-- Stale Items Details Card -->
            <div class="card" id="stale-details-card" style="display: none; margin-top: 1rem;">
                <div class="card-header">
                    <div class="card-title">
                        <svg viewBox="0 0 24 24" fill="none" stroke="#eab308" stroke-width="2" style="width: 1.1rem; height: 1.1rem; vertical-align: middle; margin-right: 0.5rem;"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>
                        Stale Items - Rebuild Needed
                    </div>
                    <span style="font-size: 0.75rem; color: var(--text-muted);">These items have outdated dependencies</span>
                </div>
                <div id="stale-items-list"></div>
            </div>

            <!-- Untracked Files Card -->
            <div class="card" id="untracked-details-card" style="display: none; margin-top: 1rem;">
                <div class="card-header">
                    <div class="card-title">
                        <svg viewBox="0 0 24 24" fill="none" stroke="#a855f7" stroke-width="2" style="width: 1.1rem; height: 1.1rem; vertical-align: middle; margin-right: 0.5rem;"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M12 18v-6M9 15h6"/></svg>
                        Untracked Files
                    </div>
                    <span style="font-size: 0.75rem; color: var(--text-muted);">Files not registered in freshness tracking</span>
                </div>
                <div id="untracked-files-list" style="max-height: 400px; overflow-y: auto;"></div>
            </div>

            <!-- Ignored Files Card -->
            <div class="card" id="ignored-details-card" style="display: none; margin-top: 1rem;">
                <div class="card-header">
                    <div class="card-title">
                        <svg viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="2" style="width: 1.1rem; height: 1.1rem; vertical-align: middle; margin-right: 0.5rem;"><circle cx="12" cy="12" r="10"/><path d="m4.93 4.93 14.14 14.14"/></svg>
                        Ignored Files
                    </div>
                    <span style="font-size: 0.75rem; color: var(--text-muted);">Files excluded by ignore patterns</span>
                </div>
                <div id="ignored-files-list" style="max-height: 300px; overflow-y: auto;"></div>
            </div>
        </div>
"""
