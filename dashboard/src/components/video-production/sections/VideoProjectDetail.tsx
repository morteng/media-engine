/**
 * VideoProjectDetail - Detailed view of a video project
 * Shows components, dependencies, and review comments
 */

import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Film,
  FileText,
  Video as VideoIcon,
  Mic,
  Subtitles,
  FileJson,
  Play,
  Clock,
  CheckCircle,
  AlertCircle,
  AlertTriangle,
  RefreshCw,
  MoreVertical,
  MessageSquare,
  ChevronDown,
  ChevronRight,
  FolderOpen,
} from 'lucide-react';
import clsx from 'clsx';
import { Spinner, Breadcrumbs, type BreadcrumbItem } from '@/components/ui';
import { useVideoProjectDetail, useVideoReviewData } from '@/hooks/useVideoApi';
import type {
  ComponentType,
  ComponentStatus,
  VideoComponent,
  ProjectStatus,
} from '@/api/video';

// Component type configuration
const COMPONENT_CONFIG: Record<ComponentType, { label: string; icon: typeof FileText; color: string }> = {
  script: { label: 'Script', icon: FileText, color: 'text-blue-500' },
  demo_definition: { label: 'Demo Definition', icon: FileJson, color: 'text-purple-500' },
  demo_clip: { label: 'Demo Clip', icon: VideoIcon, color: 'text-green-500' },
  voiceover: { label: 'Voiceover', icon: Mic, color: 'text-orange-500' },
  captions: { label: 'Captions', icon: Subtitles, color: 'text-yellow-500' },
  props: { label: 'Props', icon: FileJson, color: 'text-pink-500' },
  render: { label: 'Render', icon: Play, color: 'text-red-500' },
};

// Component status configuration
const STATUS_CONFIG: Record<ComponentStatus, { label: string; color: string; icon: typeof Clock }> = {
  pending: { label: 'Pending', color: 'badge-ghost', icon: Clock },
  generating: { label: 'Generating', color: 'badge-info', icon: RefreshCw },
  ready: { label: 'Ready', color: 'badge-success', icon: CheckCircle },
  stale: { label: 'Stale', color: 'badge-warning', icon: AlertTriangle },
  error: { label: 'Error', color: 'badge-error', icon: AlertCircle },
};

// Project status configuration
const PROJECT_STATUS_CONFIG: Record<ProjectStatus, { label: string; color: string }> = {
  draft: { label: 'Draft', color: 'badge-ghost' },
  in_review: { label: 'In Review', color: 'badge-warning' },
  approved: { label: 'Approved', color: 'badge-info' },
  rendering: { label: 'Rendering', color: 'badge-secondary' },
  published: { label: 'Published', color: 'badge-success' },
};

interface ComponentItemProps {
  component: VideoComponent;
  onRegenerate: (id: string) => void;
  isRegenerating: boolean;
}

function ComponentItem({ component, onRegenerate, isRegenerating }: ComponentItemProps) {
  const typeConfig = COMPONENT_CONFIG[component.type];
  const statusConfig = STATUS_CONFIG[component.status];
  const TypeIcon = typeConfig.icon;
  const StatusIcon = statusConfig.icon;

  return (
    <div className="flex items-center gap-3 p-3 rounded-lg bg-base-300 hover:bg-base-300/80">
      <div className={clsx('p-2 rounded', typeConfig.color, 'bg-base-200')}>
        <TypeIcon size={16} />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium truncate">{typeConfig.label}</span>
          {component.scene_id && (
            <span className="badge badge-sm badge-outline">{component.scene_id}</span>
          )}
        </div>
        <div className="text-xs text-base-content/50 truncate">
          {component.path}
        </div>
      </div>

      <span className={`badge ${statusConfig.color} gap-1`}>
        <StatusIcon size={12} className={component.status === 'generating' ? 'animate-spin' : ''} />
        {statusConfig.label}
      </span>

      <div className="dropdown dropdown-end">
        <label tabIndex={0} className="btn btn-ghost btn-xs btn-circle">
          <MoreVertical size={14} />
        </label>
        <ul tabIndex={0} className="dropdown-content z-[1] menu p-1 shadow bg-base-100 rounded-box w-36 text-sm">
          <li>
            <button
              onClick={() => onRegenerate(component.id)}
              disabled={isRegenerating}
            >
              <RefreshCw size={12} /> Regenerate
            </button>
          </li>
        </ul>
      </div>
    </div>
  );
}

