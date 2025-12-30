/**
 * VideoProjects - Video project management section
 * Lists all video projects with status, progress, and actions
 */

import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  FolderPlus,
  Film,
  Clock,
  CheckCircle,
  AlertCircle,
  Eye,
  Trash2,
  MoreVertical,
  RefreshCw,
  Filter,
} from 'lucide-react';
import clsx from 'clsx';
import { Spinner } from '@/components/ui';
import { useVideoProjectsData } from '@/hooks/useVideoApi';
import type { ProjectStatus, VideoProjectSummary } from '@/api/video';

const STATUS_CONFIG: Record<ProjectStatus, { label: string; color: string; icon: typeof Clock }> = {
  draft: { label: 'Draft', color: 'badge-ghost', icon: Clock },
  in_review: { label: 'In Review', color: 'badge-warning', icon: Eye },
  approved: { label: 'Approved', color: 'badge-info', icon: CheckCircle },
  rendering: { label: 'Rendering', color: 'badge-secondary', icon: RefreshCw },
  published: { label: 'Published', color: 'badge-success', icon: Film },
};

interface ProjectCardProps {
  project: VideoProjectSummary;
  onView: (id: string) => void;
  onDelete: (id: string) => void;
}

function ProjectCard({ project, onView, onDelete }: ProjectCardProps) {
  const config = STATUS_CONFIG[project.status];
  const StatusIcon = config.icon;

  return (
    <div className="card bg-base-200 hover:bg-base-300 transition-colors">
      <div className="card-body p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <Film size={20} className="text-primary" />
            </div>
            <div>
              <h3 className="font-semibold">{project.name}</h3>
              <div className="flex items-center gap-2 text-xs text-base-content/60">
                <span>{project.language.toUpperCase()}</span>
                <span>-</span>
                <span>{project.components_count} components</span>
              </div>
            </div>
          </div>

          <div className="dropdown dropdown-end">
            <label tabIndex={0} className="btn btn-ghost btn-sm btn-circle">
              <MoreVertical size={16} />
            </label>
            <ul tabIndex={0} className="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-40">
              <li>
                <button onClick={() => onView(project.id)}>
                  <Eye size={14} /> View Details
                </button>
              </li>
              <li>
                <button onClick={() => onDelete(project.id)} className="text-error">
                  <Trash2 size={14} /> Delete
                </button>
              </li>
            </ul>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-4">
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="text-base-content/60">Progress</span>
            <span className="font-medium">{Math.round(project.progress * 100)}%</span>
          </div>
          <progress
            className={clsx('progress w-full', {
              'progress-primary': project.progress < 1,
              'progress-success': project.progress === 1,
            })}
            value={project.progress * 100}
            max="100"
          />
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between mt-3">
          <span className={`badge ${config.color} gap-1`}>
            <StatusIcon size={12} className={project.status === 'rendering' ? 'animate-spin' : ''} />
            {config.label}
          </span>
          <span className="text-xs text-base-content/50">
            {new Date(project.modified_at).toLocaleDateString()}
          </span>
        </div>
      </div>
    </div>
  );
}

interface CreateProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (name: string, language: string) => void;
  isCreating: boolean;
}

function CreateProjectModal({ isOpen, onClose, onCreate, isCreating }: CreateProjectModalProps) {
  const [name, setName] = useState('');
  const [language, setLanguage] = useState('en');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim()) {
      onCreate(name.trim(), language);
    }
  };

  if (!isOpen) return null;

  return (
    <dialog className="modal modal-open">
      <div className="modal-box">
        <h3 className="font-bold text-lg mb-4">Create Video Project</h3>
        <form onSubmit={handleSubmit}>
          <div className="form-control mb-4">
            <label className="label">
              <span className="label-text">Project Name</span>
            </label>
            <input
              type="text"
              placeholder="e.g., Dashboard Demo, Feature Overview"
              className="input input-bordered"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
            />
          </div>

          <div className="form-control mb-6">
            <label className="label">
              <span className="label-text">Language</span>
            </label>
            <select
              className="select select-bordered"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              <option value="en">English</option>
              <option value="no">Norwegian</option>
              <option value="de">German</option>
              <option value="fr">French</option>
              <option value="es">Spanish</option>
            </select>
          </div>

          <div className="modal-action">
            <button type="button" className="btn" onClick={onClose} disabled={isCreating}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!name.trim() || isCreating}
            >
              {isCreating ? <Spinner size="sm" /> : <FolderPlus size={16} />}
              Create Project
            </button>
          </div>
        </form>
      </div>
      <form method="dialog" className="modal-backdrop">
        <button onClick={onClose}>close</button>
      </form>
    </dialog>
  );
}

