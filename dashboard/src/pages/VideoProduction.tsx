import { useState, type ReactNode } from 'react';
import { Routes, Route, NavLink } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Film,
  Code,
  Play,
  Package,
  Settings,
  Clock,
  FileVideo,
  Mic,
  RefreshCw,
  Loader2,
  CheckCircle,
  XCircle,
  AlertCircle,
  Monitor,
} from 'lucide-react';
import clsx from 'clsx';
import type {
  VideoScriptItem,
  RenderJob,
  VideoAssetsResponse,
} from '@/api/types';
import { RemotionPreview, SceneNavigator, ComponentLibrary, VoiceoverPanel } from '@/components/video-production';
import { Wrench } from 'lucide-react';

// API functions
const getVideoScripts = async () => {
  const res = await fetch('/api/video/scripts');
  if (!res.ok) throw new Error('Failed to fetch scripts');
  return res.json();
};

const getVideoScript = async (scriptId: string) => {
  const res = await fetch(`/api/video/scripts/${scriptId}`);
  if (!res.ok) throw new Error('Failed to fetch script');
  return res.json();
};

const updateVideoScript = async ({ scriptId, content }: { scriptId: string; content: string }) => {
  const res = await fetch(`/api/video/scripts/${scriptId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  });
  if (!res.ok) throw new Error('Failed to update script');
  return res.json();
};

const startRender = async ({ scriptId, quality }: { scriptId: string; quality: string }) => {
  const res = await fetch('/api/video/render', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ script_id: scriptId, quality }),
  });
  if (!res.ok) throw new Error('Failed to start render');
  return res.json();
};

const getRenderQueue = async () => {
  const res = await fetch('/api/video/queue');
  if (!res.ok) throw new Error('Failed to fetch queue');
  return res.json();
};

const getVideoAssets = async () => {
  const res = await fetch('/api/video/assets');
  if (!res.ok) throw new Error('Failed to fetch assets');
  return res.json();
};

const getMotionComponents = async () => {
  const res = await fetch('/api/video/components');
  if (!res.ok) throw new Error('Failed to fetch components');
  return res.json();
};

// Tab configuration - use absolute paths to avoid nested routing issues
const tabs = [
  { path: '/video', icon: Film, label: 'Overview' },
  { path: '/video/scripts', icon: Code, label: 'Scripts' },
  { path: '/video/preview', icon: Monitor, label: 'Preview' },
  { path: '/video/render', icon: Play, label: 'Render' },
  { path: '/video/assets', icon: Package, label: 'Assets' },
  { path: '/video/tools', icon: Wrench, label: 'Tools' },
];

// ============================================================================
// Overview Tab
// ============================================================================
function VideoOverview() {
  const { data: scriptsData, isLoading: scriptsLoading } = useQuery({
    queryKey: ['videoScripts'],
    queryFn: getVideoScripts,
  });

  const { data: queueData, isLoading: queueLoading } = useQuery({
    queryKey: ['renderQueue'],
    queryFn: getRenderQueue,
  });

  const { data: assetsData, isLoading: assetsLoading } = useQuery({
    queryKey: ['videoAssets'],
    queryFn: getVideoAssets,
  });

  if (scriptsLoading || queueLoading || assetsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <span className="loading loading-spinner loading-lg text-primary" />
      </div>
    );
  }

  const scripts: VideoScriptItem[] = scriptsData?.scripts || [];
  const queue = queueData || { jobs: [], active: 0, completed: 0, failed: 0 };
  const assets: VideoAssetsResponse = assetsData || { demos: [], audio: [], graphics: [], outputs: [] };

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card bg-base-200">
          <div className="card-body p-4">
            <div className="text-2xl font-bold text-primary">{scripts.length}</div>
            <div className="text-sm text-base-content/60">Video Scripts</div>
          </div>
        </div>
        <div className="card bg-base-200">
          <div className="card-body p-4">
            <div className="text-2xl font-bold text-success">{scripts.filter(s => s.has_output).length}</div>
            <div className="text-sm text-base-content/60">Rendered Videos</div>
          </div>
        </div>
        <div className="card bg-base-200">
          <div className="card-body p-4">
            <div className="text-2xl font-bold text-warning">{queue.active}</div>
            <div className="text-sm text-base-content/60">Active Renders</div>
          </div>
        </div>
        <div className="card bg-base-200">
          <div className="card-body p-4">
            <div className="text-2xl font-bold text-info">{assets.demos.length}</div>
            <div className="text-sm text-base-content/60">Demo Clips</div>
          </div>
        </div>
      </div>

      {/* Recent Scripts */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="font-semibold flex items-center gap-2 mb-4">
            <Film size={18} className="text-primary" />
            Video Scripts
          </h3>
          {scripts.length === 0 ? (
            <p className="text-base-content/60 text-sm">No video scripts found</p>
          ) : (
            <div className="space-y-2">
              {scripts.slice(0, 5).map((script) => (
                <div key={script.id} className="flex items-center gap-3 p-3 rounded-lg bg-base-300">
                  <FileVideo size={16} className="text-primary" />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">{script.name}</div>
                    <div className="text-xs text-base-content/60">
                      {script.scenes} scenes
                      {script.duration && ` • ${Math.round(script.duration)}s`}
                    </div>
                  </div>
                  {script.has_output ? (
                    <CheckCircle size={16} className="text-success" />
                  ) : (
                    <AlertCircle size={16} className="text-warning" />
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Active Renders */}
      {queue.jobs.length > 0 && (
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="font-semibold flex items-center gap-2 mb-4">
              <Play size={18} className="text-success" />
              Recent Renders
            </h3>
            <div className="space-y-2">
              {queue.jobs.slice(0, 3).map((job: RenderJob) => (
                <RenderJobCard key={job.id} job={job} />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Scripts Tab
// ============================================================================
function VideoScripts() {
  const [selectedScript, setSelectedScript] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');
  const queryClient = useQueryClient();

  const { data: scriptsData, isLoading } = useQuery({
    queryKey: ['videoScripts'],
    queryFn: getVideoScripts,
  });

  const { data: scriptDetail, isLoading: detailLoading } = useQuery({
    queryKey: ['videoScript', selectedScript],
    queryFn: () => selectedScript ? getVideoScript(selectedScript) : null,
    enabled: !!selectedScript,
  });

  const updateMutation = useMutation({
    mutationFn: updateVideoScript,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videoScripts'] });
      queryClient.invalidateQueries({ queryKey: ['videoScript', selectedScript] });
    },
  });

  // Update edit content when script loads
  useState(() => {
    if (scriptDetail?.content) {
      setEditContent(scriptDetail.content);
    }
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <span className="loading loading-spinner loading-lg text-primary" />
      </div>
    );
  }

  const scripts: VideoScriptItem[] = scriptsData?.scripts || [];

  return (
    <div className="flex gap-6 h-[calc(100vh-280px)]">
      {/* Script List */}
      <aside className="w-72 flex-shrink-0 flex flex-col bg-base-200 rounded-lg overflow-hidden">
        <div className="p-4 border-b border-base-300">
          <h3 className="font-semibold flex items-center gap-2">
            <Film size={16} />
            Scripts
            <span className="badge badge-ghost badge-sm ml-auto">{scripts.length}</span>
          </h3>
        </div>
        <nav className="flex-1 overflow-y-auto p-2 space-y-1">
          {scripts.map((script) => (
            <button
              key={script.id}
              onClick={() => {
                setSelectedScript(script.id);
                setEditContent('');
              }}
              className={clsx(
                'w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-sm transition-colors',
                selectedScript === script.id
                  ? 'bg-primary/20 text-primary'
                  : 'hover:bg-base-300 text-base-content/80'
              )}
            >
              <FileVideo size={14} />
              <span className="flex-1 truncate">{script.name}</span>
              {script.has_output && <CheckCircle size={12} className="text-success" />}
            </button>
          ))}
        </nav>
      </aside>

      {/* Editor */}
      <main className="flex-1 min-w-0 flex flex-col">
        {selectedScript ? (
          detailLoading ? (
            <div className="flex items-center justify-center h-full">
              <span className="loading loading-spinner loading-lg text-primary" />
            </div>
          ) : scriptDetail ? (
            <>
              <div className="flex items-center gap-4 mb-4">
                <h2 className="text-lg font-semibold">{scriptDetail.parsed?.title || selectedScript}</h2>
                <span className="badge badge-ghost">{scriptDetail.parsed?.language || 'en'}</span>
                {scriptDetail.parsed?.metadata?.version && (
                  <span className="badge badge-info">v{scriptDetail.parsed.metadata.version}</span>
                )}
                <div className="flex-1" />
                <button
                  onClick={() => updateMutation.mutate({ scriptId: selectedScript, content: editContent })}
                  disabled={updateMutation.isPending || editContent === scriptDetail.content}
                  className="btn btn-primary btn-sm gap-2"
                >
                  {updateMutation.isPending ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : (
                    'Save'
                  )}
                </button>
              </div>
              <textarea
                className="textarea textarea-bordered flex-1 font-mono text-sm"
                value={editContent || scriptDetail.content}
                onChange={(e) => setEditContent(e.target.value)}
                placeholder="Script content..."
              />
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-base-content/60">
              Failed to load script
            </div>
          )
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Code size={48} className="text-base-content/30 mb-4" />
            <h3 className="text-lg font-semibold">Select a Script</h3>
            <p className="text-base-content/60">Choose a video script to edit</p>
          </div>
        )}
      </main>
    </div>
  );
}

// ============================================================================
// Render Tab
// ============================================================================
function VideoRender() {
  const [selectedScript, setSelectedScript] = useState<string>('');
  const [quality, setQuality] = useState<'preview' | 'production'>('production');
  const queryClient = useQueryClient();

  const { data: scriptsData } = useQuery({
    queryKey: ['videoScripts'],
    queryFn: getVideoScripts,
  });

  const { data: queueData, refetch: refetchQueue } = useQuery({
    queryKey: ['renderQueue'],
    queryFn: getRenderQueue,
    refetchInterval: 2000, // Poll every 2 seconds
  });

  const renderMutation = useMutation({
    mutationFn: startRender,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['renderQueue'] });
      setSelectedScript('');
    },
  });

  const scripts: VideoScriptItem[] = scriptsData?.scripts || [];
  const queue = queueData || { jobs: [], active: 0, completed: 0, failed: 0 };

  return (
    <div className="space-y-6">
      {/* Render Controls */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="font-semibold flex items-center gap-2 mb-4">
            <Settings size={18} />
            Start New Render
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="label">
                <span className="label-text">Script</span>
              </label>
              <select
                className="select select-bordered w-full"
                value={selectedScript}
                onChange={(e) => setSelectedScript(e.target.value)}
              >
                <option value="">Select a script...</option>
                {scripts.map((script) => (
                  <option key={script.id} value={script.id}>
                    {script.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">
                <span className="label-text">Quality</span>
              </label>
              <select
                className="select select-bordered w-full"
                value={quality}
                onChange={(e) => setQuality(e.target.value as 'preview' | 'production')}
              >
                <option value="preview">Preview (720p, fast)</option>
                <option value="production">Production (1080p, high quality)</option>
              </select>
            </div>
            <div className="flex items-end">
              <button
                onClick={() => renderMutation.mutate({ scriptId: selectedScript, quality })}
                disabled={!selectedScript || renderMutation.isPending}
                className="btn btn-primary w-full gap-2"
              >
                {renderMutation.isPending ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  <Play size={16} />
                )}
                Start Render
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Render Queue */}
      <div className="card bg-base-200">
        <div className="card-body">
          <div className="flex items-center gap-2 mb-4">
            <h3 className="font-semibold flex items-center gap-2">
              <Clock size={18} />
              Render Queue
            </h3>
            <div className="flex-1" />
            <button onClick={() => refetchQueue()} className="btn btn-ghost btn-sm">
              <RefreshCw size={14} />
            </button>
          </div>

          {queue.jobs.length === 0 ? (
            <p className="text-base-content/60 text-sm">No render jobs</p>
          ) : (
            <div className="space-y-3">
              {queue.jobs.map((job: RenderJob) => (
                <RenderJobCard key={job.id} job={job} showDetails />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Assets Tab
// ============================================================================
function VideoAssets() {
  const { data: assetsData, isLoading } = useQuery({
    queryKey: ['videoAssets'],
    queryFn: getVideoAssets,
  });

  const { data: componentsData } = useQuery({
    queryKey: ['motionComponents'],
    queryFn: getMotionComponents,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <span className="loading loading-spinner loading-lg text-primary" />
      </div>
    );
  }

  const assets: VideoAssetsResponse = assetsData || { demos: [], audio: [], graphics: [], outputs: [] };
  const components = componentsData || { components: [], backgrounds: [], transitions: [], text_effects: [] };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-6">
      {/* Demo Clips */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="font-semibold flex items-center gap-2 mb-4">
            <FileVideo size={18} className="text-primary" />
            Demo Clips
            <span className="badge badge-ghost badge-sm">{assets.demos.length}</span>
          </h3>
          {assets.demos.length === 0 ? (
            <p className="text-base-content/60 text-sm">No demo clips captured</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {assets.demos.map((demo) => (
                <div key={demo.path} className="flex items-center gap-3 p-3 rounded-lg bg-base-300">
                  <FileVideo size={16} />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate text-sm">{demo.name}</div>
                    <div className="text-xs text-base-content/60">{formatSize(demo.size)}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Audio Files */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="font-semibold flex items-center gap-2 mb-4">
            <Mic size={18} className="text-success" />
            Voiceover Audio
            <span className="badge badge-ghost badge-sm">{assets.audio.length}</span>
          </h3>
          {assets.audio.length === 0 ? (
            <p className="text-base-content/60 text-sm">No voiceover files generated</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {assets.audio.map((audio) => (
                <div key={audio.path} className="flex items-center gap-3 p-3 rounded-lg bg-base-300">
                  <Mic size={16} />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate text-sm">{audio.name}</div>
                    <div className="text-xs text-base-content/60">
                      {audio.language} • {formatSize(audio.size)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Motion Components */}
      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="font-semibold flex items-center gap-2 mb-4">
            <Package size={18} className="text-info" />
            Motion Graphics Components
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {components.components.map((comp: any) => (
              <div key={comp.id} className="p-3 rounded-lg bg-base-300">
                <div className="font-medium text-sm">{comp.name}</div>
                <div className="text-xs text-base-content/60 mt-1">{comp.description}</div>
                <div className="flex flex-wrap gap-1 mt-2">
                  {comp.props.slice(0, 3).map((prop: string) => (
                    <span key={prop} className="badge badge-ghost badge-xs">{prop}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Quick reference */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6 pt-4 border-t border-base-300">
            <div>
              <h4 className="text-sm font-medium mb-2">Backgrounds</h4>
              <div className="flex flex-wrap gap-1">
                {components.backgrounds.map((bg: string) => (
                  <span key={bg} className="badge badge-primary badge-sm">{bg}</span>
                ))}
              </div>
            </div>
            <div>
              <h4 className="text-sm font-medium mb-2">Transitions</h4>
              <div className="flex flex-wrap gap-1">
                {components.transitions.slice(0, 8).map((t: string) => (
                  <span key={t} className="badge badge-secondary badge-sm">{t}</span>
                ))}
              </div>
            </div>
            <div>
              <h4 className="text-sm font-medium mb-2">Text Effects</h4>
              <div className="flex flex-wrap gap-1">
                {components.text_effects.map((e: string) => (
                  <span key={e} className="badge badge-accent badge-sm">{e}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Tools Tab
// ============================================================================
function VideoTools() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-280px)]">
      {/* Component Library */}
      <div className="card bg-base-200 overflow-hidden">
        <div className="card-body p-0 flex flex-col h-full">
          <div className="p-4 border-b border-base-300">
            <h3 className="font-semibold flex items-center gap-2">
              <Package size={16} />
              Component Library
            </h3>
            <p className="text-xs text-base-content/60 mt-1">
              Browse motion graphics components for your videos
            </p>
          </div>
          <ComponentLibrary
            className="flex-1"
            onSelectComponent={(comp) => {
              // Could be used to insert component into script
              console.log('Selected component:', comp);
            }}
          />
        </div>
      </div>

      {/* Voiceover Panel */}
      <div className="card bg-base-200 overflow-hidden">
        <div className="card-body p-0 flex flex-col h-full">
          <div className="p-4 border-b border-base-300">
            <h3 className="font-semibold flex items-center gap-2">
              <Mic size={16} />
              Voiceover Preview
            </h3>
            <p className="text-xs text-base-content/60 mt-1">
              Preview and configure text-to-speech voiceovers
            </p>
          </div>
          <VoiceoverPanel className="flex-1" />
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Preview Tab
// ============================================================================
function VideoPreviewTab() {
  const [selectedScript, setSelectedScript] = useState<string | null>(null);
  const [currentFrame, setCurrentFrame] = useState(0);

  const { data: scriptsData } = useQuery({
    queryKey: ['videoScripts'],
    queryFn: getVideoScripts,
  });

  const { data: scriptDetail } = useQuery({
    queryKey: ['videoScript', selectedScript],
    queryFn: () => selectedScript ? getVideoScript(selectedScript) : null,
    enabled: !!selectedScript,
  });

  const scripts: VideoScriptItem[] = scriptsData?.scripts || [];
  const scenes = scriptDetail?.parsed?.scenes || [];

  // Transform scenes for navigator
  const fps = 30;
  let frameOffset = 0;
  const transformedScenes = scenes.map((scene: any, index: number) => {
    const duration = scene.duration || 5;
    const durationFrames = duration * fps;
    const startFrame = frameOffset;
    const endFrame = startFrame + durationFrames;
    frameOffset = endFrame;

    return {
      id: scene.id || `scene-${index}`,
      type: scene.type || 'default',
      title: scene.title || scene.text?.substring(0, 30),
      duration,
      startFrame,
      endFrame,
      background: scene.background,
      transition_in: scene.transition_in,
    };
  });

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Script Selector & Scene Navigator */}
      <div className="space-y-4">
        {/* Script Selection */}
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="font-semibold flex items-center gap-2 mb-3">
              <Film size={16} />
              Select Script
            </h3>
            <select
              className="select select-bordered w-full"
              value={selectedScript || ''}
              onChange={(e) => {
                setSelectedScript(e.target.value || null);
                setCurrentFrame(0);
              }}
            >
              <option value="">Choose a script to preview...</option>
              {scripts.map((script) => (
                <option key={script.id} value={script.id}>
                  {script.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Scene Navigator */}
        {selectedScript && transformedScenes.length > 0 && (
          <div className="card bg-base-200">
            <div className="card-body">
              <SceneNavigator
                scenes={transformedScenes}
                currentFrame={currentFrame}
                fps={fps}
                onSeek={setCurrentFrame}
                onSceneSelect={(id) => {
                  const scene = transformedScenes.find((s: any) => s.id === id);
                  if (scene) setCurrentFrame(scene.startFrame);
                }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Preview Player */}
      <div className="lg:col-span-2">
        <RemotionPreview
          scriptId={selectedScript || undefined}
          className="h-[600px] card bg-base-200"
        />
      </div>
    </div>
  );
}

// ============================================================================
// Render Job Card Component
// ============================================================================
function RenderJobCard({ job, showDetails = false }: { job: RenderJob; showDetails?: boolean }) {
  const statusIcons: Record<string, ReactNode> = {
    queued: <Clock size={16} className="text-info" />,
    rendering: <Loader2 size={16} className="text-warning animate-spin" />,
    completed: <CheckCircle size={16} className="text-success" />,
    failed: <XCircle size={16} className="text-error" />,
    cancelled: <XCircle size={16} className="text-base-content/40" />,
  };

  const statusColors: Record<string, string> = {
    queued: 'badge-info',
    rendering: 'badge-warning',
    completed: 'badge-success',
    failed: 'badge-error',
    cancelled: 'badge-ghost',
  };

  return (
    <div className="p-3 rounded-lg bg-base-300">
      <div className="flex items-center gap-3">
        {statusIcons[job.status]}
        <div className="flex-1 min-w-0">
          <div className="font-medium text-sm truncate">{job.script_id}</div>
          {showDetails && (
            <div className="text-xs text-base-content/60">
              {job.stage} • {job.quality}
            </div>
          )}
        </div>
        <span className={clsx('badge badge-sm', statusColors[job.status])}>
          {job.status}
        </span>
      </div>
      {job.status === 'rendering' && (
        <div className="mt-2">
          <progress
            className="progress progress-primary w-full"
            value={job.progress}
            max={100}
          />
          <div className="text-xs text-base-content/60 mt-1">{job.progress}%</div>
        </div>
      )}
      {job.error && (
        <div className="text-xs text-error mt-2">{job.error}</div>
      )}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================
export function VideoProduction() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Film className="w-6 h-6 text-primary" />
          Video Production
        </h1>
        <p className="text-base-content/60 mt-1">
          Create and render motion graphics videos from YAML scripts
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="tabs tabs-boxed bg-base-200 p-1">
        {tabs.map((tab) => (
          <NavLink
            key={tab.path}
            to={tab.path}
            end={tab.path === '/video'}
            className={({ isActive }) =>
              clsx('tab gap-2', { 'tab-active': isActive })
            }
          >
            <tab.icon size={16} />
            {tab.label}
          </NavLink>
        ))}
      </div>

      {/* Tab Content */}
      <Routes>
        <Route index element={<VideoOverview />} />
        <Route path="scripts" element={<VideoScripts />} />
        <Route path="preview" element={<VideoPreviewTab />} />
        <Route path="render" element={<VideoRender />} />
        <Route path="assets" element={<VideoAssets />} />
        <Route path="tools" element={<VideoTools />} />
      </Routes>
    </div>
  );
}

export default VideoProduction;
