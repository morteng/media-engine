"""
Dashboard Provenance Tab

Provides the provenance tab HTML for the Media Engine Dashboard.
Shows claims, verification status, approvals, and publish readiness.
"""


def get_provenance_tab() -> str:
    """Generate the provenance tab HTML with claims tracking and approval workflow."""
    return """
        <div id="tab-provenance" style="display: none;">
            <div class="card">
                <div class="card-header">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div class="card-title">Provenance & Claims</div>
                        <span id="provenance-status" style="font-size: 0.75rem; color: var(--text-muted);"></span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <button onclick="scanDocumentsForClaims()" style="padding: 0.4rem 0.75rem; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text); font-size: 0.8rem; cursor: pointer; display: flex; align-items: center; gap: 0.4rem;" title="Scan documents for potential claims">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 0.9rem; height: 0.9rem;"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
                            <span>Scan for Claims</span>
                        </button>
                        <button onclick="validateAllUrls()" style="padding: 0.4rem 0.75rem; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text); font-size: 0.8rem; cursor: pointer; display: flex; align-items: center; gap: 0.4rem;" title="Validate all source URLs">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 0.9rem; height: 0.9rem;"><path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/></svg>
                            <span>Validate URLs</span>
                        </button>
                        <button onclick="exportReport('provenance')" style="padding: 0.4rem 0.75rem; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text); font-size: 0.8rem; cursor: pointer; display: flex; align-items: center; gap: 0.4rem;" title="Export report">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 0.9rem; height: 0.9rem;"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
                            <span>Export</span>
                        </button>
                        <button id="provenance-refresh-btn" onclick="refreshProvenance()" style="padding: 0.4rem 0.75rem; background: var(--primary); border: none; border-radius: 0.25rem; color: white; font-size: 0.8rem; cursor: pointer; display: flex; align-items: center; gap: 0.4rem;">
                            <svg id="provenance-refresh-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 0.9rem; height: 0.9rem;"><path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg>
                            <span id="provenance-refresh-text">Refresh</span>
                        </button>
                    </div>
                </div>

                <!-- Summary Cards -->
                <div id="provenance-summary" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.75rem; margin-bottom: 1rem;">
                    <div class="stat-card" style="background: var(--bg-secondary); padding: 0.75rem; border-radius: 0.5rem; text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: 600; color: var(--primary);" id="provenance-total-docs">-</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">Documents</div>
                    </div>
                    <div class="stat-card" style="background: var(--bg-secondary); padding: 0.75rem; border-radius: 0.5rem; text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: 600; color: #3b82f6;" id="provenance-total-claims">-</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">Total Claims</div>
                    </div>
                    <div class="stat-card" style="background: var(--bg-secondary); padding: 0.75rem; border-radius: 0.5rem; text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: 600; color: #22c55e;" id="provenance-verified">-</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">Verified</div>
                    </div>
                    <div class="stat-card" style="background: var(--bg-secondary); padding: 0.75rem; border-radius: 0.5rem; text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: 600; color: #eab308;" id="provenance-unverified">-</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">Unverified</div>
                    </div>
                    <div class="stat-card" style="background: var(--bg-secondary); padding: 0.75rem; border-radius: 0.5rem; text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: 600; color: #ef4444;" id="provenance-expired">-</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">Expired</div>
                    </div>
                    <div class="stat-card" style="background: var(--bg-secondary); padding: 0.75rem; border-radius: 0.5rem; text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: 600; color: #f97316;" id="provenance-expiring">-</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">Expiring Soon</div>
                    </div>
                </div>

                <!-- Filter Tabs -->
                <div style="display: flex; gap: 0.5rem; margin-bottom: 1rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; flex-wrap: wrap;">
                    <button class="provenance-filter active" data-filter="all" onclick="filterProvenance('all')" style="padding: 0.4rem 0.75rem; background: var(--primary); border: none; border-radius: 0.25rem; color: white; font-size: 0.75rem; cursor: pointer;">All Claims</button>
                    <button class="provenance-filter" data-filter="unverified" onclick="filterProvenance('unverified')" style="padding: 0.4rem 0.75rem; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text); font-size: 0.75rem; cursor: pointer;">Unverified</button>
                    <button class="provenance-filter" data-filter="expired" onclick="filterProvenance('expired')" style="padding: 0.4rem 0.75rem; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text); font-size: 0.75rem; cursor: pointer;">Expired</button>
                    <button class="provenance-filter" data-filter="expiring" onclick="filterProvenance('expiring')" style="padding: 0.4rem 0.75rem; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text); font-size: 0.75rem; cursor: pointer;">Expiring Soon</button>
                    <button class="provenance-filter" data-filter="verified" onclick="filterProvenance('verified')" style="padding: 0.4rem 0.75rem; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text); font-size: 0.75rem; cursor: pointer;">Verified</button>
                    <div style="flex: 1;"></div>
                    <select id="provenance-type-filter" onchange="loadProvenance()" style="padding: 0.4rem 0.5rem; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text); font-size: 0.75rem;">
                        <option value="">All Source Types</option>
                        <option value="internal">Internal</option>
                        <option value="external">External</option>
                        <option value="research">Research</option>
                        <option value="data">Data</option>
                    </select>
                </div>

                <!-- Claims List -->
                <div id="provenance-claims" style="max-height: 400px; overflow-y: auto;">
                    <div class="loading">Loading provenance data...</div>
                </div>
            </div>

            <!-- Approval Workflow Card -->
            <div class="card" style="margin-top: 1rem;">
                <div class="card-header">
                    <div class="card-title">Approval Workflow</div>
                    <span style="font-size: 0.75rem; color: var(--text-muted);">Document review queue and status</span>
                </div>

                <!-- Status Distribution -->
                <div id="approval-status-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 0.5rem; margin-bottom: 1rem;">
                    <div class="status-badge" style="background: var(--bg-secondary); padding: 0.5rem; border-radius: 0.25rem; text-align: center; cursor: pointer;" onclick="filterApprovalStatus('draft')">
                        <div style="font-size: 1.25rem; font-weight: 600;" id="status-draft">-</div>
                        <div style="font-size: 0.65rem; color: var(--text-muted);">Draft</div>
                    </div>
                    <div class="status-badge" style="background: var(--bg-secondary); padding: 0.5rem; border-radius: 0.25rem; text-align: center; cursor: pointer;" onclick="filterApprovalStatus('in_review')">
                        <div style="font-size: 1.25rem; font-weight: 600; color: #3b82f6;" id="status-in-review">-</div>
                        <div style="font-size: 0.65rem; color: var(--text-muted);">In Review</div>
                    </div>
                    <div class="status-badge" style="background: var(--bg-secondary); padding: 0.5rem; border-radius: 0.25rem; text-align: center; cursor: pointer;" onclick="filterApprovalStatus('changes_requested')">
                        <div style="font-size: 1.25rem; font-weight: 600; color: #f97316;" id="status-changes">-</div>
                        <div style="font-size: 0.65rem; color: var(--text-muted);">Changes</div>
                    </div>
                    <div class="status-badge" style="background: var(--bg-secondary); padding: 0.5rem; border-radius: 0.25rem; text-align: center; cursor: pointer;" onclick="filterApprovalStatus('approved')">
                        <div style="font-size: 1.25rem; font-weight: 600; color: #22c55e;" id="status-approved">-</div>
                        <div style="font-size: 0.65rem; color: var(--text-muted);">Approved</div>
                    </div>
                    <div class="status-badge" style="background: var(--bg-secondary); padding: 0.5rem; border-radius: 0.25rem; text-align: center; cursor: pointer;" onclick="filterApprovalStatus('published')">
                        <div style="font-size: 1.25rem; font-weight: 600; color: #a855f7;" id="status-published">-</div>
                        <div style="font-size: 0.65rem; color: var(--text-muted);">Published</div>
                    </div>
                </div>

                <!-- Review Queue -->
                <div id="review-queue" style="max-height: 300px; overflow-y: auto;">
                    <div class="loading">Loading review queue...</div>
                </div>
            </div>

            <!-- URL Validation Results (hidden by default) -->
            <div class="card" id="url-validation-card" style="display: none; margin-top: 1rem;">
                <div class="card-header">
                    <div class="card-title">URL Validation Results</div>
                    <button onclick="document.getElementById('url-validation-card').style.display='none'" style="background: none; border: none; color: var(--text-muted); cursor: pointer;">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 1rem; height: 1rem;"><path d="M18 6L6 18M6 6l12 12"/></svg>
                    </button>
                </div>
                <div id="url-validation-results"></div>
            </div>

            <!-- Claim Scan Results (hidden by default) -->
            <div class="card" id="claim-scan-card" style="display: none; margin-top: 1rem;">
                <div class="card-header">
                    <div class="card-title">Potential Claims Found</div>
                    <button onclick="document.getElementById('claim-scan-card').style.display='none'" style="background: none; border: none; color: var(--text-muted); cursor: pointer;">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 1rem; height: 1rem;"><path d="M18 6L6 18M6 6l12 12"/></svg>
                    </button>
                </div>
                <div id="claim-scan-results" style="max-height: 400px; overflow-y: auto;"></div>
            </div>
        </div>
"""
