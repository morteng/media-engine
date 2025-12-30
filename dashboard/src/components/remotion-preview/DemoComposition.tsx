/**
 * DemoComposition - Core component for rendering camera animations over screenshots
 *
 * This is a pure React component (no Remotion hooks required) that renders
 * the screenshot with camera transforms applied. The @remotion/player
 * passes the current frame as a prop.
 */

import { useMemo } from 'react';
import {
  interpolateCameraPath,
  calculateCameraStyle,
} from '@/lib/camera';
import {
  generateVignetteStyle,
  calculateEffectsTransform,
  defaultEffectsConfig,
} from '@/lib/effects';
import type { DemoCompositionProps } from './types';

export function DemoComposition({
  screenshotUrl,
  captureWidth,
  captureHeight,
  keyframes,
  background,
  shadow,
  effects,
  totalFrames,
  fps,
  frame,
}: DemoCompositionProps) {
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
            <ScreenshotPlaceholder
              width={captureWidth}
              height={captureHeight}
            />
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

      {/* Debug overlay (frame info) - shown in dev mode */}
      {import.meta.env.DEV && (
        <DebugOverlay
          frame={frame}
          totalFrames={totalFrames}
          fps={fps}
          cameraState={cameraState}
        />
      )}
    </div>
  );
}

/**
 * Placeholder when no screenshot is available
 */
function ScreenshotPlaceholder({
  width,
  height,
}: {
  width: number;
  height: number;
}) {
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

/**
 * Debug overlay showing frame and camera info
 */
function DebugOverlay({
  frame,
  totalFrames,
  fps,
  cameraState,
}: {
  frame: number;
  totalFrames: number;
  fps: number;
  cameraState: { centerX: number; centerY: number; zoom: number };
}) {
  const timeSeconds = (frame / fps).toFixed(2);

  return (
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
        Frame: {frame}/{totalFrames} ({timeSeconds}s)
      </div>
      <div>
        Zoom: {cameraState.zoom.toFixed(2)}x @ ({Math.round(cameraState.centerX)},{' '}
        {Math.round(cameraState.centerY)})
      </div>
    </div>
  );
}

export default DemoComposition;
