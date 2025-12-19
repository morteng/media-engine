"""
Dashboard JavaScript

Provides all JavaScript functionality for the Media Engine Dashboard.
"""


def get_javascript() -> str:
    """Generate all dashboard JavaScript including WebSocket handling and UI interactions."""
    return """
    <script>
        const API_BASE = '';
        let ws = null;
        const userId = 'user-' + Math.random().toString(36).substr(2, 9);

        async function fetchAPI(endpoint) {
            const res = await fetch(API_BASE + endpoint);
            return res.json();
        }

        async function postAPI(endpoint, data) {
            const params = new URLSearchParams(data);
            const res = await fetch(API_BASE + endpoint + '?' + params.toString(), { method: 'POST' });
            return res.json();
        }

        async function deleteAPI(endpoint, data) {
            const params = new URLSearchParams(data);
            const res = await fetch(API_BASE + endpoint + '?' + params.toString(), { method: 'DELETE' });
            return res.json();
        }

        // Project Switching Functions
        let currentProjectPath = '';

        function toggleProjectDropdown() {
            const dropdown = document.getElementById('project-dropdown');
            const isOpen = dropdown.classList.contains('open');
            if (isOpen) {
                dropdown.classList.remove('open');
            } else {
                dropdown.classList.add('open');
                loadRecentProjects();
            }
        }

        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            const selector = document.querySelector('.project-selector');
            const dropdown = document.getElementById('project-dropdown');
            if (selector && !selector.contains(e.target)) {
                dropdown.classList.remove('open');
            }
        });

        async function loadRecentProjects() {
            const data = await fetchAPI('/api/recent-projects');
            const list = document.getElementById('project-list');

            if (data.current) {
                currentProjectPath = data.current.path;
            }

            if (!data.recent || data.recent.length === 0) {
                list.innerHTML = '<div style="padding: 1rem; text-align: center; color: var(--text-muted);">No recent projects</div>';
                return;
            }

            let html = '';
            for (const proj of data.recent) {
                const isCurrent = proj.path === currentProjectPath;
                const classes = ['project-item'];
                if (isCurrent) classes.push('current');
                if (!proj.exists) classes.push('missing');

                html += '<div class="' + classes.join(' ') + '" data-path="' + escapeHtml(proj.path) + '">';
                html += '<div class="project-item-icon">';
                html += '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>';
                html += '</div>';
                html += '<div class="project-item-info" onclick="switchProject(\\'' + escapeHtml(proj.path) + '\\')">';
                html += '<div class="project-item-name">' + escapeHtml(proj.name) + (isCurrent ? ' (current)' : '') + '</div>';
                html += '<div class="project-item-path">' + escapeHtml(proj.path) + '</div>';
                html += '</div>';
                if (!isCurrent) {
                    html += '<button class="project-item-remove" onclick="event.stopPropagation(); removeRecentProject(\\'' + escapeHtml(proj.path) + '\\')" title="Remove from recent">';
                    html += '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M18 6L6 18M6 6l12 12"/></svg>';
                    html += '</button>';
                }
                html += '</div>';
            }
            list.innerHTML = html;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        async function switchProject(path) {
            if (path === currentProjectPath) {
                document.getElementById('project-dropdown').classList.remove('open');
                return;
            }

            try {
                const result = await postAPI('/api/open-project', { path: path });
                if (result.status === 'switched') {
                    // Reload all dashboard data
                    document.getElementById('project-dropdown').classList.remove('open');
                    location.reload();
                }
            } catch (err) {
                alert('Failed to switch project: ' + err.message);
            }
        }

        async function removeRecentProject(path) {
            try {
                await deleteAPI('/api/recent-projects', { path: path });
                loadRecentProjects();
            } catch (err) {
                console.error('Failed to remove project:', err);
            }
        }

        async function promptOpenProject() {
            // Show loading state
            const btn = document.querySelector('.open-project-btn');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<svg class="spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation: spin 1s linear infinite;"><circle cx="12" cy="12" r="10" stroke-opacity="0.25"/><path d="M12 2a10 10 0 0110 10" stroke-opacity="1"/></svg> Waiting for selection...';
            btn.disabled = true;

            try {
                const result = await postAPI('/api/browse-project', {});

                if (result.status === 'selected') {
                    switchProject(result.path);
                } else if (result.status === 'invalid') {
                    alert('Invalid project folder: ' + result.error);
                } else if (result.status === 'prompt' || result.status === 'cancelled') {
                    // Fallback to manual prompt
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                    const path = prompt('Enter the path to a project folder:');
                    if (path && path.trim()) {
                        switchProject(path.trim());
                    }
                    return;
                }
            } catch (err) {
                // Fallback to prompt if browse fails
                const path = prompt('Enter the path to a project folder:');
                if (path && path.trim()) {
                    switchProject(path.trim());
                }
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        }

        async function loadProject() {
            const data = await fetchAPI('/api/project');
            document.getElementById('project-name').textContent = data.name;
            document.getElementById('project-path').textContent = data.root;
            document.getElementById('stat-langs').textContent = Object.keys(data.languages).length;
            // Update project selector
            document.getElementById('project-selector-name').textContent = data.name;
            currentProjectPath = data.root;
        }

        async function loadStatus() {
            const data = await fetchAPI('/api/status');
            // Count ALL documents, not just chapters
            let totalDocs = 0;
            let details = [];
            for (const lang in data.content) {
                const langData = data.content[lang];
                // Sum all document types
                const chapters = langData.chapters || 0;
                const scripts = langData.scripts || 0;
                const diagrams = langData.diagrams || 0;
                const slides = langData.slides || 0;
                totalDocs += chapters + scripts + diagrams + slides;
            }
            document.getElementById('stat-docs').textContent = totalDocs;
            // Show breakdown if there are multiple languages
            const langCount = Object.keys(data.content).length;
            document.getElementById('stat-docs-detail').textContent = langCount > 1
                ? 'across ' + langCount + ' languages'
                : 'total documents';
        }

        async function loadTranslations() {
            const data = await fetchAPI('/api/translations');
            document.getElementById('stat-trans').textContent = data.current + '/' + data.total;
            document.getElementById('stat-trans-detail').textContent =
                data.outdated > 0 ? data.outdated + ' outdated' : 'all synced';

            // Full table
            let html = '<table><thead><tr><th>Source</th><th>Translation</th><th>Status</th><th>Version</th></tr></thead><tbody>';
            for (const t of data.translations) {
                const statusClass = t.is_outdated ? 'status-warn' : 'status-ok';
                html += '<tr>';
                html += '<td>' + t.source_title + '</td>';
                html += '<td>' + t.translation_title + ' (' + t.target_language + ')</td>';
                html += '<td><span class="status-badge ' + statusClass + '">' + t.status + '</span></td>';
                html += '<td>' + t.translated_version + ' / ' + t.source_version + '</td>';
                html += '</tr>';
            }
            html += '</tbody></table>';
            document.getElementById('translations-table').innerHTML = html;
        }

        async function loadMatrix() {
            const data = await fetchAPI('/api/translations/matrix');
            let html = '<table><thead><tr><th>Document</th>';
            for (const lang of data.languages) {
                html += '<th style="text-align:center">' + lang.toUpperCase() + '</th>';
            }
            html += '</tr></thead><tbody>';

            for (const doc of data.documents) {
                html += '<tr><td title="' + doc.source_path + '">' + doc.title + '</td>';
                for (const lang of data.languages) {
                    const t = doc.translations[lang];
                    const cellClass = 'cell-' + t.status;
                    const icon = t.status === 'source' ? 'S' :
                                 t.status === 'current' ? '\\u2713' :
                                 t.status === 'outdated' ? '!' : '?';
                    html += '<td style="text-align:center"><span class="matrix-cell ' + cellClass + '">' + icon + '</span></td>';
                }
                html += '</tr>';
            }
            html += '</tbody></table>';
            document.getElementById('matrix-container').innerHTML = html;
        }

        let qualityAutoRefresh = true;
        let qualityRefreshInterval = null;
        let isQualityLoading = false;

        async function loadQuality(showSpinner = true) {
            if (isQualityLoading) return;
            isQualityLoading = true;

            const btn = document.getElementById('quality-refresh-btn');
            const icon = document.getElementById('quality-refresh-icon');
            const text = document.getElementById('quality-refresh-text');

            if (showSpinner && btn) {
                btn.disabled = true;
                icon.style.animation = 'spin 1s linear infinite';
                text.textContent = 'Running...';
            }

            try {
                const data = await fetchAPI('/api/quality');
                const qualityStat = document.getElementById('stat-quality');
                const qualityDetail = document.getElementById('stat-quality-detail');
                if (data.total === 0) {
                    qualityStat.textContent = '✓';
                    qualityStat.style.color = 'var(--success)';
                    qualityDetail.textContent = 'all checks passed';
                } else {
                    qualityStat.textContent = data.total;
                    qualityStat.style.color = data.errors > 0 ? 'var(--error)' : 'var(--warning)';
                    qualityDetail.textContent = data.errors > 0 ? data.errors + ' errors' : data.warnings + ' warnings';
                }

                // Update status timestamp
                const statusEl = document.getElementById('quality-status');
                if (statusEl) {
                    const now = new Date();
                    statusEl.textContent = 'Last checked: ' + now.toLocaleTimeString();
                }

                // Issues list
                let html = '';
                const recentIssues = data.issues.slice(0, 5);
                if (recentIssues.length === 0) {
                    html = '<div style="color: var(--success);">No issues found</div>';
                }
                for (const issue of recentIssues) {
                    const issueClass = issue.severity === 'error' ? 'issue-error' : 'issue-warning';
                    const clickable = issue.file ? ' issue-clickable' : '';
                    const onclick = issue.file ? ' onclick="openIssueFile(\\'' + issue.file.replace(/'/g, "\\\\'") + '\\', ' + (issue.line || 0) + ')"' : '';
                    html += '<div class="issue ' + issueClass + clickable + '"' + onclick + '>';
                    html += '<strong>' + issue.category + '</strong>: ' + issue.message;
                    if (issue.file) html += '<br><small class="issue-file">' + issue.file + '</small>';
                    html += '</div>';
                }
                document.getElementById('issues-container').innerHTML = html;

                // Full report
                let reportHtml = '<div style="margin-bottom: 1rem; display: flex; gap: 1rem;">';
                reportHtml += '<span style="color: var(--error);">Errors: ' + data.errors + '</span>';
                reportHtml += '<span style="color: var(--warning);">Warnings: ' + data.warnings + '</span>';
                reportHtml += '<span style="color: var(--text-muted);">Info: ' + data.info + '</span>';
                reportHtml += '</div>';

                if (data.issues.length === 0) {
                    reportHtml += '<div style="color: var(--success); padding: 2rem; text-align: center;">All quality checks passed!</div>';
                }

                for (const issue of data.issues) {
                    const issueClass = issue.severity === 'error' ? 'issue-error' : 'issue-warning';
                    const clickable = issue.file ? ' issue-clickable' : '';
                    const onclick = issue.file ? ' onclick="openIssueFile(\\'' + issue.file.replace(/'/g, "\\\\'") + '\\', ' + (issue.line || 0) + ')"' : '';
                    reportHtml += '<div class="issue ' + issueClass + clickable + '"' + onclick + '>';
                    reportHtml += '<strong>' + issue.category + '</strong>: ' + issue.message;
                    if (issue.file) reportHtml += '<br><small class="issue-file">' + issue.file + (issue.line ? ':' + issue.line : '') + '</small>';
                    reportHtml += '</div>';
                }
                document.getElementById('quality-report').innerHTML = reportHtml;
            } finally {
                isQualityLoading = false;
                if (btn) {
                    btn.disabled = false;
                    icon.style.animation = '';
                    text.textContent = 'Re-run';
                }
            }
        }

        function refreshQuality() {
            loadQuality(true);
        }

        function toggleQualityAutoRefresh() {
            const checkbox = document.getElementById('quality-auto-refresh');
            qualityAutoRefresh = checkbox.checked;

            if (qualityAutoRefresh) {
                startQualityAutoRefresh();
            } else {
                stopQualityAutoRefresh();
            }
        }

        function startQualityAutoRefresh() {
            if (qualityRefreshInterval) clearInterval(qualityRefreshInterval);
            // Auto-refresh every 30 seconds
            qualityRefreshInterval = setInterval(() => {
                const qualityTab = document.getElementById('tab-quality-report');
                if (qualityAutoRefresh && qualityTab && qualityTab.style.display !== 'none') {
                    loadQuality(false);
                }
            }, 30000);
        }

        function stopQualityAutoRefresh() {
            if (qualityRefreshInterval) {
                clearInterval(qualityRefreshInterval);
                qualityRefreshInterval = null;
            }
        }

        async function loadAuditLog() {
            try {
                const data = await fetchAPI('/api/audit-log');
                let html = '<table><thead><tr><th>Time</th><th>Action</th><th>User</th><th>Details</th></tr></thead><tbody>';
                for (const entry of data.entries.reverse().slice(0, 50)) {
                    html += '<tr>';
                    html += '<td>' + new Date(entry.timestamp).toLocaleString() + '</td>';
                    html += '<td>' + entry.action + '</td>';
                    html += '<td>' + (entry.user || '-') + '</td>';
                    html += '<td>' + (entry.details || '-') + '</td>';
                    html += '</tr>';
                }
                html += '</tbody></table>';
                document.getElementById('audit-log').innerHTML = html || '<div>No audit entries</div>';
            } catch (e) {
                document.getElementById('audit-log').innerHTML = '<div>Audit log not available</div>';
            }
        }

        async function loadFreshnessOverview() {
            try {
                const data = await fetchAPI('/api/freshness');
                const total = data.total_items;
                const stale = data.stale_count + data.expired_count;

                const statFreshness = document.getElementById('stat-freshness');
                const statDetail = document.getElementById('stat-freshness-detail');
                const card = document.getElementById('freshness-overview-card');

                if (statFreshness) statFreshness.textContent = total;

                if (stale > 0) {
                    if (statDetail) {
                        statDetail.textContent = stale + ' need attention';
                        statDetail.style.color = '#eab308';
                    }
                    if (card) card.style.borderColor = '#eab308';
                } else {
                    if (statDetail) {
                        statDetail.textContent = 'all fresh';
                        statDetail.style.color = '#22c55e';
                    }
                    if (card) card.style.borderColor = '';
                }
            } catch (e) {
                const statFreshness = document.getElementById('stat-freshness');
                const statDetail = document.getElementById('stat-freshness-detail');
                if (statFreshness) statFreshness.textContent = '-';
                if (statDetail) statDetail.textContent = 'not available';
            }
        }

        // State management for active tabs
        let activeMainTab = 'overview';
        let activeSubTabs = {
            'content': 'documents',
            'quality': 'quality-report'
        };

        function showTab(name, evt) {
            // Hide all main tab content
            document.querySelectorAll('[id^="tab-"]').forEach(el => el.style.display = 'none');

            // Update main tab button states
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            // Find and activate the clicked tab button
            const clickedTab = evt?.target || document.querySelector('.tab[onclick*="' + name + '"]');
            if (clickedTab) clickedTab.classList.add('active');

            // Hide all sub-tab containers and dropdowns
            document.querySelectorAll('.subtabs').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.subtabs-dropdown').forEach(el => el.style.display = 'none');

            activeMainTab = name;

            // Handle sections with sub-tabs
            if (name === 'content') {
                // Show sub-tabs (desktop) or dropdown (mobile)
                const subtabsContent = document.getElementById('subtabs-content');
                const subtabsDropdown = document.getElementById('subtabs-dropdown-content');
                if (window.innerWidth > 768) {
                    if (subtabsContent) subtabsContent.style.display = 'flex';
                } else {
                    if (subtabsDropdown) subtabsDropdown.style.display = 'block';
                }

                const activeSubTab = activeSubTabs['content'];
                const tabEl = document.getElementById('tab-' + activeSubTab);
                if (tabEl) tabEl.style.display = 'block';
                updateSubTabStates('content', activeSubTab);

                // Lazy load
                if (activeSubTab === 'documents' && !documentsLoaded) {
                    initDocumentBrowser();
                }
                if (activeSubTab === 'media' && !mediaLoaded) {
                    loadMedia();
                }
                if (activeSubTab === 'packs' && !packsLoaded) {
                    loadPacks();
                }
                if (activeSubTab === 'assets' && !assetsLoaded) {
                    loadAssets();
                }
            } else if (name === 'quality') {
                // Show sub-tabs (desktop) or dropdown (mobile)
                const subtabsQuality = document.getElementById('subtabs-quality');
                const subtabsDropdownQuality = document.getElementById('subtabs-dropdown-quality');
                if (window.innerWidth > 768) {
                    if (subtabsQuality) subtabsQuality.style.display = 'flex';
                } else {
                    if (subtabsDropdownQuality) subtabsDropdownQuality.style.display = 'block';
                }

                const activeSubTab = activeSubTabs['quality'];
                const qualityTabEl = document.getElementById('tab-' + activeSubTab);
                if (qualityTabEl) qualityTabEl.style.display = 'block';
                updateSubTabStates('quality', activeSubTab);
            } else {
                // Simple standalone tabs
                const standaloneTab = document.getElementById('tab-' + name);
                if (standaloneTab) standaloneTab.style.display = 'block';

                // Existing lazy load logic
                if (name === 'insights' && !insightsLoaded) {
                    loadInsights();
                }
                if (name === 'build' && !buildLoaded) {
                    loadBuildStatus();
                }
                if (name === 'search' && !searchLoaded) {
                    initSearch();
                }
            }
        }

        function showSubTab(section, subTabName) {
            // Hide all content within this section
            const tabIds = {
                'content': ['documents', 'media', 'packs', 'assets', 'translations'],
                'quality': ['quality-report', 'freshness', 'provenance', 'dependencies']
            };

            tabIds[section].forEach(id => {
                const el = document.getElementById('tab-' + id);
                if (el) el.style.display = 'none';
            });

            // Show selected sub-tab content
            const targetTab = document.getElementById('tab-' + subTabName);
            if (targetTab) {
                targetTab.style.display = 'block';
            }

            // Remember active sub-tab
            activeSubTabs[section] = subTabName;

            // Update sub-tab button states
            updateSubTabStates(section, subTabName);

            // Update mobile dropdown
            const dropdown = document.getElementById('subtabs-select-' + section);
            if (dropdown) {
                dropdown.value = subTabName;
            }

            // Trigger lazy loading
            if (subTabName === 'documents' && !documentsLoaded) {
                initDocumentBrowser();
            }
            if (subTabName === 'media' && !mediaLoaded) {
                loadMedia();
            }
            if (subTabName === 'packs' && !packsLoaded) {
                loadPacks();
            }
            if (subTabName === 'assets' && !assetsLoaded) {
                loadAssets();
            }
            if (subTabName === 'freshness' && !freshnessLoaded) {
                loadFreshness();
            }
            if (subTabName === 'provenance' && !provenanceLoaded) {
                loadProvenance();
            }
            if (subTabName === 'dependencies' && !depsLoaded) {
                loadDependencies();
            }
        }

        function updateSubTabStates(section, activeSubTab) {
            const container = document.getElementById('subtabs-' + section);
            if (!container) return;

            container.querySelectorAll('.subtab').forEach(btn => {
                btn.classList.remove('active');
                const onclick = btn.getAttribute('onclick');
                if (onclick && onclick.includes("'" + activeSubTab + "'")) {
                    btn.classList.add('active');
                }
            });
        }

        function onSubTabDropdownChange(section) {
            const select = document.getElementById('subtabs-select-' + section);
            if (select) {
                showSubTab(section, select.value);
            }
        }

        // Handle window resize (switch between desktop/mobile sub-tab display)
        window.addEventListener('resize', () => {
            const subtabsContent = document.getElementById('subtabs-content');
            const subtabsDropdownContent = document.getElementById('subtabs-dropdown-content');
            const subtabsQuality = document.getElementById('subtabs-quality');
            const subtabsDropdownQuality = document.getElementById('subtabs-dropdown-quality');

            if (activeMainTab === 'content') {
                if (window.innerWidth > 768) {
                    if (subtabsContent) subtabsContent.style.display = 'flex';
                    if (subtabsDropdownContent) subtabsDropdownContent.style.display = 'none';
                } else {
                    if (subtabsContent) subtabsContent.style.display = 'none';
                    if (subtabsDropdownContent) subtabsDropdownContent.style.display = 'block';
                }
            } else if (activeMainTab === 'quality') {
                if (window.innerWidth > 768) {
                    if (subtabsQuality) subtabsQuality.style.display = 'flex';
                    if (subtabsDropdownQuality) subtabsDropdownQuality.style.display = 'none';
                } else {
                    if (subtabsQuality) subtabsQuality.style.display = 'none';
                    if (subtabsDropdownQuality) subtabsDropdownQuality.style.display = 'block';
                }
            }
        });

        // Freshness tab state
        let freshnessLoaded = false;
        let freshnessData = null;
        let currentFreshnessFilter = 'all';
        let ignorePatternsVisible = false;

        function toggleIgnorePatterns() {
            const panel = document.getElementById('ignore-patterns-panel');
            ignorePatternsVisible = !ignorePatternsVisible;
            panel.style.display = ignorePatternsVisible ? 'block' : 'none';
        }

        function updateIgnorePatternsPanel() {
            const list = document.getElementById('ignore-patterns-list');
            if (!freshnessData || !freshnessData.ignore_patterns) {
                list.innerHTML = '<span style="color: var(--text-muted); font-size: 0.8rem;">No ignore patterns configured</span>';
                return;
            }

            let html = '';
            for (const pattern of freshnessData.ignore_patterns) {
                html += `<span style="display: inline-block; background: var(--bg-card); border: 1px solid var(--border); padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; font-family: monospace; color: var(--text-muted);">${escapeHtml(pattern)}</span>`;
            }
            list.innerHTML = html || '<span style="color: var(--text-muted); font-size: 0.8rem;">No ignore patterns configured</span>';
        }

        async function loadFreshness(showSpinner = true) {
            const content = document.getElementById('freshness-content');
            const btn = document.getElementById('freshness-refresh-btn');
            const icon = document.getElementById('freshness-refresh-icon');
            const text = document.getElementById('freshness-refresh-text');

            if (showSpinner) {
                content.innerHTML = '<div class="loading">Loading freshness data...</div>';
                if (btn) {
                    btn.disabled = true;
                    icon.style.animation = 'spin 1s linear infinite';
                    text.textContent = 'Loading...';
                }
            }

            try {
                const typeFilter = document.getElementById('freshness-type-filter').value;
                const url = typeFilter ? `/api/freshness?content_type=${typeFilter}` : '/api/freshness';
                freshnessData = await fetchAPI(url);
                freshnessLoaded = true;

                // Update summary stats
                document.getElementById('freshness-total').textContent = freshnessData.total_items;
                document.getElementById('freshness-fresh').textContent = freshnessData.fresh_count;
                document.getElementById('freshness-stale').textContent = freshnessData.stale_count;
                document.getElementById('freshness-expired').textContent = freshnessData.expired_count;
                document.getElementById('freshness-untracked').textContent = freshnessData.untracked_count;
                document.getElementById('freshness-ignored').textContent = freshnessData.ignored_count || 0;

                // Update status
                const issues = freshnessData.stale_count + freshnessData.expired_count;
                document.getElementById('freshness-status').textContent =
                    issues > 0
                        ? `${issues} item${issues !== 1 ? 's' : ''} need attention`
                        : 'All content is fresh';

                // Update ignore patterns panel
                updateIgnorePatternsPanel();

                renderFreshnessContent();
                updateFreshnessDetails();

            } catch (e) {
                content.innerHTML = '<div class="empty-state">Error loading freshness data</div>';
            } finally {
                if (btn) {
                    btn.disabled = false;
                    icon.style.animation = '';
                    text.textContent = 'Refresh';
                }
            }
        }

        function renderFreshnessContent() {
            const content = document.getElementById('freshness-content');
            if (!freshnessData) return;

            let items = freshnessData.items;

            // Apply filter
            if (currentFreshnessFilter === 'fresh') {
                items = items.filter(i => i.status === 'fresh');
            } else if (currentFreshnessFilter === 'stale') {
                items = items.filter(i => i.status === 'stale');
            } else if (currentFreshnessFilter === 'expired') {
                items = items.filter(i => i.status === 'expired');
            } else if (currentFreshnessFilter === 'untracked') {
                // Show untracked files instead
                if (!freshnessData.untracked_files || freshnessData.untracked_files.length === 0) {
                    content.innerHTML = '<div class="empty-state">No untracked files found</div>';
                    return;
                }
                let html = '<table><thead><tr><th>Untracked File</th><th>Suggestion</th></tr></thead><tbody>';
                for (const file of freshnessData.untracked_files) {
                    const filePath = typeof file === 'object' ? file.path : file;
                    const suggestion = typeof file === 'object' ? file.suggestion : '';
                    const suggestionBadge = suggestion === 'track'
                        ? '<span style="font-size: 0.7rem; background: #22c55e20; color: #22c55e; padding: 0.15rem 0.4rem; border-radius: 0.25rem;">Track</span>'
                        : suggestion === 'ignore'
                        ? '<span style="font-size: 0.7rem; background: #6b728020; color: #6b7280; padding: 0.15rem 0.4rem; border-radius: 0.25rem;">Ignore</span>'
                        : '<span style="font-size: 0.7rem; color: var(--text-muted);">-</span>';
                    html += `<tr><td style="color: #a855f7;" title="${escapeHtml(filePath)}">${escapeHtml(filePath.split('/').pop())}</td><td>${suggestionBadge}</td></tr>`;
                }
                html += '</tbody></table>';
                content.innerHTML = html;
                return;
            } else if (currentFreshnessFilter === 'ignored') {
                // Show ignored files
                if (!freshnessData.ignored_files || freshnessData.ignored_files.length === 0) {
                    content.innerHTML = '<div class="empty-state">No ignored files found</div>';
                    return;
                }
                let html = '<table><thead><tr><th>Ignored File</th></tr></thead><tbody>';
                for (const file of freshnessData.ignored_files) {
                    html += `<tr><td style="color: #6b7280;" title="${escapeHtml(file)}">${escapeHtml(file.split('/').pop())}</td></tr>`;
                }
                html += '</tbody></table>';
                content.innerHTML = html;
                return;
            }

            if (items.length === 0) {
                content.innerHTML = '<div class="empty-state">No items match the current filter</div>';
                return;
            }

            let html = '<table><thead><tr><th>Path</th><th>Type</th><th>Status</th><th>Modified</th></tr></thead><tbody>';
            for (const item of items) {
                const statusColor = {
                    'fresh': '#22c55e',
                    'stale': '#eab308',
                    'expired': '#ef4444',
                    'missing': '#9ca3af'
                }[item.status] || 'var(--text)';

                const typeLabel = item.content_type.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase());
                const modified = item.last_modified ? new Date(item.last_modified).toLocaleDateString() : '-';

                html += `<tr>
                    <td title="${escapeHtml(item.path)}">${escapeHtml(item.path.split('/').pop())}</td>
                    <td><span style="font-size: 0.7rem; background: var(--bg-secondary); padding: 0.2rem 0.4rem; border-radius: 0.25rem;">${typeLabel}</span></td>
                    <td><span style="color: ${statusColor}; font-weight: 500;">${item.status}</span></td>
                    <td style="color: var(--text-muted); font-size: 0.8rem;">${modified}</td>
                </tr>`;
            }
            html += '</tbody></table>';
            content.innerHTML = html;
        }

        function updateFreshnessDetails() {
            // Stale items card
            const staleCard = document.getElementById('stale-details-card');
            const staleList = document.getElementById('stale-items-list');
            if (freshnessData.stale_items && freshnessData.stale_items.length > 0) {
                staleCard.style.display = 'block';
                let html = '<table><thead><tr><th>Item</th><th>Type</th><th>Dependencies</th></tr></thead><tbody>';
                for (const item of freshnessData.stale_items) {
                    const deps = item.depends_on.map(d => d.split('/').pop()).join(', ');
                    html += `<tr>
                        <td style="color: #eab308;">${escapeHtml(item.path.split('/').pop())}</td>
                        <td>${item.content_type.replace(/_/g, ' ')}</td>
                        <td style="font-size: 0.75rem; color: var(--text-muted);">${deps || '-'}</td>
                    </tr>`;
                }
                html += '</tbody></table>';
                staleList.innerHTML = html;
            } else {
                staleCard.style.display = 'none';
            }

            // Untracked files card
            const untrackedCard = document.getElementById('untracked-details-card');
            const untrackedList = document.getElementById('untracked-files-list');
            if (freshnessData.untracked_files && freshnessData.untracked_files.length > 0) {
                untrackedCard.style.display = 'block';
                let html = '<div style="padding: 0.5rem;">';
                for (const file of freshnessData.untracked_files.slice(0, 50)) {
                    const filePath = typeof file === 'object' ? file.path : file;
                    const suggestion = typeof file === 'object' ? file.suggestion : '';
                    const suggestionBadge = suggestion === 'track'
                        ? ' <span style="font-size: 0.65rem; background: #22c55e20; color: #22c55e; padding: 0.1rem 0.3rem; border-radius: 0.2rem; margin-left: 0.5rem;">suggest track</span>'
                        : suggestion === 'ignore'
                        ? ' <span style="font-size: 0.65rem; background: #6b728020; color: #6b7280; padding: 0.1rem 0.3rem; border-radius: 0.2rem; margin-left: 0.5rem;">suggest ignore</span>'
                        : '';
                    html += `<div style="padding: 0.3rem 0; font-size: 0.8rem; color: #a855f7;" title="${escapeHtml(filePath)}">${escapeHtml(filePath.split('/').pop())}${suggestionBadge}</div>`;
                }
                if (freshnessData.untracked_files.length > 50) {
                    html += `<div style="padding: 0.5rem 0; font-size: 0.8rem; color: var(--text-muted);">... and ${freshnessData.untracked_files.length - 50} more</div>`;
                }
                html += '</div>';
                untrackedList.innerHTML = html;
            } else {
                untrackedCard.style.display = 'none';
            }

            // Ignored files card
            const ignoredCard = document.getElementById('ignored-details-card');
            const ignoredList = document.getElementById('ignored-files-list');
            if (freshnessData.ignored_files && freshnessData.ignored_files.length > 0) {
                ignoredCard.style.display = 'block';
                let html = '<div style="padding: 0.5rem;">';
                for (const file of freshnessData.ignored_files.slice(0, 30)) {
                    html += `<div style="padding: 0.3rem 0; font-size: 0.8rem; color: #6b7280;" title="${escapeHtml(file)}">${escapeHtml(file.split('/').pop())}</div>`;
                }
                if (freshnessData.ignored_files.length > 30) {
                    html += `<div style="padding: 0.5rem 0; font-size: 0.8rem; color: var(--text-muted);">... and ${freshnessData.ignored_files.length - 30} more</div>`;
                }
                html += '</div>';
                ignoredList.innerHTML = html;
            } else {
                ignoredCard.style.display = 'none';
            }
        }

        function filterFreshness(filter) {
            currentFreshnessFilter = filter;

            // Update filter button styles
            document.querySelectorAll('.freshness-filter').forEach(btn => {
                if (btn.dataset.filter === filter) {
                    btn.style.background = 'var(--primary)';
                    btn.style.color = 'white';
                } else {
                    btn.style.background = 'transparent';
                    btn.style.color = 'var(--text-muted)';
                }
            });

            // Update stat card highlighting
            document.querySelectorAll('#freshness-summary .stat-card').forEach(card => {
                if (card.dataset.stat === filter) {
                    card.style.borderColor = 'var(--primary)';
                    card.style.background = 'var(--bg-secondary)';
                } else {
                    card.style.borderColor = 'transparent';
                    card.style.background = 'var(--bg)';
                }
            });

            renderFreshnessContent();
        }

        function refreshFreshness() {
            loadFreshness(true);
        }

        async function scanFreshness() {
            const btn = document.getElementById('freshness-scan-btn');
            btn.disabled = true;
            btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 0.9rem; height: 0.9rem; animation: spin 1s linear infinite;"><path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg><span>Scanning...</span>';

            try {
                await fetchAPI('/api/freshness/scan', { method: 'POST' });
                await loadFreshness(true);
            } catch (e) {
                console.error('Scan failed:', e);
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 0.9rem; height: 0.9rem;"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg><span>Re-scan</span>';
            }
        }

        // ==================== PROVENANCE TAB ====================
        let provenanceLoaded = false;
        let provenanceData = null;
        let provenanceFilter = 'all';

        async function loadProvenance(showSpinner = true) {
            if (showSpinner) {
                document.getElementById('provenance-claims').innerHTML = '<div class="loading">Loading provenance data...</div>';
            }

            const refreshBtn = document.getElementById('provenance-refresh-btn');
            const refreshIcon = document.getElementById('provenance-refresh-icon');
            refreshBtn.disabled = true;
            refreshIcon.style.animation = 'spin 1s linear infinite';

            try {
                const [report, claims, approvals, reviewQueue] = await Promise.all([
                    fetchAPI('/api/provenance'),
                    fetchAPI('/api/provenance/claims'),
                    fetchAPI('/api/provenance/approvals'),
                    fetchAPI('/api/provenance/review-queue'),
                ]);

                provenanceLoaded = true;
                provenanceData = { report, claims: claims.claims, approvals: approvals.by_status, reviewQueue: reviewQueue.queue };

                // Update summary
                document.getElementById('provenance-total-docs').textContent = report.summary.total_documents;
                document.getElementById('provenance-total-claims').textContent = report.summary.total_claims;
                document.getElementById('provenance-verified').textContent = report.summary.verified_claims;
                document.getElementById('provenance-unverified').textContent = report.summary.unverified_claims;
                document.getElementById('provenance-expired').textContent = report.summary.expired_claims;
                document.getElementById('provenance-expiring').textContent = report.summary.expiring_soon;

                // Update approval status
                for (const status of ['draft', 'in_review', 'changes_requested', 'approved', 'published']) {
                    const count = approvals.by_status[status]?.count || 0;
                    const elemId = 'status-' + status.replace('_', '-');
                    const elem = document.getElementById(elemId);
                    if (elem) elem.textContent = count;
                }

                // Update status text
                const statusEl = document.getElementById('provenance-status');
                statusEl.textContent = 'Last updated: ' + new Date().toLocaleTimeString();

                // Render content
                renderProvenanceClaims();
                renderReviewQueue();

            } catch (e) {
                console.error('Failed to load provenance:', e);
                document.getElementById('provenance-claims').innerHTML = '<div class="empty-state">Failed to load provenance data</div>';
            } finally {
                refreshBtn.disabled = false;
                refreshIcon.style.animation = '';
            }
        }

        function renderProvenanceClaims() {
            if (!provenanceData || !provenanceData.claims) return;

            const container = document.getElementById('provenance-claims');
            const typeFilter = document.getElementById('provenance-type-filter').value;

            let filtered = provenanceData.claims;

            // Apply status filter
            if (provenanceFilter === 'unverified') {
                filtered = filtered.filter(c => c.status === 'unverified');
            } else if (provenanceFilter === 'expired') {
                filtered = filtered.filter(c => c.is_expired);
            } else if (provenanceFilter === 'expiring') {
                filtered = filtered.filter(c => c.days_until_expiry !== null && c.days_until_expiry > 0 && c.days_until_expiry <= 30);
            } else if (provenanceFilter === 'verified') {
                filtered = filtered.filter(c => c.status === 'verified' && !c.is_expired);
            }

            // Apply type filter
            if (typeFilter) {
                filtered = filtered.filter(c => c.source_type === typeFilter);
            }

            if (filtered.length === 0) {
                container.innerHTML = '<div class="empty-state">No claims match the current filter</div>';
                return;
            }

            let html = '<table><thead><tr><th>Document</th><th>Claim</th><th>Source</th><th>Status</th><th>Expires</th><th>Actions</th></tr></thead><tbody>';
            for (const claim of filtered) {
                const statusClass = getClaimStatusClass(claim);
                const statusText = getClaimStatusText(claim);
                const expiryText = claim.expires ? formatExpiryDate(claim.expires, claim.days_until_expiry) : '-';

                html += `<tr>
                    <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(claim.document_path)}">${escapeHtml(claim.document_path.split('/').pop())}</td>
                    <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis;" title="${escapeHtml(claim.text)}">${escapeHtml(claim.text.substring(0, 80))}${claim.text.length > 80 ? '...' : ''}</td>
                    <td>
                        ${claim.source_url ?
                            `<a href="${escapeHtml(claim.source_url)}" target="_blank" style="color: var(--primary);">${escapeHtml(claim.source)}</a>` :
                            escapeHtml(claim.source)}
                        <span class="status-badge" style="margin-left: 0.25rem; font-size: 0.6rem;">${claim.source_type}</span>
                    </td>
                    <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                    <td style="color: var(--text-muted); font-size: 0.8rem;">${expiryText}</td>
                    <td>
                        ${claim.status === 'unverified' ?
                            `<button onclick="verifyClaim('${escapeHtml(claim.document_path)}', '${claim.claim_id}')" class="action-btn" title="Verify claim">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 0.9rem; height: 0.9rem;"><path d="M20 6L9 17l-5-5"/></svg>
                            </button>` :
                            claim.is_expired ?
                                `<button onclick="renewClaim('${escapeHtml(claim.document_path)}', '${claim.claim_id}')" class="action-btn" title="Renew verification">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 0.9rem; height: 0.9rem;"><path d="M23 4v6h-6M1 20v-6h6"/></svg>
                                </button>` : ''}
                    </td>
                </tr>`;
            }
            html += '</tbody></table>';
            container.innerHTML = html;
        }

        function getClaimStatusClass(claim) {
            if (claim.is_expired) return 'status-error';
            if (claim.status === 'unverified') return 'status-warn';
            if (claim.days_until_expiry !== null && claim.days_until_expiry <= 30) return 'status-warn';
            return 'status-ok';
        }

        function getClaimStatusText(claim) {
            if (claim.is_expired) return 'Expired';
            if (claim.status === 'unverified') return 'Unverified';
            if (claim.days_until_expiry !== null && claim.days_until_expiry <= 30) return 'Expiring';
            return 'Verified';
        }

        function formatExpiryDate(expires, daysLeft) {
            const date = new Date(expires);
            const formatted = date.toLocaleDateString();
            if (daysLeft !== null && daysLeft >= 0) {
                return `${formatted} (${daysLeft}d)`;
            }
            return formatted;
        }

        function renderReviewQueue() {
            const container = document.getElementById('review-queue');
            const queue = provenanceData?.reviewQueue || [];

            if (queue.length === 0) {
                container.innerHTML = '<div class="empty-state">No documents in review</div>';
                return;
            }

            let html = '<table><thead><tr><th>Document</th><th>Requested By</th><th>Issues</th><th>Actions</th></tr></thead><tbody>';
            for (const doc of queue) {
                const issues = [];
                if (doc.unverified_claims > 0) issues.push(`${doc.unverified_claims} unverified`);
                if (doc.expired_claims > 0) issues.push(`${doc.expired_claims} expired`);

                html += `<tr>
                    <td>${escapeHtml(doc.document_path.split('/').pop())}</td>
                    <td>${escapeHtml(doc.requester || '-')}</td>
                    <td>${issues.length > 0 ? `<span class="status-badge status-warn">${issues.join(', ')}</span>` : '<span class="status-badge status-ok">Ready</span>'}</td>
                    <td style="display: flex; gap: 0.25rem;">
                        <button onclick="approveDocument('${escapeHtml(doc.document_path)}')" class="action-btn" title="Approve" ${issues.length > 0 ? 'disabled' : ''}>
                            <svg viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2" style="width: 0.9rem; height: 0.9rem;"><path d="M20 6L9 17l-5-5"/></svg>
                        </button>
                        <button onclick="rejectDocument('${escapeHtml(doc.document_path)}')" class="action-btn" title="Request changes">
                            <svg viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" style="width: 0.9rem; height: 0.9rem;"><path d="M18 6L6 18M6 6l12 12"/></svg>
                        </button>
                    </td>
                </tr>`;
            }
            html += '</tbody></table>';
            container.innerHTML = html;
        }

        function filterProvenance(filter) {
            provenanceFilter = filter;

            document.querySelectorAll('.provenance-filter').forEach(btn => {
                if (btn.dataset.filter === filter) {
                    btn.style.background = 'var(--primary)';
                    btn.style.color = 'white';
                    btn.style.border = 'none';
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                    btn.style.background = 'var(--bg-secondary)';
                    btn.style.color = 'var(--text)';
                    btn.style.border = '1px solid var(--border)';
                }
            });

            renderProvenanceClaims();
        }

        function filterApprovalStatus(status) {
            // Show documents with this approval status
            const docs = provenanceData?.approvals[status]?.documents || [];
            if (docs.length === 0) {
                showToast(`No documents with status: ${status}`, 'info');
                return;
            }
            showToast(`${docs.length} document(s) with status: ${status}`, 'info');
        }

        function refreshProvenance() {
            loadProvenance(true);
        }

        async function verifyClaim(documentPath, claimId) {
            const verifier = prompt('Enter your name to verify this claim:');
            if (!verifier) return;

            try {
                const res = await fetch('/api/provenance/claims/verify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        document_path: documentPath,
                        claim_id: claimId,
                        verifier: verifier,
                        expiry_days: 365
                    })
                });
                if (res.ok) {
                    showToast('Claim verified successfully', 'success');
                    loadProvenance();
                } else {
                    showToast('Failed to verify claim', 'error');
                }
            } catch (e) {
                showToast('Error: ' + e.message, 'error');
            }
        }

        async function renewClaim(documentPath, claimId) {
            const verifier = prompt('Enter your name to renew this claim verification:');
            if (!verifier) return;

            try {
                const res = await fetch('/api/provenance/claims/verify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        document_path: documentPath,
                        claim_id: claimId,
                        verifier: verifier,
                        expiry_days: 365
                    })
                });
                if (res.ok) {
                    showToast('Claim renewed successfully', 'success');
                    loadProvenance();
                } else {
                    showToast('Failed to renew claim', 'error');
                }
            } catch (e) {
                showToast('Error: ' + e.message, 'error');
            }
        }

        async function approveDocument(documentPath) {
            const approver = prompt('Enter your name to approve this document:');
            if (!approver) return;

            try {
                const res = await fetch('/api/provenance/approve', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        document_path: documentPath,
                        user: approver
                    })
                });
                if (res.ok) {
                    showToast('Document approved', 'success');
                    loadProvenance();
                } else {
                    showToast('Failed to approve document', 'error');
                }
            } catch (e) {
                showToast('Error: ' + e.message, 'error');
            }
        }

        async function rejectDocument(documentPath) {
            const reviewer = prompt('Enter your name:');
            if (!reviewer) return;
            const comments = prompt('Enter reason for requesting changes:');
            if (!comments) return;

            try {
                const res = await fetch('/api/provenance/reject', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        document_path: documentPath,
                        user: reviewer,
                        comments: comments
                    })
                });
                if (res.ok) {
                    showToast('Changes requested', 'success');
                    loadProvenance();
                } else {
                    showToast('Failed to request changes', 'error');
                }
            } catch (e) {
                showToast('Error: ' + e.message, 'error');
            }
        }

        async function scanDocumentsForClaims() {
            showToast('Scanning documents for claims...', 'info');
            try {
                const res = await fetch('/api/provenance/scan', { method: 'POST' });
                const data = await res.json();

                const card = document.getElementById('claim-scan-card');
                const results = document.getElementById('claim-scan-results');

                if (data.total_claims_found === 0) {
                    showToast('No potential claims found', 'info');
                    card.style.display = 'none';
                    return;
                }

                let html = `<div style="padding: 0.75rem; background: var(--bg-secondary); border-radius: 0.25rem; margin-bottom: 0.5rem;">
                    Found <strong>${data.total_claims_found}</strong> potential claims in <strong>${data.documents_scanned}</strong> documents
                </div>`;

                for (const [docPath, claims] of Object.entries(data.results)) {
                    html += `<div style="border-bottom: 1px solid var(--border); padding: 0.5rem 0;">
                        <div style="font-weight: 500; margin-bottom: 0.25rem;">${escapeHtml(docPath)}</div>`;
                    for (const claim of claims) {
                        html += `<div style="font-size: 0.8rem; color: var(--text-muted); margin-left: 1rem; margin-bottom: 0.25rem;">
                            <span class="status-badge">${claim.type}</span>
                            "${escapeHtml(claim.match)}"
                        </div>`;
                    }
                    html += '</div>';
                }

                results.innerHTML = html;
                card.style.display = 'block';
                showToast(`Found ${data.total_claims_found} potential claims`, 'success');
            } catch (e) {
                showToast('Scan failed: ' + e.message, 'error');
            }
        }

        async function validateAllUrls() {
            showToast('Validating source URLs...', 'info');
            try {
                const res = await fetch('/api/provenance/validate-urls', { method: 'POST' });
                const data = await res.json();

                const card = document.getElementById('url-validation-card');
                const results = document.getElementById('url-validation-results');

                if (data.total_urls === 0) {
                    showToast('No URLs to validate', 'info');
                    card.style.display = 'none';
                    return;
                }

                let html = `<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; margin-bottom: 1rem;">
                    <div style="text-align: center; padding: 0.5rem; background: var(--bg-secondary); border-radius: 0.25rem;">
                        <div style="font-size: 1.25rem; font-weight: 600;">${data.total_urls}</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">Total URLs</div>
                    </div>
                    <div style="text-align: center; padding: 0.5rem; background: var(--bg-secondary); border-radius: 0.25rem;">
                        <div style="font-size: 1.25rem; font-weight: 600; color: #22c55e;">${data.valid}</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">Valid</div>
                    </div>
                    <div style="text-align: center; padding: 0.5rem; background: var(--bg-secondary); border-radius: 0.25rem;">
                        <div style="font-size: 1.25rem; font-weight: 600; color: #ef4444;">${data.invalid}</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">Invalid</div>
                    </div>
                </div>`;

                if (data.results.length > 0) {
                    html += '<table><thead><tr><th>URL</th><th>Status</th><th>Claims</th></tr></thead><tbody>';
                    for (const result of data.results) {
                        const statusClass = result.valid ? 'status-ok' : 'status-error';
                        const statusText = result.valid ? `OK (${result.status})` : `Error: ${result.error || 'Unknown'}`;
                        html += `<tr>
                            <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis;">
                                <a href="${escapeHtml(result.url)}" target="_blank" style="color: var(--primary);">${escapeHtml(result.url)}</a>
                            </td>
                            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                            <td>${result.claims?.length || 0} claim(s)</td>
                        </tr>`;
                    }
                    html += '</tbody></table>';
                }

                results.innerHTML = html;
                card.style.display = 'block';
                showToast(`Validation complete: ${data.valid} valid, ${data.invalid} invalid`, data.invalid > 0 ? 'warning' : 'success');
            } catch (e) {
                showToast('Validation failed: ' + e.message, 'error');
            }
        }

        // ==================== BUILD TAB ====================
        let buildLoaded = false;

        async function loadBuildStatus() {
            try {
                const data = await fetchAPI('/api/build/status');
                buildLoaded = true;

                // Update freshness warning
                const warningBanner = document.getElementById('build-freshness-warning');
                if (data.freshness_warning) {
                    warningBanner.style.display = 'block';
                    document.getElementById('build-freshness-message').textContent = data.freshness_warning.message;
                } else {
                    warningBanner.style.display = 'none';
                }

                // Update status badge
                const badge = document.getElementById('build-status-badge');
                badge.style.display = 'inline-block';
                if (data.active) {
                    badge.textContent = 'Building...';
                    badge.className = 'status-badge status-warn';
                } else {
                    badge.textContent = 'Ready';
                    badge.className = 'status-badge status-ok';
                }

                // Update status content
                const statusContent = document.getElementById('build-status-content');
                if (data.last_build) {
                    statusContent.innerHTML = `
                        <div style="font-size: 0.85rem; color: var(--text-muted);">
                            Last build: ${new Date(data.last_build).toLocaleString()}
                        </div>
                    `;
                }

                // Update outputs
                renderBuildOutputs(data.outputs);

                // Populate language checkboxes
                const langContainer = document.getElementById('build-languages');
                const projectData = await fetchAPI('/api/project');
                langContainer.innerHTML = '';
                for (const lang of Object.keys(projectData.languages)) {
                    langContainer.innerHTML += `
                        <label class="build-format-checkbox">
                            <input type="checkbox" id="build-lang-${lang}" checked> ${lang.toUpperCase()}
                        </label>
                    `;
                }

            } catch (e) {
                console.error('Failed to load build status:', e);
            }
        }

        function renderBuildOutputs(outputs) {
            const container = document.getElementById('build-outputs');
            if (!outputs || outputs.length === 0) {
                container.innerHTML = '<div class="empty-state">No output files yet</div>';
                return;
            }

            let html = '<table><thead><tr><th>File</th><th>Format</th><th>Language</th><th>Size</th><th>Modified</th></tr></thead><tbody>';
            for (const out of outputs) {
                html += `<tr>
                    <td>${escapeHtml(out.name)}</td>
                    <td><span class="status-badge">${out.format}</span></td>
                    <td>${out.language.toUpperCase()}</td>
                    <td>${formatSize(out.size)}</td>
                    <td style="color: var(--text-muted);">${new Date(out.modified).toLocaleDateString()}</td>
                </tr>`;
            }
            html += '</tbody></table>';
            container.innerHTML = html;
        }

        function formatSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        }

        async function startBuild() {
            const btn = document.getElementById('build-start-btn');
            btn.disabled = true;
            btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 1.1rem; height: 1.1rem; animation: spin 1s linear infinite;"><path d="M23 4v6h-6M1 20v-6h6"/></svg> Building...';

            // Gather selected formats
            const formats = [];
            if (document.getElementById('build-html').checked) formats.push('html');
            if (document.getElementById('build-pdf').checked) formats.push('pdf');
            if (document.getElementById('build-pptx').checked) formats.push('pptx');
            if (document.getElementById('build-xlsx').checked) formats.push('xlsx');

            // Gather selected languages
            const languages = [];
            document.querySelectorAll('[id^="build-lang-"]').forEach(cb => {
                if (cb.checked) languages.push(cb.id.replace('build-lang-', ''));
            });

            const force = document.getElementById('build-force').checked;

            try {
                const params = new URLSearchParams({
                    formats: formats.join(','),
                    languages: languages.join(','),
                    force: force,
                });
                await fetchAPI('/api/build/start?' + params, { method: 'POST' });
                showToast('Build started', 'success');

                // Clear log and start polling
                document.getElementById('build-log').innerHTML = '<div style="color: var(--text-muted);">Build starting...</div>';
                pollBuildStatus();
            } catch (e) {
                showToast('Failed to start build: ' + e.message, 'error');
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 1.1rem; height: 1.1rem;"><polygon points="5 3 19 12 5 21 5 3"/></svg> Start Build';
            }
        }

        async function pollBuildStatus() {
            const data = await fetchAPI('/api/build/status');
            updateBuildLog(data.logs);
            if (data.active) {
                setTimeout(pollBuildStatus, 1000);
            } else {
                loadBuildStatus();
            }
        }

        function updateBuildLog(logs) {
            const container = document.getElementById('build-log');
            let html = '';
            for (const entry of logs) {
                const levelClass = 'build-log-' + entry.level;
                html += `<div class="build-log-entry ${levelClass}">[${new Date(entry.timestamp).toLocaleTimeString()}] ${escapeHtml(entry.message)}</div>`;
            }
            container.innerHTML = html || '<div style="color: var(--text-muted);">No log entries</div>';
            container.scrollTop = container.scrollHeight;
        }

        function clearBuildLog() {
            document.getElementById('build-log').innerHTML = '<div style="color: var(--text-muted);">Build output will appear here...</div>';
        }

        function refreshBuildStatus() {
            loadBuildStatus();
        }

        // ==================== SEARCH TAB ====================
        let searchLoaded = false;
        let recentSearches = JSON.parse(localStorage.getItem('recentSearches') || '[]');

        async function initSearch() {
            searchLoaded = true;

            // Populate language filter
            const langSelect = document.getElementById('search-lang-filter');
            const projectData = await fetchAPI('/api/project');
            for (const lang of Object.keys(projectData.languages)) {
                langSelect.innerHTML += `<option value="${lang}">${lang.toUpperCase()} - ${projectData.languages[lang].name}</option>`;
            }

            // Load recent searches
            renderRecentSearches();
        }

        function renderRecentSearches() {
            const container = document.getElementById('recent-searches');
            if (recentSearches.length === 0) {
                container.innerHTML = '<span style="color: var(--text-muted); font-size: 0.85rem;">No recent searches</span>';
                return;
            }

            container.innerHTML = recentSearches.map(q =>
                `<span class="search-tag" onclick="quickSearch('${escapeHtml(q)}')">${escapeHtml(q)}</span>`
            ).join('');
        }

        function quickSearch(query) {
            document.getElementById('search-input').value = query;
            performSearch();
        }

        async function performSearch() {
            const query = document.getElementById('search-input').value.trim();
            if (!query) return;

            // Add to recent searches
            recentSearches = [query, ...recentSearches.filter(q => q !== query)].slice(0, 10);
            localStorage.setItem('recentSearches', JSON.stringify(recentSearches));
            renderRecentSearches();

            const resultsContainer = document.getElementById('search-results');
            resultsContainer.innerHTML = '<div class="loading">Searching...</div>';

            try {
                const lang = document.getElementById('search-lang-filter').value;
                const type = document.getElementById('search-type-filter').value;
                const params = new URLSearchParams({ q: query });
                if (lang) params.set('lang', lang);
                if (type) params.set('type', type);

                const data = await fetchAPI('/api/search?' + params);

                document.getElementById('search-result-count').textContent = `${data.total} results`;

                if (data.results.length === 0) {
                    resultsContainer.innerHTML = '<div class="empty-state">No results found for "' + escapeHtml(query) + '"</div>';
                    return;
                }

                let html = '';
                for (const result of data.results) {
                    html += `
                        <div class="search-result-item" onclick="openSearchResult('${escapeHtml(result.path)}')">
                            <div class="search-result-title">${escapeHtml(result.title)}</div>
                            <div class="search-result-path">${escapeHtml(result.path)} - ${result.language.toUpperCase()} - ${result.type}</div>
                            <div class="search-result-snippet">${result.snippet || ''}</div>
                        </div>
                    `;
                }
                resultsContainer.innerHTML = html;

            } catch (e) {
                resultsContainer.innerHTML = '<div class="empty-state">Search failed: ' + e.message + '</div>';
            }
        }

        function openSearchResult(path) {
            // Switch to documents tab and open the file
            showTab('documents');
            // Try to load the document
            setTimeout(() => {
                if (typeof loadDocumentDirect === 'function') {
                    loadDocumentDirect(path, 'chapter');
                }
            }, 100);
        }

        function clearRecentSearches() {
            recentSearches = [];
            localStorage.removeItem('recentSearches');
            renderRecentSearches();
        }

        // ==================== DEPENDENCIES TAB ====================
        let depsLoaded = false;
        let depsData = null;

        async function loadDependencies() {
            depsLoaded = true;
            const content = document.getElementById('deps-content');
            content.innerHTML = '<div class="loading">Loading dependencies...</div>';

            try {
                depsData = await fetchAPI('/api/dependencies');
                updateDepsView();

                // Populate impact analysis file selector
                const filesData = await fetchAPI('/api/dependencies/files');
                const select = document.getElementById('impact-file-select');
                select.innerHTML = '<option value="">Select a file...</option>';
                for (const file of filesData.files) {
                    select.innerHTML += `<option value="${escapeHtml(file.path)}">${escapeHtml(file.path)}</option>`;
                }
            } catch (e) {
                content.innerHTML = '<div class="empty-state">Failed to load dependencies: ' + e.message + '</div>';
            }
        }

        function updateDepsView() {
            const mode = document.getElementById('deps-view-mode').value;
            const content = document.getElementById('deps-content');
            const impactCard = document.getElementById('impact-analysis-card');

            impactCard.style.display = mode === 'impact' ? 'block' : 'none';

            if (!depsData) return;

            if (mode === 'tree') {
                renderDepsTree(content);
            } else if (mode === 'list') {
                renderDepsList(content);
            } else if (mode === 'impact') {
                renderDepsTree(content);
            }
        }

        function renderDepsTree(container) {
            if (!depsData.tree || depsData.tree.length === 0) {
                container.innerHTML = '<div class="empty-state">No dependencies tracked yet. Run freshness scan first.</div>';
                return;
            }

            let html = '';
            for (const group of depsData.tree) {
                html += `
                    <div class="dep-tree-node">
                        <div style="font-weight: 600; padding: 0.5rem; background: var(--bg-secondary); border-radius: 0.25rem; margin-bottom: 0.5rem;">
                            ${escapeHtml(group.name)} <span style="color: var(--text-muted); font-weight: normal;">(${group.count})</span>
                        </div>
                        <div class="dep-tree-children">
                `;
                for (const item of group.children.slice(0, 20)) {
                    const staleClass = item.status === 'stale' ? 'stale' : '';
                    html += `
                        <div class="dep-tree-item ${staleClass}">
                            <span class="dep-type-badge dep-type-${item.item_type}">${item.item_type.replace(/_/g, ' ')}</span>
                            <span style="flex: 1;">${escapeHtml(item.path.split('/').pop())}</span>
                            ${item.deps_count > 0 ? `<span style="font-size: 0.75rem; color: var(--text-muted);">${item.deps_count} deps</span>` : ''}
                        </div>
                    `;
                }
                if (group.children.length > 20) {
                    html += `<div style="padding: 0.5rem; color: var(--text-muted); font-size: 0.85rem;">... and ${group.children.length - 20} more</div>`;
                }
                html += '</div></div>';
            }
            container.innerHTML = html;
        }

        function renderDepsList(container) {
            if (!depsData.items || depsData.items.length === 0) {
                container.innerHTML = '<div class="empty-state">No dependencies tracked</div>';
                return;
            }

            // Show items with dependencies
            const withDeps = depsData.items.filter(i => i.depends_on.length > 0);

            let html = '<div style="margin-bottom: 1rem; color: var(--text-muted); font-size: 0.85rem;">Showing items with dependencies</div>';
            for (const item of withDeps.slice(0, 30)) {
                html += `
                    <div class="dep-list-item">
                        <div>
                            <div style="font-weight: 500;">${escapeHtml(item.path.split('/').pop())}</div>
                            <div style="font-size: 0.75rem; color: var(--text-muted);">${item.type.replace(/_/g, ' ')}</div>
                        </div>
                        <div class="dep-arrow">→</div>
                        <div style="text-align: right;">
                            <div style="font-size: 0.85rem;">${item.depends_on.length} dependencies</div>
                            <div style="font-size: 0.75rem; color: var(--text-muted);">${item.dependents.length} dependents</div>
                        </div>
                    </div>
                `;
            }
            container.innerHTML = html;
        }

        async function analyzeImpact() {
            const path = document.getElementById('impact-file-select').value;
            if (!path) {
                showToast('Please select a file', 'warning');
                return;
            }

            const resultsDiv = document.getElementById('impact-results');
            const listDiv = document.getElementById('impact-items-list');
            resultsDiv.style.display = 'block';
            listDiv.innerHTML = '<div class="loading">Analyzing...</div>';

            try {
                const data = await fetchAPI('/api/dependencies/impact/' + encodeURIComponent(path));

                if (data.affected.length === 0) {
                    listDiv.innerHTML = '<div style="color: var(--text-muted);">No items depend on this file</div>';
                } else {
                    let html = '';
                    for (const item of data.affected) {
                        html += `
                            <div style="padding: 0.5rem; border: 1px solid var(--border); border-radius: 0.25rem; margin-bottom: 0.5rem;">
                                <span class="dep-type-badge dep-type-${item.type}">${item.type.replace(/_/g, ' ')}</span>
                                <span style="margin-left: 0.5rem;">${escapeHtml(item.path)}</span>
                            </div>
                        `;
                    }
                    listDiv.innerHTML = html;
                }
            } catch (e) {
                listDiv.innerHTML = '<div style="color: #ef4444;">Failed: ' + e.message + '</div>';
            }
        }

        function refreshDependencies() {
            loadDependencies();
        }

        // ==================== TOAST NOTIFICATIONS ====================
        function showToast(message, type = 'info') {
            const container = document.getElementById('toast-container') || createToastContainer();

            const toast = document.createElement('div');
            toast.className = 'toast toast-' + type;
            toast.innerHTML = `
                <span>${escapeHtml(message)}</span>
                <button onclick="this.parentElement.remove()" style="background: none; border: none; color: inherit; cursor: pointer; padding: 0; margin-left: 0.5rem;">&times;</button>
            `;

            container.appendChild(toast);

            // Auto-remove after 4 seconds
            setTimeout(() => {
                toast.style.animation = 'slideOut 0.3s ease forwards';
                setTimeout(() => toast.remove(), 300);
            }, 4000);
        }

        function createToastContainer() {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = 'position: fixed; bottom: 1rem; right: 1rem; z-index: 9999; display: flex; flex-direction: column; gap: 0.5rem;';
            document.body.appendChild(container);

            // Add toast styles
            const style = document.createElement('style');
            style.textContent = `
                .toast {
                    padding: 0.75rem 1rem;
                    border-radius: 0.5rem;
                    display: flex;
                    align-items: center;
                    animation: slideIn 0.3s ease;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                }
                .toast-info { background: #3b82f6; color: white; }
                .toast-success { background: #22c55e; color: white; }
                .toast-warning { background: #f59e0b; color: white; }
                .toast-error { background: #ef4444; color: white; }
                @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
                @keyframes slideOut { from { transform: translateX(0); opacity: 1; } to { transform: translateX(100%); opacity: 0; } }
            `;
            document.head.appendChild(style);

            return container;
        }

        // ==================== KEYBOARD SHORTCUTS ====================
        document.addEventListener('keydown', function(e) {
            // Ignore if typing in input
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

            // Ctrl/Cmd + number for tabs
            if ((e.ctrlKey || e.metaKey) && e.key >= '1' && e.key <= '9') {
                e.preventDefault();
                const tabs = ['overview', 'documents', 'media', 'packs', 'assets', 'translations', 'quality', 'freshness', 'build', 'search', 'dependencies', 'activity'];
                const idx = parseInt(e.key) - 1;
                if (idx < tabs.length) {
                    showTab(tabs[idx]);
                    document.querySelectorAll('.tab')[idx].classList.add('active');
                }
            }

            // Ctrl/Cmd + K for search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                showTab('search');
                document.getElementById('search-input').focus();
            }

            // Ctrl/Cmd + B for build
            if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
                e.preventDefault();
                showTab('build');
            }

            // ? for keyboard shortcuts help
            if (e.key === '?' && !e.ctrlKey && !e.metaKey) {
                showKeyboardShortcuts();
            }
        });

        function showKeyboardShortcuts() {
            const shortcuts = [
                ['Ctrl/Cmd + 1-9', 'Switch tabs'],
                ['Ctrl/Cmd + K', 'Open search'],
                ['Ctrl/Cmd + B', 'Open build'],
                ['?', 'Show this help'],
            ];

            let html = '<div style="padding: 1rem;"><h3 style="margin-bottom: 1rem;">Keyboard Shortcuts</h3><table>';
            for (const [key, desc] of shortcuts) {
                html += `<tr><td style="padding: 0.25rem 1rem 0.25rem 0; font-family: monospace; background: var(--bg-secondary); padding: 0.25rem 0.5rem; border-radius: 0.25rem;">${key}</td><td>${desc}</td></tr>`;
            }
            html += '</table></div>';

            showModal('Keyboard Shortcuts', html);
        }

        function showModal(title, content) {
            const existing = document.getElementById('modal-overlay');
            if (existing) existing.remove();

            const modal = document.createElement('div');
            modal.id = 'modal-overlay';
            modal.style.cssText = 'position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 10000;';
            modal.onclick = (e) => { if (e.target === modal) modal.remove(); };

            modal.innerHTML = `
                <div style="background: var(--bg-card); border-radius: 0.5rem; max-width: 500px; max-height: 80vh; overflow: auto; box-shadow: 0 20px 40px rgba(0,0,0,0.3);">
                    <div style="padding: 1rem; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center;">
                        <strong>${escapeHtml(title)}</strong>
                        <button onclick="this.closest('#modal-overlay').remove()" style="background: none; border: none; font-size: 1.5rem; cursor: pointer; color: var(--text-muted);">&times;</button>
                    </div>
                    ${content}
                </div>
            `;

            document.body.appendChild(modal);
        }

        // ==================== EXPORT REPORTS ====================
        async function exportReport(type) {
            showToast('Generating ' + type + ' report...', 'info');

            try {
                let data, filename, content;

                if (type === 'freshness') {
                    data = await fetchAPI('/api/freshness');
                    filename = 'freshness-report.json';
                    content = JSON.stringify(data, null, 2);
                } else if (type === 'quality') {
                    data = await fetchAPI('/api/quality');
                    filename = 'quality-report.json';
                    content = JSON.stringify(data, null, 2);
                } else if (type === 'dependencies') {
                    data = await fetchAPI('/api/dependencies');
                    filename = 'dependencies-report.json';
                    content = JSON.stringify(data, null, 2);
                }

                downloadFile(content, filename, 'application/json');
                showToast('Report downloaded!', 'success');
            } catch (e) {
                showToast('Export failed: ' + e.message, 'error');
            }
        }

        function downloadFile(content, filename, mimeType) {
            const blob = new Blob([content], { type: mimeType });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            URL.revokeObjectURL(url);
        }

        // ==================== BATCH ACTIONS ====================
        let selectedStaleItems = new Set();

        function toggleStaleItemSelection(path) {
            if (selectedStaleItems.has(path)) {
                selectedStaleItems.delete(path);
            } else {
                selectedStaleItems.add(path);
            }
            updateBatchActionButton();
        }

        function selectAllStaleItems() {
            if (freshnessData && freshnessData.stale_items) {
                for (const item of freshnessData.stale_items) {
                    selectedStaleItems.add(item.path);
                }
            }
            updateBatchActionButton();
            renderFreshnessContent();
        }

        function clearStaleItemSelection() {
            selectedStaleItems.clear();
            updateBatchActionButton();
            renderFreshnessContent();
        }

        function updateBatchActionButton() {
            const btn = document.getElementById('batch-rebuild-btn');
            if (btn) {
                btn.textContent = selectedStaleItems.size > 0
                    ? `Rebuild Selected (${selectedStaleItems.size})`
                    : 'Select items to rebuild';
                btn.disabled = selectedStaleItems.size === 0;
            }
        }

        async function rebuildSelectedItems() {
            if (selectedStaleItems.size === 0) return;

            showToast(`Rebuilding ${selectedStaleItems.size} items...`, 'info');

            // For now, trigger a full build - in future could be selective
            showTab('build');
            setTimeout(() => startBuild(), 500);
        }

        // Media tab state
        let mediaLoaded = false;
        let mediaData = null;

        async function loadMedia() {
            const mediaList = document.getElementById('media-list');
            mediaList.innerHTML = '<div class="loading">Loading media files...</div>';

            try {
                mediaData = await fetchAPI('/api/media');
                mediaLoaded = true;

                // Update stats
                document.getElementById('stat-audio').textContent = mediaData.by_type.audio || 0;
                document.getElementById('stat-video').textContent = mediaData.by_type.video || 0;
                document.getElementById('stat-demos').textContent = mediaData.by_type.demo || 0;
                document.getElementById('stat-docs-output').textContent = mediaData.by_type.document || 0;

                renderMediaList(mediaData.files);
            } catch (e) {
                mediaList.innerHTML = '<div class="empty-state">Error loading media files</div>';
            }
        }

        function filterMedia() {
            if (!mediaData) return;
            const filter = document.getElementById('media-filter').value;
            const filtered = filter === 'all'
                ? mediaData.files
                : mediaData.files.filter(f => f.type === filter);
            renderMediaList(filtered);
        }

        function renderMediaList(files) {
            const mediaList = document.getElementById('media-list');

            if (files.length === 0) {
                mediaList.innerHTML = '<div class="empty-state">No media files found</div>';
                return;
            }

            let html = '<div class="media-grid">';
            for (const file of files) {
                const sizeStr = formatFileSize(file.size);
                const dateStr = new Date(file.modified).toLocaleString();

                html += '<div class="media-item">';
                html += '<div class="media-item-header">';
                html += '<div class="media-item-title">' + escapeHtml(file.filename) + '</div>';
                html += '<span class="media-item-type type-' + file.type + '">' + file.type + '</span>';
                html += '</div>';
                html += '<div class="media-item-meta">';
                html += '<div>' + sizeStr + ' &middot; ' + file.format.toUpperCase() + '</div>';
                html += '<div>' + dateStr + '</div>';
                html += '</div>';

                // Source document link
                if (file.source) {
                    html += '<div class="media-item-source">';
                    html += 'Source: <a href="#" onclick="viewSourceDoc(\\'' + escapeHtml(file.source.path) + '\\', \\'' + file.source.type + '\\'); return false;">';
                    html += escapeHtml(file.source.name) + ' (' + file.source.language + ')';
                    html += '</a>';
                    html += '</div>';
                }

                // Inline audio player for audio files
                if (file.type === 'audio') {
                    html += '<audio class="audio-player" controls preload="none">';
                    html += '<source src="' + file.url + '" type="audio/mpeg">';
                    html += '</audio>';
                }

                // Action buttons
                html += '<div class="media-item-actions">';
                if (file.type === 'audio' || file.type === 'video' || file.type === 'demo') {
                    html += '<button class="media-btn media-btn-primary" onclick="previewMedia(\\'' + escapeHtml(file.url) + '\\', \\'' + file.type + '\\', \\'' + escapeHtml(file.filename) + '\\')">Preview</button>';
                }
                if (file.type === 'captions' || file.type === 'video_props') {
                    html += '<button class="media-btn" onclick="viewFileContent(\\'' + escapeHtml(file.path) + '\\', \\'' + escapeHtml(file.filename) + '\\')">View</button>';
                }
                html += '<a href="' + file.url + '" download class="media-btn">Download</a>';
                html += '</div>';
                html += '</div>';
            }
            html += '</div>';
            mediaList.innerHTML = html;
        }

        function formatFileSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        }

        function previewMedia(url, type, filename) {
            const modal = document.getElementById('media-preview-modal');
            const title = document.getElementById('media-preview-title');
            const body = document.getElementById('media-preview-body');

            title.textContent = filename;

            if (type === 'audio') {
                body.innerHTML = '<audio controls autoplay style="width: 100%;"><source src="' + url + '" type="audio/mpeg"></audio>';
            } else if (type === 'video') {
                body.innerHTML = '<video controls autoplay><source src="' + url + '" type="video/mp4"></video>';
            } else if (type === 'demo') {
                body.innerHTML = '<iframe src="' + url + '"></iframe>';
            }

            modal.style.display = 'flex';
        }

        async function viewFileContent(path, filename) {
            const modal = document.getElementById('media-preview-modal');
            const title = document.getElementById('media-preview-title');
            const body = document.getElementById('media-preview-body');

            title.textContent = filename;
            body.innerHTML = '<div class="loading">Loading...</div>';
            modal.style.display = 'flex';

            try {
                const data = await fetchAPI('/api/file?path=' + encodeURIComponent(path));
                body.innerHTML = '<pre>' + escapeHtml(data.content) + '</pre>';
            } catch (e) {
                body.innerHTML = '<div class="empty-state">Error loading file</div>';
            }
        }

        function viewSourceDoc(path, type) {
            // Switch to documents tab and load the source
            showTab('documents');
            setTimeout(() => {
                loadDocumentDirect(path, type);
            }, 100);
        }

        function closeMediaPreview() {
            const modal = document.getElementById('media-preview-modal');
            const body = document.getElementById('media-preview-body');
            // Stop any playing media
            body.innerHTML = '';
            modal.style.display = 'none';
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            // Don't trigger when typing in inputs
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

            if (e.key === 'Escape') {
                closeMediaPreview();
            }

            // Video keyboard controls (Space, arrows, J/K/L)
            const video = document.getElementById('script-video-player');
            if (video) {
                if (e.key === ' ' || e.key === 'k') {
                    e.preventDefault();
                    toggleVideoPlayback();
                } else if (e.key === 'ArrowLeft' || e.key === 'j') {
                    e.preventDefault();
                    video.currentTime = Math.max(0, video.currentTime - 5);
                    updateVideoProgress();
                    updateCurrentScene(video.currentTime);
                } else if (e.key === 'ArrowRight' || e.key === 'l') {
                    e.preventDefault();
                    video.currentTime = Math.min(video.duration || 0, video.currentTime + 5);
                    updateVideoProgress();
                    updateCurrentScene(video.currentTime);
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    video.volume = Math.min(1, video.volume + 0.1);
                } else if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    video.volume = Math.max(0, video.volume - 0.1);
                } else if (e.key === '0') {
                    video.currentTime = 0;
                    updateVideoProgress();
                    updateCurrentScene(0);
                } else if (e.key === 'm') {
                    video.muted = !video.muted;
                }
            }
        });

        // Packs tab state
        let packsLoaded = false;

        async function loadPacks() {
            try {
                const [packsData, registryData] = await Promise.all([
                    fetchAPI('/api/packs'),
                    fetchAPI('/api/registry')
                ]);
                packsLoaded = true;

                // Render investor pack
                renderPackContents('investor-pack-contents', packsData.packs.investor);
                renderPackContents('pilot-pack-contents', packsData.packs.pilot);

                // Render registry overview
                if (registryData.found) {
                    renderRegistryOverview(registryData);
                } else {
                    document.getElementById('registry-overview').innerHTML =
                        '<div class="empty-state">No document registry found (documents.yaml)</div>';
                }
            } catch (e) {
                document.getElementById('investor-pack-contents').innerHTML = '<div class="empty-state">Error loading packs</div>';
            }
        }

        function renderPackContents(containerId, pack) {
            const container = document.getElementById(containerId);
            let html = '<table><thead><tr><th>Item</th><th>Type</th><th>Status</th></tr></thead><tbody>';

            for (const item of pack.contents) {
                const statusClass = item.exists ? 'cell-current' : 'cell-missing';
                const statusText = item.exists ? '\\u2713' : '\\u2717';
                html += '<tr>';
                html += '<td>' + escapeHtml(item.name) + '</td>';
                html += '<td><span class="doc-type-badge">' + item.type + '</span></td>';
                html += '<td><span class="matrix-cell ' + statusClass + '">' + statusText + '</span></td>';
                html += '</tr>';
            }

            html += '</tbody></table>';
            html += '<div class="stat-label" style="margin-top: 1rem;">Audience: ' + escapeHtml(pack.audience) + '</div>';
            container.innerHTML = html;
        }

        function renderRegistryOverview(data) {
            const container = document.getElementById('registry-overview');
            let html = '<div class="grid" style="grid-template-columns: repeat(5, 1fr); margin-bottom: 1rem;">';

            // Status summary cards
            html += '<div style="text-align: center; padding: 1rem; background: var(--bg); border-radius: 0.25rem;">';
            html += '<div style="font-size: 1.5rem; font-weight: bold; color: var(--success);">' + (data.status_counts.complete || 0) + '</div>';
            html += '<div class="stat-label">Complete</div></div>';

            html += '<div style="text-align: center; padding: 1rem; background: var(--bg); border-radius: 0.25rem;">';
            html += '<div style="font-size: 1.5rem; font-weight: bold; color: var(--success);">' + data.status_counts.final + '</div>';
            html += '<div class="stat-label">Final</div></div>';

            html += '<div style="text-align: center; padding: 1rem; background: var(--bg); border-radius: 0.25rem;">';
            html += '<div style="font-size: 1.5rem; font-weight: bold; color: var(--primary);">' + data.status_counts.draft + '</div>';
            html += '<div class="stat-label">Draft</div></div>';

            html += '<div style="text-align: center; padding: 1rem; background: var(--bg); border-radius: 0.25rem;">';
            html += '<div style="font-size: 1.5rem; font-weight: bold; color: var(--warning);">' + data.status_counts.review + '</div>';
            html += '<div class="stat-label">Review</div></div>';

            html += '<div style="text-align: center; padding: 1rem; background: var(--bg); border-radius: 0.25rem;">';
            html += '<div style="font-size: 1.5rem; font-weight: bold; color: var(--text-muted);">' + data.status_counts.not_started + '</div>';
            html += '<div class="stat-label">Not Started</div></div>';
            html += '</div>';

            // Categories
            const categoryNames = {
                source_documents: 'Source Documents',
                deliverables: 'Deliverables',
                video_scripts: 'Video Scripts',
                diagrams: 'Diagrams',
                templates: 'Templates',
                demo: 'Demo',
            };

            for (const [catId, catName] of Object.entries(categoryNames)) {
                const docs = data.categories[catId];
                if (!docs || Object.keys(docs).length === 0) continue;

                html += '<details style="margin-bottom: 0.5rem;"><summary style="cursor: pointer; padding: 0.5rem; background: var(--bg); border-radius: 0.25rem;">';
                html += '<strong>' + catName + '</strong> (' + Object.keys(docs).length + ' items)</summary>';
                html += '<table style="margin-top: 0.5rem;"><thead><tr><th>Document</th><th>Status</th><th>Version</th></tr></thead><tbody>';

                for (const [docId, doc] of Object.entries(docs)) {
                    if (typeof doc !== 'object') continue;
                    const status = doc.status || 'unknown';
                    const statusClass = status === 'final' ? 'cell-current' : status === 'draft' ? 'cell-source' : status === 'review' ? 'cell-outdated' : 'cell-missing';
                    html += '<tr>';
                    html += '<td>' + escapeHtml(doc.title || docId) + '</td>';
                    html += '<td><span class="matrix-cell ' + statusClass + '" style="width: auto; height: auto; padding: 0.2rem 0.5rem;">' + status + '</span></td>';
                    html += '<td>' + escapeHtml(doc.version || '-') + '</td>';
                    html += '</tr>';
                }
                html += '</tbody></table></details>';
            }

            html += '<div class="stat-label" style="margin-top: 1rem;">Registry version: ' + data.version + ' (updated: ' + data.last_updated + ')</div>';
            container.innerHTML = html;
        }

        function generatePack(packType) {
            alert('To generate ' + packType + ' pack, run:\\n\\nuv run media-engine pack ' + packType);
        }

        // Assets tab state
        let assetsLoaded = false;

        async function loadAssets() {
            try {
                const data = await fetchAPI('/api/assets');
                assetsLoaded = true;

                // Update stats
                document.getElementById('stat-diagrams').textContent = data.by_type.diagram || 0;
                document.getElementById('stat-logos').textContent = data.by_type.logo || 0;
                document.getElementById('stat-video-assets').textContent = data.by_type.video_asset || 0;
                document.getElementById('stat-total-assets').textContent = data.total;

                // Render assets grid
                renderAssetsGrid(data.assets);
            } catch (e) {
                document.getElementById('assets-grid').innerHTML = '<div class="empty-state">Error loading assets</div>';
            }
        }

        function renderAssetsGrid(assets) {
            const container = document.getElementById('assets-grid');

            if (assets.length === 0) {
                container.innerHTML = '<div class="empty-state">No assets found</div>';
                return;
            }

            let html = '';
            for (const asset of assets) {
                const sizeStr = formatFileSize(asset.size);
                const dateStr = new Date(asset.modified).toLocaleDateString();

                html += '<div class="media-item">';
                html += '<div class="media-item-header">';
                html += '<div class="media-item-title">' + escapeHtml(asset.filename) + '</div>';
                html += '<span class="media-item-type type-' + (asset.type === 'diagram' ? 'demo' : asset.type === 'logo' ? 'audio' : 'document') + '">' + asset.type + '</span>';
                html += '</div>';
                html += '<div class="media-item-meta">' + sizeStr + ' &middot; ' + asset.format.toUpperCase() + ' &middot; ' + dateStr + '</div>';

                // Preview for images
                if (['svg', 'png', 'jpg', 'jpeg'].includes(asset.format)) {
                    html += '<div style="margin: 0.5rem 0; padding: 0.5rem; background: #fff; border-radius: 0.25rem; text-align: center;">';
                    html += '<img src="/assets/' + asset.relative_path + '" alt="' + escapeHtml(asset.filename) + '" style="max-width: 100%; max-height: 150px;">';
                    html += '</div>';
                }

                html += '<div class="media-item-meta" style="font-size: 0.7rem;">' + escapeHtml(asset.relative_path) + '</div>';
                html += '</div>';
            }

            container.innerHTML = html;
        }

        // Document browser state
        let documentsLoaded = false;
        let currentDoc = null;
        let currentDocData = null;
        let currentScriptPath = null;
        let previewMode = 'preview';
        let projectLanguages = [];
        let projectName = '';
        let sceneNotes = {};

        async function initDocumentBrowser() {
            const data = await fetchAPI('/api/project');
            projectLanguages = Object.keys(data.languages);
            projectName = data.name || 'Documentation';

            const select = document.getElementById('lang-select');
            select.innerHTML = projectLanguages.map(lang =>
                '<option value="' + lang + '">' + lang.toUpperCase() + ' - ' + data.languages[lang].name + '</option>'
            ).join('');

            documentsLoaded = true;
            loadDocuments();
        }

        async function loadDocuments() {
            const lang = document.getElementById('lang-select').value;
            if (!lang) return;

            const docList = document.getElementById('doc-list');
            docList.innerHTML = '<div class="loading">Loading...</div>';

            try {
                const data = await fetchAPI('/api/documents/' + lang);

                // Group ALL documents together
                const allDocs = data.documents;

                // Separate into groups with multiple items vs individual items
                const chapters = allDocs.filter(d => d.type === 'chapter');
                const deliverables = allDocs.filter(d => d.type === 'deliverable');
                const scripts = allDocs.filter(d => d.type === 'script');
                const others = allDocs.filter(d => !['chapter', 'deliverable', 'script'].includes(d.type));

                let html = '';

                // All Documents section header
                html += '<div style="padding: 0.5rem 1rem; background: var(--bg); font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">All Documents</div>';

                // Render chapters as a collapsible group with project name
                if (chapters.length > 0) {
                    html += renderDocumentGroup('chapters', projectName, chapters, true);
                }

                // Render deliverables grouped by category
                if (deliverables.length > 0) {
                    const byCategory = {};
                    for (const doc of deliverables) {
                        const cat = doc.category || 'Other';
                        if (!byCategory[cat]) byCategory[cat] = [];
                        byCategory[cat].push(doc);
                    }
                    for (const [category, docs] of Object.entries(byCategory)) {
                        html += renderDocumentGroup('deliverable-' + category.toLowerCase(), category, docs, false);
                    }
                }

                // Render scripts as a collapsible group
                if (scripts.length > 0) {
                    html += renderDocumentGroup('scripts', 'Video Scripts', scripts, false);
                }

                // Render other document types
                const otherTypes = {};
                for (const doc of others) {
                    if (!otherTypes[doc.type]) otherTypes[doc.type] = [];
                    otherTypes[doc.type].push(doc);
                }
                const typeLabels = { diagram: 'Diagrams', slides: 'Slides', data: 'Data Files', demo: 'Interactive Demos' };
                for (const [type, docs] of Object.entries(otherTypes)) {
                    html += renderDocumentGroup(type, typeLabels[type] || type, docs, false);
                }

                docList.innerHTML = html || '<div class="empty-state">No documents found</div>';
            } catch (e) {
                docList.innerHTML = '<div class="empty-state">Error loading documents</div>';
            }
        }

        function renderDocumentGroup(groupId, title, docs, showChapterNumbers) {
            let html = '<div class="doc-group" id="group-' + groupId + '">';
            html += '<div class="doc-group-header" onclick="toggleChapterGroup(\\'group-' + groupId + '\\')">';
            html += '<svg class="doc-group-toggle" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>';
            html += '<div class="doc-group-info">';
            html += '<div class="doc-group-title">' + escapeHtml(title) + '</div>';
            html += '<div class="doc-group-meta">';
            html += '<span class="doc-group-badge">' + docs.length + '</span>';
            html += '</div></div></div>';

            html += '<div class="doc-group-children" id="group-' + groupId + '-children">';

            // Sort docs - numbered ones first
            const sorted = [...docs].sort((a, b) => {
                const aNum = parseInt(a.filename.match(/^(\\d+)/)?.[1] || '999');
                const bNum = parseInt(b.filename.match(/^(\\d+)/)?.[1] || '999');
                return aNum - bNum;
            });

            for (const doc of sorted) {
                const isActive = currentDoc === doc.path ? 'active' : '';
                const chapterMatch = doc.filename.match(/^(\\d+)/);
                const chapterNum = showChapterNumbers && chapterMatch ? chapterMatch[1] : null;

                html += '<div class="doc-item ' + isActive + '" onclick="loadDocument(\\'' + doc.path.replace(/'/g, "\\\\'") + '\\', \\'' + doc.type + '\\')">';
                html += '<div class="doc-item-row">';
                if (chapterNum) {
                    html += '<span style="font-weight: 600; color: var(--primary); min-width: 1.5rem; margin-right: 0.5rem;">' + chapterNum + '</span>';
                }
                html += '<div class="doc-item-content">';
                html += '<div class="doc-item-title">' + escapeHtml(doc.title) + '</div>';
                html += '<div class="doc-item-meta">' + escapeHtml(doc.filename) + '</div>';
                html += '</div>';
                html += '</div></div>';
            }
            html += '</div></div>';
            return html;
        }

        // Toggle chapter group expansion
        function toggleChapterGroup(groupId) {
            const toggle = document.querySelector('#' + groupId + ' .doc-group-toggle');
            const children = document.getElementById(groupId + '-children');
            toggle.classList.toggle('expanded');
            children.classList.toggle('expanded');
        }

        async function loadDocument(path, type) {
            currentDoc = path;
            currentScriptPath = null;

            // Update active state in list
            document.querySelectorAll('.doc-item').forEach(el => el.classList.remove('active'));
            if (event && event.target) {
                const item = event.target.closest('.doc-item');
                if (item) item.classList.add('active');
            }

            const previewContent = document.getElementById('preview-content');
            previewContent.innerHTML = '<div class="loading">Loading...</div>';

            try {
                if (type === 'chapter' || type === 'deliverable') {
                    const data = await fetchAPI('/api/document?path=' + encodeURIComponent(path));
                    currentDocData = { ...data, docType: type };
                    document.getElementById('preview-title').textContent = data.title;
                    document.getElementById('preview-path').textContent = data.path;
                    renderDocPreview();
                } else if (type === 'script') {
                    const data = await fetchAPI('/api/file?path=' + encodeURIComponent(path));
                    currentDocData = {
                        title: data.filename,
                        content: data.content,
                        metadata: data.parsed || {},
                        isScript: true,
                        docType: 'script',
                        video: data.video || null
                    };
                    currentScriptPath = path;
                    document.getElementById('preview-title').textContent = data.parsed?.title || data.filename;
                    document.getElementById('preview-path').textContent = data.path;
                    // Load scene notes for this script
                    await loadSceneNotes(path);
                    renderDocPreview();
                } else if (type === 'slides') {
                    const data = await fetchAPI('/api/file?path=' + encodeURIComponent(path));
                    const parsed = data.parsed || {};
                    const slideCount = (parsed.slides || []).length;
                    currentDocData = {
                        title: parsed.title || data.filename,
                        content: data.content,
                        metadata: parsed,
                        isSlides: true,
                        docType: 'slides'
                    };
                    document.getElementById('preview-title').textContent = (parsed.title || data.filename) + ' (' + slideCount + ' slides)';
                    document.getElementById('preview-path').textContent = data.path;
                    renderDocPreview();
                } else {
                    const data = await fetchAPI('/api/file?path=' + encodeURIComponent(path));
                    currentDocData = {
                        title: data.filename,
                        content: data.content,
                        html: '<pre class="yaml-viewer">' + escapeHtml(data.content) + '</pre>',
                        metadata: data.parsed || {},
                        isYaml: true,
                        docType: type
                    };
                    document.getElementById('preview-title').textContent = data.filename;
                    document.getElementById('preview-path').textContent = data.path;
                    renderDocPreview();
                }
            } catch (e) {
                previewContent.innerHTML = '<div class="empty-state">Error loading document</div>';
            }
        }

        async function loadSceneNotes(scriptPath) {
            try {
                const data = await fetchAPI('/api/scene-notes/' + encodeURIComponent(scriptPath));
                sceneNotes = data.notes || {};
                updateExportButton();
            } catch (e) {
                sceneNotes = {};
            }
        }

        function updateExportButton() {
            const btn = document.getElementById('export-notes-btn');
            const hasNotes = Object.keys(sceneNotes).length > 0;
            btn.classList.toggle('visible', hasNotes);
        }

        async function saveSceneNote(sceneId) {
            if (!currentScriptPath) return;
            const textarea = document.getElementById('note-' + sceneId);
            const note = textarea.value.trim();

            try {
                await postAPI('/api/scene-notes/' + encodeURIComponent(currentScriptPath), {
                    scene_id: sceneId,
                    note: note
                });
                if (note) {
                    sceneNotes[sceneId] = { text: note, created: new Date().toISOString() };
                } else {
                    delete sceneNotes[sceneId];
                }
                updateExportButton();
                // Update the badge
                const badge = document.getElementById('note-badge-' + sceneId);
                if (badge) {
                    badge.style.display = note ? 'inline-block' : 'none';
                }
                const savedMsg = document.getElementById('note-saved-' + sceneId);
                if (savedMsg) {
                    savedMsg.textContent = note ? 'Saved!' : 'Deleted';
                    setTimeout(() => { savedMsg.textContent = ''; }, 2000);
                }
            } catch (e) {
                alert('Error saving note');
            }
        }

        async function deleteSceneNote(sceneId) {
            if (!currentScriptPath) return;
            if (!confirm('Delete this note?')) return;

            const textarea = document.getElementById('note-' + sceneId);
            textarea.value = '';
            await saveSceneNote(sceneId);
        }

        async function exportSceneNotes() {
            try {
                const data = await fetchAPI('/api/scene-notes-export');
                // Download as JSON
                const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'scene-notes-todo.json';
                a.click();
                URL.revokeObjectURL(url);
            } catch (e) {
                alert('Error exporting notes');
            }
        }

        function renderDocPreview() {
            const previewContent = document.getElementById('preview-content');
            if (!currentDocData) return;

            // Special handling for video scripts
            if (currentDocData.isScript && previewMode === 'preview') {
                previewContent.className = 'doc-preview-content script-viewer';
                previewContent.innerHTML = renderScriptViewer(currentDocData.metadata);
                return;
            }

            // Special handling for slide decks
            if (currentDocData.isSlides && previewMode === 'preview') {
                previewContent.className = 'doc-preview-content';
                previewContent.style.padding = '0';
                previewContent.innerHTML = renderSlideViewer(currentDocData.metadata);
                return;
            } else {
                previewContent.style.padding = '';
            }

            if (previewMode === 'preview') {
                previewContent.className = 'doc-preview-content preview-mode';
                previewContent.innerHTML = currentDocData.html || '<pre class="yaml-viewer">' + escapeHtml(currentDocData.content) + '</pre>';
            } else if (previewMode === 'source') {
                previewContent.className = 'doc-preview-content source-mode';
                previewContent.textContent = currentDocData.content;
            } else if (previewMode === 'metadata') {
                previewContent.className = 'doc-preview-content';
                previewContent.innerHTML = renderMetadataViewer(currentDocData.metadata, currentDocData.docType || 'document');
            }
        }

        // Render rich video script viewer
        function renderScriptViewer(script) {
            if (!script || !script.scenes) {
                return '<div class="empty-state">Invalid script format</div>';
            }

            const scenes = script.scenes || [];
            const totalDuration = scenes.reduce((sum, s) => sum + (s.duration || 0), 0);
            const totalWords = scenes.reduce((sum, s) => sum + countWords(s.voiceover || ''), 0);
            const narrator = script.narrator || {};
            const production = script.production || {};
            const output = script.output || {};

            const sceneColors = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#6366f1'];

            let html = '';

            // Header
            html += '<div class="script-header">';
            html += '<div class="script-title">' + escapeHtml(script.title || 'Untitled Script') + '</div>';
            html += '<div class="script-description">' + escapeHtml(script.description || '') + '</div>';
            html += '<div class="script-meta">';
            if (script.language) {
                html += '<div class="script-meta-item"><svg class="script-meta-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg><span class="script-meta-value">' + escapeHtml(script.language.toUpperCase()) + '</span></div>';
            }
            if (script.target_audience) {
                const audiences = Array.isArray(script.target_audience) ? script.target_audience : [script.target_audience];
                html += '<div class="script-meta-item"><svg class="script-meta-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg><span class="script-meta-value">' + audiences.map(a => escapeHtml(a.replace(/_/g, ' '))).join(', ') + '</span></div>';
            }
            if (production.version) {
                html += '<div class="script-meta-item"><span class="script-meta-label">v</span><span class="script-meta-value">' + escapeHtml(production.version) + '</span></div>';
            }
            if (production.status) {
                html += '<div class="script-meta-item"><span class="script-scene-badge type-' + (production.status === 'complete' ? 'web' : 'text') + '">' + escapeHtml(production.status) + '</span></div>';
            }
            html += '</div></div>';

            // Stats
            const wpm = totalDuration > 0 ? Math.round((totalWords / totalDuration) * 60) : 0;
            const avgSceneDuration = scenes.length > 0 ? Math.round(totalDuration / scenes.length) : 0;
            html += '<div class="script-stats">';
            html += '<div class="script-stat"><div class="script-stat-value">' + formatDuration(totalDuration) + '</div><div class="script-stat-label">Total Duration</div></div>';
            html += '<div class="script-stat"><div class="script-stat-value">' + scenes.length + '</div><div class="script-stat-label">Scenes</div></div>';
            html += '<div class="script-stat"><div class="script-stat-value">' + totalWords.toLocaleString() + '</div><div class="script-stat-label">Words</div></div>';
            html += '<div class="script-stat"><div class="script-stat-value">' + wpm + '</div><div class="script-stat-label">Words/Min</div></div>';
            html += '<div class="script-stat"><div class="script-stat-value">' + avgSceneDuration + 's</div><div class="script-stat-label">Avg Scene</div></div>';
            html += '</div>';

            // Video Player Section
            const video = currentDocData?.video;
            if (video && video.hasVideo) {
                html += '<div class="script-video-section">';
                html += '<div class="script-video-container">';
                html += '<video id="script-video-player" class="script-video-player" preload="metadata">';
                html += '<source src="' + escapeHtml(video.videoUrl) + '" type="video/mp4">';
                if (video.captionsUrl) {
                    html += '<track kind="captions" src="' + escapeHtml(video.captionsUrl) + '" srclang="en" label="Captions">';
                }
                html += '</video>';
                html += '<div class="script-video-controls">';
                html += '<button class="video-play-btn" onclick="toggleVideoPlayback()">';
                html += '<svg id="video-play-icon" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg>';
                html += '<span id="video-play-text">Play</span>';
                html += '</button>';
                html += '<div class="video-progress" onclick="seekVideo(event)">';
                html += '<div class="video-progress-fill" id="video-progress-fill" style="width:0%"></div>';
                html += '</div>';
                html += '<div class="video-time"><span id="video-current-time">0:00</span> / <span id="video-duration">' + formatDuration(video.duration || 0) + '</span></div>';
                html += '</div>';
                html += '</div></div>';
            } else if (video && !video.hasVideo && video.hasAudio) {
                // Audio-only preview
                html += '<div class="script-video-section" style="background:var(--bg-card)">';
                html += '<div class="script-video-container">';
                html += '<div class="video-no-render">';
                html += '<svg class="video-no-render-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v4M8 23h8"/></svg>';
                html += '<div class="video-no-render-text">Audio available (no video render)</div>';
                html += '<audio id="script-audio-player" controls style="width:100%;max-width:400px"><source src="' + escapeHtml(video.audioUrl) + '" type="audio/mpeg"></audio>';
                html += '</div></div></div>';
            } else {
                // No video rendered yet
                html += '<div class="script-video-section" style="background:var(--bg-card)">';
                html += '<div class="script-video-container">';
                html += '<div class="video-no-render">';
                html += '<svg class="video-no-render-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"/><line x1="7" y1="2" x2="7" y2="22"/><line x1="17" y1="2" x2="17" y2="22"/><line x1="2" y1="12" x2="22" y2="12"/><line x1="2" y1="7" x2="7" y2="7"/><line x1="2" y1="17" x2="7" y2="17"/><line x1="17" y1="17" x2="22" y2="17"/><line x1="17" y1="7" x2="22" y2="7"/></svg>';
                html += '<div class="video-no-render-text">Video not rendered yet</div>';
                html += '<button class="video-render-btn" onclick="renderVideo()" disabled title="Build video via CLI: media-engine video build">Build Video</button>';
                html += '</div></div></div>';
            }

            // Production settings
            if (narrator.voice || output.resolution) {
                html += '<div class="script-production">';
                html += '<div class="script-production-title"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:1rem;height:1rem"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>Production Settings</div>';
                html += '<div class="script-production-grid">';
                if (narrator.voice) html += '<div class="script-production-item"><div class="script-production-label">Voice</div><div class="script-production-value">' + escapeHtml(narrator.voice) + '</div></div>';
                if (narrator.voice_id) html += '<div class="script-production-item"><div class="script-production-label">Voice ID</div><div class="script-production-value">' + escapeHtml(narrator.voice_id) + '</div></div>';
                if (narrator.speed) html += '<div class="script-production-item"><div class="script-production-label">Speed</div><div class="script-production-value">' + narrator.speed + 'x</div></div>';
                if (output.resolution) html += '<div class="script-production-item"><div class="script-production-label">Resolution</div><div class="script-production-value">' + output.resolution.width + 'x' + output.resolution.height + '</div></div>';
                if (output.framerate) html += '<div class="script-production-item"><div class="script-production-label">Framerate</div><div class="script-production-value">' + output.framerate + ' fps</div></div>';
                if (output.filename) html += '<div class="script-production-item"><div class="script-production-label">Output</div><div class="script-production-value">' + escapeHtml(output.filename) + '</div></div>';
                if (script.demo_url) html += '<div class="script-production-item"><div class="script-production-label">Demo URL</div><div class="script-production-value">' + escapeHtml(script.demo_url) + '</div></div>';
                html += '</div></div>';
            }

            // Build scene timing lookup from actual video props (if available)
            // This ensures sync matches the rendered video, not just YAML durations
            const sceneTimingMap = {};
            if (video && video.sceneTiming && Array.isArray(video.sceneTiming)) {
                video.sceneTiming.forEach(st => {
                    if (st.id) {
                        sceneTimingMap[st.id] = { start: st.startTime || 0, end: st.endTime || 0 };
                    }
                });
            }
            const hasActualTiming = Object.keys(sceneTimingMap).length > 0;
            const actualTotalDuration = video && video.duration ? video.duration : totalDuration;

            // Timeline
            html += '<div class="script-timeline">';
            html += '<div class="script-timeline-title"><span>Scene Timeline</span><span style="font-weight:normal;color:var(--text-muted)">' + formatDuration(actualTotalDuration) + ' total</span></div>';
            html += '<div class="script-timeline-bar">';
            let cumulativeTime = 0;
            scenes.forEach((scene, i) => {
                const sceneId = scene.id || 'scene-' + i;
                const timing = sceneTimingMap[sceneId];
                const sceneDur = timing ? (timing.end - timing.start) : (scene.duration || 0);
                const width = actualTotalDuration > 0 ? (sceneDur / actualTotalDuration * 100) : 0;
                const color = sceneColors[i % sceneColors.length];
                html += '<div class="script-timeline-segment" style="width:' + width + '%;background:' + color + '" title="' + escapeHtml(scene.name || scene.id) + ' (' + sceneDur.toFixed(1) + 's)" onclick="scrollToScene(' + i + ')"></div>';
            });
            html += '</div>';

            // Scenes
            html += '<div class="script-scenes">';
            cumulativeTime = 0;
            scenes.forEach((scene, i) => {
                const sceneId = scene.id || 'scene-' + i;
                const sceneType = scene.scene_type || 'unknown';
                const typeClass = sceneType === 'web' ? 'type-web' : (sceneType === 'text_overlay' ? 'type-text' : 'type-video');
                const words = countWords(scene.voiceover || '');
                const color = sceneColors[i % sceneColors.length];
                const hasNote = sceneNotes[sceneId] && sceneNotes[sceneId].text;

                // Use actual timing from video props if available, otherwise fall back to YAML
                const timing = sceneTimingMap[sceneId];
                const sceneStartTime = timing ? timing.start : cumulativeTime;
                const sceneEndTime = timing ? timing.end : (cumulativeTime + (scene.duration || 0));
                const actualSceneDuration = sceneEndTime - sceneStartTime;

                html += '<div class="script-scene" id="scene-' + i + '" data-start="' + sceneStartTime + '" data-end="' + sceneEndTime + '">';
                html += '<div class="script-scene-header" onclick="toggleScene(' + i + ')">';
                html += '<div class="script-scene-number" style="background:' + color + '">' + (i + 1) + '</div>';
                html += '<div class="script-scene-info">';
                html += '<div class="script-scene-name">' + escapeHtml(scene.name || 'Scene ' + (i + 1)) + '</div>';
                html += '<div class="script-scene-id">' + escapeHtml(sceneId) + ' \\u00B7 starts at ' + formatDuration(sceneStartTime) + '</div>';
                html += '</div>';
                html += '<div class="script-scene-badges">';
                html += '<span class="script-scene-badge ' + typeClass + '">' + escapeHtml(sceneType.replace('_', ' ')) + '</span>';
                html += '<span class="script-scene-badge duration">' + actualSceneDuration.toFixed(1) + 's</span>';
                if (words > 0) html += '<span class="script-scene-badge duration">' + words + ' words</span>';
                html += '<span class="script-scene-badge has-note" id="note-badge-' + sceneId + '" style="display:' + (hasNote ? 'inline-block' : 'none') + '">Note</span>';
                html += '</div>';
                // Play from here button (only if video is available)
                if (video && video.hasVideo) {
                    html += '<button class="scene-play-btn" onclick="event.stopPropagation(); playFromScene(' + i + ', ' + sceneStartTime + ')" title="Play from this scene">';
                    html += '<svg viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg>';
                    html += '<span>Play</span>';
                    html += '</button>';
                }
                html += '<svg class="script-scene-toggle" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>';
                html += '</div>';

                // Scene content (expandable)
                html += '<div class="script-scene-content">';

                // Scene-specific video player (if video available)
                if (video && video.hasVideo) {
                    html += '<div class="script-scene-section scene-video-section">';
                    html += '<div class="script-scene-section-title"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5,3 19,12 5,21"/></svg>Scene Preview (' + actualSceneDuration.toFixed(1) + 's)</div>';
                    html += '<div class="scene-video-container">';
                    html += '<video class="scene-video-player" id="scene-video-' + i + '" preload="metadata" data-start="' + sceneStartTime + '" data-end="' + sceneEndTime + '">';
                    html += '<source src="' + escapeHtml(video.videoUrl) + '" type="video/mp4">';
                    html += '</video>';
                    html += '<div class="scene-video-controls">';
                    html += '<button class="scene-video-play-btn" onclick="toggleSceneVideo(' + i + ')">';
                    html += '<svg id="scene-video-icon-' + i + '" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg>';
                    html += '</button>';
                    html += '<div class="scene-video-progress" onclick="seekSceneVideo(event, ' + i + ')">';
                    html += '<div class="scene-video-progress-fill" id="scene-progress-' + i + '" style="width:0%"></div>';
                    html += '</div>';
                    html += '<span class="scene-video-time" id="scene-time-' + i + '">0:00 / ' + formatDuration(actualSceneDuration) + '</span>';
                    html += '<button class="scene-video-loop-btn" id="scene-loop-btn-' + i + '" onclick="toggleSceneLoop(' + i + ')" title="Loop scene">';
                    html += '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 1l4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><path d="M7 23l-4-4 4-4"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>';
                    html += '</button>';
                    html += '</div></div></div>';
                }

                // Scene Composition Preview - supports both old (background.color) and new (visual.*) formats
                const visual = scene.visual || {};
                const hasVisualProps = visual.background || visual.transition_in || visual.feature_card || visual.pipeline || visual.terminal || visual.icons || visual.metrics;
                if (sceneType === 'text_overlay' || scene.background || (scene.text_overlays && scene.text_overlays.length > 0) || hasVisualProps) {
                    const bgPresets = {
                        'dark': '#0f0f1a', 'aurora': 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
                        'grid': '#1a1a2e', 'particles': '#0a0a14', 'pulse': '#1a0a2e', 'cyber': '#0a1a1a',
                        'waves': 'linear-gradient(180deg, #1a1a2e 0%, #0f3460 100%)'
                    };
                    const rawBgColor = scene.background?.color || bgPresets[visual.background] || '#1a1a2e';
                    const bgColor = typeof rawBgColor === 'string' && rawBgColor.startsWith('linear') ? rawBgColor : resolveColor(rawBgColor);
                    html += '<div class="script-scene-section">';
                    html += '<div class="script-scene-section-title"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>Scene Composition</div>';
                    html += '<div class="script-composition-preview" style="background:' + escapeHtml(bgColor) + '">';

                    // New visual format - show visual properties
                    if (hasVisualProps) {
                        html += '<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:0.5rem;gap:0.25rem">';
                        if (visual.show_logo) {
                            html += '<div style="font-size:0.6rem;font-weight:700;color:#fff;text-transform:uppercase;letter-spacing:0.1em;opacity:0.9">MEDIA ENGINE</div>';
                        }
                        if (scene.name) {
                            html += '<div style="font-size:0.5rem;color:' + (visual.gradient_text ? '#60a5fa' : '#fff') + ';text-align:center;max-width:90%;font-weight:500">' + escapeHtml(scene.name) + '</div>';
                        }
                        if (visual.pipeline && visual.pipeline.length > 0) {
                            html += '<div style="display:flex;gap:0.15rem;margin-top:0.25rem;flex-wrap:wrap;justify-content:center">';
                            visual.pipeline.forEach((step, idx) => {
                                html += '<span style="font-size:0.35rem;background:rgba(255,255,255,0.15);padding:0.1rem 0.2rem;border-radius:2px;color:#fff">' + escapeHtml(step) + '</span>';
                                if (idx < visual.pipeline.length - 1) html += '<span style="color:#60a5fa;font-size:0.35rem">→</span>';
                            });
                            html += '</div>';
                        }
                        if (visual.icons && visual.icons.length > 0) {
                            html += '<div style="display:flex;gap:0.2rem;margin-top:0.2rem;flex-wrap:wrap;justify-content:center">';
                            visual.icons.forEach(icon => {
                                html += '<span style="font-size:0.3rem;background:rgba(96,165,250,0.2);padding:0.1rem 0.15rem;border-radius:2px;color:#60a5fa;text-transform:uppercase">' + escapeHtml(icon) + '</span>';
                            });
                            html += '</div>';
                        }
                        if (visual.terminal) {
                            html += '<div style="background:#000;border-radius:2px;padding:0.2rem;margin-top:0.2rem;width:80%">';
                            (visual.terminal.commands || []).forEach(cmd => {
                                html += '<div style="font-size:0.3rem;font-family:monospace;color:#22c55e">$ ' + escapeHtml(cmd) + '</div>';
                            });
                            html += '</div>';
                        }
                        if (visual.feature_card) {
                            const highlights = { cyan: '#06b6d4', purple: '#a855f7', hot: '#f97316' };
                            const color = highlights[visual.feature_card.highlight] || '#60a5fa';
                            html += '<div style="position:absolute;top:0.25rem;right:0.25rem;width:0.5rem;height:0.5rem;border-radius:50%;background:' + color + ';opacity:0.8"></div>';
                        }
                        if (visual.metrics && visual.metrics.length > 0) {
                            html += '<div style="display:flex;gap:0.15rem;margin-top:0.2rem">';
                            visual.metrics.forEach(m => {
                                html += '<span style="font-size:0.3rem;background:rgba(34,197,94,0.2);padding:0.1rem 0.15rem;border-radius:2px;color:#22c55e">✓ ' + escapeHtml(m) + '</span>';
                            });
                            html += '</div>';
                        }
                        if (visual.cta) {
                            html += '<div style="position:absolute;bottom:0.25rem;font-size:0.25rem;color:#60a5fa">' + escapeHtml(visual.cta.secondary || '') + '</div>';
                        }
                        html += '</div>';
                    }

                    // Old format - text overlays
                    if (scene.text_overlays && scene.text_overlays.length > 0) {
                        scene.text_overlays.forEach(overlay => {
                            const pos = overlay.position || 'center';
                            const isLight = isLightColor(rawBgColor);
                            const rawTextColor = overlay.style?.color || (isLight ? '#1a1a2e' : '#ffffff');
                            const textColor = resolveColor(rawTextColor);
                            const fontSize = Math.min(overlay.style?.font_size || 32, 48);
                            const posClass = 'comp-pos-' + pos.replace(/[^a-z]/g, '-');
                            html += '<div class="script-comp-text ' + posClass + '" style="color:' + escapeHtml(textColor) + ';font-size:' + Math.round(fontSize * 0.25) + 'px">';
                            html += escapeHtml(overlay.text || '');
                            html += '</div>';
                        });
                    }
                    if (sceneType === 'web') {
                        html += '<div class="script-comp-web-indicator"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>Demo</div>';
                    }
                    html += '</div></div>';
                }

                // Voiceover
                if (scene.voiceover) {
                    html += '<div class="script-scene-section">';
                    html += '<div class="script-scene-section-title"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v4M8 23h8"/></svg>Voiceover</div>';
                    html += '<div class="script-scene-voiceover">' + escapeHtml(scene.voiceover.trim()) + '</div>';
                    html += '</div>';
                }

                // Background (old format)
                if (scene.background && !hasVisualProps) {
                    html += '<div class="script-scene-section">';
                    html += '<div class="script-scene-section-title"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/></svg>Background</div>';
                    html += '<div class="script-background">';
                    if (scene.background.color) {
                        html += '<div class="script-background-preview" style="background:' + escapeHtml(scene.background.color) + '"></div>';
                        html += '<span>' + escapeHtml(scene.background.type || 'solid') + ': ' + escapeHtml(scene.background.color) + '</span>';
                    }
                    html += '</div></div>';
                }

                // Visual Properties (new format)
                if (hasVisualProps) {
                    html += '<div class="script-scene-section">';
                    html += '<div class="script-scene-section-title"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>Visual Properties</div>';
                    html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:0.5rem">';
                    if (visual.background) html += '<div style="background:var(--bg);padding:0.5rem;border-radius:0.25rem"><div style="font-size:0.7rem;color:var(--text-muted);margin-bottom:0.25rem">Background</div><div style="font-size:0.85rem;font-weight:500">' + escapeHtml(visual.background) + '</div></div>';
                    if (visual.transition_in) html += '<div style="background:var(--bg);padding:0.5rem;border-radius:0.25rem"><div style="font-size:0.7rem;color:var(--text-muted);margin-bottom:0.25rem">Transition In</div><div style="font-size:0.85rem;font-weight:500">' + escapeHtml(visual.transition_in) + '</div></div>';
                    if (visual.text_effect) html += '<div style="background:var(--bg);padding:0.5rem;border-radius:0.25rem"><div style="font-size:0.7rem;color:var(--text-muted);margin-bottom:0.25rem">Text Effect</div><div style="font-size:0.85rem;font-weight:500">' + escapeHtml(visual.text_effect) + '</div></div>';
                    if (visual.feature_card) html += '<div style="background:var(--bg);padding:0.5rem;border-radius:0.25rem"><div style="font-size:0.7rem;color:var(--text-muted);margin-bottom:0.25rem">Feature Card</div><div style="font-size:0.85rem;font-weight:500">' + escapeHtml(visual.feature_card.icon || '') + ' <span style="color:' + (visual.feature_card.highlight === 'cyan' ? '#06b6d4' : visual.feature_card.highlight === 'purple' ? '#a855f7' : '#f97316') + '">' + escapeHtml(visual.feature_card.highlight || '') + '</span></div></div>';
                    if (visual.show_logo) html += '<div style="background:var(--bg);padding:0.5rem;border-radius:0.25rem"><div style="font-size:0.7rem;color:var(--text-muted);margin-bottom:0.25rem">Logo</div><div style="font-size:0.85rem;font-weight:500;color:var(--success)">✓ Visible</div></div>';
                    if (visual.gradient_text) html += '<div style="background:var(--bg);padding:0.5rem;border-radius:0.25rem"><div style="font-size:0.7rem;color:var(--text-muted);margin-bottom:0.25rem">Gradient Text</div><div style="font-size:0.85rem;font-weight:500;color:var(--success)">✓ Enabled</div></div>';
                    if (visual.glow) html += '<div style="background:var(--bg);padding:0.5rem;border-radius:0.25rem"><div style="font-size:0.7rem;color:var(--text-muted);margin-bottom:0.25rem">Glow Effect</div><div style="font-size:0.85rem;font-weight:500;color:var(--success)">✓ Enabled</div></div>';
                    if (visual.flying_outputs) html += '<div style="background:var(--bg);padding:0.5rem;border-radius:0.25rem"><div style="font-size:0.7rem;color:var(--text-muted);margin-bottom:0.25rem">Flying Outputs</div><div style="font-size:0.85rem;font-weight:500;color:var(--success)">✓ Enabled</div></div>';
                    if (visual.fade_out) html += '<div style="background:var(--bg);padding:0.5rem;border-radius:0.25rem"><div style="font-size:0.7rem;color:var(--text-muted);margin-bottom:0.25rem">Fade Out</div><div style="font-size:0.85rem;font-weight:500;color:var(--success)">✓ Enabled</div></div>';
                    html += '</div></div>';
                }

                // Text overlays
                if (scene.text_overlays && scene.text_overlays.length > 0) {
                    html += '<div class="script-scene-section">';
                    html += '<div class="script-scene-section-title"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/></svg>Text Overlays (' + scene.text_overlays.length + ')</div>';
                    html += '<div class="script-scene-overlays">';
                    scene.text_overlays.forEach(overlay => {
                        html += '<div class="script-overlay-item">';
                        html += '<div class="script-overlay-text">' + escapeHtml(overlay.text || '') + '</div>';
                        html += '<div class="script-overlay-meta">';
                        if (overlay.time !== undefined) html += '<span>@ ' + overlay.time + 's</span>';
                        if (overlay.duration) html += '<span>for ' + overlay.duration + 's</span>';
                        if (overlay.position) html += '<span>' + escapeHtml(overlay.position) + '</span>';
                        html += '</div>';
                        if (overlay.style) {
                            html += '<div class="script-overlay-style">';
                            if (overlay.style.color) html += '<div class="script-overlay-color" style="background:' + escapeHtml(overlay.style.color) + '"></div>';
                            if (overlay.style.font_size) html += '<span style="font-size:0.75rem">' + overlay.style.font_size + 'px</span>';
                            if (overlay.style.animation) html += '<span class="script-scene-badge type-text">' + escapeHtml(overlay.style.animation) + '</span>';
                            html += '</div>';
                        }
                        html += '</div>';
                    });
                    html += '</div></div>';
                }

                // Action script
                if (scene.action) {
                    html += '<div class="script-scene-section">';
                    html += '<div class="script-scene-section-title"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>Action Script</div>';
                    html += '<div class="script-scene-action">' + escapeHtml(scene.action.trim()) + '</div>';
                    html += '</div>';
                }

                // URL (for web scenes)
                if (scene.url) {
                    html += '<div class="script-scene-section">';
                    html += '<div class="script-scene-section-title"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>URL</div>';
                    html += '<div class="script-production-value">' + escapeHtml(scene.url) + '</div>';
                    html += '</div>';
                }

                // Notes/Suggestions section
                html += '<div class="script-scene-section scene-note-section">';
                html += '<div class="script-scene-section-title"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>Notes & Suggestions</div>';
                html += '<textarea id="note-' + sceneId + '" class="scene-note-input" placeholder="Add notes, suggestions, or todos for this scene...">' + escapeHtml(hasNote ? sceneNotes[sceneId].text : '') + '</textarea>';
                html += '<div class="scene-note-actions">';
                html += '<button class="scene-note-btn save" onclick="saveSceneNote(\\'' + sceneId + '\\')">Save Note</button>';
                if (hasNote) {
                    html += '<button class="scene-note-btn delete" onclick="deleteSceneNote(\\'' + sceneId + '\\')">Delete</button>';
                }
                html += '<span class="scene-note-saved" id="note-saved-' + sceneId + '"></span>';
                html += '</div></div>';

                html += '</div></div>';
                // Update cumulative time for fallback calculation (when no video timing available)
                if (!timing) {
                    cumulativeTime += (scene.duration || 0);
                }
            });
            html += '</div></div>';

            return html;
        }

        function toggleScene(index) {
            const scene = document.getElementById('scene-' + index);
            if (scene) scene.classList.toggle('expanded');
        }

        function scrollToScene(index) {
            const scene = document.getElementById('scene-' + index);
            if (scene) {
                scene.scrollIntoView({ behavior: 'smooth', block: 'center' });
                scene.classList.add('expanded');
            }
        }

        // Video playback functions
        let videoSyncInterval = null;
        let currentPlayingScene = -1;

        function toggleVideoPlayback() {
            const video = document.getElementById('script-video-player');
            if (!video) return;

            if (video.paused) {
                video.play();
                updatePlayButton(true);
                startVideoSync();
            } else {
                video.pause();
                updatePlayButton(false);
                stopVideoSync();
            }
        }

        function updatePlayButton(isPlaying) {
            const icon = document.getElementById('video-play-icon');
            const text = document.getElementById('video-play-text');
            if (isPlaying) {
                icon.innerHTML = '<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>';
                text.textContent = 'Pause';
            } else {
                icon.innerHTML = '<polygon points="5,3 19,12 5,21"/>';
                text.textContent = 'Play';
            }
        }

        function seekVideo(event) {
            const video = document.getElementById('script-video-player');
            if (!video) return;

            const progressBar = event.currentTarget;
            const rect = progressBar.getBoundingClientRect();
            const percent = (event.clientX - rect.left) / rect.width;
            video.currentTime = percent * video.duration;
            updateVideoProgress();
            updateCurrentScene(video.currentTime);
        }

        function updateVideoProgress() {
            const video = document.getElementById('script-video-player');
            if (!video) return;

            const progress = document.getElementById('video-progress-fill');
            const currentTime = document.getElementById('video-current-time');

            if (video.duration) {
                const percent = (video.currentTime / video.duration) * 100;
                progress.style.width = percent + '%';
            }
            currentTime.textContent = formatDuration(Math.floor(video.currentTime));
        }

        function startVideoSync() {
            if (videoSyncInterval) clearInterval(videoSyncInterval);
            videoSyncInterval = setInterval(() => {
                const video = document.getElementById('script-video-player');
                if (!video) return;

                updateVideoProgress();
                updateCurrentScene(video.currentTime);

                // Check if video ended
                if (video.ended) {
                    updatePlayButton(false);
                    stopVideoSync();
                    clearPlayingScene();
                }
            }, 100);
        }

        function stopVideoSync() {
            if (videoSyncInterval) {
                clearInterval(videoSyncInterval);
                videoSyncInterval = null;
            }
        }

        function updateCurrentScene(currentTime) {
            const scenes = document.querySelectorAll('.script-scene');
            let foundScene = -1;

            scenes.forEach((scene, index) => {
                const start = parseFloat(scene.dataset.start || 0);
                const end = parseFloat(scene.dataset.end || 0);

                if (currentTime >= start && currentTime < end) {
                    foundScene = index;
                }
            });

            if (foundScene !== currentPlayingScene) {
                clearPlayingScene();
                if (foundScene >= 0) {
                    const scene = document.getElementById('scene-' + foundScene);
                    if (scene) {
                        scene.classList.add('playing');
                        // Scroll scene into view if not visible
                        const rect = scene.getBoundingClientRect();
                        const viewHeight = window.innerHeight;
                        if (rect.top < 0 || rect.bottom > viewHeight) {
                            scene.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        }
                    }
                }
                currentPlayingScene = foundScene;
            }
        }

        function clearPlayingScene() {
            document.querySelectorAll('.script-scene.playing').forEach(el => {
                el.classList.remove('playing');
            });
            currentPlayingScene = -1;
        }

        function playFromScene(sceneIndex, startTime) {
            const video = document.getElementById('script-video-player');
            if (!video) return;

            video.currentTime = startTime;
            video.play();
            updatePlayButton(true);
            startVideoSync();

            // Scroll to the video player
            const videoSection = document.querySelector('.script-video-section');
            if (videoSection) {
                videoSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }

        // Scene-specific video player functions
        const sceneVideoLoops = {};
        const sceneVideoIntervals = {};

        function toggleSceneVideo(sceneIndex) {
            const video = document.getElementById('scene-video-' + sceneIndex);
            if (!video) return;

            const startTime = parseFloat(video.dataset.start) || 0;
            const endTime = parseFloat(video.dataset.end) || 0;

            if (video.paused) {
                // If video hasn't been set to scene start yet, set it
                if (video.currentTime < startTime || video.currentTime >= endTime) {
                    video.currentTime = startTime;
                }
                video.play();
                updateSceneVideoIcon(sceneIndex, true);
                startSceneVideoSync(sceneIndex, startTime, endTime);
            } else {
                video.pause();
                updateSceneVideoIcon(sceneIndex, false);
                stopSceneVideoSync(sceneIndex);
            }
        }

        function updateSceneVideoIcon(sceneIndex, isPlaying) {
            const icon = document.getElementById('scene-video-icon-' + sceneIndex);
            if (icon) {
                icon.innerHTML = isPlaying
                    ? '<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>'
                    : '<polygon points="5,3 19,12 5,21"/>';
            }
        }

        function startSceneVideoSync(sceneIndex, startTime, endTime) {
            stopSceneVideoSync(sceneIndex);
            const video = document.getElementById('scene-video-' + sceneIndex);
            const progress = document.getElementById('scene-progress-' + sceneIndex);
            const timeEl = document.getElementById('scene-time-' + sceneIndex);
            const duration = endTime - startTime;

            sceneVideoIntervals[sceneIndex] = setInterval(() => {
                if (!video) return;
                const currentTime = video.currentTime;
                const sceneTime = currentTime - startTime;
                const pct = Math.max(0, Math.min(100, (sceneTime / duration) * 100));

                if (progress) progress.style.width = pct + '%';
                if (timeEl) timeEl.textContent = formatDuration(Math.floor(Math.max(0, sceneTime))) + ' / ' + formatDuration(Math.floor(duration));

                // Loop or stop at scene end
                if (currentTime >= endTime) {
                    if (sceneVideoLoops[sceneIndex]) {
                        video.currentTime = startTime;
                    } else {
                        video.pause();
                        video.currentTime = startTime;
                        updateSceneVideoIcon(sceneIndex, false);
                        stopSceneVideoSync(sceneIndex);
                        if (progress) progress.style.width = '0%';
                        if (timeEl) timeEl.textContent = '0:00 / ' + formatDuration(Math.floor(duration));
                    }
                }
            }, 100);
        }

        function stopSceneVideoSync(sceneIndex) {
            if (sceneVideoIntervals[sceneIndex]) {
                clearInterval(sceneVideoIntervals[sceneIndex]);
                delete sceneVideoIntervals[sceneIndex];
            }
        }

        function seekSceneVideo(event, sceneIndex) {
            const video = document.getElementById('scene-video-' + sceneIndex);
            if (!video) return;

            const startTime = parseFloat(video.dataset.start) || 0;
            const endTime = parseFloat(video.dataset.end) || 0;
            const duration = endTime - startTime;

            const rect = event.currentTarget.getBoundingClientRect();
            const pct = (event.clientX - rect.left) / rect.width;
            video.currentTime = startTime + (pct * duration);
        }

        function toggleSceneLoop(sceneIndex) {
            sceneVideoLoops[sceneIndex] = !sceneVideoLoops[sceneIndex];
            const btn = document.getElementById('scene-loop-btn-' + sceneIndex);
            if (btn) {
                btn.style.color = sceneVideoLoops[sceneIndex] ? 'var(--primary)' : 'var(--text-muted)';
                btn.style.background = sceneVideoLoops[sceneIndex] ? 'rgba(59, 130, 246, 0.2)' : 'transparent';
            }
        }

        function renderVideo() {
            alert('Video rendering requires CLI: media-engine video build <script>');
        }

        function formatDuration(seconds) {
            seconds = Math.floor(seconds);
            const mins = Math.floor(seconds / 60);
            const secs = seconds % 60;
            return mins + ':' + String(secs).padStart(2, '0');
        }

        function countWords(text) {
            if (!text) return 0;
            return text.trim().split(/\\s+/).filter(w => w.length > 0).length;
        }

        // Color token mapping for video scripts
        const colorTokens = {
            'dark_bg': '#0f172a',
            'dark_background': '#0f172a',
            'dark': '#1e293b',
            'light_bg': '#f8fafc',
            'light_background': '#f8fafc',
            'light': '#ffffff',
            'text_primary': '#f1f5f9',
            'text_muted': '#94a3b8',
            'text_dark': '#1e293b',
            'accent': '#4299e1',
            'primary': '#1a365d',
            'secondary': '#475569',
            'success': '#059669',
            'warning': '#d97706',
            'error': '#dc2626',
        };

        function resolveColor(color) {
            if (!color) return '#1a1a2e';
            if (color.startsWith('#')) return color;
            return colorTokens[color] || colorTokens[color.toLowerCase()] || '#1a1a2e';
        }

        function isLightColor(color) {
            const resolved = resolveColor(color);
            if (!resolved || !resolved.startsWith('#')) return false;
            const hex = resolved.slice(1);
            const r = parseInt(hex.substr(0, 2), 16);
            const g = parseInt(hex.substr(2, 2), 16);
            const b = parseInt(hex.substr(4, 2), 16);
            const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
            return luminance > 0.5;
        }

        function setPreviewMode(mode) {
            previewMode = mode;
            document.querySelectorAll('.preview-tab').forEach(el => el.classList.remove('active'));
            event.target.classList.add('active');
            renderDocPreview();
        }

        // ==================== SLIDE DECK VIEWER ====================
        let currentSlideIndex = 0;
        let slidesData = null;

        function renderSlideViewer(data) {
            slidesData = data;
            currentSlideIndex = 0;

            const slides = data.slides || [];
            const deckTitle = data.title || 'Untitled Presentation';
            const deckSubtitle = data.subtitle || '';

            let html = '<div class="slide-viewer">';
            html += '<div class="slide-viewer-main">';

            // Sidebar with thumbnails
            html += '<div class="slide-viewer-sidebar">';
            slides.forEach((slide, idx) => {
                const isActive = idx === 0 ? 'active' : '';
                const thumbTitle = slide.title || slide.quote?.substring(0, 30) || 'Slide ' + (idx + 1);
                html += '<div class="slide-thumb ' + isActive + '" onclick="goToSlide(' + idx + ')" data-slide="' + idx + '">';
                html += renderSlideThumb(slide, idx);
                html += '<span class="slide-thumb-number">' + (idx + 1) + '</span>';
                html += '</div>';
            });
            html += '</div>';

            // Main content area
            html += '<div class="slide-viewer-content">';
            html += '<div class="slide-canvas" id="slide-canvas">';
            html += renderSlide(slides[0], 0);
            html += '</div>';

            // Speaker notes
            const firstNotes = slides[0]?.notes || '';
            html += '<div class="slide-notes" id="slide-notes" style="display:' + (firstNotes ? 'block' : 'none') + '">';
            html += '<div class="slide-notes-label"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>Speaker Notes</div>';
            html += '<div id="slide-notes-content">' + escapeHtml(firstNotes) + '</div>';
            html += '</div>';

            html += '</div></div>';

            // Navigation controls
            html += '<div class="slide-controls">';
            html += '<button class="slide-nav-btn" onclick="prevSlide()" id="prev-slide-btn" disabled>';
            html += '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>';
            html += 'Previous';
            html += '</button>';
            html += '<span class="slide-counter" id="slide-counter">1 / ' + slides.length + '</span>';
            html += '<button class="slide-nav-btn" onclick="nextSlide()" id="next-slide-btn"' + (slides.length <= 1 ? ' disabled' : '') + '>';
            html += 'Next';
            html += '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>';
            html += '</button>';
            html += '</div>';

            html += '</div>';
            return html;
        }

        function renderSlideThumb(slide, idx) {
            const type = slide.type || 'content';
            let html = '<div class="slide-thumb-content">';

            if (type === 'title' || type === 'section') {
                html += '<div class="slide-thumb-title">' + escapeHtml(slide.title || '') + '</div>';
                if (slide.subtitle) html += '<div style="font-size:0.35rem;color:var(--text-muted)">' + escapeHtml(slide.subtitle.substring(0, 30)) + '</div>';
            } else if (type === 'quote') {
                html += '<div style="font-style:italic;font-size:0.35rem">"' + escapeHtml((slide.quote || '').substring(0, 40)) + '..."</div>';
            } else if (type === 'two_column') {
                html += '<div class="slide-thumb-title">' + escapeHtml(slide.title || '') + '</div>';
                html += '<div style="display:flex;gap:0.1rem;width:100%"><div style="flex:1;background:var(--border);height:0.5rem;border-radius:1px"></div><div style="flex:1;background:var(--border);height:0.5rem;border-radius:1px"></div></div>';
            } else {
                html += '<div class="slide-thumb-title">' + escapeHtml(slide.title || '') + '</div>';
                const bullets = slide.bullets || [];
                if (bullets.length > 0) {
                    html += '<div style="width:100%;text-align:left">';
                    bullets.slice(0, 3).forEach(() => {
                        html += '<div style="background:var(--border);height:2px;margin:1px 0;border-radius:1px"></div>';
                    });
                    html += '</div>';
                }
            }
            html += '</div>';
            return html;
        }

        function renderSlide(slide, idx) {
            if (!slide) return '<div class="empty-state">No slide data</div>';

            const type = slide.type || 'content';
            let html = '<div class="slide-frame slide-type-' + type + '">';
            html += '<div class="slide-frame-inner">';

            switch (type) {
                case 'title':
                    html += '<div class="slide-main-title">' + escapeHtml(slide.title || '') + '</div>';
                    if (slide.subtitle) html += '<div class="slide-subtitle">' + escapeHtml(slide.subtitle) + '</div>';
                    html += '<div class="slide-accent"></div>';
                    break;

                case 'section':
                    html += '<div class="slide-main-title">' + escapeHtml(slide.title || '') + '</div>';
                    if (slide.subtitle) html += '<div class="slide-subtitle">' + escapeHtml(slide.subtitle) + '</div>';
                    break;

                case 'content':
                    html += '<div class="slide-header">';
                    html += '<div class="slide-main-title">' + escapeHtml(slide.title || '') + '</div>';
                    html += '<div class="slide-title-accent"></div>';
                    html += '</div>';
                    if (slide.bullets && slide.bullets.length > 0) {
                        html += '<ul class="slide-bullets">';
                        slide.bullets.forEach(bullet => {
                            html += '<li class="slide-bullet">' + escapeHtml(bullet) + '</li>';
                        });
                        html += '</ul>';
                    }
                    break;

                case 'two_column':
                    html += '<div class="slide-header">';
                    html += '<div class="slide-main-title">' + escapeHtml(slide.title || '') + '</div>';
                    html += '</div>';
                    html += '<div class="slide-columns">';
                    html += '<div class="slide-column">';
                    if (slide.left_title) html += '<div class="slide-column-title">' + escapeHtml(slide.left_title) + '</div>';
                    if (slide.left_bullets && slide.left_bullets.length > 0) {
                        html += '<ul class="slide-bullets">';
                        slide.left_bullets.forEach(bullet => {
                            html += '<li class="slide-bullet">' + escapeHtml(bullet) + '</li>';
                        });
                        html += '</ul>';
                    }
                    html += '</div>';
                    html += '<div class="slide-column">';
                    if (slide.right_title) html += '<div class="slide-column-title">' + escapeHtml(slide.right_title) + '</div>';
                    if (slide.right_bullets && slide.right_bullets.length > 0) {
                        html += '<ul class="slide-bullets">';
                        slide.right_bullets.forEach(bullet => {
                            html += '<li class="slide-bullet">' + escapeHtml(bullet) + '</li>';
                        });
                        html += '</ul>';
                    }
                    html += '</div></div>';
                    break;

                case 'quote':
                    html += '<div class="slide-quote-mark">"</div>';
                    html += '<div class="slide-quote-text">' + escapeHtml(slide.quote || '') + '</div>';
                    if (slide.author) html += '<div class="slide-quote-author">' + escapeHtml(slide.author) + '</div>';
                    break;

                case 'image':
                    html += '<div class="slide-header">';
                    html += '<div class="slide-main-title">' + escapeHtml(slide.title || '') + '</div>';
                    html += '</div>';
                    html += '<div class="slide-image-container">';
                    if (slide.image_path) {
                        html += '<img src="' + escapeHtml(slide.image_path) + '" alt="' + escapeHtml(slide.title || 'Slide image') + '" style="max-width:100%;max-height:100%;object-fit:contain">';
                    } else {
                        html += '<div class="slide-image-placeholder">';
                        html += '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>';
                        html += '<span>Image placeholder</span>';
                        html += '</div>';
                    }
                    html += '</div>';
                    if (slide.image_caption) html += '<div class="slide-image-caption">' + escapeHtml(slide.image_caption) + '</div>';
                    break;

                default:
                    html += '<div class="slide-main-title">' + escapeHtml(slide.title || 'Untitled Slide') + '</div>';
            }

            html += '</div></div>';
            return html;
        }

        function goToSlide(idx) {
            if (!slidesData || !slidesData.slides) return;
            const slides = slidesData.slides;
            if (idx < 0 || idx >= slides.length) return;

            currentSlideIndex = idx;

            // Update canvas
            document.getElementById('slide-canvas').innerHTML = renderSlide(slides[idx], idx);

            // Update counter
            document.getElementById('slide-counter').textContent = (idx + 1) + ' / ' + slides.length;

            // Update buttons
            document.getElementById('prev-slide-btn').disabled = idx === 0;
            document.getElementById('next-slide-btn').disabled = idx === slides.length - 1;

            // Update thumbnails
            document.querySelectorAll('.slide-thumb').forEach((el, i) => {
                el.classList.toggle('active', i === idx);
            });

            // Scroll thumbnail into view
            const activeThumb = document.querySelector('.slide-thumb.active');
            if (activeThumb) activeThumb.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

            // Update notes
            const notes = slides[idx].notes || '';
            const notesEl = document.getElementById('slide-notes');
            const notesContentEl = document.getElementById('slide-notes-content');
            notesEl.style.display = notes ? 'block' : 'none';
            notesContentEl.textContent = notes;
        }

        function prevSlide() {
            goToSlide(currentSlideIndex - 1);
        }

        function nextSlide() {
            goToSlide(currentSlideIndex + 1);
        }

        // Keyboard navigation for slides
        document.addEventListener('keydown', function(e) {
            if (!slidesData || document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'TEXTAREA') return;
            const docsTab = document.getElementById('tab-documents');
            if (!docsTab || docsTab.style.display === 'none') return;
            if (!currentDocData?.isSlides) return;

            if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
                prevSlide();
                e.preventDefault();
            } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === ' ') {
                nextSlide();
                e.preventDefault();
            }
        });

        // ==================== METADATA VIEWER ====================
        function renderMetadataViewer(metadata, docType) {
            if (!metadata || Object.keys(metadata).length === 0) {
                return '<div class="empty-state">No metadata available</div>';
            }

            let html = '<div class="metadata-viewer">';

            // Group metadata into sections
            const documentInfo = {};
            const statusInfo = {};
            const translationInfo = {};
            const dateInfo = {};
            const referencesInfo = {};
            const otherInfo = {};

            // Categorize metadata fields
            const documentFields = ['title', 'description', 'summary', 'author', 'category', 'reference_id', 'type'];
            const statusFields = ['status', 'accuracy', 'version', 'review_status'];
            const translationFields = ['language', 'source_document', 'source_version', 'translated_from'];
            const dateFields = ['last_modified', 'last_reviewed', 'created', 'published', 'freshness_days'];
            const referenceFields = ['references', 'depends_on', 'tags', 'related'];

            for (const [key, value] of Object.entries(metadata)) {
                if (documentFields.includes(key)) documentInfo[key] = value;
                else if (statusFields.includes(key)) statusInfo[key] = value;
                else if (translationFields.includes(key)) translationInfo[key] = value;
                else if (dateFields.includes(key)) dateInfo[key] = value;
                else if (referenceFields.includes(key)) referencesInfo[key] = value;
                else otherInfo[key] = value;
            }

            // Render sections
            if (Object.keys(documentInfo).length > 0) {
                html += renderMetadataSection('Document', documentInfo, 'info', '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>');
            }

            if (Object.keys(statusInfo).length > 0) {
                html += renderMetadataSection('Status', statusInfo, 'status', '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>');
            }

            if (Object.keys(translationInfo).length > 0) {
                html += renderMetadataSection('Translation', translationInfo, 'translation', '<circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>');
            }

            if (Object.keys(dateInfo).length > 0) {
                html += renderMetadataSection('Dates', dateInfo, 'dates', '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>');
            }

            if (Object.keys(referencesInfo).length > 0) {
                html += renderMetadataSection('References', referencesInfo, 'refs', '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>');
            }

            if (Object.keys(otherInfo).length > 0) {
                html += renderMetadataSection('Other', otherInfo, 'other', '<circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/>');
            }

            html += '</div>';
            return html;
        }

        function renderMetadataSection(title, data, sectionType, svgPath) {
            const count = Object.keys(data).length;
            let html = '<div class="metadata-section" data-section="' + sectionType + '">';
            html += '<div class="metadata-section-header" onclick="toggleMetadataSection(this)">';
            html += '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' + svgPath + '</svg>';
            html += '<span class="metadata-section-title">' + title + '</span>';
            html += '<span class="metadata-section-badge">' + count + '</span>';
            html += '<svg class="metadata-section-toggle" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>';
            html += '</div>';
            html += '<div class="metadata-section-content">';

            for (const [key, value] of Object.entries(data)) {
                html += renderMetadataRow(key, value);
            }

            html += '</div></div>';
            return html;
        }

        function renderMetadataRow(key, value) {
            let html = '<div class="metadata-row">';
            html += '<div class="metadata-key">' + escapeHtml(key.replace(/_/g, ' ')) + '</div>';
            html += '<div class="metadata-value">';

            // Special formatting based on key type
            if (key === 'version' && value) {
                html += '<span class="metadata-badge badge-version">v' + escapeHtml(String(value)) + '</span>';
            } else if (key === 'status' && value) {
                html += '<span class="metadata-badge badge-status status-' + String(value).toLowerCase() + '">' + escapeHtml(String(value)) + '</span>';
            } else if (key === 'accuracy' && value) {
                html += '<span class="metadata-badge badge-accuracy">' + escapeHtml(String(value)) + '</span>';
            } else if (key === 'language' && value) {
                html += '<span class="metadata-badge badge-language">' + escapeHtml(String(value).toUpperCase()) + '</span>';
            } else if (key === 'tags' && Array.isArray(value)) {
                html += '<div class="metadata-tags">';
                value.forEach(tag => {
                    html += '<span class="metadata-tag">' + escapeHtml(String(tag)) + '</span>';
                });
                html += '</div>';
            } else if ((key === 'depends_on' || key === 'related') && Array.isArray(value)) {
                if (value.length === 0) {
                    html += '<span class="metadata-empty">None</span>';
                } else {
                    html += '<ul class="metadata-list">';
                    value.forEach(item => {
                        html += '<li>' + escapeHtml(String(item)) + '</li>';
                    });
                    html += '</ul>';
                }
            } else if (key === 'references' && Array.isArray(value)) {
                if (value.length === 0) {
                    html += '<span class="metadata-empty">None</span>';
                } else {
                    html += '<ul class="metadata-list">';
                    value.forEach(ref => {
                        if (typeof ref === 'object') {
                            html += '<li>' + escapeHtml(ref.title || ref.id || JSON.stringify(ref)) + '</li>';
                        } else {
                            html += '<li>' + escapeHtml(String(ref)) + '</li>';
                        }
                    });
                    html += '</ul>';
                }
            } else if ((key.includes('date') || key.includes('modified') || key.includes('reviewed') || key.includes('created') || key.includes('published')) && value) {
                const dateStr = String(value);
                html += '<div class="metadata-date">';
                html += '<span>' + escapeHtml(dateStr) + '</span>';
                try {
                    const date = new Date(dateStr);
                    if (!isNaN(date.getTime())) {
                        const days = Math.floor((Date.now() - date.getTime()) / (1000 * 60 * 60 * 24));
                        if (days === 0) html += '<span class="metadata-date-relative">(today)</span>';
                        else if (days === 1) html += '<span class="metadata-date-relative">(yesterday)</span>';
                        else if (days < 30) html += '<span class="metadata-date-relative">(' + days + ' days ago)</span>';
                        else if (days < 365) html += '<span class="metadata-date-relative">(' + Math.floor(days/30) + ' months ago)</span>';
                    }
                } catch(e) {}
                html += '</div>';
            } else if (typeof value === 'object' && value !== null) {
                html += '<div class="metadata-json">' + escapeHtml(JSON.stringify(value, null, 2)) + '</div>';
            } else if (value === null || value === undefined || value === '') {
                html += '<span class="metadata-empty">Not set</span>';
            } else {
                html += escapeHtml(String(value));
            }

            html += '</div></div>';
            return html;
        }

        function toggleMetadataSection(header) {
            const section = header.parentElement;
            section.classList.toggle('collapsed');
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Open file from issue click
        let pendingLine = 0;
        async function openIssueFile(filePath, line) {
            pendingLine = line;

            const langMatch = filePath.match(/\\/content\\/([a-z]{2})\\//);
            const lang = langMatch ? langMatch[1] : projectLanguages[0];

            let fileType = 'chapter';
            if (filePath.includes('/scripts/')) fileType = 'script';
            else if (filePath.includes('/diagrams/')) fileType = 'diagram';
            else if (filePath.includes('/slides/')) fileType = 'slides';
            else if (filePath.includes('/data/')) fileType = 'data';
            else if (filePath.includes('/demos/')) fileType = 'demo';

            document.querySelectorAll('[id^="tab-"]').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            const tabDocs = document.getElementById('tab-documents');
            if (tabDocs) tabDocs.style.display = 'block';
            const tabs = document.querySelectorAll('.tab');
            if (tabs[1]) tabs[1].classList.add('active');

            if (!documentsLoaded) {
                await initDocumentBrowser();
            }

            const select = document.getElementById('lang-select');
            if (select.value !== lang) {
                select.value = lang;
                await loadDocuments();
            }

            previewMode = 'source';
            document.querySelectorAll('.preview-tab').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.preview-tab')[1].classList.add('active');

            await loadDocumentDirect(filePath, fileType);
        }

        async function loadDocumentDirect(path, type) {
            currentDoc = path;

            const previewContent = document.getElementById('preview-content');
            previewContent.innerHTML = '<div class="loading">Loading...</div>';

            try {
                if (type === 'chapter') {
                    const data = await fetchAPI('/api/document?path=' + encodeURIComponent(path));
                    currentDocData = data;
                    document.getElementById('preview-title').textContent = data.title;
                    document.getElementById('preview-path').textContent = data.path;
                } else {
                    const data = await fetchAPI('/api/file?path=' + encodeURIComponent(path));
                    currentDocData = {
                        title: data.filename,
                        content: data.content,
                        html: '<pre class="yaml-viewer">' + escapeHtml(data.content) + '</pre>',
                        metadata: data.parsed || {},
                        isYaml: true
                    };
                    document.getElementById('preview-title').textContent = data.filename;
                    document.getElementById('preview-path').textContent = data.path;
                }

                renderDocPreviewWithHighlight(pendingLine);
                pendingLine = 0;

                document.querySelectorAll('.doc-item').forEach(el => el.classList.remove('active'));
            } catch (e) {
                previewContent.innerHTML = '<div class="empty-state">Error loading document</div>';
            }
        }

        function renderDocPreviewWithHighlight(line) {
            const previewContent = document.getElementById('preview-content');
            if (!currentDocData) return;

            previewContent.className = 'doc-preview-content source-mode';
            const lines = currentDocData.content.split('\\n');
            let html = '<div class="source-lines">';
            for (let i = 0; i < lines.length; i++) {
                const lineNum = i + 1;
                const highlight = lineNum === line ? ' highlight-line' : '';
                const lineId = lineNum === line ? ' id="target-line"' : '';
                html += '<div class="source-line' + highlight + '"' + lineId + '>';
                html += '<span class="line-number">' + lineNum + '</span>';
                html += '<span class="line-content">' + escapeHtml(lines[i]) + '</span>';
                html += '</div>';
            }
            html += '</div>';
            previewContent.innerHTML = html;

            if (line > 0) {
                setTimeout(() => {
                    const targetLine = document.getElementById('target-line');
                    if (targetLine) {
                        targetLine.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }, 100);
            }
        }

        // Dark/Light mode toggle
        let darkMode = true;
        function toggleTheme() {
            darkMode = !darkMode;
            document.body.classList.toggle('light-mode', !darkMode);
            localStorage.setItem('theme', darkMode ? 'dark' : 'light');
            document.getElementById('theme-toggle').textContent = darkMode ? '\\u2600\\uFE0F' : '\\uD83C\\uDF19';
        }

        // Load saved theme
        (function() {
            if (localStorage.getItem('theme') === 'light') {
                darkMode = false;
                document.body.classList.add('light-mode');
            }
            document.addEventListener('DOMContentLoaded', function() {
                document.getElementById('theme-toggle').textContent = darkMode ? '\\u2600\\uFE0F' : '\\uD83C\\uDF19';
            });
        })();

        function connectWebSocket() {
            ws = new WebSocket('ws://' + window.location.host + '/ws/' + userId);
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'user_joined' || data.type === 'user_left') {
                    updateOnlineUsers();
                } else if (data.type === 'document_saved') {
                    loadAll();
                }
            };
            ws.onclose = function() {
                setTimeout(connectWebSocket, 3000);
            };
        }

        function updateOnlineUsers() {
            // Placeholder - would show connected users
        }

        async function loadAll() {
            await Promise.all([
                loadProject(),
                loadStatus(),
                loadTranslations(),
                loadMatrix(),
                loadQuality(),
                loadAuditLog(),
                loadFreshnessOverview(),
            ]);
        }

        loadAll();
        connectWebSocket();
        startQualityAutoRefresh();
        // Note: Quality has its own auto-refresh that only runs when tab is visible
        // This interval refreshes other data
        setInterval(function() {
            loadProject();
            loadStatus();
            loadTranslations();
            loadMatrix();
            loadAuditLog();
        }, 30000);
    </script>
"""
