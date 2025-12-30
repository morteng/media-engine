/**
 * VideoProduction - Main page for video production
 * Routes to modular section components for each tab
 *
 * Tab Structure:
 * - Overview: Stats, quick actions, recent activity
 * - Projects: Video project management with component tracking
 * - Scripts: Script browser + editor with parsed structure view
 * - Timeline: Visual scene timeline with frame-accurate editing
 * - Props: Props viewer with scene timing visualization
 * - Assets: Unified media browser (demos, audio, captions, outputs)
 * - Render: Render queue with quality selection
 */

import { Routes, Route, NavLink, useLocation } from 'react-router-dom';
import {
  Code,
  Play,
  Package,
  Layers,
  FileJson,
  Film,
  FolderKanban,
} from 'lucide-react';
import clsx from 'clsx';
import {
  VideoOverview,
  VideoScripts,
  VideoTimeline,
  VideoProps,
  VideoRender,
  VideoAssets,
  VideoProjects,
  VideoProjectDetail,
} from '@/components/video-production/sections';

// Tab configuration - use absolute paths to avoid nested routing issues
const tabs = [
  { path: '/video', icon: Film, label: 'Overview' },
  { path: '/video/projects', icon: FolderKanban, label: 'Projects' },
  { path: '/video/scripts', icon: Code, label: 'Scripts' },
  { path: '/video/timeline', icon: Layers, label: 'Timeline' },
  { path: '/video/props', icon: FileJson, label: 'Props' },
  { path: '/video/assets', icon: Package, label: 'Assets' },
  { path: '/video/render', icon: Play, label: 'Render' },
];

export function VideoProduction() {
  const location = useLocation();

  // Hide tabs when viewing project details
  const isProjectDetail = location.pathname.match(/^\/video\/projects\/[^/]+$/);

  return (
    <div className="space-y-4">
      {/* Tab Navigation - hide on project detail pages */}
      {!isProjectDetail && (
        <div className="tabs tabs-boxed bg-base-200 p-1">
          {tabs.map((tab) => (
            <NavLink
              key={tab.path}
              to={tab.path}
              end={tab.path === '/video' || tab.path === '/video/projects'}
              className={({ isActive }) =>
                clsx('tab gap-2', { 'tab-active': isActive })
              }
            >
              <tab.icon size={16} />
              {tab.label}
            </NavLink>
          ))}
        </div>
      )}

      {/* Tab Content */}
      <Routes>
        <Route index element={<VideoOverview />} />
        <Route path="projects" element={<VideoProjects />} />
        <Route path="projects/:projectId" element={<VideoProjectDetail />} />
        <Route path="scripts" element={<VideoScripts />} />
        <Route path="timeline" element={<VideoTimeline />} />
        <Route path="props" element={<VideoProps />} />
        <Route path="assets" element={<VideoAssets />} />
        <Route path="render" element={<VideoRender />} />
      </Routes>
    </div>
  );
}

export default VideoProduction;
