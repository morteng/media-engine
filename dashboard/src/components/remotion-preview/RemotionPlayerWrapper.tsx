/**
 * RemotionPlayerWrapper - Wrapper for @remotion/player
 *
 * Embeds the Remotion Player with the DemoComposition component.
 * Handles the integration between our props and Remotion's API.
 */

import { useCallback, useMemo, useRef, useEffect } from 'react';
import { Player, type PlayerRef } from '@remotion/player';
import { useCurrentFrame } from 'remotion';
import {
  interpolateCameraPath,
  calculateCameraStyle,
} from '@/lib/camera';
import {
  generateVignetteStyle,
  calculateEffectsTransform,
  defaultEffectsConfig,
} from '@/lib/effects';
import type { RemotionDemoProps } from './types';

interface RemotionPlayerWrapperProps extends Omit<RemotionDemoProps, 'frame'> {
  /** Called when frame changes during playback */
  onFrameChange?: (frame: number) => void;
  /** Called when play state changes */
  onPlayChange?: (isPlaying: boolean) => void;
  /** External control: current frame to seek to */
  seekToFrame?: number;
  /** External control: play state */
  isPlaying?: boolean;
  /** Whether to show built-in controls */
  showControls?: boolean;
  /** Whether to loop playback */
  loop?: boolean;
  /** Playback speed multiplier */
  playbackRate?: number;
  /** CSS class for the container */
  className?: string;
}

/**
 * The actual composition that renders inside the Remotion Player.
 * Uses useCurrentFrame() to get the current frame from Remotion's context.
 */
