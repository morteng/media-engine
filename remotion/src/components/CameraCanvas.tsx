/**
 * CameraCanvas Component
 *
 * Core component for animated camera movements over high-res screenshots.
 * Uses CSS transforms to simulate pan/zoom on a floating page image.
 *
 * Features:
 * - High-res screenshot rendering with drop shadow
 * - Smooth camera interpolation via keyframes
 * - Catmull-Rom spline paths for professional motion
 * - Configurable background and shadow
 *
 * Visual:
 * ┌─────────────────────────────────────────────────────┐
 * │                  Background Color                   │
 * │    ┌────────────────────────────────────────┐       │
 * │    │                                        │       │
 * │    │         High-res Screenshot            │       │
 * │    │         (with camera transforms)       │       │
 * │    │                                        │       │
 * │    └────────────────────────────────────────┘       │
 * │                    ▓▓▓ shadow ▓▓▓                   │
 * └─────────────────────────────────────────────────────┘
 */

import React, { useMemo, useRef } from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  Img,
  staticFile,
  interpolate,
  Easing,
} from 'remotion';
import {
  interpolateCameraPath,
  calculateCameraStyle,
  type CameraKeyframe,
} from '../lib/camera';
import {
  CameraEffectsConfig,
  defaultEffectsConfig,
  calculateShakeOffset,
  calculatePerspectiveTilt,
} from '../lib/effects';
import { VignetteOverlay } from './CameraEffects';

// ============================================================================
// Types
// ============================================================================

export interface CameraCanvasProps {
  /** Path to high-res screenshot (relative to public folder) */
  imagePath: string;
  /** Width of the captured image in pixels */
  captureWidth: number;
  /** Height of the captured image in pixels */
  captureHeight: number;
  /** Camera keyframes for interpolation */
  keyframes: CameraKeyframe[];
  /** Background color for the canvas */
  background?: string;
  /** Whether to show drop shadow on the floating page */
  shadow?: boolean;
  /** Border radius for the floating page image */
  borderRadius?: number;
  /** Optional children (overlays, highlights, etc.) */
  children?: React.ReactNode;
  /** Whether to use Catmull-Rom splines (default: true) */
  useSpline?: boolean;
  /** Fade in duration in frames (default: 15) */
  fadeInFrames?: number;
  /** Fade out duration in frames (default: 15) */
  fadeOutFrames?: number;
  /** Visual effects configuration */
  effects?: CameraEffectsConfig;
}

// ============================================================================
// Component
// ============================================================================

