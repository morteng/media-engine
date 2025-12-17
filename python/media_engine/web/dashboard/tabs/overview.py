"""
Dashboard Overview Tab

Provides the overview tab HTML for the Media Engine Dashboard.
"""


def get_overview_tab() -> str:
    """Generate the overview tab HTML with project statistics and matrix."""
    return """
        <div id="tab-overview">
            <div class="grid grid-4" style="margin-bottom: 1.5rem;">
                <div class="card">
                    <div class="card-title">Documents</div>
                    <div class="stat" id="stat-docs">-</div>
                    <div class="stat-label" id="stat-docs-detail">total documents</div>
                </div>
                <div class="card">
                    <div class="card-title">Languages</div>
                    <div class="stat" id="stat-langs">-</div>
                    <div class="stat-label">configured</div>
                </div>
                <div class="card">
                    <div class="card-title">Translations</div>
                    <div class="stat" id="stat-trans">-</div>
                    <div class="stat-label" id="stat-trans-detail">synced</div>
                </div>
                <div class="card">
                    <div class="card-title">Quality</div>
                    <div class="stat" id="stat-quality">-</div>
                    <div class="stat-label" id="stat-quality-detail">issues</div>
                </div>
            </div>

            <div class="grid grid-2">
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">Translation Matrix</div>
                    </div>
                    <div id="matrix-container"><div class="loading">Loading...</div></div>
                </div>
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">Recent Issues</div>
                    </div>
                    <div id="issues-container"><div class="loading">Loading...</div></div>
                </div>
            </div>
        </div>
"""
