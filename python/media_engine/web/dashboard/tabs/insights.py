"""
Dashboard Insights Tab

Provides a consolidated view of project health, statistics, and intelligence
features from the insights module.
"""


def get_insights_tab() -> str:
    """Generate the insights tab HTML with health score and metrics."""
    return """
        <div id="tab-insights">
            <!-- Health Score Section -->
            <div class="grid grid-3" style="margin-bottom: 1.5rem;">
                <div class="card" style="text-align: center;">
                    <div class="card-title">Project Health</div>
                    <div class="health-score-circle" id="health-score-circle">
                        <svg viewBox="0 0 36 36" class="circular-chart">
                            <path class="circle-bg"
                                d="M18 2.0845
                                   a 15.9155 15.9155 0 0 1 0 31.831
                                   a 15.9155 15.9155 0 0 1 0 -31.831"
                            />
                            <path class="circle" id="health-circle"
                                stroke-dasharray="0, 100"
                                d="M18 2.0845
                                   a 15.9155 15.9155 0 0 1 0 31.831
                                   a 15.9155 15.9155 0 0 1 0 -31.831"
                            />
                            <text x="18" y="20.35" class="percentage" id="health-score-text">-</text>
                        </svg>
                    </div>
                    <div class="stat-label" id="health-grade">Loading...</div>
                </div>
                <div class="card">
                    <div class="card-title">Component Breakdown</div>
                    <div id="health-components">
                        <div class="loading">Loading...</div>
                    </div>
                </div>
                <div class="card">
                    <div class="card-title">Recommendations</div>
                    <div id="health-recommendations">
                        <div class="loading">Loading...</div>
                    </div>
                </div>
            </div>

            <!-- Statistics Section -->
            <div class="grid grid-4" style="margin-bottom: 1.5rem;">
                <div class="card">
                    <div class="card-title">Total Documents</div>
                    <div class="stat" id="insights-docs">-</div>
                    <div class="stat-label" id="insights-docs-languages">across languages</div>
                </div>
                <div class="card">
                    <div class="card-title">Total Words</div>
                    <div class="stat" id="insights-words">-</div>
                    <div class="stat-label">content words</div>
                </div>
                <div class="card">
                    <div class="card-title">Activity</div>
                    <div class="stat" id="insights-activity">-</div>
                    <div class="stat-label">modified this week</div>
                </div>
                <div class="card">
                    <div class="card-title">Issues</div>
                    <div class="stat" id="insights-issues">-</div>
                    <div class="stat-label">requiring attention</div>
                </div>
            </div>

            <!-- Detailed Insights -->
            <div class="grid grid-2">
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">Content Velocity</div>
                        <button class="btn btn-sm" onclick="refreshVelocity()">Refresh</button>
                    </div>
                    <div id="velocity-content">
                        <div class="loading">Loading...</div>
                    </div>
                </div>
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">Incomplete Content</div>
                        <button class="btn btn-sm" onclick="refreshIncomplete()">Refresh</button>
                    </div>
                    <div id="incomplete-content">
                        <div class="loading">Loading...</div>
                    </div>
                </div>
            </div>

            <div class="grid grid-2" style="margin-top: 1.5rem;">
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">Translation Parity</div>
                    </div>
                    <div id="parity-content">
                        <div class="loading">Loading...</div>
                    </div>
                </div>
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">Knowledge Graph</div>
                        <button class="btn btn-sm" onclick="downloadGraph()">Export DOT</button>
                    </div>
                    <div id="graph-summary">
                        <div class="loading">Loading...</div>
                    </div>
                </div>
            </div>

            <div class="grid grid-1" style="margin-top: 1.5rem;">
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">Suggested Reading Path</div>
                        <div style="display: flex; gap: 0.5rem;">
                            <button class="btn btn-sm" onclick="showPath('dependency')">By Prerequisites</button>
                            <button class="btn btn-sm" onclick="showPath('complexity')">By Complexity</button>
                        </div>
                    </div>
                    <div id="reading-path">
                        <div class="loading">Loading...</div>
                    </div>
                </div>
            </div>
        </div>
"""


