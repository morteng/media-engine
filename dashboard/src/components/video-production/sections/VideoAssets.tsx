/**
 * VideoAssets - Assets browser tab for video production
 * Displays demo clips, audio files, and motion components
 * With inline video preview for demo clips
 */

import { useState, useRef, useCallback } from 'react';
import {
  FileVideo,
  Mic,
  Package,
  Play,
  Pause,
  Volume2,
  VolumeX,
  Maximize2,
} from 'lucide-react';
import { Spinner, Modal } from '@/components/ui';
import { formatSize } from '@/utils/format';
import { useVideoAssets, useMotionComponents } from '@/hooks/useVideoApi';
import type { VideoAssetsResponse } from '@/api/types';
import clsx from 'clsx';

interface VideoPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  videoPath: string | null;
  videoName: string;
}

function VideoPreviewModal({ isOpen, onClose, videoPath, videoName }: VideoPreviewModalProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  const togglePlay = useCallback(() => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  }, [isPlaying]);

  const toggleMute = useCallback(() => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  }, [isMuted]);

  const handleTimeUpdate = useCallback(() => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  }, []);

  const handleLoadedMetadata = useCallback(() => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  }, []);

  const handleSeek = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (videoRef.current) {
      const time = parseFloat(e.target.value);
      videoRef.current.currentTime = time;
      setCurrentTime(time);
    }
  }, []);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleFullscreen = useCallback(() => {
    if (videoRef.current) {
      videoRef.current.requestFullscreen?.();
    }
  }, []);

  if (!videoPath) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={videoName}
      size="lg"
      className="!max-w-4xl"
    >
      <div className="flex flex-col gap-3">
        {/* Video */}
        <div className="relative bg-black rounded-lg overflow-hidden aspect-video">
          <video
            ref={videoRef}
            src={`/api/video/asset?path=${encodeURIComponent(videoPath)}`}
            className="w-full h-full object-contain"
            onTimeUpdate={handleTimeUpdate}
            onLoadedMetadata={handleLoadedMetadata}
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
            onEnded={() => setIsPlaying(false)}
            onClick={togglePlay}
            playsInline
          />

          {/* Play overlay */}
          {!isPlaying && (
            <button
              onClick={togglePlay}
              className="absolute inset-0 flex items-center justify-center bg-black/30 hover:bg-black/40 transition-colors"
            >
              <div className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center">
                <Play size={32} className="text-white ml-1" />
              </div>
            </button>
          )}
        </div>

        {/* Controls */}
        <div className="flex items-center gap-3 bg-base-300 rounded-lg p-2">
          <button onClick={togglePlay} className="btn btn-ghost btn-sm btn-square">
            {isPlaying ? <Pause size={18} /> : <Play size={18} />}
          </button>

          <span className="text-sm font-mono text-base-content/70 min-w-[70px]">
            {formatTime(currentTime)}
          </span>

          <input
            type="range"
            min="0"
            max={duration || 100}
            value={currentTime}
            onChange={handleSeek}
            className="range range-xs flex-1"
          />

          <span className="text-sm font-mono text-base-content/70 min-w-[70px]">
            {formatTime(duration)}
          </span>

          <button onClick={toggleMute} className="btn btn-ghost btn-sm btn-square">
            {isMuted ? <VolumeX size={16} /> : <Volume2 size={16} />}
          </button>

          <button onClick={handleFullscreen} className="btn btn-ghost btn-sm btn-square">
            <Maximize2 size={16} />
          </button>
        </div>
      </div>
    </Modal>
  );
}

export function VideoAssets() {
  const { data: assetsData, isLoading } = useVideoAssets();
  const { data: componentsData } = useMotionComponents();
  const [selectedVideo, setSelectedVideo] = useState<{ path: string; name: string } | null>(null);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" className="text-primary" />
      </div>
    );
  }

  const assets: VideoAssetsResponse = assetsData || { demos: [], audio: [], graphics: [], outputs: [] };
  const components = componentsData || { components: [], backgrounds: [], transitions: [], text_effects: [] };

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
                <button
                  key={demo.path}
                  onClick={() => setSelectedVideo({ path: demo.path, name: demo.name })}
                  className={clsx(
                    'flex items-center gap-3 p-3 rounded-lg bg-base-300',
                    'hover:bg-primary/20 hover:ring-1 hover:ring-primary/30',
                    'transition-colors cursor-pointer text-left group'
                  )}
                >
                  <div className="relative">
                    <FileVideo size={16} className="group-hover:hidden" />
                    <Play size={16} className="hidden group-hover:block text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate text-sm group-hover:text-primary">{demo.name}</div>
                    <div className="text-xs text-base-content/60">{formatSize(demo.size)}</div>
                  </div>
                </button>
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

      {/* Video Preview Modal */}
      <VideoPreviewModal
        isOpen={!!selectedVideo}
        onClose={() => setSelectedVideo(null)}
        videoPath={selectedVideo?.path ?? null}
        videoName={selectedVideo?.name ?? ''}
      />
    </div>
  );
}
