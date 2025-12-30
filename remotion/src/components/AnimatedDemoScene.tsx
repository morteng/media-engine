/**
 * AnimatedDemoScene Component
 *
 * Scene component for video compositions that displays demo screenshots
 * with animated camera movements. Wraps CameraCanvas with scene-specific
 * logic for voiceover sync, captions, and visual effects.
 *
 * Features:
 * - High-res demo screenshot with camera animation
 * - Voiceover text overlay with auto-caption
 * - Focus highlight on current target element
 * - Smooth transitions in/out
 *
 * Props (from video builder):
 * - demo: Demo name (e.g., "dashboard")
 * - state: State ID (e.g., "main_view")
 * - camera_data: Camera configuration from Python builder
 * - text: Voiceover text for captions
 */

import React, { useMemo } from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  staticFile,
} from 'remotion';
import {
  CameraCanvas,
  FocusHighlight,
  CaptionOverlay,
} from './CameraCanvas';
import { interpolateCameraPath, type CameraKeyframe } from '../lib/camera';
import { colors } from '../lib/theme';

// ============================================================================
// Types
// ============================================================================

export interface CameraData {
  mode: string;
  capture_scale: number;
  background: string;
  shadow: boolean;
  viewport_width: number;
  viewport_height: number;
  fps: number;
  total_frames: number;
  keyframes: CameraKeyframe[];
  element_bounds: Record<string, {
    x: number;
    y: number;
    width: number;
    height: number;
    centerX: number;
    centerY: number;
  }>;
  image_path?: string;
}

