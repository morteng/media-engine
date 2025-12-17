"""
Dashboard Quality Tab

Provides the quality tab HTML for the Media Engine Dashboard.
"""


def get_quality_tab() -> str:
    """Generate the quality tab HTML with quality report and refresh controls."""
    return """
        <div id="tab-quality" style="display: none;">
            <div class="card">
                <div class="card-header">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div class="card-title">Quality Report</div>
                        <span id="quality-status" style="font-size: 0.75rem; color: var(--text-muted);"></span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <label style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.8rem; color: var(--text-muted); cursor: pointer;">
                            <input type="checkbox" id="quality-auto-refresh" checked onchange="toggleQualityAutoRefresh()" style="cursor: pointer;">
                            Auto-refresh
                        </label>
                        <button id="quality-refresh-btn" onclick="refreshQuality()" style="padding: 0.4rem 0.75rem; background: var(--primary); border: none; border-radius: 0.25rem; color: white; font-size: 0.8rem; cursor: pointer; display: flex; align-items: center; gap: 0.4rem;">
                            <svg id="quality-refresh-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 0.9rem; height: 0.9rem;"><path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg>
                            <span id="quality-refresh-text">Re-run</span>
                        </button>
                    </div>
                </div>
                <div id="quality-report"><div class="loading">Loading...</div></div>
            </div>
        </div>
"""
