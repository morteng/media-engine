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
                if (qualityAutoRefresh && document.getElementById('tab-quality').style.display !== 'none') {
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

        function showTab(name) {
            document.querySelectorAll('[id^="tab-"]').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            document.getElementById('tab-' + name).style.display = 'block';
            event.target.classList.add('active');
            if (name === 'documents' && !documentsLoaded) {
                initDocumentBrowser();
            }
            if (name === 'media' && !mediaLoaded) {
                loadMedia();
            }
            if (name === 'packs' && !packsLoaded) {
                loadPacks();
            }
            if (name === 'assets' && !assetsLoaded) {
                loadAssets();
            }
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
                    currentDocData = data;
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
                        video: data.video || null
                    };
                    currentScriptPath = path;
                    document.getElementById('preview-title').textContent = data.parsed?.title || data.filename;
                    document.getElementById('preview-path').textContent = data.path;
                    // Load scene notes for this script
                    await loadSceneNotes(path);
                    renderDocPreview();
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

            if (previewMode === 'preview') {
                previewContent.className = 'doc-preview-content preview-mode';
                previewContent.innerHTML = currentDocData.html || '<pre class="yaml-viewer">' + escapeHtml(currentDocData.content) + '</pre>';
            } else if (previewMode === 'source') {
                previewContent.className = 'doc-preview-content source-mode';
                previewContent.textContent = currentDocData.content;
            } else if (previewMode === 'metadata') {
                previewContent.className = 'doc-preview-content';
                let html = '<div class="doc-metadata"><dl>';
                for (const [key, value] of Object.entries(currentDocData.metadata || {})) {
                    html += '<dt>' + escapeHtml(key) + '</dt>';
                    html += '<dd>' + escapeHtml(typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)) + '</dd>';
                }
                html += '</dl></div>';
                if (Object.keys(currentDocData.metadata || {}).length === 0) {
                    html = '<div class="empty-state">No metadata available</div>';
                }
                previewContent.innerHTML = html;
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

            // Timeline
            html += '<div class="script-timeline">';
            html += '<div class="script-timeline-title"><span>Scene Timeline</span><span style="font-weight:normal;color:var(--text-muted)">' + formatDuration(totalDuration) + ' total</span></div>';
            html += '<div class="script-timeline-bar">';
            let cumulativeTime = 0;
            scenes.forEach((scene, i) => {
                const width = totalDuration > 0 ? ((scene.duration || 0) / totalDuration * 100) : 0;
                const color = sceneColors[i % sceneColors.length];
                html += '<div class="script-timeline-segment" style="width:' + width + '%;background:' + color + '" title="' + escapeHtml(scene.name || scene.id) + ' (' + (scene.duration || 0) + 's)" onclick="scrollToScene(' + i + ')"></div>';
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
                const sceneStartTime = cumulativeTime;

                html += '<div class="script-scene" id="scene-' + i + '" data-start="' + sceneStartTime + '" data-end="' + (sceneStartTime + (scene.duration || 0)) + '">';
                html += '<div class="script-scene-header" onclick="toggleScene(' + i + ')">';
                html += '<div class="script-scene-number" style="background:' + color + '">' + (i + 1) + '</div>';
                html += '<div class="script-scene-info">';
                html += '<div class="script-scene-name">' + escapeHtml(scene.name || 'Scene ' + (i + 1)) + '</div>';
                html += '<div class="script-scene-id">' + escapeHtml(sceneId) + ' \\u00B7 starts at ' + formatDuration(cumulativeTime) + '</div>';
                html += '</div>';
                html += '<div class="script-scene-badges">';
                html += '<span class="script-scene-badge ' + typeClass + '">' + escapeHtml(sceneType.replace('_', ' ')) + '</span>';
                html += '<span class="script-scene-badge duration">' + (scene.duration || 0) + 's</span>';
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
                    const sceneDuration = scene.duration || 0;
                    html += '<div class="script-scene-section scene-video-section">';
                    html += '<div class="script-scene-section-title"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5,3 19,12 5,21"/></svg>Scene Preview (' + sceneDuration + 's)</div>';
                    html += '<div class="scene-video-container">';
                    html += '<video class="scene-video-player" id="scene-video-' + i + '" preload="metadata" data-start="' + sceneStartTime + '" data-end="' + (sceneStartTime + sceneDuration) + '">';
                    html += '<source src="' + escapeHtml(video.videoUrl) + '" type="video/mp4">';
                    html += '</video>';
                    html += '<div class="scene-video-controls">';
                    html += '<button class="scene-video-play-btn" onclick="toggleSceneVideo(' + i + ')">';
                    html += '<svg id="scene-video-icon-' + i + '" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg>';
                    html += '</button>';
                    html += '<div class="scene-video-progress" onclick="seekSceneVideo(event, ' + i + ')">';
                    html += '<div class="scene-video-progress-fill" id="scene-progress-' + i + '" style="width:0%"></div>';
                    html += '</div>';
                    html += '<span class="scene-video-time" id="scene-time-' + i + '">0:00 / ' + formatDuration(sceneDuration) + '</span>';
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
                cumulativeTime += (scene.duration || 0);
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
            document.getElementById('tab-documents').style.display = 'block';
            document.querySelectorAll('.tab')[1].classList.add('active');

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
