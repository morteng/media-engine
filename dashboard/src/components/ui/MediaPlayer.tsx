import { useRef, useState, useEffect } from 'react';
import { Play, Pause, Volume2, VolumeX, Maximize, SkipBack, SkipForward } from 'lucide-react';
import { Button } from './Button';
import './MediaPlayer.css';

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
    <div className={`media-player media-player--${type} ${className}`}>
      {title && <div className="media-player__title">{title}</div>}

      <div className="media-player__container">
        {type === 'video' ? (
          <video
            ref={mediaRef as React.RefObject<HTMLVideoElement>}
            src={src}
            poster={poster}
            onClick={togglePlay}
          >
            {captions && <track kind="captions" src={captions} srcLang="en" label="English" default />}
          </video>
        ) : (
          <div className="media-player__audio-visual">
            <div className="audio-wave" />
            <audio ref={mediaRef as React.RefObject<HTMLAudioElement>} src={src} />
          </div>
        )}
      </div>

      <div className="media-player__controls">
        <div className="media-player__buttons">
          <Button variant="ghost" size="sm" onClick={skipBack} title="Skip back 10s">
            <SkipBack size={16} />
          </Button>
          <Button variant="ghost" size="sm" onClick={togglePlay}>
            {isPlaying ? <Pause size={20} /> : <Play size={20} />}
          </Button>
          <Button variant="ghost" size="sm" onClick={skipForward} title="Skip forward 10s">
            <SkipForward size={16} />
          </Button>
        </div>

        <div className="media-player__time">{formatTime(currentTime)}</div>

        <div className="media-player__progress" onClick={handleProgressClick}>
          <div
            className="media-player__progress-bar"
            style={{ width: `${(currentTime / duration) * 100}%` }}
          />
          {sceneTiming?.map(scene => (
            <div
              key={scene.id}
              className={`media-player__scene-marker ${currentScene === scene.id ? 'active' : ''}`}
              style={{ left: `${(scene.startTime / duration) * 100}%` }}
              title={scene.name || scene.id}
              onClick={(e) => {
                e.stopPropagation();
                seekToScene(scene.id);
              }}
            />
          ))}
        </div>

        <div className="media-player__time">{formatTime(duration)}</div>

        <div className="media-player__buttons">
          <Button variant="ghost" size="sm" onClick={toggleMute}>
            {isMuted ? <VolumeX size={16} /> : <Volume2 size={16} />}
          </Button>
          {type === 'video' && (
            <Button variant="ghost" size="sm" onClick={toggleFullscreen}>
              <Maximize size={16} />
            </Button>
          )}
        </div>
      </div>

      {sceneTiming && sceneTiming.length > 0 && (
        <div className="media-player__scenes">
          {sceneTiming.map(scene => (
            <button
              key={scene.id}
              className={`scene-chip ${currentScene === scene.id ? 'active' : ''}`}
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