interface ComponentBrowserProps {
  components: Record<ComponentType, VideoComponent[]>;
  onRegenerate: (componentId: string) => void;
  isRegenerating: boolean;
}

function ComponentBrowser({ components, onRegenerate, isRegenerating }: ComponentBrowserProps) {
  const [expandedTypes, setExpandedTypes] = useState<Set<ComponentType>>(
    new Set(Object.keys(COMPONENT_CONFIG) as ComponentType[])
  );

  const toggleType = (type: ComponentType) => {
    const newExpanded = new Set(expandedTypes);
    if (newExpanded.has(type)) {
      newExpanded.delete(type);
    } else {
      newExpanded.add(type);
    }
    setExpandedTypes(newExpanded);
  };

  const sortedTypes = Object.keys(COMPONENT_CONFIG) as ComponentType[];

  return (
    <div className="space-y-2">
      {sortedTypes.map((type) => {
        const items = components[type] || [];
        const config = COMPONENT_CONFIG[type];
        const isExpanded = expandedTypes.has(type);
        const TypeIcon = config.icon;

        return (
          <div key={type} className="border border-base-300 rounded-lg overflow-hidden">
            <button
              className="flex items-center gap-2 w-full p-3 bg-base-200 hover:bg-base-300 transition-colors"
              onClick={() => toggleType(type)}
            >
              {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
              <TypeIcon size={16} className={config.color} />
              <span className="font-medium">{config.label}</span>
              <span className="badge badge-sm ml-auto">{items.length}</span>
            </button>

            {isExpanded && (
              <div className="p-2 space-y-2">
                {items.length === 0 ? (
                  <div className="text-sm text-base-content/50 text-center py-2">
                    No {config.label.toLowerCase()} components
                  </div>
                ) : (
                  items.map((component) => (
                    <ComponentItem
                      key={component.id}
                      component={component}
                      onRegenerate={onRegenerate}
                      isRegenerating={isRegenerating}
                    />
                  ))
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

export function VideoProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const {
    project,
    projectLoading,
    projectError,
    components,
    componentsLoading,
    regenerateComponent,
  } = useVideoProjectDetail(projectId || null);

  const {
    comments,
    stats: commentStats,
    isLoading: commentsLoading,
  } = useVideoReviewData(projectId || null);

  const handleRegenerate = (componentId: string) => {
    if (projectId) {
      regenerateComponent.mutate({
        projectId,
        componentId,
        cascade: true,
      });
    }
  };

  if (projectLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" className="text-primary" />
      </div>
    );
  }

  if (projectError || !project) {
    return (
      <div className="alert alert-error">
        <AlertCircle size={20} />
        <span>Failed to load project</span>
        <button className="btn btn-sm" onClick={() => navigate('/video/projects')}>
          Back to Projects
        </button>
      </div>
    );
  }

  const statusConfig = PROJECT_STATUS_CONFIG[project.status];

  // Breadcrumb navigation
  const breadcrumbItems: BreadcrumbItem[] = [
    { label: 'Video', href: '/video', icon: <VideoIcon size={14} /> },
    { label: 'Projects', href: '/video/projects', icon: <FolderOpen size={14} /> },
    { label: project.name },
  ];

  return (
    <div className="space-y-6">
      {/* Breadcrumbs */}
      <Breadcrumbs items={breadcrumbItems} className="mb-2" />

      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          className="btn btn-ghost btn-circle"
          onClick={() => navigate('/video/projects')}
        >
          <ArrowLeft size={20} />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{project.name}</h1>
            <span className={`badge ${statusConfig.color}`}>{statusConfig.label}</span>
          </div>
          <div className="text-sm text-base-content/60 flex items-center gap-2">
            <span>{project.language.toUpperCase()}</span>
            <span>-</span>
            <span>{Object.keys(project.components).length} components</span>
            <span>-</span>
            <span>{Math.round(project.progress * 100)}% complete</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            className="btn btn-outline gap-2"
            onClick={() => navigate(`/video/review?project=${projectId}`)}
          >
            <MessageSquare size={16} />
            Comments
            {commentStats && commentStats.pending > 0 && (
              <span className="badge badge-warning badge-sm">{commentStats.pending}</span>
            )}
          </button>
          <button
            className="btn btn-primary gap-2"
            onClick={() => navigate(`/video/timeline?project=${projectId}`)}
          >
            <Play size={16} />
            Preview
          </button>
        </div>
      </div>

      {/* Progress */}
      <div className="card bg-base-200">
        <div className="card-body p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium">Project Progress</span>
            <span className="text-sm">{Math.round(project.progress * 100)}%</span>
          </div>
          <progress
            className={clsx('progress w-full', {
              'progress-primary': project.progress < 1,
              'progress-success': project.progress === 1,
            })}
            value={project.progress * 100}
            max="100"
          />
          {components && (
            <div className="flex items-center gap-4 mt-2 text-xs text-base-content/60">
              <span className="flex items-center gap-1">
                <CheckCircle size={12} className="text-success" />
                {components.ready} ready
              </span>
              <span className="flex items-center gap-1">
                <AlertTriangle size={12} className="text-warning" />
                {components.stale} stale
              </span>
              <span className="flex items-center gap-1">
                <Clock size={12} className="text-base-content/40" />
                {components.pending} pending
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Components */}
        <div className="lg:col-span-2">
          <div className="card bg-base-200">
            <div className="card-body">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold flex items-center gap-2">
                  <Film size={18} className="text-primary" />
                  Components
                </h2>
                <button
                  className="btn btn-ghost btn-sm"
                  onClick={() => {
                    // Regenerate all stale components
                    const staleComponents = Object.values(project.components)
                      .filter(c => c.status === 'stale');
                    staleComponents.forEach(c => handleRegenerate(c.id));
                  }}
                  disabled={regenerateComponent.isPending}
                >
                  <RefreshCw size={14} />
                  Regenerate Stale
                </button>
              </div>

              {componentsLoading ? (
                <div className="flex justify-center py-8">
                  <Spinner size="md" />
                </div>
              ) : components ? (
                <ComponentBrowser
                  components={components.by_type}
                  onRegenerate={handleRegenerate}
                  isRegenerating={regenerateComponent.isPending}
                />
              ) : (
                <div className="text-center text-base-content/50 py-8">
                  No components found
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Project Info */}
          <div className="card bg-base-200">
            <div className="card-body">
              <h3 className="font-semibold mb-3">Project Info</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-base-content/60">Created</span>
                  <span>{new Date(project.created_at).toLocaleDateString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-base-content/60">Modified</span>
                  <span>{new Date(project.modified_at).toLocaleDateString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-base-content/60">Language</span>
                  <span>{project.language.toUpperCase()}</span>
                </div>
                {project.source_documents.length > 0 && (
                  <div className="pt-2 border-t border-base-300">
                    <span className="text-base-content/60">Source Documents</span>
                    <ul className="mt-1 space-y-1">
                      {project.source_documents.slice(0, 3).map((doc, i) => (
                        <li key={i} className="truncate text-xs">
                          {doc.split('/').pop()}
                        </li>
                      ))}
                      {project.source_documents.length > 3 && (
                        <li className="text-xs text-base-content/50">
                          +{project.source_documents.length - 3} more
                        </li>
                      )}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Review Comments Summary */}
          <div className="card bg-base-200">
            <div className="card-body">
              <h3 className="font-semibold mb-3 flex items-center gap-2">
                <MessageSquare size={16} />
                Review Comments
              </h3>
              {commentsLoading ? (
                <Spinner size="sm" />
              ) : commentStats ? (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-base-content/60">Pending</span>
                    <span className="badge badge-warning badge-sm">{commentStats.pending}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-base-content/60">Processing</span>
                    <span className="badge badge-info badge-sm">{commentStats.processing}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-base-content/60">Resolved</span>
                    <span className="badge badge-success badge-sm">{commentStats.resolved}</span>
                  </div>
                  {comments.length > 0 && (
                    <div className="pt-2 border-t border-base-300 mt-2">
                      <span className="text-xs text-base-content/60">Recent Comments</span>
                      <div className="mt-2 space-y-2">
                        {comments.slice(0, 3).map((comment) => (
                          <div key={comment.id} className="text-xs p-2 bg-base-300 rounded">
                            <div className="truncate">{comment.text}</div>
                            <div className="text-base-content/50 mt-1">
                              {comment.author} - {new Date(comment.created_at).toLocaleDateString()}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-sm text-base-content/50">No comments</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
