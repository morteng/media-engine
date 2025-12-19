"""
Dashboard CSS Styles

This module contains all CSS styles for the Media Engine Dashboard.
"""


def get_styles() -> str:
    """Return the complete CSS stylesheet for the dashboard."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Media Engine Dashboard</title>
    <style>
        :root {
            --bg: #0f172a;
            --bg-card: #1e293b;
            --border: #334155;
            --text: #f1f5f9;
            --text-muted: #94a3b8;
            --primary: #3b82f6;
            --success: #22c55e;
            --warning: #f59e0b;
            --error: #ef4444;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.5;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 2rem; }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border);
        }
        h1 { font-size: 1.5rem; font-weight: 600; }
        .status-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 500;
        }
        .status-ok { background: var(--success); color: #000; }
        .status-warn { background: var(--warning); color: #000; }
        .status-error { background: var(--error); color: #fff; }
        .grid { display: grid; gap: 1.5rem; }
        .grid-2 { grid-template-columns: repeat(2, 1fr); }
        .grid-3 { grid-template-columns: repeat(3, 1fr); }
        .grid-4 { grid-template-columns: repeat(4, 1fr); }
        .grid-5 { grid-template-columns: repeat(5, 1fr); }
        @media (max-width: 1200px) { .grid-5 { grid-template-columns: repeat(3, 1fr); } }
        @media (max-width: 1024px) { .grid-3, .grid-4, .grid-5 { grid-template-columns: repeat(2, 1fr); } }
        @media (max-width: 640px) { .grid-2, .grid-3, .grid-4, .grid-5 { grid-template-columns: 1fr; } }
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            padding: 1.5rem;
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        .card-title { font-size: 0.875rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
        .stat { font-size: 2.5rem; font-weight: 700; }
        .stat-label { font-size: 0.875rem; color: var(--text-muted); }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 0.75rem; text-align: left; border-bottom: 1px solid var(--border); }
        th { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; }
        .matrix-cell {
            width: 2rem;
            height: 2rem;
            border-radius: 0.25rem;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
        }
        .cell-source { background: var(--primary); }
        .cell-current { background: var(--success); }
        .cell-outdated { background: var(--warning); }
        .cell-missing { background: var(--border); }
        .issue { padding: 0.5rem; border-radius: 0.25rem; margin-bottom: 0.5rem; font-size: 0.875rem; }
        .issue-error { background: rgba(239, 68, 68, 0.2); border-left: 3px solid var(--error); }
        .issue-warning { background: rgba(245, 158, 11, 0.2); border-left: 3px solid var(--warning); }
        .users-online { display: flex; gap: 0.5rem; }
        .user-avatar {
            width: 2rem;
            height: 2rem;
            border-radius: 50%;
            background: var(--primary);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .loading { text-align: center; padding: 2rem; color: var(--text-muted); }
        .tabs { display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
        .tab {
            padding: 0.5rem 1rem;
            background: transparent;
            border: 1px solid var(--border);
            border-radius: 0.25rem;
            color: var(--text-muted);
            cursor: pointer;
            transition: all 0.2s;
        }
        .tab:hover { border-color: var(--primary); color: var(--text); }
        .tab.active { background: var(--primary); border-color: var(--primary); color: #fff; }

        /* Sub-tabs horizontal navigation */
        .subtabs {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
            padding: 0.75rem 1rem;
            background: var(--bg-card);
            border-radius: 0.5rem;
            border: 1px solid var(--border);
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }
        .subtab {
            padding: 0.4rem 0.9rem;
            background: transparent;
            border: 1px solid transparent;
            border-radius: 0.25rem;
            color: var(--text-muted);
            cursor: pointer;
            transition: all 0.2s;
            white-space: nowrap;
            font-size: 0.875rem;
        }
        .subtab:hover {
            color: var(--text);
            background: rgba(59, 130, 246, 0.1);
        }
        .subtab.active {
            background: var(--primary);
            border-color: var(--primary);
            color: #fff;
        }

        /* Mobile sub-tab dropdowns */
        .subtabs-dropdown {
            display: none;
            margin-bottom: 1rem;
        }
        .subtabs-select {
            width: 100%;
            padding: 0.75rem;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            color: var(--text);
            font-size: 0.9rem;
        }

        /* Responsive: Mobile sub-tabs */
        @media (max-width: 768px) {
            .subtabs {
                display: none !important;
            }
            .subtabs-dropdown {
                display: block;
            }
        }

        /* Document browser styles */
        .doc-browser { display: grid; grid-template-columns: 320px 1fr; gap: 1.5rem; min-height: calc(100vh - 200px); }
        .doc-sidebar { background: var(--bg-card); border: 1px solid var(--border); border-radius: 0.5rem; overflow: hidden; display: flex; flex-direction: column; }
        .doc-sidebar-header { padding: 1rem; border-bottom: 1px solid var(--border); }
        .doc-list { flex: 1; overflow-y: auto; }
        .doc-item { padding: 0.75rem 1rem; cursor: pointer; border-bottom: 1px solid var(--border); transition: background 0.2s; }
        .doc-item:hover { background: rgba(59, 130, 246, 0.1); }
        .doc-item.active { background: rgba(59, 130, 246, 0.2); border-left: 3px solid var(--primary); }
        .doc-item-title { font-weight: 500; margin-bottom: 0.25rem; }
        .doc-item-meta { font-size: 0.75rem; color: var(--text-muted); }
        .doc-type-badge { font-size: 0.65rem; padding: 0.15rem 0.4rem; border-radius: 3px; background: var(--border); margin-left: 0.5rem; }
        .doc-preview { background: var(--bg-card); border: 1px solid var(--border); border-radius: 0.5rem; display: flex; flex-direction: column; }
        .doc-preview-header { padding: 1rem; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; background: var(--bg-card); z-index: 10; }
        .doc-preview-tabs { display: flex; gap: 0.5rem; }
        .preview-tab { padding: 0.25rem 0.75rem; background: transparent; border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text-muted); cursor: pointer; font-size: 0.8rem; }
        .preview-tab.active { background: var(--primary); border-color: var(--primary); color: #fff; }
        .doc-preview-content { flex: 1; padding: 1.5rem; }
        .doc-preview-content.preview-mode { background: #fff; color: #1a1a1a; }
        .doc-preview-content.preview-mode h1, .doc-preview-content.preview-mode h2, .doc-preview-content.preview-mode h3 { color: #1a1a1a; margin-top: 1.5em; margin-bottom: 0.5em; }
        .doc-preview-content.preview-mode h1 { font-size: 2rem; border-bottom: 1px solid #e5e5e5; padding-bottom: 0.3em; }
        .doc-preview-content.preview-mode h2 { font-size: 1.5rem; }
        .doc-preview-content.preview-mode h3 { font-size: 1.25rem; }
        .doc-preview-content.preview-mode p { margin: 1em 0; line-height: 1.7; }
        .doc-preview-content.preview-mode code { background: #f5f5f5; padding: 0.2em 0.4em; border-radius: 3px; font-size: 0.9em; }
        .doc-preview-content.preview-mode pre { background: #f5f5f5; padding: 1em; border-radius: 5px; overflow-x: auto; }
        .doc-preview-content.preview-mode pre code { background: none; padding: 0; }
        .doc-preview-content.preview-mode blockquote { border-left: 4px solid var(--primary); margin: 1em 0; padding-left: 1em; color: #666; }
        .doc-preview-content.preview-mode table { border-collapse: collapse; width: 100%; margin: 1em 0; }
        .doc-preview-content.preview-mode th, .doc-preview-content.preview-mode td { border: 1px solid #ddd; padding: 0.5em; text-align: left; }
        .doc-preview-content.preview-mode th { background: #f5f5f5; }
        .doc-preview-content.preview-mode ul, .doc-preview-content.preview-mode ol { margin: 1em 0; padding-left: 2em; }
        .doc-preview-content.preview-mode li { margin: 0.5em 0; }
        .doc-preview-content.preview-mode a { color: var(--primary); }
        .doc-preview-content.source-mode { font-family: 'Monaco', 'Menlo', monospace; font-size: 0.85rem; white-space: pre-wrap; }
        .doc-metadata { background: var(--bg); padding: 1rem; border-radius: 0.25rem; margin-bottom: 1rem; font-size: 0.85rem; }
        .doc-metadata dt { color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; margin-top: 0.5rem; }
        .doc-metadata dd { margin: 0; margin-bottom: 0.5rem; }
        .lang-select { padding: 0.5rem; background: var(--bg); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text); width: 100%; }
        .yaml-viewer { background: #1e1e1e; color: #d4d4d4; padding: 1rem; border-radius: 0.25rem; font-family: monospace; font-size: 0.85rem; white-space: pre-wrap; overflow-x: auto; }
        .yaml-key { color: #9cdcfe; }
        .yaml-string { color: #ce9178; }
        .yaml-number { color: #b5cea8; }
        .empty-state { text-align: center; padding: 3rem; color: var(--text-muted); }

        /* Document group styles */
        .doc-group { border-bottom: 1px solid var(--border); }
        .doc-group-header { padding: 0.75rem 1rem; cursor: pointer; display: flex; align-items: center; gap: 0.5rem; transition: background 0.2s; }
        .doc-group-header:hover { background: rgba(59, 130, 246, 0.1); }
        .doc-group-toggle { width: 1rem; height: 1rem; transition: transform 0.2s; color: var(--text-muted); }
        .doc-group-toggle.expanded { transform: rotate(90deg); }
        .doc-group-info { flex: 1; }
        .doc-group-title { font-weight: 500; }
        .doc-group-meta { font-size: 0.75rem; color: var(--text-muted); display: flex; gap: 0.5rem; align-items: center; }
        .doc-group-badge { font-size: 0.65rem; padding: 0.1rem 0.35rem; border-radius: 3px; background: var(--primary); color: white; }
        .doc-group-children { display: none; background: var(--bg); border-left: 2px solid var(--primary); margin-left: 1rem; }
        .doc-group-children.expanded { display: block; }
        .doc-group-children .doc-item { padding-left: 1.5rem; border-bottom: 1px solid var(--border); }
        .doc-group-children .doc-item:last-child { border-bottom: none; }
        .doc-item-thumb { width: 40px; height: 30px; object-fit: cover; border-radius: 3px; background: var(--border); margin-right: 0.5rem; }
        .doc-item-row { display: flex; align-items: center; }
        .doc-item-content { flex: 1; min-width: 0; }
        .doc-item-registry { font-size: 0.65rem; padding: 0.1rem 0.35rem; border-radius: 3px; background: var(--border); color: var(--text-muted); margin-left: auto; }

        /* Video Script Viewer Styles */
        .script-viewer { padding: 0; }
        .script-header { background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg) 100%); padding: 1.5rem; border-bottom: 1px solid var(--border); }
        .script-title { font-size: 1.5rem; font-weight: 600; margin-bottom: 0.5rem; }
        .script-description { color: var(--text-muted); margin-bottom: 1rem; }
        .script-meta { display: flex; flex-wrap: wrap; gap: 1rem; }
        .script-meta-item { display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; }
        .script-meta-icon { width: 1.25rem; height: 1.25rem; color: var(--primary); }
        .script-meta-label { color: var(--text-muted); }
        .script-meta-value { font-weight: 500; }
        .script-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 1rem; padding: 1rem 1.5rem; background: var(--bg); border-bottom: 1px solid var(--border); }
        .script-stat { text-align: center; }
        .script-stat-value { font-size: 1.5rem; font-weight: 600; color: var(--primary); }
        .script-stat-label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; }
        .script-production { padding: 1rem 1.5rem; background: var(--bg-card); border-bottom: 1px solid var(--border); }
        .script-production-title { font-size: 0.85rem; font-weight: 600; margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem; }
        .script-production-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }
        .script-production-item { font-size: 0.8rem; }
        .script-production-label { color: var(--text-muted); margin-bottom: 0.25rem; }
        .script-production-value { font-family: monospace; background: var(--bg); padding: 0.25rem 0.5rem; border-radius: 3px; }
        .script-timeline { padding: 1rem 1.5rem; }
        .script-timeline-title { font-size: 0.85rem; font-weight: 600; margin-bottom: 1rem; display: flex; align-items: center; justify-content: space-between; }
        .script-timeline-bar { display: flex; height: 8px; border-radius: 4px; overflow: hidden; background: var(--border); margin-bottom: 1rem; }
        .script-timeline-segment { height: 100%; transition: opacity 0.2s; cursor: pointer; }
        .script-timeline-segment:hover { opacity: 0.8; }
        .script-scenes { display: flex; flex-direction: column; gap: 0.75rem; }
        .script-scene { background: var(--bg-card); border: 1px solid var(--border); border-radius: 0.5rem; overflow: hidden; transition: border-color 0.2s, box-shadow 0.2s; }
        .script-scene:hover { border-color: var(--primary); }
        .script-scene.expanded { box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .script-scene-header { padding: 0.75rem 1rem; display: flex; align-items: center; gap: 0.75rem; cursor: pointer; }
        .script-scene-number { width: 2rem; height: 2rem; background: var(--primary); color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 600; flex-shrink: 0; }
        .script-scene-info { flex: 1; min-width: 0; }
        .script-scene-name { font-weight: 500; margin-bottom: 0.15rem; }
        .script-scene-id { font-size: 0.75rem; color: var(--text-muted); font-family: monospace; }
        .script-scene-badges { display: flex; gap: 0.5rem; flex-shrink: 0; }
        .script-scene-badge { font-size: 0.7rem; padding: 0.2rem 0.5rem; border-radius: 3px; font-weight: 500; }
        .script-scene-badge.type-web { background: rgba(59, 130, 246, 0.2); color: #3b82f6; }
        .script-scene-badge.type-text { background: rgba(168, 85, 247, 0.2); color: #a855f7; }
        .script-scene-badge.type-video { background: rgba(236, 72, 153, 0.2); color: #ec4899; }
        .script-scene-badge.duration { background: var(--border); color: var(--text-muted); }
        .script-scene-badge.has-note { background: rgba(34, 197, 94, 0.2); color: #22c55e; }
        .script-scene-toggle { width: 1.5rem; height: 1.5rem; color: var(--text-muted); transition: transform 0.2s; flex-shrink: 0; }
        .script-scene.expanded .script-scene-toggle { transform: rotate(180deg); }
        .script-scene-content { display: none; border-top: 1px solid var(--border); }
        .script-scene.expanded .script-scene-content { display: block; }
        .script-scene-section { padding: 1rem; border-bottom: 1px solid var(--border); }
        .script-scene-section:last-child { border-bottom: none; }
        .script-scene-section-title { font-size: 0.75rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem; }
        .script-scene-section-title svg { width: 1rem; height: 1rem; }
        .script-scene-voiceover { background: var(--bg); padding: 0.75rem; border-radius: 0.25rem; font-size: 0.9rem; line-height: 1.6; white-space: pre-wrap; }
        .script-scene-voiceover::before { content: '"'; font-size: 1.5rem; color: var(--primary); line-height: 0; vertical-align: -0.3em; margin-right: 0.25rem; }
        .script-scene-action { background: #1e1e1e; color: #d4d4d4; padding: 0.75rem; border-radius: 0.25rem; font-family: monospace; font-size: 0.8rem; white-space: pre-wrap; overflow-x: auto; }
        .script-scene-overlays { display: flex; flex-direction: column; gap: 0.5rem; }
        .script-overlay-item { background: var(--bg); padding: 0.75rem; border-radius: 0.25rem; border-left: 3px solid var(--primary); }
        .script-overlay-text { font-size: 1.1rem; font-weight: 500; margin-bottom: 0.5rem; }
        .script-overlay-meta { display: flex; gap: 1rem; font-size: 0.75rem; color: var(--text-muted); }
        .script-overlay-style { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.5rem; }
        .script-overlay-color { width: 1rem; height: 1rem; border-radius: 3px; border: 1px solid var(--border); }
        .script-background { display: flex; align-items: center; gap: 0.75rem; }
        .script-background-preview { width: 3rem; height: 2rem; border-radius: 3px; border: 1px solid var(--border); }

        /* Smaller composition preview */
        .script-composition-preview { position: relative; width: 100%; max-width: 280px; aspect-ratio: 16/9; border-radius: 0.375rem; border: 1px solid var(--border); overflow: hidden; display: flex; flex-direction: column; justify-content: center; align-items: center; font-size: 0.7rem; }
        .script-comp-text { position: absolute; text-align: center; padding: 0.15rem 0.35rem; font-weight: 600; max-width: 90%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 0.6rem; }
        .comp-pos-center { top: 50%; left: 50%; transform: translate(-50%, -50%); }
        .comp-pos-top { top: 10%; left: 50%; transform: translateX(-50%); }
        .comp-pos-bottom { bottom: 10%; left: 50%; transform: translateX(-50%); }
        .comp-pos-top-left { top: 10%; left: 5%; }
        .comp-pos-top-right { top: 10%; right: 5%; }
        .comp-pos-bottom-left { bottom: 10%; left: 5%; }
        .comp-pos-bottom-right { bottom: 10%; right: 5%; }
        .script-comp-web-indicator { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); display: flex; flex-direction: column; align-items: center; gap: 0.25rem; color: var(--text-muted); font-size: 0.6rem; }
        .script-comp-web-indicator svg { width: 1.25rem; height: 1.25rem; opacity: 0.5; }

        /* Scene Notes styles */
        .scene-note-section { background: rgba(34, 197, 94, 0.1); border-left: 3px solid var(--success); }
        .scene-note-input { width: 100%; min-height: 80px; padding: 0.75rem; background: var(--bg); border: 1px solid var(--border); border-radius: 0.25rem; color: var(--text); font-family: inherit; font-size: 0.9rem; resize: vertical; }
        .scene-note-input:focus { outline: none; border-color: var(--primary); }
        .scene-note-actions { display: flex; gap: 0.5rem; margin-top: 0.5rem; }
        .scene-note-btn { padding: 0.35rem 0.75rem; border-radius: 0.25rem; font-size: 0.8rem; cursor: pointer; border: 1px solid var(--border); background: var(--bg-card); color: var(--text); transition: all 0.2s; }
        .scene-note-btn:hover { background: var(--primary); border-color: var(--primary); color: #fff; }
        .scene-note-btn.save { background: var(--success); border-color: var(--success); color: #fff; }
        .scene-note-btn.save:hover { opacity: 0.9; }
        .scene-note-btn.delete { background: var(--error); border-color: var(--error); color: #fff; }
        .scene-note-btn.delete:hover { opacity: 0.9; }
        .scene-note-saved { font-size: 0.75rem; color: var(--text-muted); margin-top: 0.5rem; }

        /* Video Player styles */
        .script-video-section { background: #000; padding: 1rem 1.5rem; border-bottom: 1px solid var(--border); }
        .script-video-container { position: relative; max-width: 800px; margin: 0 auto; }
        .script-video-player { width: 100%; aspect-ratio: 16/9; background: #000; border-radius: 0.5rem; }
        .script-video-controls { display: flex; align-items: center; gap: 1rem; margin-top: 0.75rem; padding: 0.5rem; background: var(--bg-card); border-radius: 0.25rem; }
        .video-play-btn { background: var(--primary); border: none; color: #fff; padding: 0.5rem 1rem; border-radius: 0.25rem; cursor: pointer; display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; font-weight: 500; }
        .video-play-btn:hover { opacity: 0.9; }
        .video-play-btn svg { width: 1rem; height: 1rem; }
        .video-progress { flex: 1; height: 6px; background: var(--border); border-radius: 3px; cursor: pointer; position: relative; }
        .video-progress-fill { height: 100%; background: var(--primary); border-radius: 3px; transition: width 0.1s; }
        .video-time { font-size: 0.8rem; color: var(--text-muted); font-family: monospace; min-width: 80px; text-align: right; }
        .video-no-render { background: var(--bg-card); padding: 1.5rem; border-radius: 0.5rem; text-align: center; }
        .video-no-render-icon { width: 3rem; height: 3rem; color: var(--text-muted); margin-bottom: 0.75rem; }
        .video-no-render-text { color: var(--text-muted); font-size: 0.9rem; margin-bottom: 0.75rem; }
        .video-render-btn { background: var(--primary); border: none; color: #fff; padding: 0.5rem 1rem; border-radius: 0.25rem; cursor: pointer; font-size: 0.85rem; font-weight: 500; }
        .video-render-btn:hover { opacity: 0.9; }
        .video-render-btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .scene-play-btn { background: transparent; border: 1px solid var(--border); color: var(--text-muted); padding: 0.25rem 0.5rem; border-radius: 0.25rem; cursor: pointer; font-size: 0.7rem; display: flex; align-items: center; gap: 0.25rem; transition: all 0.2s; margin-left: auto; }
        .scene-play-btn:hover { border-color: var(--primary); color: var(--primary); background: rgba(59, 130, 246, 0.1); }
        .scene-play-btn svg { width: 0.75rem; height: 0.75rem; }
        .script-scene.playing { border-color: var(--primary); box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3); }
        .script-scene.playing .script-scene-number { animation: pulse 1s ease-in-out infinite; }
        @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.1); } }

        /* Scene-specific video player styles */
        .scene-video-section { background: var(--bg); border-radius: 0.25rem; }
        .scene-video-container { display: flex; flex-direction: column; gap: 0.5rem; }
        .scene-video-player { width: 100%; max-width: 640px; aspect-ratio: 16/9; background: #000; border-radius: 0.375rem; }
        .scene-video-controls { display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem; background: var(--bg-card); border-radius: 0.25rem; max-width: 640px; }
        .scene-video-play-btn { background: var(--primary); border: none; color: #fff; width: 2rem; height: 2rem; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
        .scene-video-play-btn:hover { opacity: 0.9; }
        .scene-video-play-btn svg { width: 0.875rem; height: 0.875rem; }
        .scene-video-progress { flex: 1; height: 6px; background: var(--border); border-radius: 3px; cursor: pointer; position: relative; }
        .scene-video-progress-fill { height: 100%; background: var(--primary); border-radius: 3px; transition: width 0.1s; }
        .scene-video-time { font-size: 0.75rem; color: var(--text-muted); font-family: monospace; min-width: 70px; text-align: right; }
        .scene-video-loop-btn { background: transparent; border: 1px solid var(--border); color: var(--text-muted); width: 1.75rem; height: 1.75rem; border-radius: 0.25rem; cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0; transition: all 0.2s; }
        .scene-video-loop-btn:hover { border-color: var(--primary); color: var(--primary); }
        .scene-video-loop-btn svg { width: 0.875rem; height: 0.875rem; }

        .issue-clickable { cursor: pointer; transition: transform 0.1s, box-shadow 0.1s; }
        .issue-clickable:hover { transform: translateX(4px); box-shadow: -4px 0 0 var(--primary); }
        .issue-file { opacity: 0.8; }
        .issue-file:hover { text-decoration: underline; }
        .highlight-line { background: rgba(255, 235, 59, 0.3); animation: highlight-fade 2s ease-out; }
        @keyframes highlight-fade { from { background: rgba(255, 235, 59, 0.5); } to { background: transparent; } }
        .source-lines { font-family: 'Monaco', 'Menlo', 'Consolas', monospace; font-size: 0.85rem; }
        .source-line { display: flex; line-height: 1.5; padding: 0 0.5rem; }
        .source-line:hover { background: rgba(59, 130, 246, 0.1); }
        .line-number { color: var(--text-muted); min-width: 3rem; text-align: right; padding-right: 1rem; user-select: none; }
        .line-content { white-space: pre-wrap; word-break: break-all; flex: 1; }
        .theme-toggle { background: transparent; border: 1px solid var(--border); padding: 0.5rem; border-radius: 0.25rem; cursor: pointer; font-size: 1rem; }
        .theme-toggle:hover { background: var(--border); }

        /* Light mode styles */
        body.light-mode { --bg: #f8fafc; --bg-card: #ffffff; --border: #e2e8f0; --text: #1e293b; --text-muted: #64748b; }
        body.light-mode .doc-preview-content.source-mode { background: #f8f8f8; color: #333; }
        body.light-mode .yaml-viewer { background: #f5f5f5; color: #333; }
        body.light-mode .issue-warning { background: #fef3c7; border-left-color: #f59e0b; }
        body.light-mode .issue-error { background: #fee2e2; border-left-color: #ef4444; }
        body.light-mode .matrix-cell { color: #fff; }

        /* Media tab styles */
        .media-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 1rem; }
        .media-item {
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            padding: 1rem;
            transition: all 0.2s;
        }
        .media-item:hover { border-color: var(--primary); transform: translateY(-2px); }
        .media-item-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem; }
        .media-item-title { font-weight: 600; word-break: break-all; }
        .media-item-type {
            font-size: 0.65rem;
            padding: 0.2rem 0.5rem;
            border-radius: 9999px;
            text-transform: uppercase;
            font-weight: 600;
        }
        .type-audio { background: #8b5cf6; color: #fff; }
        .type-video { background: #ef4444; color: #fff; }
        .type-demo { background: #22c55e; color: #fff; }
        .type-captions { background: #f59e0b; color: #000; }
        .type-document { background: #3b82f6; color: #fff; }
        .type-video_props { background: #6366f1; color: #fff; }
        .media-item-meta { font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.5rem; }
        .media-item-source { font-size: 0.75rem; color: var(--text-muted); padding: 0.5rem; background: var(--bg-card); border-radius: 0.25rem; margin-top: 0.5rem; }
        .media-item-source a { color: var(--primary); text-decoration: none; }
        .media-item-source a:hover { text-decoration: underline; }
        .media-item-actions { display: flex; gap: 0.5rem; margin-top: 0.75rem; }
        .media-btn {
            padding: 0.35rem 0.75rem;
            border-radius: 0.25rem;
            font-size: 0.8rem;
            cursor: pointer;
            border: 1px solid var(--border);
            background: var(--bg-card);
            color: var(--text);
            transition: all 0.2s;
        }
        .media-btn:hover { background: var(--primary); border-color: var(--primary); color: #fff; }
        .media-btn-primary { background: var(--primary); border-color: var(--primary); color: #fff; }
        .media-btn-primary:hover { opacity: 0.9; }

        /* Audio player styles */
        .audio-player {
            width: 100%;
            margin-top: 0.5rem;
            height: 40px;
            border-radius: 0.25rem;
        }

        /* Media modal styles */
        .media-modal {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        .media-modal-content {
            background: var(--bg-card);
            border-radius: 0.5rem;
            max-width: 90vw;
            max-height: 90vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        .media-modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem;
            border-bottom: 1px solid var(--border);
        }
        #media-preview-body {
            padding: 1rem;
            overflow: auto;
            max-height: calc(90vh - 60px);
        }
        #media-preview-body iframe {
            width: 800px;
            height: 600px;
            border: none;
            background: #fff;
        }
        #media-preview-body video {
            max-width: 100%;
            max-height: 70vh;
        }
        #media-preview-body audio {
            width: 100%;
            min-width: 400px;
        }
        #media-preview-body pre {
            background: var(--bg);
            padding: 1rem;
            border-radius: 0.25rem;
            overflow: auto;
            max-height: 500px;
            font-size: 0.85rem;
        }

        /* Export notes button */
        .export-notes-btn {
            position: fixed;
            bottom: 1.5rem;
            right: 1.5rem;
            padding: 0.75rem 1.25rem;
            background: var(--success);
            color: #fff;
            border: none;
            border-radius: 0.5rem;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 100;
            display: none;
        }
        .export-notes-btn:hover { opacity: 0.9; }
        .export-notes-btn.visible { display: block; }

        /* Project Switcher Styles */
        .project-selector { position: relative; display: inline-block; }
        .project-selector-btn {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 0.75rem;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 0.375rem;
            color: var(--text);
            cursor: pointer;
            font-size: 0.9rem;
            transition: border-color 0.2s;
        }
        .project-selector-btn:hover { border-color: var(--primary); }
        .project-selector-btn svg { width: 1rem; height: 1rem; }
        .project-selector-name { max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500; }
        .project-dropdown {
            position: absolute;
            top: calc(100% + 0.5rem);
            left: 0;
            min-width: 320px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            z-index: 1000;
            display: none;
        }
        .project-dropdown.open { display: block; }
        .project-dropdown-header { padding: 0.75rem 1rem; border-bottom: 1px solid var(--border); font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; }
        .project-list { max-height: 300px; overflow-y: auto; }
        .project-item {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem 1rem;
            cursor: pointer;
            transition: background 0.2s;
            border-bottom: 1px solid var(--border);
        }
        .project-item:last-child { border-bottom: none; }
        .project-item:hover { background: rgba(59, 130, 246, 0.1); }
        .project-item.current { background: rgba(59, 130, 246, 0.15); }
        .project-item.missing { opacity: 0.5; }
        .project-item-icon { width: 2rem; height: 2rem; background: var(--primary); border-radius: 0.375rem; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
        .project-item-icon svg { width: 1rem; height: 1rem; color: white; }
        .project-item-info { flex: 1; min-width: 0; }
        .project-item-name { font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .project-item-path { font-size: 0.75rem; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .project-item-remove {
            padding: 0.25rem;
            background: transparent;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            opacity: 0;
            transition: opacity 0.2s, color 0.2s;
        }
        .project-item:hover .project-item-remove { opacity: 1; }
        .project-item-remove:hover { color: var(--error); }
        .project-dropdown-footer { padding: 0.75rem 1rem; border-top: 1px solid var(--border); }
        .open-project-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            width: 100%;
            padding: 0.5rem;
            background: transparent;
            border: 1px dashed var(--border);
            border-radius: 0.375rem;
            color: var(--text-muted);
            cursor: pointer;
            font-size: 0.85rem;
            transition: all 0.2s;
        }
        .open-project-btn:hover { border-color: var(--primary); color: var(--primary); background: rgba(59, 130, 246, 0.1); }
        .open-project-btn svg { width: 1rem; height: 1rem; }
        .open-project-btn:disabled { opacity: 0.7; cursor: wait; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

        /* Slide Deck Preview Styles */
        .slide-viewer { display: flex; flex-direction: column; height: 100%; min-height: 600px; background: var(--bg); }
        .slide-viewer-main { display: flex; flex: 1; gap: 1rem; padding: 1rem; overflow: hidden; }
        .slide-viewer-sidebar { width: 180px; flex-shrink: 0; overflow-y: auto; display: flex; flex-direction: column; gap: 0.5rem; padding-right: 0.5rem; }
        .slide-thumb { aspect-ratio: 16/9; background: var(--bg-card); border: 2px solid var(--border); border-radius: 0.375rem; cursor: pointer; overflow: hidden; transition: all 0.2s; position: relative; }
        .slide-thumb:hover { border-color: var(--primary); transform: scale(1.02); }
        .slide-thumb.active { border-color: var(--primary); box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3); }
        .slide-thumb-number { position: absolute; bottom: 0.25rem; right: 0.25rem; background: rgba(0,0,0,0.7); color: #fff; font-size: 0.65rem; padding: 0.1rem 0.35rem; border-radius: 3px; }
        .slide-thumb-content { width: 100%; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 0.25rem; text-align: center; font-size: 0.45rem; color: var(--text); overflow: hidden; }
        .slide-thumb-title { font-weight: 600; font-size: 0.5rem; margin-bottom: 0.15rem; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .slide-viewer-content { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
        .slide-canvas { flex: 1; display: flex; justify-content: center; align-items: center; padding: 1rem; }
        .slide-frame { width: 100%; max-width: 900px; aspect-ratio: 16/9; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 0.5rem; box-shadow: 0 10px 40px rgba(0,0,0,0.4); overflow: hidden; position: relative; }
        .slide-frame-inner { width: 100%; height: 100%; display: flex; flex-direction: column; padding: 2rem 2.5rem; position: relative; }
        .slide-controls { display: flex; justify-content: center; align-items: center; gap: 1rem; padding: 1rem; background: var(--bg-card); border-top: 1px solid var(--border); }
        .slide-nav-btn { background: var(--bg); border: 1px solid var(--border); color: var(--text); padding: 0.5rem 1rem; border-radius: 0.375rem; cursor: pointer; display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; transition: all 0.2s; }
        .slide-nav-btn:hover:not(:disabled) { background: var(--primary); border-color: var(--primary); color: #fff; }
        .slide-nav-btn:disabled { opacity: 0.4; cursor: not-allowed; }
        .slide-nav-btn svg { width: 1rem; height: 1rem; }
        .slide-counter { font-size: 0.9rem; color: var(--text-muted); min-width: 80px; text-align: center; }

        /* Slide Type Styles */
        .slide-type-title .slide-frame { background: linear-gradient(135deg, #1a1a2e 0%, #0f3460 100%); }
        .slide-type-title .slide-frame-inner { justify-content: center; align-items: center; text-align: center; }
        .slide-type-title .slide-main-title { font-size: 2.5rem; font-weight: 700; color: #fff; margin-bottom: 0.75rem; text-shadow: 0 2px 4px rgba(0,0,0,0.3); }
        .slide-type-title .slide-subtitle { font-size: 1.25rem; color: rgba(255,255,255,0.7); }
        .slide-type-title .slide-accent { width: 80px; height: 4px; background: var(--primary); border-radius: 2px; margin-top: 1.5rem; }

        .slide-type-section .slide-frame { background: linear-gradient(135deg, #0f3460 0%, #16213e 100%); }
        .slide-type-section .slide-frame-inner { justify-content: center; align-items: center; text-align: center; }
        .slide-type-section .slide-main-title { font-size: 2rem; font-weight: 600; color: #fff; margin-bottom: 0.5rem; }
        .slide-type-section .slide-subtitle { font-size: 1.1rem; color: rgba(255,255,255,0.6); }

        .slide-type-content .slide-frame-inner { padding-top: 1.5rem; }
        .slide-type-content .slide-header { margin-bottom: 1.25rem; }
        .slide-type-content .slide-main-title { font-size: 1.5rem; font-weight: 600; color: #fff; margin-bottom: 0.5rem; }
        .slide-type-content .slide-title-accent { width: 50px; height: 3px; background: var(--primary); border-radius: 2px; }
        .slide-type-content .slide-bullets { list-style: none; padding: 0; margin: 0; }
        .slide-type-content .slide-bullet { display: flex; align-items: flex-start; gap: 0.75rem; margin-bottom: 0.75rem; font-size: 1rem; color: rgba(255,255,255,0.9); line-height: 1.5; }
        .slide-type-content .slide-bullet::before { content: ''; width: 8px; height: 8px; background: var(--primary); border-radius: 50%; flex-shrink: 0; margin-top: 0.5rem; }

        .slide-type-two_column .slide-frame-inner { padding-top: 1.5rem; }
        .slide-type-two_column .slide-header { margin-bottom: 1rem; }
        .slide-type-two_column .slide-main-title { font-size: 1.5rem; font-weight: 600; color: #fff; margin-bottom: 0.5rem; }
        .slide-type-two_column .slide-columns { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; flex: 1; }
        .slide-type-two_column .slide-column { }
        .slide-type-two_column .slide-column-title { font-size: 1.1rem; font-weight: 600; color: var(--primary); margin-bottom: 0.75rem; padding-bottom: 0.5rem; border-bottom: 2px solid var(--primary); }
        .slide-type-two_column .slide-bullets { list-style: none; padding: 0; margin: 0; }
        .slide-type-two_column .slide-bullet { display: flex; align-items: flex-start; gap: 0.5rem; margin-bottom: 0.5rem; font-size: 0.9rem; color: rgba(255,255,255,0.85); line-height: 1.4; }
        .slide-type-two_column .slide-bullet::before { content: '•'; color: var(--primary); font-weight: bold; flex-shrink: 0; }

        .slide-type-quote .slide-frame { background: linear-gradient(135deg, #1a1a2e 0%, #2d1f4e 100%); }
        .slide-type-quote .slide-frame-inner { justify-content: center; align-items: center; text-align: center; padding: 2rem 3rem; }
        .slide-type-quote .slide-quote-mark { font-size: 4rem; color: var(--primary); opacity: 0.5; line-height: 1; margin-bottom: 0.5rem; }
        .slide-type-quote .slide-quote-text { font-size: 1.5rem; font-style: italic; color: #fff; line-height: 1.6; max-width: 700px; margin-bottom: 1.5rem; }
        .slide-type-quote .slide-quote-author { font-size: 1rem; color: rgba(255,255,255,0.6); }
        .slide-type-quote .slide-quote-author::before { content: '— '; }

        .slide-type-image .slide-frame-inner { padding: 1.5rem; }
        .slide-type-image .slide-header { margin-bottom: 1rem; }
        .slide-type-image .slide-main-title { font-size: 1.25rem; font-weight: 600; color: #fff; }
        .slide-type-image .slide-image-container { flex: 1; display: flex; justify-content: center; align-items: center; background: rgba(0,0,0,0.2); border-radius: 0.375rem; }
        .slide-type-image .slide-image-placeholder { color: rgba(255,255,255,0.4); font-size: 0.9rem; display: flex; flex-direction: column; align-items: center; gap: 0.5rem; }
        .slide-type-image .slide-image-placeholder svg { width: 3rem; height: 3rem; opacity: 0.5; }
        .slide-type-image .slide-image-caption { font-size: 0.85rem; color: rgba(255,255,255,0.5); text-align: center; margin-top: 0.75rem; }

        .slide-notes { background: var(--bg-card); border-top: 1px solid var(--border); padding: 0.75rem 1rem; font-size: 0.85rem; color: var(--text-muted); max-height: 100px; overflow-y: auto; }
        .slide-notes-label { font-size: 0.7rem; text-transform: uppercase; color: var(--text-muted); margin-bottom: 0.25rem; display: flex; align-items: center; gap: 0.5rem; }
        .slide-notes-label svg { width: 0.875rem; height: 0.875rem; }

        /* Metadata Viewer Styles */
        .metadata-viewer { padding: 1rem; }
        .metadata-section { background: var(--bg); border-radius: 0.5rem; margin-bottom: 1rem; overflow: hidden; border: 1px solid var(--border); }
        .metadata-section-header { padding: 0.75rem 1rem; background: var(--bg-card); border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 0.75rem; cursor: pointer; transition: background 0.2s; }
        .metadata-section-header:hover { background: rgba(59, 130, 246, 0.1); }
        .metadata-section-header svg { width: 1.25rem; height: 1.25rem; color: var(--primary); flex-shrink: 0; }
        .metadata-section-title { font-weight: 600; font-size: 0.9rem; flex: 1; }
        .metadata-section-badge { font-size: 0.7rem; padding: 0.15rem 0.5rem; border-radius: 9999px; background: var(--border); color: var(--text-muted); }
        .metadata-section-toggle { width: 1rem; height: 1rem; color: var(--text-muted); transition: transform 0.2s; }
        .metadata-section.collapsed .metadata-section-toggle { transform: rotate(-90deg); }
        .metadata-section-content { padding: 0.75rem 1rem; }
        .metadata-section.collapsed .metadata-section-content { display: none; }
        .metadata-row { display: flex; padding: 0.5rem 0; border-bottom: 1px solid var(--border); }
        .metadata-row:last-child { border-bottom: none; }
        .metadata-key { width: 140px; flex-shrink: 0; font-size: 0.8rem; color: var(--text-muted); text-transform: capitalize; }
        .metadata-value { flex: 1; font-size: 0.9rem; word-break: break-word; }
        .metadata-value.status-draft { color: var(--text-muted); }
        .metadata-value.status-in_review { color: var(--warning); }
        .metadata-value.status-approved { color: var(--success); }
        .metadata-value.status-published { color: var(--primary); }
        .metadata-badge { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 3px; font-size: 0.75rem; font-weight: 500; }
        .metadata-badge.badge-version { background: rgba(59, 130, 246, 0.2); color: var(--primary); }
        .metadata-badge.badge-status { background: rgba(34, 197, 94, 0.2); color: var(--success); }
        .metadata-badge.badge-accuracy { background: rgba(168, 85, 247, 0.2); color: #a855f7; }
        .metadata-badge.badge-language { background: rgba(236, 72, 153, 0.2); color: #ec4899; }
        .metadata-tags { display: flex; flex-wrap: wrap; gap: 0.35rem; }
        .metadata-tag { font-size: 0.75rem; padding: 0.2rem 0.5rem; background: var(--bg-card); border: 1px solid var(--border); border-radius: 3px; }
        .metadata-list { list-style: none; padding: 0; margin: 0; }
        .metadata-list li { padding: 0.25rem 0; font-size: 0.85rem; display: flex; align-items: center; gap: 0.5rem; }
        .metadata-list li::before { content: '→'; color: var(--primary); font-size: 0.75rem; }
        .metadata-date { display: flex; align-items: center; gap: 0.5rem; }
        .metadata-date-relative { font-size: 0.75rem; color: var(--text-muted); }
        .metadata-empty { color: var(--text-muted); font-style: italic; font-size: 0.85rem; }
        .metadata-json { background: var(--bg-card); padding: 0.5rem; border-radius: 0.25rem; font-family: monospace; font-size: 0.8rem; white-space: pre-wrap; max-height: 200px; overflow-y: auto; }
    </style>
</head>
"""
