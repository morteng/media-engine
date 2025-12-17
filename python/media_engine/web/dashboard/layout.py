"""
Dashboard Layout Components

Provides HTML layout functions for the Media Engine Dashboard.
"""


def get_body_start() -> str:
    """Generate the dashboard body start HTML with header and navigation tabs."""
    return """<body>
    <div class="container">
        <header>
            <div style="display: flex; align-items: center; gap: 1rem;">
                <div class="project-selector">
                    <button class="project-selector-btn" onclick="toggleProjectDropdown()" id="project-selector-btn">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>
                        <span class="project-selector-name" id="project-selector-name">Loading...</span>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 0.75rem; height: 0.75rem;"><path d="M6 9l6 6 6-6"/></svg>
                    </button>
                    <div class="project-dropdown" id="project-dropdown">
                        <div class="project-dropdown-header">Recent Projects</div>
                        <div class="project-list" id="project-list">
                            <div class="loading" style="padding: 1rem;">Loading...</div>
                        </div>
                        <div class="project-dropdown-footer">
                            <button class="open-project-btn" onclick="promptOpenProject()">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
                                Open Project...
                            </button>
                        </div>
                    </div>
                </div>
                <div>
                    <h1 id="project-name" style="font-size: 1.25rem;">Media Engine Dashboard</h1>
                    <span class="stat-label" id="project-path"></span>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <div class="users-online" id="users-online"></div>
                <button class="theme-toggle" id="theme-toggle" onclick="toggleTheme()" title="Toggle theme"></button>
            </div>
        </header>

        <div class="tabs">
            <button class="tab active" onclick="showTab('overview')">Overview</button>
            <button class="tab" onclick="showTab('documents')">Documents</button>
            <button class="tab" onclick="showTab('media')">Media</button>
            <button class="tab" onclick="showTab('packs')">Packs</button>
            <button class="tab" onclick="showTab('assets')">Assets</button>
            <button class="tab" onclick="showTab('translations')">Translations</button>
            <button class="tab" onclick="showTab('quality')">Quality</button>
            <button class="tab" onclick="showTab('activity')">Activity</button>
        </div>
"""


def get_body_end() -> str:
    """Generate the dashboard body end HTML."""
    return """
    </div>
"""