def get_insights_styles() -> str:
    """Additional CSS styles for the insights tab."""
    return """<style>
        /* Health Score Circle */
        .health-score-circle {
            width: 120px;
            height: 120px;
            margin: 1rem auto;
        }
        .circular-chart {
            display: block;
            margin: 10px auto;
            max-width: 100%;
            max-height: 120px;
        }
        .circle-bg {
            fill: none;
            stroke: var(--surface);
            stroke-width: 3.8;
        }
        .circle {
            fill: none;
            stroke-width: 2.8;
            stroke-linecap: round;
            animation: progress 1s ease-out forwards;
            stroke: var(--primary);
        }
        .circle.excellent { stroke: var(--success); }
        .circle.good { stroke: var(--primary); }
        .circle.attention { stroke: var(--warning); }
        .circle.critical { stroke: var(--error); }

        @keyframes progress {
            0% { stroke-dasharray: 0 100; }
        }
        .percentage {
            fill: var(--text);
            font-family: var(--font-mono);
            font-size: 0.5rem;
            text-anchor: middle;
        }

        /* Component Bar */
        .component-row {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.5rem;
        }
        .component-name {
            width: 100px;
            font-size: 0.75rem;
            color: var(--text-secondary);
        }
        .component-bar {
            flex: 1;
            height: 8px;
            background: var(--surface);
            border-radius: 4px;
            overflow: hidden;
        }
        .component-bar-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease;
        }
        .component-bar-fill.excellent { background: var(--success); }
        .component-bar-fill.good { background: var(--primary); }
        .component-bar-fill.attention { background: var(--warning); }
        .component-bar-fill.critical { background: var(--error); }

        .component-score {
            width: 40px;
            text-align: right;
            font-family: var(--font-mono);
            font-size: 0.75rem;
        }

        /* Velocity Chart */
        .velocity-row {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.25rem 0;
            border-bottom: 1px solid var(--border);
        }
        .velocity-row:last-child {
            border-bottom: none;
        }
        .velocity-area {
            width: 150px;
            font-size: 0.8rem;
        }
        .velocity-trend {
            font-size: 0.8rem;
        }
        .velocity-trend.up { color: var(--success); }
        .velocity-trend.down { color: var(--error); }
        .velocity-trend.stable { color: var(--text-secondary); }

        /* Incomplete items */
        .incomplete-item {
            display: flex;
            align-items: flex-start;
            gap: 0.5rem;
            padding: 0.5rem;
            border-bottom: 1px solid var(--border);
        }
        .incomplete-item:last-child {
            border-bottom: none;
        }
        .incomplete-priority {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            flex-shrink: 0;
            margin-top: 0.25rem;
        }
        .incomplete-priority.high { background: var(--error); }
        .incomplete-priority.medium { background: var(--warning); }
        .incomplete-priority.low { background: var(--text-secondary); }
        .incomplete-content {
            font-size: 0.8rem;
        }
        .incomplete-doc {
            font-size: 0.7rem;
            color: var(--text-secondary);
        }

        /* Recommendation items */
        .recommendation-item {
            display: flex;
            align-items: flex-start;
            gap: 0.5rem;
            padding: 0.5rem;
            border-bottom: 1px solid var(--border);
        }
        .recommendation-item:last-child {
            border-bottom: none;
        }
        .recommendation-icon {
            color: var(--primary);
        }

        /* Reading path */
        .path-node {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 0.75rem;
            border-bottom: 1px solid var(--border);
        }
        .path-node:last-child {
            border-bottom: none;
        }
        .path-order {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: var(--primary);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: bold;
            flex-shrink: 0;
        }
        .path-info {
            flex: 1;
        }
        .path-title {
            font-weight: 500;
        }
        .path-meta {
            font-size: 0.75rem;
            color: var(--text-secondary);
        }
        .path-time {
            font-family: var(--font-mono);
            font-size: 0.8rem;
            color: var(--text-secondary);
        }

        /* Parity table */
        .parity-table {
            width: 100%;
            font-size: 0.8rem;
        }
        .parity-table th {
            text-align: left;
            padding: 0.5rem;
            border-bottom: 2px solid var(--border);
            font-weight: 600;
        }
        .parity-table td {
            padding: 0.5rem;
            border-bottom: 1px solid var(--border);
        }
        .parity-table td:not(:first-child) {
            text-align: center;
        }
        .parity-coverage {
            display: inline-block;
            padding: 0.125rem 0.5rem;
            border-radius: 4px;
            font-family: var(--font-mono);
        }
        .parity-coverage.full { background: var(--success-bg); color: var(--success); }
        .parity-coverage.partial { background: var(--warning-bg); color: var(--warning); }
        .parity-coverage.low { background: var(--error-bg); color: var(--error); }

        /* Graph summary */
        .graph-stat {
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid var(--border);
        }
        .graph-stat:last-child {
            border-bottom: none;
        }
        .graph-stat-label {
            color: var(--text-secondary);
        }
        .graph-stat-value {
            font-family: var(--font-mono);
            font-weight: 600;
        }
</style>"""


