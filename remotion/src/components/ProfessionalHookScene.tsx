/**
 * Professional Hook Scene - "The Problem"
 *
 * A proof-of-concept for professional video production showing:
 * - Multi-layer composition (background, content, overlay, text)
 * - Ken Burns motion on screenshots
 * - Timeline-based segment transitions
 * - Theme-aware visual effects
 *
 * Scene narrative:
 * 0-2s: Show markdown being written (zoom into code)
 * 2-4s: "You write great documentation" - content transforms
 * 4-6s: "But turning it into polished deliverables?" - output icons appear
 * 6-8s: "That takes forever." - frustration visual
 */

import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Img,
  staticFile,
  Easing,
} from 'remotion';
import { Background } from './Background';
import { Vignette, HighlightBox, ProgressIndicator, ScreenChrome } from './overlays';
import { interpolateKeyframes, transformToStyle, motionPresets, type Keyframe } from '../lib/motion';
import { colors, gradients, glows, typography } from '../lib/theme';

// ============================================================================
// Types
// ============================================================================

interface ProfessionalHookSceneProps {
  durationFrames: number;
}

interface Segment {
  id: string;
  startProgress: number;
  endProgress: number;
  content: 'markdown' | 'dashboard' | 'outputs' | 'clock';
  motion: Keyframe[];
  text?: string;
  overlay?: 'vignette' | 'icons' | 'frustration';
}

// ============================================================================
// Scene Segments Definition
// ============================================================================

const segments: Segment[] = [
  {
    id: 'markdown',
    startProgress: 0,
    endProgress: 0.25,
    content: 'markdown',
    motion: [
      { at: 0, scale: 1.1, x: 0, y: 0, opacity: 0 },
      { at: 0.2, scale: 1.1, x: 0, y: 0, opacity: 1 },
      { at: 1, scale: 1.3, x: -50, y: -30, opacity: 1 },
    ],
    overlay: 'vignette',
  },
  {
    id: 'transition-to-dashboard',
    startProgress: 0.25,
    endProgress: 0.5,
    content: 'dashboard',
    motion: [
      { at: 0, scale: 1.2, x: 0, y: 0, opacity: 0 },
      { at: 0.3, scale: 1.2, x: 0, y: 0, opacity: 1 },
      { at: 1, scale: 1.4, x: -100, y: -80, opacity: 1 },
    ],
    text: 'You write great documentation.',
    overlay: 'vignette',
  },
  {
    id: 'outputs',
    startProgress: 0.5,
    endProgress: 0.75,
    content: 'outputs',
    motion: [
      { at: 0, scale: 1.4, x: -100, y: -80, opacity: 1 },
      { at: 1, scale: 1.2, x: 50, y: 20, opacity: 0.6 },
    ],
    text: 'But turning it into polished deliverables?',
    overlay: 'icons',
  },
  {
    id: 'frustration',
    startProgress: 0.75,
    endProgress: 1,
    content: 'clock',
    motion: [
      { at: 0, scale: 1.2, opacity: 0.6 },
      { at: 0.5, scale: 1, opacity: 0.3 },
      { at: 1, scale: 0.95, opacity: 0 },
    ],
    text: 'That takes forever.',
    overlay: 'frustration',
  },
];

// ============================================================================
// Output Icons Component
// ============================================================================

