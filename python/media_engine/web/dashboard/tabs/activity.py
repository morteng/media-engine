"""
Dashboard Activity Tab

Provides the activity tab HTML for the Media Engine Dashboard.
"""


def get_activity_tab() -> str:
    """Generate the activity tab HTML with audit log display."""
    return """
        <div id="tab-activity" style="display: none;">
            <div class="card">
                <div class="card-header">
                    <div class="card-title">Audit Log</div>
                </div>
                <div id="audit-log"><div class="loading">Loading...</div></div>
            </div>
        </div>
"""