export interface AnimatedDemoSceneProps {
  /** Demo name (matches folder in public/demos/) */
  demo: string;
  /** State ID within the demo */
  state: string;
  /** Camera configuration from Python builder */
  cameraData: CameraData;
  /** Voiceover text for captions */
  text?: string;
  /** Whether to show captions */
  showCaptions?: boolean;
  /** Caption position */
  captionPosition?: 'bottom' | 'top' | 'center';
  /** Whether to show focus highlight on current target */
  showFocusHighlight?: boolean;
  /** Focus highlight style */
  focusHighlightStyle?: 'glow' | 'outline' | 'dim-others';
  /** Highlight color */
  highlightColor?: string;
  /** Frame offset within the composition */
  sceneFrame?: number;
  /** Override fade in frames */
  fadeInFrames?: number;
  /** Override fade out frames */
  fadeOutFrames?: number;
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Find which keyframe target is active at the current frame
 */
function getCurrentTarget(
  keyframes: CameraKeyframe[],
  frame: number
): string | null {
  if (!keyframes || keyframes.length === 0) return null;

  // Find the keyframe we're currently at or transitioning from
  let currentKeyframe = keyframes[0];

  for (const kf of keyframes) {
    if (kf.frame <= frame) {
      currentKeyframe = kf;
    } else {
      break;
    }
  }

  // The target is stored in the original focus_sequence, but we only have
  // resolved keyframes with coordinates. Return null for now - focus
  // highlighting requires additional metadata.
  return null;
}

/**
 * Get the bounds for the current focus target
 */
function getCurrentTargetBounds(
  keyframes: CameraKeyframe[],
  elementBounds: Record<string, { x: number; y: number; width: number; height: number }>,
  frame: number
): { x: number; y: number; width: number; height: number } | null {
  // For now, we don't track which selector maps to which keyframe
  // This would require extending the keyframe data to include the original selector
  return null;
}

// ============================================================================
// Component
// ============================================================================

export const AnimatedDemoScene: React.FC<AnimatedDemoSceneProps> = ({
  demo,
  state,
  cameraData,
  text,
  showCaptions = true,
  captionPosition = 'bottom',
  showFocusHighlight = false,
  focusHighlightStyle = 'glow',
  highlightColor = colors.accent,
  sceneFrame,
  fadeInFrames = 15,
  fadeOutFrames = 15,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height, durationInFrames } = useVideoConfig();

  // Use scene frame if provided, otherwise use composition frame
  const currentFrame = sceneFrame ?? frame;

  // Construct image path
  const imagePath = cameraData.image_path
    || `demos/${demo}/states/${state}_${cameraData.capture_scale}x.png`;

  // Calculate capture dimensions
  const captureWidth = cameraData.viewport_width * cameraData.capture_scale;
  const captureHeight = cameraData.viewport_height * cameraData.capture_scale;

  // Get current camera state for highlight positioning
  const cameraState = useMemo(
    () => interpolateCameraPath(cameraData.keyframes, currentFrame, true),
    [cameraData.keyframes, currentFrame]
  );

  // Get current focus target bounds (if highlight is enabled)
  const focusBounds = useMemo(() => {
    if (!showFocusHighlight) return null;
    return getCurrentTargetBounds(
      cameraData.keyframes,
      cameraData.element_bounds,
      currentFrame
    );
  }, [showFocusHighlight, cameraData.keyframes, cameraData.element_bounds, currentFrame]);

  return (
    <AbsoluteFill>
      <CameraCanvas
        imagePath={imagePath}
        captureWidth={captureWidth}
        captureHeight={captureHeight}
        keyframes={cameraData.keyframes}
        background={cameraData.background}
        shadow={cameraData.shadow}
        fadeInFrames={fadeInFrames}
        fadeOutFrames={fadeOutFrames}
      >
        {/* Focus highlight overlay */}
        {showFocusHighlight && focusBounds && (
          <FocusHighlight
            bounds={focusBounds}
            style={focusHighlightStyle}
            color={highlightColor}
            cameraState={cameraState}
            viewportWidth={width}
            viewportHeight={height}
          />
        )}
      </CameraCanvas>

      {/* Voiceover captions */}
      {showCaptions && text && (
        <CaptionOverlay
          text={text}
          position={captionPosition}
          fontSize={24}
          backgroundStyle="gradient"
        />
      )}
    </AbsoluteFill>
  );
};

// ============================================================================
// Static Demo Scene (no camera animation)
// ============================================================================

export interface StaticDemoSceneProps {
  /** Path to demo image */
  imagePath: string;
  /** Voiceover text */
  text?: string;
  /** Whether to show captions */
  showCaptions?: boolean;
  /** Caption position */
  captionPosition?: 'bottom' | 'top' | 'center';
  /** Background color */
  background?: string;
  /** Ken Burns effect config */
  kenBurns?: {
    startScale: number;
    endScale: number;
    startX: number;
    startY: number;
    endX: number;
    endY: number;
  };
}

export const StaticDemoScene: React.FC<StaticDemoSceneProps> = ({
  imagePath,
  text,
  showCaptions = true,
  captionPosition = 'bottom',
  background = colors.dark.bgPrimary,
  kenBurns,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Ken Burns animation
  const progress = frame / durationInFrames;
  const scale = kenBurns
    ? interpolate(progress, [0, 1], [kenBurns.startScale, kenBurns.endScale])
    : 1;
  const translateX = kenBurns
    ? interpolate(progress, [0, 1], [kenBurns.startX, kenBurns.endX])
    : 0;
  const translateY = kenBurns
    ? interpolate(progress, [0, 1], [kenBurns.startY, kenBurns.endY])
    : 0;

  // Fade in/out
  const opacity = interpolate(
    frame,
    [0, fps * 0.5, durationInFrames - fps * 0.5, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  return (
    <AbsoluteFill style={{ background, opacity }}>
      <div
        style={{
          width: '100%',
          height: '100%',
          overflow: 'hidden',
        }}
      >
        <img
          src={staticFile(imagePath)}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${scale}) translate(${translateX}px, ${translateY}px)`,
            transformOrigin: 'center center',
          }}
        />
      </div>

      {showCaptions && text && (
        <CaptionOverlay
          text={text}
          position={captionPosition}
          fontSize={24}
          backgroundStyle="gradient"
        />
      )}
    </AbsoluteFill>
  );
};

export default AnimatedDemoScene;