const OutputIcons: React.FC<{ progress: number }> = ({ progress }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const formats = [
    { name: 'PDF', color: colors.accentHot, x: -200, y: -100 },
    { name: 'PPTX', color: colors.warning, x: 200, y: -80 },
    { name: 'HTML', color: colors.accent, x: -180, y: 100 },
    { name: 'XLSX', color: colors.success, x: 220, y: 120 },
    { name: 'MP4', color: colors.accentSecondary, x: 0, y: -150 },
  ];

  return (
    <AbsoluteFill
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {formats.map((format, index) => {
        const delay = index * 5;
        const iconProgress = interpolate(progress, [0, 0.3, 0.7, 1], [0, 1, 1, 0.5], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });

        const iconScale = spring({
          frame: Math.max(0, frame - delay),
          fps,
          config: { damping: 8, stiffness: 150, mass: 0.5 },
        });

        // Shake effect for frustration
        const shake = progress > 0.5
          ? Math.sin(frame * 0.5 + index) * 5 * (progress - 0.5) * 2
          : 0;

        // Loading spinner rotation
        const spinnerRotation = frame * 3;

        // Show X or loading based on progress
        const showError = progress > 0.6;

        return (
          <div
            key={format.name}
            style={{
              position: 'absolute',
              transform: `translate(${format.x + shake}px, ${format.y}px) scale(${Math.max(0, iconScale) * iconProgress})`,
              opacity: iconProgress,
            }}
          >
            <div
              style={{
                width: 100,
                height: 120,
                background: `linear-gradient(135deg, ${colors.dark.bgSecondary}, ${colors.dark.bgTertiary})`,
                borderRadius: 16,
                border: `2px solid ${format.color}`,
                boxShadow: `0 0 30px ${format.color}44, 0 10px 40px rgba(0,0,0,0.4)`,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 10,
              }}
            >
              {/* Document fold */}
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  right: 0,
                  width: 24,
                  height: 24,
                  background: format.color,
                  clipPath: 'polygon(100% 0, 100% 100%, 0 100%)',
                  borderRadius: '0 16px 0 0',
                }}
              />

              {/* Format name */}
              <span
                style={{
                  fontFamily: typography.fonts.mono,
                  fontSize: 18,
                  fontWeight: typography.weights.bold,
                  color: format.color,
                  textShadow: `0 0 10px ${format.color}`,
                }}
              >
                {format.name}
              </span>

              {/* Status indicator */}
              <div
                style={{
                  width: 30,
                  height: 30,
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {showError ? (
                  // X icon
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path
                      d="M6 6L18 18M6 18L18 6"
                      stroke={colors.accentHot}
                      strokeWidth="3"
                      strokeLinecap="round"
                    />
                  </svg>
                ) : (
                  // Loading spinner
                  <div
                    style={{
                      width: 24,
                      height: 24,
                      border: `3px solid ${colors.dark.bgTertiary}`,
                      borderTopColor: format.color,
                      borderRadius: '50%',
                      transform: `rotate(${spinnerRotation}deg)`,
                    }}
                  />
                )}
              </div>
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

// ============================================================================
// Clock Animation Component
// ============================================================================

const ClockAnimation: React.FC<{ progress: number }> = ({ progress }) => {
  const frame = useCurrentFrame();

  // Speed up the clock as progress increases
  const clockSpeed = 5 + progress * 20;
  const hourRotation = (frame * clockSpeed / 60) % 360;
  const minuteRotation = (frame * clockSpeed) % 360;

  const opacity = interpolate(progress, [0, 0.3, 0.7, 1], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        opacity,
      }}
    >
      <div
        style={{
          width: 200,
          height: 200,
          borderRadius: '50%',
          background: colors.dark.bgSecondary,
          border: `4px solid ${colors.accent}`,
          boxShadow: glows.cyan,
          position: 'relative',
        }}
      >
        {/* Hour hand */}
        <div
          style={{
            position: 'absolute',
            left: '50%',
            bottom: '50%',
            width: 6,
            height: 50,
            background: colors.dark.textPrimary,
            borderRadius: 3,
            transformOrigin: 'center bottom',
            transform: `translateX(-50%) rotate(${hourRotation}deg)`,
          }}
        />
        {/* Minute hand */}
        <div
          style={{
            position: 'absolute',
            left: '50%',
            bottom: '50%',
            width: 4,
            height: 70,
            background: colors.accent,
            borderRadius: 2,
            transformOrigin: 'center bottom',
            transform: `translateX(-50%) rotate(${minuteRotation}deg)`,
            boxShadow: `0 0 10px ${colors.accent}`,
          }}
        />
        {/* Center dot */}
        <div
          style={{
            position: 'absolute',
            left: '50%',
            top: '50%',
            transform: 'translate(-50%, -50%)',
            width: 12,
            height: 12,
            borderRadius: '50%',
            background: colors.accentHot,
            boxShadow: `0 0 10px ${colors.accentHot}`,
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// Text Overlay Component
// ============================================================================

const TextOverlay: React.FC<{ text: string; progress: number }> = ({ text, progress }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = interpolate(progress, [0, 0.2, 0.8, 1], [0, 1, 1, 0.8], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const y = interpolate(progress, [0, 0.2], [30, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 150,
        left: 0,
        right: 0,
        textAlign: 'center',
        opacity,
        transform: `translateY(${y}px)`,
      }}
    >
      <div
        style={{
          display: 'inline-block',
          background: `${colors.dark.bgPrimary}dd`,
          backdropFilter: 'blur(10px)',
          padding: '20px 50px',
          borderRadius: 16,
          border: `1px solid ${colors.dark.border}`,
        }}
      >
        <span
          style={{
            fontFamily: typography.fonts.heading,
            fontSize: typography.sizes.h2,
            fontWeight: typography.weights.semibold,
            color: colors.dark.textPrimary,
            textShadow: `0 0 20px ${colors.accent}44`,
          }}
        >
          {text}
        </span>
      </div>
    </div>
  );
};

// ============================================================================
// Main Component
// ============================================================================

export const ProfessionalHookScene: React.FC<ProfessionalHookSceneProps> = ({
  durationFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Overall progress through the scene
  const progress = frame / durationFrames;

  // Find current segment
  const currentSegment = segments.find(
    s => progress >= s.startProgress && progress < s.endProgress
  ) || segments[segments.length - 1];

  // Calculate local progress within segment
  const segmentDuration = currentSegment.endProgress - currentSegment.startProgress;
  const segmentProgress = (progress - currentSegment.startProgress) / segmentDuration;

  // Get transform for current segment
  const transform = interpolateKeyframes(currentSegment.motion, segmentProgress);

  // Dashboard image path
  const dashboardImage = staticFile('assets/captures/dashboard-overview.png');
  const insightsImage = staticFile('assets/captures/dashboard-insights.png');

  return (
    <AbsoluteFill style={{ backgroundColor: colors.dark.bgPrimary }}>
      {/* Layer 1: Animated Background */}
      <Background variant="cyber" intensity="low" />

      {/* Layer 2: Main Content (Screenshots with motion) */}
      <AbsoluteFill
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div
          style={{
            width: '85%',
            height: '75%',
            position: 'relative',
            ...transformToStyle(transform),
          }}
        >
          {/* Show different content based on segment */}
          {(currentSegment.content === 'markdown' || currentSegment.content === 'dashboard') && (
            <ScreenChrome title="Media Engine Dashboard">
              <Img
                src={currentSegment.content === 'markdown' ? dashboardImage : insightsImage}
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover',
                }}
              />
            </ScreenChrome>
          )}

          {currentSegment.content === 'outputs' && (
            <Img
              src={dashboardImage}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                borderRadius: 12,
                filter: 'brightness(0.4) blur(2px)',
              }}
            />
          )}

          {currentSegment.content === 'clock' && (
            <Img
              src={dashboardImage}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                borderRadius: 12,
                filter: 'brightness(0.2) blur(4px) grayscale(100%)',
              }}
            />
          )}
        </div>
      </AbsoluteFill>

      {/* Layer 3: Overlays */}
      {currentSegment.overlay === 'vignette' && (
        <Vignette intensity={0.4} />
      )}

      {currentSegment.overlay === 'icons' && (
        <OutputIcons progress={segmentProgress} />
      )}

      {currentSegment.overlay === 'frustration' && (
        <>
          <Vignette intensity={0.6} color={colors.dark.bgPrimary} />
          <ClockAnimation progress={segmentProgress} />
        </>
      )}

      {/* Layer 4: Text Overlay */}
      {currentSegment.text && (
        <TextOverlay text={currentSegment.text} progress={segmentProgress} />
      )}

      {/* Layer 5: Progress Indicator */}
      <ProgressIndicator
        progress={progress}
        segments={segments.length}
        currentSegment={segments.indexOf(currentSegment)}
      />

      {/* Fade in/out */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: colors.dark.bgPrimary,
          opacity: interpolate(frame, [0, 15, durationFrames - 15, durationFrames], [1, 0, 0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          }),
          pointerEvents: 'none',
        }}
      />
    </AbsoluteFill>
  );
};

export default ProfessionalHookScene;