function DemoCompositionInternal({
  screenshotUrl,
  captureWidth,
  captureHeight,
  keyframes,
  background,
  shadow,
  effects,
  totalFrames,
  fps,
}: RemotionDemoProps) {
  // Get current frame from Remotion context
  const frame = useCurrentFrame();

  // Calculate current camera state
  const cameraState = useMemo(
    () => interpolateCameraPath(keyframes, frame, true),
    [keyframes, frame]
  );

  // Calculate previous camera state for effects that need velocity
  const prevCameraState = useMemo(
    () => (frame > 0 ? interpolateCameraPath(keyframes, frame - 1, true) : cameraState),
    [keyframes, frame, cameraState]
  );

  // Calculate camera transform
  const cameraStyle = useMemo(
    () => calculateCameraStyle(cameraState, captureWidth, captureHeight),
    [cameraState, captureWidth, captureHeight]
  );

  // Calculate effects
  const effectsConfig = effects || defaultEffectsConfig;
  const effectsTransform = useMemo(
    () =>
      calculateEffectsTransform(
        effectsConfig,
        frame,
        fps,
        cameraState,
        prevCameraState
      ),
    [effectsConfig, frame, fps, cameraState, prevCameraState]
  );

  const vignetteStyle = useMemo(
    () => generateVignetteStyle(effectsConfig.vignette, cameraState.zoom),
    [effectsConfig.vignette, cameraState.zoom]
  );

  // Container styles
  const containerStyle: React.CSSProperties = {
    width: captureWidth,
    height: captureHeight,
    background,
    overflow: 'hidden',
    position: 'relative',
  };

  // Effects wrapper style
  const effectsWrapperStyle: React.CSSProperties = {
    width: '100%',
    height: '100%',
    position: 'relative',
    perspective: effectsTransform.perspective,
  };

  // Image wrapper style with camera transform and effects
  const imageWrapperStyle: React.CSSProperties = {
    ...cameraStyle,
    transform: `${cameraStyle.transform} ${effectsTransform.transform !== 'none' ? effectsTransform.transform : ''}`,
    filter: effectsTransform.filter,
  };

  // Shadow style for the screenshot
  const shadowStyle: React.CSSProperties = shadow
    ? {
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
        borderRadius: '8px',
      }
    : {};

  return (
    <div style={containerStyle}>
      <div style={effectsWrapperStyle}>
        {/* Screenshot with camera animation */}
        <div style={imageWrapperStyle}>
          {screenshotUrl ? (
            <img
              src={screenshotUrl}
              alt="Demo screenshot"
              style={{
                width: captureWidth,
                height: captureHeight,
                objectFit: 'cover',
                display: 'block',
                ...shadowStyle,
              }}
              draggable={false}
            />
          ) : (
            <ScreenshotPlaceholder width={captureWidth} height={captureHeight} />
          )}
        </div>

        {/* Vignette overlay */}
        {effectsConfig.vignette.enabled && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              pointerEvents: 'none',
              ...vignetteStyle,
            }}
          />
        )}
      </div>

      {/* Debug overlay */}
      {import.meta.env.DEV && (
        <div
          style={{
            position: 'absolute',
            bottom: 8,
            right: 8,
            background: 'rgba(0, 0, 0, 0.7)',
            color: '#fff',
            padding: '4px 8px',
            borderRadius: 4,
            fontSize: 11,
            fontFamily: 'monospace',
            pointerEvents: 'none',
          }}
        >
          <div>
            Frame: {frame}/{totalFrames}
          </div>
          <div>
            Zoom: {cameraState.zoom.toFixed(2)}x @ ({Math.round(cameraState.centerX)},{' '}
            {Math.round(cameraState.centerY)})
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Placeholder when no screenshot is available
 */
function ScreenshotPlaceholder({ width, height }: { width: number; height: number }) {
  return (
    <div
      style={{
        width,
        height,
        background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#64748b',
        fontSize: 14,
        fontFamily: 'system-ui, sans-serif',
      }}
    >
      <div style={{ textAlign: 'center' }}>
        <svg
          width={48}
          height={48}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={1.5}
          style={{ margin: '0 auto 12px' }}
        >
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
          <circle cx="8.5" cy="8.5" r="1.5" />
          <path d="m21 15-5-5L5 21" />
        </svg>
        <div>Screenshot not captured</div>
        <div style={{ fontSize: 12, marginTop: 4, opacity: 0.7 }}>
          Run demo capture to generate screenshots
        </div>
      </div>
    </div>
  );
}

export function RemotionPlayerWrapper({
  screenshotUrl,
  captureWidth,
  captureHeight,
  keyframes,
  background,
  shadow,
  effects,
  totalFrames,
  fps,
  onFrameChange,
  onPlayChange,
  seekToFrame,
  isPlaying,
  showControls = true,
  loop = true,
  playbackRate = 1,
  className,
}: RemotionPlayerWrapperProps) {
  const playerRef = useRef<PlayerRef>(null);
  const lastReportedFrame = useRef<number>(-1);

  // Input props for the composition
  const inputProps = useMemo(
    () => ({
      screenshotUrl,
      captureWidth,
      captureHeight,
      keyframes,
      background,
      shadow,
      effects,
      totalFrames,
      fps,
    }),
    [screenshotUrl, captureWidth, captureHeight, keyframes, background, shadow, effects, totalFrames, fps]
  );

  // Handle frame updates
  const handleFrameUpdate = useCallback(
    (e: { detail: { frame: number } }) => {
      const frame = e.detail.frame;
      if (frame !== lastReportedFrame.current) {
        lastReportedFrame.current = frame;
        onFrameChange?.(frame);
      }
    },
    [onFrameChange]
  );

  // Handle play state changes
  const handlePlay = useCallback(() => {
    onPlayChange?.(true);
  }, [onPlayChange]);

  const handlePause = useCallback(() => {
    onPlayChange?.(false);
  }, [onPlayChange]);

  // Subscribe to player events
  useEffect(() => {
    const player = playerRef.current;
    if (!player) return;

    player.addEventListener('frameupdate', handleFrameUpdate);
    player.addEventListener('play', handlePlay);
    player.addEventListener('pause', handlePause);

    return () => {
      player.removeEventListener('frameupdate', handleFrameUpdate);
      player.removeEventListener('play', handlePlay);
      player.removeEventListener('pause', handlePause);
    };
  }, [handleFrameUpdate, handlePlay, handlePause]);

  // Seek to frame when seekToFrame changes
  useEffect(() => {
    if (seekToFrame !== undefined && playerRef.current) {
      playerRef.current.seekTo(seekToFrame);
    }
  }, [seekToFrame]);

  // Control play state externally
  useEffect(() => {
    if (isPlaying !== undefined && playerRef.current) {
      if (isPlaying) {
        playerRef.current.play();
      } else {
        playerRef.current.pause();
      }
    }
  }, [isPlaying]);

  // Ensure valid duration
  const durationInFrames = Math.max(1, totalFrames);

  return (
    <div className={className} style={{ width: '100%', height: '100%' }}>
      <Player
        ref={playerRef}
        component={DemoCompositionInternal}
        inputProps={inputProps}
        durationInFrames={durationInFrames}
        compositionWidth={captureWidth}
        compositionHeight={captureHeight}
        fps={fps}
        controls={showControls}
        loop={loop}
        playbackRate={playbackRate}
        style={{
          width: '100%',
          height: '100%',
        }}
        clickToPlay={!showControls}
        doubleClickToFullscreen
        spaceKeyToPlayOrPause
        moveToBeginningWhenEnded={!loop}
      />
    </div>
  );
}

export default RemotionPlayerWrapper;