export function VideoProjects() {
  const [searchParams, setSearchParams] = useSearchParams();
  const statusFilter = searchParams.get('status') as ProjectStatus | null;
  const navigate = useNavigate();

  const [showCreateModal, setShowCreateModal] = useState(false);

  const {
    projects,
    count,
    isLoading,
    error,
    create,
  } = useVideoProjectsData(statusFilter || undefined);

  const handleCreateProject = (name: string, language: string) => {
    create.mutate({ name, language }, {
      onSuccess: (data) => {
        setShowCreateModal(false);
        navigate(`/video/projects/${data.id}`);
      },
    });
  };

  const handleViewProject = (id: string) => {
    navigate(`/video/projects/${id}`);
  };

  const handleDeleteProject = (_id: string) => {
    if (confirm('Are you sure you want to delete this project?')) {
      // TODO: implement delete
    }
  };

  const setStatusFilter = (status: ProjectStatus | null) => {
    if (status) {
      searchParams.set('status', status);
    } else {
      searchParams.delete('status');
    }
    setSearchParams(searchParams);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" className="text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-error">
        <AlertCircle size={20} />
        <span>Failed to load video projects</span>
      </div>
    );
  }

  // Stats by status
  const statsByStatus = projects.reduce((acc, p) => {
    acc[p.status] = (acc[p.status] || 0) + 1;
    return acc;
  }, {} as Record<ProjectStatus, number>);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold">Video Projects</h2>
          <p className="text-sm text-base-content/60">
            Manage video production with component tracking and cascade regeneration
          </p>
        </div>
        <button
          className="btn btn-primary gap-2"
          onClick={() => setShowCreateModal(true)}
        >
          <FolderPlus size={16} />
          New Project
        </button>
      </div>

      {/* Stats */}
      <div className="stats bg-base-200 w-full">
        <div className="stat">
          <div className="stat-title">Total Projects</div>
          <div className="stat-value text-primary">{count}</div>
        </div>
        {Object.entries(STATUS_CONFIG).map(([status, config]) => (
          <div key={status} className="stat">
            <div className="stat-title">{config.label}</div>
            <div className="stat-value text-lg">
              {statsByStatus[status as ProjectStatus] || 0}
            </div>
          </div>
        ))}
      </div>

      {/* Filter */}
      <div className="flex items-center gap-2">
        <Filter size={16} className="text-base-content/60" />
        <span className="text-sm text-base-content/60">Filter:</span>
        <div className="join">
          <button
            className={clsx('btn btn-sm join-item', !statusFilter && 'btn-active')}
            onClick={() => setStatusFilter(null)}
          >
            All
          </button>
          {Object.entries(STATUS_CONFIG).map(([status, config]) => (
            <button
              key={status}
              className={clsx('btn btn-sm join-item', statusFilter === status && 'btn-active')}
              onClick={() => setStatusFilter(status as ProjectStatus)}
            >
              {config.label}
            </button>
          ))}
        </div>
      </div>

      {/* Projects Grid */}
      {projects.length === 0 ? (
        <div className="card bg-base-200">
          <div className="card-body items-center text-center">
            <Film size={48} className="text-base-content/30" />
            <h3 className="font-semibold mt-2">No Video Projects</h3>
            <p className="text-sm text-base-content/60">
              {statusFilter
                ? `No projects with status "${STATUS_CONFIG[statusFilter].label}"`
                : 'Create your first video project to get started'}
            </p>
            {!statusFilter && (
              <button
                className="btn btn-primary mt-4"
                onClick={() => setShowCreateModal(true)}
              >
                <FolderPlus size={16} />
                Create Project
              </button>
            )}
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onView={handleViewProject}
              onDelete={handleDeleteProject}
            />
          ))}
        </div>
      )}

      {/* Create Modal */}
      <CreateProjectModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={handleCreateProject}
        isCreating={create.isPending}
      />
    </div>
  );
}
