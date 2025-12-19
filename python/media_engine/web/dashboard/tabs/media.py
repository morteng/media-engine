"""
Dashboard Media Tab

Provides the media tab HTML for the Media Engine Dashboard.
"""


def get_media_tab() -> str:
    """Generate the media tab HTML with media files list and preview."""
    return """
        <div id="tab-media" style="display: none;">
            <div class="stats-grid" style="margin-bottom: 1.5rem;">
                <div class="card">
                    <div class="card-title">Audio Files</div>
                    <div class="stat" id="stat-audio">-</div>
                    <div class="stat-label">voiceovers</div>
                </div>
                <div class="card">
                    <div class="card-title">Videos</div>
                    <div class="stat" id="stat-video">-</div>
                    <div class="stat-label">rendered</div>
                </div>
                <div class="card">
                    <div class="card-title">Demos</div>
                    <div class="stat" id="stat-demos">-</div>
                    <div class="stat-label">interactive</div>
                </div>
                <div class="card">
                    <div class="card-title">Documents</div>
                    <div class="stat" id="stat-docs-output">-</div>
                    <div class="stat-label">generated</div>
                </div>
            </div>
            <div class="card">
                <div class="card-header">
                    <div class="card-title">Generated Media Files</div>
                    <div>
                        <select id="media-filter" class="lang-select" style="width: auto;" onchange="filterMedia()">
                            <option value="all">All Types</option>
                            <option value="audio">Audio</option>
                            <option value="video">Video</option>
                            <option value="demo">Interactive Demos</option>
                            <option value="captions">Captions</option>
                            <option value="document">Documents</option>
                        </select>
                    </div>
                </div>
                <div id="media-list"><div class="loading">Loading...</div></div>
            </div>
            <div id="media-preview-modal" class="media-modal" style="display: none;">
                <div class="media-modal-content">
                    <div class="media-modal-header">
                        <strong id="media-preview-title">Preview</strong>
                        <button onclick="closeMediaPreview()" style="background: none; border: none; color: var(--text); font-size: 1.5rem; cursor: pointer;">&times;</button>
                    </div>
                    <div id="media-preview-body"></div>
                </div>
            </div>
        </div>
"""
