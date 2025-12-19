"""
Dashboard Dependencies Tab

Provides interactive visualization of content dependency relationships.
"""


def get_dependencies_tab() -> str:
    """Generate the dependencies tab HTML with graph visualization."""
    return """
        <div id="tab-dependencies" style="display: none;">
            <div class="card">
                <div class="card-header">
                    <div class="card-title">Content Dependencies</div>
                    <div style="display: flex; gap: 0.5rem;">
                        <select id="deps-view-mode" onchange="updateDepsView()" style="padding: 0.4rem 0.75rem; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text); font-size: 0.8rem;">
                            <option value="tree">Tree View</option>
                            <option value="list">List View</option>
                            <option value="impact">Impact Analysis</option>
                        </select>
                        <button onclick="refreshDependencies()" style="padding: 0.4rem 0.75rem; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text); font-size: 0.8rem; cursor: pointer; display: flex; align-items: center; gap: 0.4rem;">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 0.9rem; height: 0.9rem;"><path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg>
                            Refresh
                        </button>
                    </div>
                </div>

                <!-- Legend -->
                <div style="display: flex; gap: 1.5rem; margin-top: 1rem; padding: 0.75rem; background: var(--bg-secondary); border-radius: 0.5rem; flex-wrap: wrap;">
                    <div style="display: flex; align-items: center; gap: 0.4rem; font-size: 0.8rem;">
                        <span style="width: 12px; height: 12px; background: #3b82f6; border-radius: 50%;"></span>
                        Source Documents
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.4rem; font-size: 0.8rem;">
                        <span style="width: 12px; height: 12px; background: #8b5cf6; border-radius: 50%;"></span>
                        Video Scripts
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.4rem; font-size: 0.8rem;">
                        <span style="width: 12px; height: 12px; background: #ec4899; border-radius: 50%;"></span>
                        Video Renders
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.4rem; font-size: 0.8rem;">
                        <span style="width: 12px; height: 12px; background: #10b981; border-radius: 50%;"></span>
                        Demos
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.4rem; font-size: 0.8rem;">
                        <span style="width: 12px; height: 12px; background: #f59e0b; border-radius: 50%;"></span>
                        Deliverables
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.4rem; font-size: 0.8rem;">
                        <span style="width: 12px; height: 12px; background: #6b7280; border-radius: 50%;"></span>
                        Config/Theme
                    </div>
                </div>
            </div>

            <!-- Impact Analysis Input -->
            <div class="card" id="impact-analysis-card" style="margin-top: 1rem; display: none;">
                <div class="card-header">
                    <div class="card-title">Impact Analysis</div>
                </div>
                <div style="margin-top: 1rem;">
                    <label style="font-size: 0.85rem; color: var(--text-muted); display: block; margin-bottom: 0.5rem;">
                        Select a file to see what would be affected if it changes:
                    </label>
                    <div style="display: flex; gap: 0.75rem;">
                        <select id="impact-file-select" style="flex: 1; padding: 0.5rem 0.75rem; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text);">
                            <option value="">Select a file...</option>
                        </select>
                        <button onclick="analyzeImpact()" style="padding: 0.5rem 1rem; background: var(--primary); border: none; border-radius: 0.25rem; color: white; cursor: pointer;">
                            Analyze
                        </button>
                    </div>
                </div>
                <div id="impact-results" style="margin-top: 1rem; display: none;">
                    <div style="font-weight: 600; margin-bottom: 0.5rem;">Affected Items:</div>
                    <div id="impact-items-list"></div>
                </div>
            </div>

            <!-- Dependency Graph/Tree -->
            <div class="card" style="margin-top: 1rem;">
                <div id="deps-content" style="min-height: 400px;">
                    <div class="loading">Loading dependencies...</div>
                </div>
            </div>
        </div>

        <style>
            .dep-tree-node {
                padding: 0.5rem 0;
            }
            .dep-tree-item {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.4rem 0.75rem;
                border-radius: 0.25rem;
                cursor: pointer;
                transition: background 0.15s;
            }
            .dep-tree-item:hover {
                background: var(--bg-secondary);
            }
            .dep-tree-item.stale {
                background: rgba(234, 179, 8, 0.1);
                border-left: 3px solid #eab308;
            }
            .dep-tree-children {
                margin-left: 1.5rem;
                border-left: 1px dashed var(--border);
                padding-left: 0.75rem;
            }
            .dep-type-badge {
                font-size: 0.65rem;
                padding: 0.15rem 0.4rem;
                border-radius: 0.25rem;
                text-transform: uppercase;
                font-weight: 600;
            }
            .dep-type-source_document { background: #dbeafe; color: #1e40af; }
            .dep-type-video_script { background: #ede9fe; color: #5b21b6; }
            .dep-type-video_render { background: #fce7f3; color: #9d174d; }
            .dep-type-demo_html, .dep-type-demo_asset { background: #d1fae5; color: #065f46; }
            .dep-type-deliverable { background: #fef3c7; color: #92400e; }
            .dep-type-theme, .dep-type-config { background: #f3f4f6; color: #374151; }

            .dep-list-item {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0.75rem;
                border: 1px solid var(--border);
                border-radius: 0.5rem;
                margin-bottom: 0.5rem;
            }
            .dep-list-item:hover {
                border-color: var(--primary);
            }
            .dep-arrow {
                color: var(--text-muted);
                font-size: 1.2rem;
            }
        </style>
"""
