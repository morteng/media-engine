"""
Dashboard Documents Tab

Provides the documents tab HTML for the Media Engine Dashboard.
"""


def get_documents_tab() -> str:
    """Generate the documents tab HTML with document browser and preview."""
    return """
        <div id="tab-documents" style="display: none;">
            <div class="doc-browser">
                <div class="doc-sidebar">
                    <div class="doc-sidebar-header">
                        <select id="lang-select" class="lang-select" onchange="loadDocuments()">
                        </select>
                    </div>
                    <div class="doc-list" id="doc-list">
                        <div class="loading">Loading...</div>
                    </div>
                </div>
                <div class="doc-preview">
                    <div class="doc-preview-header">
                        <div>
                            <strong id="preview-title">Select a document</strong>
                            <span id="preview-path" class="stat-label"></span>
                        </div>
                        <div class="doc-preview-tabs">
                            <button class="preview-tab active" onclick="setPreviewMode('preview')">Preview</button>
                            <button class="preview-tab" onclick="setPreviewMode('source')">Source</button>
                            <button class="preview-tab" onclick="setPreviewMode('metadata')">Metadata</button>
                        </div>
                    </div>
                    <div class="doc-preview-content preview-mode" id="preview-content">
                        <div class="empty-state">Select a document from the list to preview</div>
                    </div>
                </div>
            </div>
            <button class="export-notes-btn" id="export-notes-btn" onclick="exportSceneNotes()">Export Scene Notes</button>
        </div>
"""
