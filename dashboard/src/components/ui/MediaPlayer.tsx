import { useRef, useState, useEffect } from 'react';
import { Play, Pause, Volume2, VolumeX, Maximize, SkipBack, SkipForward } from 'lucide-react';

interface MediaPlayerProps {
  src: string;
  type: 'video' | 'audio';
  poster?: string;
  captions?: string;
  title?: string;
  sceneTiming?: Array<{
    id: string;
    startTime: number;
    endTime: number;
    name?: string;
  }>;
  onSceneChange?: (sceneId: string) => void;
  className?: string;
}

export function MediaPlayer({
  src,
  type,
  poster,
  captions,
  title,
  sceneTiming,
  onSceneChange,
  className = '',
}: MediaPlayerProps) {
  const mediaRef = useRef<HTMLVideoElement | HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [currentScene, setCurrentScene] = useState<string | null>(null);

  useEffect(() => {
    const media = mediaRef.current;
    if (!media) return;

    const handleTimeUpdate = () => {
      setCurrentTime(media.currentTime);

      // Check which scene we're in
      if (sceneTiming) {
        for (const scene of sceneTiming) {
          if (media.currentTime >= scene.startTime && media.currentTime < scene.endTime) {
            if (currentScene !== scene.id) {
              setCurrentScene(scene.id);
              onSceneChange?.(scene.id);
            }
            break;
          }
        }
      }
    };

    const handleLoadedMetadata = () => {
      setDuration(media.duration);
    };

    const handleEnded = () => {
      setIsPlaying(false);
    };

    media.addEventListener('timeupdate', handleTimeUpdate);
    media.addEventListener('loadedmetadata', handleLoadedMetadata);
    media.addEventListener('ended', handleEnded);

    return () => {
      media.removeEventListener('timeupdate', handleTimeUpdate);
      media.removeEventListener('loadedmetadata', handleLoadedMetadata);
      media.removeEventListener('ended', handleEnded);
    };
  }, [sceneTiming, currentScene, onSceneChange]);

  const togglePlay = () => {
    const media = mediaRef.current;
    if (!media) return;

    if (isPlaying) {
      media.pause();
    } else {
      media.play();
    }
    setIsPlaying(!isPlaying);
  };

  const toggleMute = () => {
    const media = mediaRef.current;
    if (!media) return;

    media.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  const seek = (time: number) => {
    const media = mediaRef.current;
    if (!media) return;

    media.currentTime = Math.max(0, Math.min(time, duration));
  };

  const seekToScene = (sceneId: string) => {
    const scene = sceneTiming?.find(s => s.id === sceneId);
    if (scene) {
      seek(scene.startTime);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const percent = (e.clientX - rect.left) / rect.width;
    seek(percent * duration);
  };

  const toggleFullscreen = () => {
    const container = mediaRef.current?.parentElement?.parentElement;
    if (!container) return;

    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      container.requestFullscreen();
    }
  };

  const skipBack = () => seek(currentTime - 10);
  const skipForward = () => seek(currentTime + 10);

  return (
    <div className={`card bg-base-300 overflow-hidden ${className}`}>
      {title && (
        <div className="px-4 py-2 border-b border-base-content/10 text-sm font-medium">
          {title}
        </div>
      )}

      <div className="relative">
        {type === 'video' ? (
          <video
            ref={mediaRef as React.RefObject<HTMLVideoElement>}
            src={src}
            poster={poster}
            onClick={togglePlay}
            className="w-full aspect-video bg-black cursor-pointer"
          >
            {captions && <track kind="captions" src={captions} srcLang="en" label="English" default />}
          </video>
        ) : (
          <div className="flex items-center justify-center h-32 bg-gradient-to-br from-base-200 to-base-300">
            <div className="flex gap-1">
              {Array.from({ length: 12 }).map((_, i) => (
                <div
                  key={i}
                  className="w-1 bg-primary rounded-full animate-pulse"
                  style={{
                    height: `${20 + Math.sin(i * 0.5) * 15}px`,
                    animationDelay: `${i * 0.1}s`,
                  }}
                />
              ))}
            </div>
            <audio ref={mediaRef as React.RefObject<HTMLAudioElement>} src={src} />
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="flex items-center gap-2 p-2 bg-base-200">
        <div className="flex items-center gap-1">
          <button className="btn btn-ghost btn-xs btn-square" onClick={skipBack} title="Skip back 10s">
            <SkipBack size={14} />
          </button>
          <button className="btn btn-ghost btn-sm btn-square" onClick={togglePlay}>
            {isPlaying ? <Pause size={18} /> : <Play size={18} />}
          </button>
          <button className="btn btn-ghost btn-xs btn-square" onClick={skipForward} title="Skip forward 10s">
            <SkipForward size={14} />
          </button>
        </div>

        <span className="text-xs text-base-content/60 tabular-nums min-w-[40px]">
          {formatTime(currentTime)}
        </span>

        <div
          className="flex-1 h-1.5 bg-base-300 rounded-full cursor-pointer relative group"
          onClick={handleProgressClick}
        >
          <div
            className="h-full bg-primary rounded-full transition-all"
            style={{ width: `${(currentTime / duration) * 100}%` }}
          />
          {sceneTiming?.map(scene => (
            <div
              key={scene.id}
              className={`absolute top-1/2 -translate-y-1/2 w-2 h-2 rounded-full cursor-pointer transition-all ${
                currentScene === scene.id
                  ? 'bg-primary scale-125'
                  : 'bg-base-content/30 hover:bg-primary/60'
              }`}
              style={{ left: `${(scene.startTime / duration) * 100}%` }}
              title={scene.name || scene.id}
              onClick={(e) => {
                e.stopPropagation();
                seekToScene(scene.id);
              }}
            />
          ))}
        </div>

        <span className="text-xs text-base-content/60 tabular-nums min-w-[40px]">
          {formatTime(duration)}
        </span>

        <div className="flex items-center gap-1">
          <button className="btn btn-ghost btn-xs btn-square" onClick={toggleMute}>
            {isMuted ? <VolumeX size={14} /> : <Volume2 size={14} />}
          </button>
          {type === 'video' && (
            <button className="btn btn-ghost btn-xs btn-square" onClick={toggleFullscreen}>
              <Maximize size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Scene chips */}
      {sceneTiming && sceneTiming.length > 0 && (
        <div className="flex flex-wrap gap-1 p-2 border-t border-base-content/10">
          {sceneTiming.map(scene => (
            <button
              key={scene.id}
              className={`badge badge-sm cursor-pointer transition-colors ${
                currentScene === scene.id
                  ? 'badge-primary'
                  : 'badge-ghost hover:badge-primary/50'
              }`}
              onClick={() => seekToScene(scene.id)}
            >
              {scene.name || scene.id}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
