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

import { useMemo } from 'react';
import { Routes, Route, NavLink, useLocation, useParams } from 'react-router-dom';
import {
  Code,
  Play,
  Package,
  Layers,
  FileJson,
  Film,
  FolderKanban,
  MessageSquare,
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
  VideoReview,
} from '@/components/video-production/sections';
import { WorkflowProgress, useCurrentWorkflowStep } from '@/components/video-production';

// Tab configuration - use absolute paths to avoid nested routing issues
const tabs = [
  { path: '/video', icon: Film, label: 'Overview' },
  { path: '/video/projects', icon: FolderKanban, label: 'Projects' },
  { path: '/video/review', icon: MessageSquare, label: 'Review' },
  { path: '/video/scripts', icon: Code, label: 'Scripts' },
  { path: '/video/timeline', icon: Layers, label: 'Timeline' },
  { path: '/video/props', icon: FileJson, label: 'Props' },
  { path: '/video/assets', icon: Package, label: 'Assets' },
  { path: '/video/render', icon: Play, label: 'Render' },
];

// Wrapper component to extract projectId from URL params
function VideoReviewWithParams() {
  const { projectId } = useParams<{ projectId: string }>();
  return <VideoReview projectId={projectId || null} />;
}

// Steps that are part of the workflow (subset of tabs)
const WORKFLOW_STEP_PATHS = ['/video/scripts', '/video/assets', '/video/props', '/video/timeline', '/video/render'];

export function VideoProduction() {
  const location = useLocation();

  // Hide tabs when viewing project details
  const isProjectDetail = location.pathname.match(/^\/video\/projects\/[^/]+$/);

  // Determine current workflow step from URL
  const currentStep = useCurrentWorkflowStep(location.pathname);

  // Track completed steps (in a real app, this would come from project state)
  // For now, we mark steps as complete if they come before the current step
  const completedSteps = useMemo(() => {
    const completed = new Set<string>();
    const stepOrder = ['scripts', 'voiceover', 'props', 'timeline', 'render'];
    const currentIndex = stepOrder.indexOf(currentStep);

    // Mark all steps before current as complete
    for (let i = 0; i < currentIndex; i++) {
      completed.add(stepOrder[i]);
    }

    return completed;
  }, [currentStep]);

  // Check if we're on a workflow step page (not overview, projects, or review)
  const isWorkflowPage = WORKFLOW_STEP_PATHS.includes(location.pathname);

  return (
    <div className="space-y-4">
      {/* Workflow Progress Indicator - show only on workflow pages */}
      {!isProjectDetail && isWorkflowPage && (
        <WorkflowProgress
          currentStep={currentStep}
          completedSteps={completedSteps}
        />
      )}

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
        <Route path="review" element={<VideoReview projectId={null} />} />
        <Route path="review/:projectId" element={<VideoReviewWithParams />} />
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
