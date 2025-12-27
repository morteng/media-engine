/**
 * Remotion Studio Preview Component
 *
 * Embeds the Remotion Studio in an iframe for live video preview.
 */

import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Play,
  ExternalLink,
  RefreshCw,
  Loader2,
  AlertCircle,
  Monitor,
  Maximize2,
} from 'lucide-react';
import clsx from 'clsx';

interface PreviewConfig {
  enabled: boolean;
  studio_url: string;
  studio_port: number;
  compositions: string[];
  default_composition: string;
}

interface RemotionPreviewProps {
  scriptId?: string;
  className?: string;
}

const getPreviewConfig = async (): Promise<PreviewConfig> => {
  const res = await fetch('/api/video/preview/config');
  if (!res.ok) throw new Error('Failed to fetch preview config');
  return res.json();
};

const startPreviewServer = async () => {
  const res = await fetch('/api/video/preview/start', { method: 'POST' });
  if (!res.ok) throw new Error('Failed to start preview server');
  return res.json();
};

const checkServerStatus = async (url: string): Promise<boolean> => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);
    await fetch(url, { mode: 'no-cors', signal: controller.signal });
    clearTimeout(timeoutId);
    return true;
  } catch {
    return false;
  }
};

export function RemotionPreview({ scriptId, className }: RemotionPreviewProps) {
  const [isServerReady, setIsServerReady] = useState(false);
  const [composition, setComposition] = useState('Main');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [iframeKey, setIframeKey] = useState(0);

  const { data: config, isLoading: configLoading } = useQuery({
    queryKey: ['previewConfig'],
    queryFn: getPreviewConfig,
  });

  const startMutation = useMutation({
    mutationFn: startPreviewServer,
    onSuccess: () => {
      // Start polling for server ready
      const poll = setInterval(async () => {
        if (config?.studio_url) {
          const ready = await checkServerStatus(config.studio_url);
          if (ready) {
            setIsServerReady(true);
            clearInterval(poll);
          }
        }
      }, 1000);

      // Stop polling after 30 seconds
      setTimeout(() => clearInterval(poll), 30000);
    },
  });

  // Check if server is already running on mount
  useEffect(() => {
    if (config?.studio_url) {
      checkServerStatus(config.studio_url).then(setIsServerReady);
    }
  }, [config?.studio_url]);

  // Build iframe URL with composition
  const getIframeUrl = useCallback(() => {
    if (!config?.studio_url) return '';
    const url = new URL(config.studio_url);
    url.searchParams.set('composition', composition);
    return url.toString();
  }, [config?.studio_url, composition]);

  const handleRefresh = () => {
    setIframeKey((k) => k + 1);
  };

  const handleOpenExternal = () => {
    if (config?.studio_url) {
      window.open(getIframeUrl(), '_blank');
    }
  };

  const handleStartServer = () => {
    startMutation.mutate();
  };

  if (configLoading) {
    return (
      <div className={clsx('flex items-center justify-center h-64', className)}>
        <Loader2 className="animate-spin text-primary" size={32} />
      </div>
    );
  }

  if (!config?.enabled) {
    return (
      <div className={clsx('card bg-base-200', className)}>
        <div className="card-body items-center text-center">
          <AlertCircle size={48} className="text-warning mb-4" />
          <h3 className="font-semibold text-lg">Remotion Not Configured</h3>
          <p className="text-base-content/60 max-w-md">
            No Remotion project found. Create a <code className="badge badge-ghost">remotion/</code> directory
            with a Remotion project to enable video preview.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={clsx('flex flex-col', className, { 'fixed inset-0 z-50 bg-base-300': isFullscreen })}>
      {/* Controls */}
      <div className="flex items-center gap-4 mb-4 px-4 pt-4">
        <h3 className="font-semibold flex items-center gap-2">
          <Monitor size={18} className="text-primary" />
          Preview
        </h3>

        {/* Composition Selector */}
        <select
          className="select select-bordered select-sm"
          value={composition}
          onChange={(e) => setComposition(e.target.value)}
        >
          {config.compositions.map((comp) => (
            <option key={comp} value={comp}>
              {comp}
            </option>
          ))}
        </select>

        <div className="flex-1" />

        {/* Server Status */}
        {isServerReady ? (
          <span className="badge badge-success gap-1">
            <span className="w-2 h-2 bg-success rounded-full animate-pulse" />
            Live
          </span>
        ) : (
          <span className="badge badge-warning gap-1">
            <span className="w-2 h-2 bg-warning rounded-full" />
            Offline
          </span>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2">
          {!isServerReady && (
            <button
              onClick={handleStartServer}
              disabled={startMutation.isPending}
              className="btn btn-primary btn-sm gap-2"
            >
              {startMutation.isPending ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <Play size={14} />
              )}
              Start Server
            </button>
          )}

          <button onClick={handleRefresh} className="btn btn-ghost btn-sm" title="Refresh">
            <RefreshCw size={14} />
          </button>

          <button onClick={handleOpenExternal} className="btn btn-ghost btn-sm" title="Open in new tab">
            <ExternalLink size={14} />
          </button>

          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="btn btn-ghost btn-sm"
            title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
          >
            <Maximize2 size={14} />
          </button>
        </div>
      </div>

      {/* Preview Frame */}
      <div className={clsx('flex-1 bg-black rounded-lg overflow-hidden', { 'rounded-none': isFullscreen })}>
        {isServerReady ? (
          <iframe
            key={iframeKey}
            src={getIframeUrl()}
            className="w-full h-full border-0"
            title="Remotion Studio Preview"
            allow="autoplay; fullscreen"
          />
        ) : (
          <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-base-content/60">
            <Monitor size={64} className="mb-4 opacity-30" />
            <h4 className="font-medium mb-2">Preview Server Not Running</h4>
            <p className="text-sm mb-4">Start the Remotion Studio to preview videos</p>
            <button
              onClick={handleStartServer}
              disabled={startMutation.isPending}
              className="btn btn-primary gap-2"
            >
              {startMutation.isPending ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Starting...
                </>
              ) : (
                <>
                  <Play size={16} />
                  Start Preview Server
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Script Info */}
      {scriptId && (
        <div className="px-4 py-2 text-sm text-base-content/60">
          Previewing: <span className="font-mono">{scriptId}</span>
        </div>
      )}
    </div>
  );
}

export default RemotionPreview;
