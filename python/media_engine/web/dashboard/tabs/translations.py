"""
Dashboard Translations Tab

Provides the translations tab HTML for the Media Engine Dashboard.
"""


def get_translations_tab() -> str:
    """Generate the translations tab HTML with translation status table."""
    return """
        <div id="tab-translations" style="display: none;">
            <div class="card">
                <div class="card-header">
                    <div class="card-title">All Translations</div>
                </div>
                <div id="translations-table"><div class="loading">Loading...</div></div>
            </div>
        </div>
"""
