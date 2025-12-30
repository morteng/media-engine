/**
 * CameraEffects Component
 *
 * Visual effects overlays for animated camera system:
 * - Vignette overlay
 * - Depth of field simulation
 * - Motion blur indicator
 *
 * Works in conjunction with CameraCanvas and AnimatedDemoScene.
 */

import React, { useMemo } from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {
  CameraEffectsConfig,
  CameraState,
  defaultEffectsConfig,
  generateVignetteStyle,
  calculateShakeOffset,
  calculatePerspectiveTilt,
  calculateMotionBlur,
} from '../lib/effects';

// ============================================================================
// Vignette Overlay
// ============================================================================

export interface VignetteOverlayProps {
  config: CameraEffectsConfig['vignette'];
  zoom?: number;
}

export const VignetteOverlay: React.FC<VignetteOverlayProps> = ({
  config,
  zoom = 1.0,
}) => {
  if (!config.enabled) return null;

  const style = useMemo(() => generateVignetteStyle(config, zoom), [config, zoom]);

  return (
    <AbsoluteFill
      style={{
        ...style,
        pointerEvents: 'none',
        zIndex: 100,
      }}
    />
  );
};

// ============================================================================
// Depth of Field Overlay
// ============================================================================

export interface DepthOfFieldOverlayProps {
  config: CameraEffectsConfig['depthOfField'];
  focusBounds?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  cameraState?: CameraState;
}

export const DepthOfFieldOverlay: React.FC<DepthOfFieldOverlayProps> = ({
  config,
  focusBounds,
  cameraState,
}) => {
  if (!config.enabled) return null;

  // Create a mask that blurs everything except the focus area
  const blurFilter = `blur(${config.blurAmount}px)`;

  if (!focusBounds) {
    // No specific focus - apply light blur to edges
    return (
      <AbsoluteFill
        style={{
          pointerEvents: 'none',
          zIndex: 50,
          background: `radial-gradient(
            ellipse 60% 60% at center,
            transparent 30%,
            rgba(0, 0, 0, ${config.falloff * 0.1}) 100%
          )`,
          backdropFilter: `blur(${config.blurAmount * 0.3}px)`,
          maskImage: 'radial-gradient(ellipse 80% 80% at center, transparent 40%, black 100%)',
          WebkitMaskImage: 'radial-gradient(ellipse 80% 80% at center, transparent 40%, black 100%)',
        }}
      />
    );
  }

  // Create SVG mask for focus area
  return (
    <AbsoluteFill style={{ pointerEvents: 'none', zIndex: 50 }}>
      <svg width="100%" height="100%" style={{ position: 'absolute' }}>
        <defs>
          <filter id="dof-blur" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation={config.blurAmount} />
          </filter>
          <mask id="dof-mask">
            <rect width="100%" height="100%" fill="white" />
            <rect
              x={focusBounds.x}
              y={focusBounds.y}
              width={focusBounds.width}
              height={focusBounds.height}
              rx="8"
              fill="black"
            />
          </mask>
        </defs>
        <rect
          width="100%"
          height="100%"
          fill={`rgba(0, 0, 0, ${config.falloff * 0.3})`}
          mask="url(#dof-mask)"
          filter="url(#dof-blur)"
        />
      </svg>
    </AbsoluteFill>
  );
};

// ============================================================================
// Combined Effects Wrapper
// ============================================================================

export interface CameraEffectsWrapperProps {
  config?: CameraEffectsConfig;
  cameraState?: CameraState;
  previousCameraState?: CameraState;
  focusBounds?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  children: React.ReactNode;
}

export const CameraEffectsWrapper: React.FC<CameraEffectsWrapperProps> = ({
  config = defaultEffectsConfig,
  cameraState,
  previousCameraState,
  focusBounds,
  children,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Calculate shake offset
  const shakeOffset = useMemo(() => {
    if (!config.cameraShake.enabled) return { x: 0, y: 0, rotation: 0 };
    return calculateShakeOffset(frame, fps, config.cameraShake);
  }, [frame, fps, config.cameraShake]);

  // Calculate perspective tilt
  const tilt = useMemo(() => {
    if (!config.perspectiveTilt.enabled || !cameraState) {
      return { rotateX: 0, rotateY: 0, perspective: 1200 };
    }
    return calculatePerspectiveTilt(config.perspectiveTilt, cameraState, previousCameraState);
  }, [config.perspectiveTilt, cameraState, previousCameraState]);

  // Calculate motion blur
  const motionBlur = useMemo(() => {
    if (!config.motionBlur.enabled || !cameraState) {
      return { blur: 0, direction: 0, enabled: false };
    }
    return calculateMotionBlur(config.motionBlur, cameraState, previousCameraState, fps);
  }, [config.motionBlur, cameraState, previousCameraState, fps]);

  // Build transform style
  const wrapperStyle: React.CSSProperties = useMemo(() => {
    const transforms: string[] = [];
    const filters: string[] = [];

    // Camera shake
    if (shakeOffset.x !== 0 || shakeOffset.y !== 0) {
      transforms.push(`translate(${shakeOffset.x}px, ${shakeOffset.y}px)`);
    }
    if (shakeOffset.rotation !== 0) {
      transforms.push(`rotate(${shakeOffset.rotation}deg)`);
    }

    // Perspective tilt
    if (config.perspectiveTilt.enabled) {
      transforms.push(`rotateX(${tilt.rotateX}deg)`);
      transforms.push(`rotateY(${tilt.rotateY}deg)`);
    }

    // Motion blur
    if (motionBlur.enabled) {
      filters.push(`blur(${motionBlur.blur}px)`);
    }

    return {
      transform: transforms.length > 0 ? transforms.join(' ') : undefined,
      filter: filters.length > 0 ? filters.join(' ') : undefined,
      perspective: config.perspectiveTilt.enabled ? `${tilt.perspective}px` : undefined,
      transformStyle: config.perspectiveTilt.enabled ? 'preserve-3d' as const : undefined,
    };
  }, [shakeOffset, tilt, motionBlur, config.perspectiveTilt.enabled]);

  return (
    <AbsoluteFill style={wrapperStyle}>
      {children}

      {/* Vignette overlay */}
      <VignetteOverlay
        config={config.vignette}
        zoom={cameraState?.zoom}
      />

      {/* Depth of field overlay */}
      <DepthOfFieldOverlay
        config={config.depthOfField}
        focusBounds={focusBounds}
        cameraState={cameraState}
      />
    </AbsoluteFill>
  );
};

// ============================================================================
// Exports
// ============================================================================

export default CameraEffectsWrapper;