export const CameraCanvas: React.FC<CameraCanvasProps> = ({
  imagePath,
  captureWidth,
  captureHeight,
  keyframes,
  background = '#1a1a2e',
  shadow = true,
  borderRadius = 12,
  children,
  useSpline = true,
  fadeInFrames = 15,
  fadeOutFrames = 15,
  effects,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height, durationInFrames } = useVideoConfig();
  const previousCameraStateRef = useRef<{ centerX: number; centerY: number; zoom: number } | null>(null);

  // Interpolate camera state for current frame
  const cameraState = useMemo(
    () => interpolateCameraPath(keyframes, frame, useSpline),
    [keyframes, frame, useSpline]
  );

  // Get previous camera state for dynamic effects
  const previousCameraState = previousCameraStateRef.current;

  // Update ref for next frame
  useMemo(() => {
    previousCameraStateRef.current = { ...cameraState };
  }, [cameraState]);

  // Merge effects with defaults
  const effectsConfig = useMemo(
    () => effects || defaultEffectsConfig,
    [effects]
  );

  // Calculate camera shake offset
  const shakeOffset = useMemo(() => {
    if (!effectsConfig.cameraShake?.enabled) return { x: 0, y: 0, rotation: 0 };
    return calculateShakeOffset(frame, fps, effectsConfig.cameraShake);
  }, [frame, fps, effectsConfig.cameraShake]);

  // Calculate perspective tilt
  const tilt = useMemo(() => {
    if (!effectsConfig.perspectiveTilt?.enabled) {
      return { rotateX: 0, rotateY: 0, perspective: 1200 };
    }
    return calculatePerspectiveTilt(effectsConfig.perspectiveTilt, cameraState, previousCameraState || undefined);
  }, [effectsConfig.perspectiveTilt, cameraState, previousCameraState]);

  // Calculate CSS transform
  const cameraStyle = useMemo(
    () => calculateCameraStyle(cameraState, width, height),
    [cameraState, width, height]
  );

  // Fade in/out opacity
  const opacity = interpolate(
    frame,
    [0, fadeInFrames, durationInFrames - fadeOutFrames, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Shadow intensity based on zoom (deeper shadow when zoomed in)
  const shadowIntensity = interpolate(cameraState.zoom, [1, 3], [0.3, 0.6], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const shadowBlur = interpolate(cameraState.zoom, [1, 3], [30, 80], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const shadowOffset = interpolate(cameraState.zoom, [1, 3], [15, 40], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Build box shadow string
  const boxShadow = shadow
    ? `0 ${shadowOffset}px ${shadowBlur}px rgba(0, 0, 0, ${shadowIntensity}), 0 ${shadowOffset / 2}px ${shadowBlur / 2}px rgba(0, 0, 0, ${shadowIntensity * 0.5})`
    : 'none';

  // Resolve image path
  const resolvedImagePath = imagePath.startsWith('/')
    ? imagePath
    : staticFile(imagePath);

  // Build effects transform
  const effectsTransform = useMemo(() => {
    const transforms: string[] = [];

    // Camera shake
    if (shakeOffset.x !== 0 || shakeOffset.y !== 0) {
      transforms.push(`translate(${shakeOffset.x}px, ${shakeOffset.y}px)`);
    }
    if (shakeOffset.rotation !== 0) {
      transforms.push(`rotate(${shakeOffset.rotation}deg)`);
    }

    return transforms.length > 0 ? transforms.join(' ') : undefined;
  }, [shakeOffset]);

  // Wrapper style for perspective and shake
  const wrapperStyle: React.CSSProperties = useMemo(() => {
    const style: React.CSSProperties = {
      background,
      opacity,
    };

    if (effectsConfig.perspectiveTilt?.enabled) {
      style.perspective = `${tilt.perspective}px`;
      style.transformStyle = 'preserve-3d';
    }

    return style;
  }, [background, opacity, effectsConfig.perspectiveTilt?.enabled, tilt.perspective]);

  // Content style with tilt and shake
  const contentStyle: React.CSSProperties = useMemo(() => {
    const transforms: string[] = [];

    if (effectsConfig.perspectiveTilt?.enabled) {
      transforms.push(`rotateX(${tilt.rotateX}deg)`);
      transforms.push(`rotateY(${tilt.rotateY}deg)`);
    }

    if (effectsTransform) {
      transforms.push(effectsTransform);
    }

    return transforms.length > 0
      ? { transform: transforms.join(' '), width: '100%', height: '100%' }
      : { width: '100%', height: '100%' };
  }, [effectsConfig.perspectiveTilt?.enabled, tilt, effectsTransform]);

  return (
    <AbsoluteFill style={wrapperStyle}>
      <div style={contentStyle}>
        {/* Floating page container with camera transform */}
        <div
          style={{
            ...cameraStyle,
            position: 'absolute',
            top: 0,
            left: 0,
          }}
        >
          <Img
            src={resolvedImagePath}
            style={{
              width: captureWidth,
              height: captureHeight,
              borderRadius,
              boxShadow,
              // Prevent image from being blurry during transforms
              imageRendering: cameraState.zoom < 1 ? 'auto' : 'auto',
            }}
          />
        </div>

        {/* Children layer (overlays, highlights, etc.) */}
        {children && (
          <AbsoluteFill style={{ pointerEvents: 'none' }}>
            {children}
          </AbsoluteFill>
        )}
      </div>

      {/* Vignette overlay */}
      {effectsConfig.vignette?.enabled && (
        <VignetteOverlay
          config={effectsConfig.vignette}
          zoom={cameraState.zoom}
        />
      )}
    </AbsoluteFill>
  );
};

// ============================================================================
// Focus Highlight Component
// ============================================================================

export interface FocusHighlightProps {
  /** Element bounds to highlight */
  bounds: {
    x: number;
    y: number;
    width: number;
    height: number;
  } | null;
  /** Highlight style */
  style?: 'glow' | 'outline' | 'dim-others';
  /** Highlight color */
  color?: string;
  /** Camera state for transform alignment */
  cameraState?: { centerX: number; centerY: number; zoom: number };
  /** Viewport dimensions */
  viewportWidth?: number;
  viewportHeight?: number;
}

export const FocusHighlight: React.FC<FocusHighlightProps> = ({
  bounds,
  style = 'glow',
  color = '#00d4ff',
  cameraState,
  viewportWidth = 1920,
  viewportHeight = 1080,
}) => {
  const frame = useCurrentFrame();

  if (!bounds || !cameraState) return null;

  // Calculate position in viewport space
  const { centerX, centerY, zoom } = cameraState;
  const translateX = viewportWidth / 2 - centerX * zoom;
  const translateY = viewportHeight / 2 - centerY * zoom;

  // Transform bounds to viewport space
  const x = bounds.x * zoom + translateX;
  const y = bounds.y * zoom + translateY;
  const width = bounds.width * zoom;
  const height = bounds.height * zoom;

  // Pulse animation
  const pulse = Math.sin(frame * 0.15) * 0.3 + 0.7;

  if (style === 'glow') {
    return (
      <div
        style={{
          position: 'absolute',
          left: x,
          top: y,
          width,
          height,
          borderRadius: 8 * zoom,
          boxShadow: `0 0 ${20 * pulse}px ${color}66, inset 0 0 ${10 * pulse}px ${color}33`,
          border: `2px solid ${color}`,
          opacity: pulse,
          pointerEvents: 'none',
        }}
      />
    );
  }

  if (style === 'outline') {
    return (
      <div
        style={{
          position: 'absolute',
          left: x,
          top: y,
          width,
          height,
          borderRadius: 4 * zoom,
          border: `3px solid ${color}`,
          opacity: 0.8,
          pointerEvents: 'none',
        }}
      />
    );
  }

  // dim-others: Overlay with cutout
  return (
    <AbsoluteFill style={{ pointerEvents: 'none' }}>
      <svg width="100%" height="100%">
        <defs>
          <mask id="highlight-mask">
            <rect width="100%" height="100%" fill="white" />
            <rect
              x={x}
              y={y}
              width={width}
              height={height}
              rx={8 * zoom}
              fill="black"
            />
          </mask>
        </defs>
        <rect
          width="100%"
          height="100%"
          fill="rgba(0, 0, 0, 0.5)"
          mask="url(#highlight-mask)"
        />
      </svg>
    </AbsoluteFill>
  );
};

// ============================================================================
// Caption Overlay Component
// ============================================================================

export interface CaptionOverlayProps {
  /** Caption text */
  text: string;
  /** Position on screen */
  position?: 'bottom' | 'top' | 'center';
  /** Text size */
  fontSize?: number;
  /** Background style */
  backgroundStyle?: 'solid' | 'gradient' | 'blur';
}

export const CaptionOverlay: React.FC<CaptionOverlayProps> = ({
  text,
  position = 'bottom',
  fontSize = 24,
  backgroundStyle = 'gradient',
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Fade animation
  const opacity = interpolate(
    frame,
    [0, fps * 0.3, durationInFrames - fps * 0.3, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Position styles
  const positionStyles: React.CSSProperties = {
    bottom: { bottom: 60, left: 0, right: 0 },
    top: { top: 60, left: 0, right: 0 },
    center: { top: '50%', left: 0, right: 0, transform: 'translateY(-50%)' },
  }[position];

  // Background styles
  const bgStyles: React.CSSProperties = {
    solid: { background: 'rgba(0, 0, 0, 0.8)' },
    gradient: {
      background: 'linear-gradient(to top, rgba(0, 0, 0, 0.9) 0%, rgba(0, 0, 0, 0) 100%)',
    },
    blur: {
      background: 'rgba(0, 0, 0, 0.6)',
      backdropFilter: 'blur(10px)',
    },
  }[backgroundStyle];

  return (
    <div
      style={{
        position: 'absolute',
        ...positionStyles,
        padding: '40px 60px',
        ...bgStyles,
        opacity,
      }}
    >
      <p
        style={{
          fontFamily: 'Inter, system-ui, sans-serif',
          fontSize,
          fontWeight: 500,
          color: '#ffffff',
          textAlign: 'center',
          margin: 0,
          lineHeight: 1.4,
          textShadow: '0 2px 10px rgba(0, 0, 0, 0.5)',
        }}
      >
        {text}
      </p>
    </div>
  );
};

export default CameraCanvas;