def get_insights_scripts() -> str:
    """JavaScript for the insights tab."""
    return """<script>
        // Load insights data
        async function loadInsights() {
            try {
                const response = await fetch('/api/insights');
                const data = await response.json();

                // Update health score circle
                const score = data.health?.overall || 0;
                const circle = document.getElementById('health-circle');
                circle.style.strokeDasharray = `${score}, 100`;
                circle.classList.remove('excellent', 'good', 'attention', 'critical');
                if (score >= 90) circle.classList.add('excellent');
                else if (score >= 70) circle.classList.add('good');
                else if (score >= 50) circle.classList.add('attention');
                else circle.classList.add('critical');

                document.getElementById('health-score-text').textContent = Math.round(score);
                document.getElementById('health-grade').textContent =
                    `Grade: ${data.health?.grade || '-'} - ${data.health?.status || ''}`;

                // Update components
                const componentsHtml = Object.entries(data.health?.components || {})
                    .map(([name, score]) => {
                        const status = score >= 90 ? 'excellent' : score >= 70 ? 'good' : score >= 50 ? 'attention' : 'critical';
                        return `
                            <div class="component-row">
                                <span class="component-name">${name}</span>
                                <div class="component-bar">
                                    <div class="component-bar-fill ${status}" style="width: ${score}%"></div>
                                </div>
                                <span class="component-score">${Math.round(score)}</span>
                            </div>
                        `;
                    }).join('');
                document.getElementById('health-components').innerHTML = componentsHtml || 'No data';

                // Update recommendations
                const recsHtml = (data.health?.recommendations || [])
                    .map(rec => `
                        <div class="recommendation-item">
                            <span class="recommendation-icon">💡</span>
                            <span>${rec}</span>
                        </div>
                    `).join('');
                document.getElementById('health-recommendations').innerHTML = recsHtml || 'No recommendations';

                // Update stats
                const stats = data.statistics || {};
                document.getElementById('insights-docs').textContent = stats.content?.total_documents || 0;
                const langs = Object.keys(stats.content?.documents_by_language || {}).join(', ');
                document.getElementById('insights-docs-languages').textContent = langs || 'no data';
                document.getElementById('insights-words').textContent =
                    (stats.content?.total_words || 0).toLocaleString();
                document.getElementById('insights-activity').textContent =
                    stats.activity?.documents_modified_week || 0;
                document.getElementById('insights-issues').textContent =
                    (data.incomplete?.total || 0) + (data.consistency?.length || 0);

                // Update velocity
                const velocityHtml = Object.entries(data.velocity?.area_breakdown || {})
                    .slice(0, 5)
                    .map(([area, metrics]) => `
                        <div class="velocity-row">
                            <span class="velocity-area">${area}</span>
                            <span>${metrics.commits} changes</span>
                            <span class="velocity-trend ${metrics.trend}">${
                                metrics.trend === 'up' ? '↑' :
                                metrics.trend === 'down' ? '↓' : '→'
                            } ${Math.abs(metrics.trend_percent)}%</span>
                        </div>
                    `).join('');
                document.getElementById('velocity-content').innerHTML = velocityHtml || 'No velocity data';

                // Update incomplete
                const incompleteHtml = (data.incomplete?.items || [])
                    .slice(0, 5)
                    .map(item => `
                        <div class="incomplete-item">
                            <div class="incomplete-priority ${item.priority}"></div>
                            <div>
                                <div class="incomplete-content">${item.content}</div>
                                <div class="incomplete-doc">${item.document}:${item.line_number}</div>
                            </div>
                        </div>
                    `).join('');
                document.getElementById('incomplete-content').innerHTML =
                    incompleteHtml || '<div style="padding: 1rem; color: var(--success);">✓ No incomplete content</div>';

                // Update parity
                const parityData = data.parity || {};
                if (parityData.languages && parityData.matrix) {
                    let parityHtml = '<table class="parity-table"><thead><tr><th>Category</th>';
                    parityData.languages.forEach(lang => {
                        parityHtml += `<th>${lang}</th>`;
                    });
                    parityHtml += '<th>Coverage</th></tr></thead><tbody>';

                    Object.entries(parityData.matrix).forEach(([cat, langs]) => {
                        const primaryCount = langs[parityData.primary_language] || 0;
                        const total = Object.values(langs).reduce((a, b) => a + b, 0);
                        const coverage = primaryCount > 0 ?
                            Math.round((total / (primaryCount * parityData.languages.length)) * 100) : 0;
                        const coverageClass = coverage >= 100 ? 'full' : coverage >= 50 ? 'partial' : 'low';

                        parityHtml += `<tr><td>${cat}</td>`;
                        parityData.languages.forEach(lang => {
                            parityHtml += `<td>${langs[lang] || 0}</td>`;
                        });
                        parityHtml += `<td><span class="parity-coverage ${coverageClass}">${coverage}%</span></td></tr>`;
                    });
                    parityHtml += '</tbody></table>';
                    document.getElementById('parity-content').innerHTML = parityHtml;
                } else {
                    document.getElementById('parity-content').innerHTML = 'No parity data';
                }

                // Update graph summary
                const graph = data.graph || {};
                const graphHtml = `
                    <div class="graph-stat">
                        <span class="graph-stat-label">Documents</span>
                        <span class="graph-stat-value">${graph.nodes?.length || 0}</span>
                    </div>
                    <div class="graph-stat">
                        <span class="graph-stat-label">Connections</span>
                        <span class="graph-stat-value">${graph.links?.length || 0}</span>
                    </div>
                    <div class="graph-stat">
                        <span class="graph-stat-label">Hub Documents</span>
                        <span class="graph-stat-value">${graph.hubs || 0}</span>
                    </div>
                    <div class="graph-stat">
                        <span class="graph-stat-label">Orphan Documents</span>
                        <span class="graph-stat-value">${graph.orphans || 0}</span>
                    </div>
                `;
                document.getElementById('graph-summary').innerHTML = graphHtml;

                // Update reading path
                showPath('dependency');

            } catch (error) {
                console.error('Failed to load insights:', error);
            }
        }

        async function showPath(pathType) {
            try {
                const response = await fetch(`/api/insights/path?type=${pathType}`);
                const path = await response.json();

                const pathHtml = (path.documents || [])
                    .slice(0, 10)
                    .map(node => `
                        <div class="path-node">
                            <span class="path-order">${node.order}</span>
                            <div class="path-info">
                                <div class="path-title">${node.title}</div>
                                <div class="path-meta">${node.document}</div>
                            </div>
                            <span class="path-time">${node.estimated_time} min</span>
                        </div>
                    `).join('');

                document.getElementById('reading-path').innerHTML = pathHtml ||
                    '<div style="padding: 1rem;">No reading path available</div>';

            } catch (error) {
                console.error('Failed to load path:', error);
            }
        }

        async function downloadGraph() {
            try {
                const response = await fetch('/api/insights/graph?format=dot');
                const dot = await response.text();

                const blob = new Blob([dot], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'knowledge-graph.dot';
                a.click();
                URL.revokeObjectURL(url);
            } catch (error) {
                console.error('Failed to download graph:', error);
            }
        }

        function refreshVelocity() {
            loadInsights();
        }

        function refreshIncomplete() {
            loadInsights();
        }

        // Load insights when tab is shown
        document.addEventListener('DOMContentLoaded', function() {
            const originalShowTab = window.showTab;
            window.showTab = function(tabName) {
                originalShowTab(tabName);
                if (tabName === 'insights') {
                    loadInsights();
                }
            };
        });
</script>"""
