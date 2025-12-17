"""
Dashboard Assets Tab

Provides the assets tab HTML for the Media Engine Dashboard.
"""


def get_assets_tab() -> str:
    """Generate the assets tab HTML with asset statistics and grid."""
    return """
        <div id="tab-assets" style="display: none;">
            <div class="grid grid-4" style="margin-bottom: 1.5rem;">
                <div class="card">
                    <div class="card-title">Diagrams</div>
                    <div class="stat" id="stat-diagrams">-</div>
                    <div class="stat-label">architecture & flow</div>
                </div>
                <div class="card">
                    <div class="card-title">Logos</div>
                    <div class="stat" id="stat-logos">-</div>
                    <div class="stat-label">brand assets</div>
                </div>
                <div class="card">
                    <div class="card-title">Video Assets</div>
                    <div class="stat" id="stat-video-assets">-</div>
                    <div class="stat-label">thumbnails & clips</div>
                </div>
                <div class="card">
                    <div class="card-title">Total Assets</div>
                    <div class="stat" id="stat-total-assets">-</div>
                    <div class="stat-label">all files</div>
                </div>
            </div>
            <div class="card">
                <div class="card-header">
                    <div class="card-title">All Assets</div>
                </div>
                <div class="media-grid" id="assets-grid"><div class="loading">Loading...</div></div>
            </div>
        </div>
"""
