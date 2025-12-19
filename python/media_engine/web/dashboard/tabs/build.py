"""
Dashboard Build Tab

Provides build controls with freshness warnings and output management.
"""


def get_build_tab() -> str:
    """Generate the build tab HTML with build controls and status."""
    return """
        <div id="tab-build" style="display: none;">
            <!-- Freshness Warning Banner -->
            <div id="build-freshness-warning" class="card" style="display: none; background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-color: #f59e0b; margin-bottom: 1rem;">
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <svg viewBox="0 0 24 24" fill="none" stroke="#b45309" stroke-width="2" style="width: 1.5rem; height: 1.5rem; flex-shrink: 0;">
                        <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
                        <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                    </svg>
                    <div style="flex: 1;">
                        <div style="font-weight: 600; color: #92400e;">Stale Content Detected</div>
                        <div id="build-freshness-message" style="font-size: 0.85rem; color: #a16207;"></div>
                    </div>
                    <button onclick="showTab('quality', event); showSubTab('quality', 'freshness');" style="padding: 0.4rem 0.75rem; background: #f59e0b; border: none; border-radius: 0.25rem; color: white; font-size: 0.8rem; cursor: pointer;">
                        View Details
                    </button>
                </div>
            </div>

            <div class="grid grid-2" style="margin-bottom: 1rem;">
                <!-- Build Controls Card -->
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">Build Controls</div>
                    </div>

                    <div style="display: flex; flex-direction: column; gap: 1rem; margin-top: 1rem;">
                        <!-- Format Selection -->
                        <div>
                            <label style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.5rem; display: block;">Output Formats</label>
                            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                                <label class="build-format-checkbox">
                                    <input type="checkbox" id="build-html" checked> HTML
                                </label>
                                <label class="build-format-checkbox">
                                    <input type="checkbox" id="build-pdf"> PDF
                                </label>
                                <label class="build-format-checkbox">
                                    <input type="checkbox" id="build-pptx"> PPTX
                                </label>
                                <label class="build-format-checkbox">
                                    <input type="checkbox" id="build-xlsx"> XLSX
                                </label>
                            </div>
                        </div>

                        <!-- Language Selection -->
                        <div>
                            <label style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.5rem; display: block;">Languages</label>
                            <div id="build-languages" style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                                <span class="loading">Loading...</span>
                            </div>
                        </div>

                        <!-- Build Options -->
                        <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                            <label style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; cursor: pointer;">
                                <input type="checkbox" id="build-force"> Force rebuild all
                            </label>
                        </div>

                        <!-- Build Button -->
                        <div style="display: flex; gap: 0.75rem; margin-top: 0.5rem;">
                            <button id="build-start-btn" onclick="startBuild()" style="flex: 1; padding: 0.75rem 1.5rem; background: var(--primary); border: none; border-radius: 0.5rem; color: white; font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 1.1rem; height: 1.1rem;"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                                Start Build
                            </button>
                            <button onclick="refreshBuildStatus()" style="padding: 0.75rem; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 0.5rem; color: var(--text); cursor: pointer;" title="Refresh status">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 1.1rem; height: 1.1rem;"><path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg>
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Build Status Card -->
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">Build Status</div>
                        <span id="build-status-badge" class="status-badge" style="display: none;">Ready</span>
                    </div>

                    <div id="build-status-content" style="margin-top: 1rem;">
                        <div class="empty-state">No recent builds</div>
                    </div>
                </div>
            </div>

            <!-- Build Output Card -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title">Build Output</div>
                    <div style="display: flex; gap: 0.5rem;">
                        <button onclick="clearBuildLog()" style="padding: 0.3rem 0.6rem; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text-muted); font-size: 0.75rem; cursor: pointer;">Clear</button>
                    </div>
                </div>
                <div id="build-log" style="background: var(--bg-secondary); border-radius: 0.5rem; padding: 1rem; font-family: monospace; font-size: 0.8rem; max-height: 300px; overflow-y: auto; margin-top: 1rem;">
                    <div style="color: var(--text-muted);">Build output will appear here...</div>
                </div>
            </div>

            <!-- Recent Builds Card -->
            <div class="card" style="margin-top: 1rem;">
                <div class="card-header">
                    <div class="card-title">Output Files</div>
                </div>
                <div id="build-outputs" style="margin-top: 1rem;">
                    <div class="loading">Loading outputs...</div>
                </div>
            </div>
        </div>

        <style>
            .build-format-checkbox {
                display: flex;
                align-items: center;
                gap: 0.4rem;
                padding: 0.4rem 0.75rem;
                background: var(--bg-secondary);
                border: 1px solid var(--border);
                border-radius: 0.25rem;
                font-size: 0.85rem;
                cursor: pointer;
                transition: all 0.15s;
            }
            .build-format-checkbox:hover {
                border-color: var(--primary);
            }
            .build-format-checkbox input:checked + span,
            .build-format-checkbox:has(input:checked) {
                background: var(--primary);
                color: white;
                border-color: var(--primary);
            }
            .build-log-entry {
                padding: 0.25rem 0;
                border-bottom: 1px solid var(--border);
            }
            .build-log-entry:last-child {
                border-bottom: none;
            }
            .build-log-success { color: #22c55e; }
            .build-log-error { color: #ef4444; }
            .build-log-warning { color: #eab308; }
            .build-log-info { color: var(--text-muted); }
        </style>
"""
