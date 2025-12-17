"""
Dashboard Packs Tab

Provides the packs tab HTML for the Media Engine Dashboard.
"""


def get_packs_tab() -> str:
    """Generate the packs tab HTML with investor and pilot pack generators."""
    return """
        <div id="tab-packs" style="display: none;">
            <div class="grid grid-2" style="margin-bottom: 1.5rem;">
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">Investor Pack</div>
                        <button class="media-btn media-btn-primary" onclick="generatePack('investor')">Generate ZIP</button>
                    </div>
                    <div class="stat-label" style="margin-bottom: 1rem;">Materials for investor presentations</div>
                    <div id="investor-pack-contents"><div class="loading">Loading...</div></div>
                </div>
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">Pilot Customer Pack</div>
                        <button class="media-btn media-btn-primary" onclick="generatePack('pilot')">Generate ZIP</button>
                    </div>
                    <div class="stat-label" style="margin-bottom: 1rem;">Materials for pilot customer engagement</div>
                    <div id="pilot-pack-contents"><div class="loading">Loading...</div></div>
                </div>
            </div>
            <div class="card">
                <div class="card-header">
                    <div class="card-title">Document Registry</div>
                </div>
                <div id="registry-overview"><div class="loading">Loading...</div></div>
            </div>
        </div>
"""
