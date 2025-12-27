/**
 * SplitScreenDemo Component
 *
 * Displays demo video alongside motion graphics with a diagonal split.
 * The split can animate in/out and supports various layouts.
 *
 * Visual:
 * ┌─────────────────────────────┐
 * │    Demo Video       ╱╱      │
 * │                   ╱╱        │
 * │                 ╱╱          │
 * │               ╱╱  Motion    │
 * │             ╱╱   Graphics   │
 * └─────────────────────────────┘
 */

import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Easing,
  Video as RemotionVideo,
  staticFile,
} from 'remotion';
import { colors, typography, gradients, glows } from '../lib/theme';

interface SplitScreenDemoProps {
  /** Path to demo video clip (relative to public folder) */
  demoClipPath: string;
  /** Whether demo is on the left (true) or right (false) */
  demoOnLeft?: boolean;
  /** Angle of the diagonal split in degrees (default 15) */
  splitAngle?: number;
  /** Width percentage for the demo side (default 60) */
  demoWidth?: number;
  /** Title text to show on motion graphics side */
  title?: string;
  /** Body text to show on motion graphics side */
  text?: string;
  /** Feature bullets to show */
  bullets?: string[];
  /** Highlight color for accent elements */
  highlightColor?: 'cyan' | 'purple' | 'hot' | 'neon';
  /** Whether to animate the split entrance */
  animateSplit?: boolean;
  /** Frame number relative to scene start */
  sceneFrame: number;
  /** Total scene duration in frames */
  durationFrames: number;
  /** Background variant for motion graphics side */
  backgroundVariant?: 'dark' | 'aurora' | 'particles' | 'grid';
}

const getAccentColor = (highlight?: string): string => {
  switch (highlight) {
    case 'cyan': return colors.accent;
    case 'purple': return colors.accentSecondary;
    case 'hot': return colors.accentHot;
    case 'neon': return colors.accentNeon;
    default: return colors.accent;
  }
};

/**
 * SplitScreenDemo - Diagonal split between demo and motion graphics
 */
export const SplitScreenDemo: React.FC<SplitScreenDemoProps> = ({
  demoClipPath,
  demoOnLeft = true,
  splitAngle = 15,
  demoWidth = 55,
  title,
  text,
  bullets = [],
  highlightColor = 'cyan',
  animateSplit = true,
  sceneFrame,
  durationFrames,
  backgroundVariant = 'dark',
}) => {
  const { fps, width, height } = useVideoConfig();
  const accentColor = getAccentColor(highlightColor);

  // Calculate the skew offset based on angle
  // At 15 degrees, the diagonal will shift the split line
  const skewOffset = Math.tan((splitAngle * Math.PI) / 180) * height;

  // Animation for split reveal
  const splitProgress = animateSplit
    ? spring({
        frame: sceneFrame,
        fps,
        config: { damping: 15, stiffness: 80, mass: 0.8 },
      })
    : 1;

  // Fade in/out for overall opacity
  const opacity = interpolate(
    sceneFrame,
    [0, fps * 0.3, durationFrames - fps * 0.3, durationFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Calculate clip paths for the diagonal split
  // Demo side gets more space initially, then the diagonal creates the visual interest
  const demoWidthPx = (width * demoWidth) / 100;

  // Points for the diagonal clip path
  // If demo is on left: starts at 0, goes to demoWidth at top, then angles back
  const demoClipPath = demoOnLeft
    ? `polygon(0 0, ${demoWidthPx + skewOffset}px 0, ${demoWidthPx - skewOffset}px 100%, 0 100%)`
    : `polygon(${width - demoWidthPx - skewOffset}px 0, 100% 0, 100% 100%, ${width - demoWidthPx + skewOffset}px 100%)`;

  const graphicsClipPath = demoOnLeft
    ? `polygon(${demoWidthPx + skewOffset - 20}px 0, 100% 0, 100% 100%, ${demoWidthPx - skewOffset - 20}px 100%)`
    : `polygon(0 0, ${width - demoWidthPx - skewOffset + 20}px 0, ${width - demoWidthPx + skewOffset + 20}px 100%, 0 100%)`;

  // Animated entry from edge
  const demoTranslateX = animateSplit
    ? interpolate(splitProgress, [0, 1], [demoOnLeft ? -200 : 200, 0])
    : 0;

  const graphicsTranslateX = animateSplit
    ? interpolate(splitProgress, [0, 1], [demoOnLeft ? 200 : -200, 0])
    : 0;

  // Content animations
  const titleOpacity = interpolate(
    sceneFrame,
    [fps * 0.5, fps * 0.8],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const titleY = interpolate(
    sceneFrame,
    [fps * 0.5, fps * 0.9],
    [30, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

  const textOpacity = interpolate(
    sceneFrame,
    [fps * 0.7, fps * 1.0],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Diagonal edge glow effect
  const glowPulse = Math.sin(sceneFrame * 0.08) * 0.3 + 0.7;

  return (
    <AbsoluteFill style={{ opacity }}>
      {/* Demo Video Side */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          clipPath: demoClipPath,
          transform: `translateX(${demoTranslateX}px)`,
          overflow: 'hidden',
        }}
      >
        {/* Video player */}
        <RemotionVideo
          src={staticFile(demoClipPath)}
          startFrom={0}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />

        {/* Subtle vignette on video */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: `radial-gradient(ellipse at ${demoOnLeft ? '30% 50%' : '70% 50%'}, transparent 30%, ${colors.dark.bgPrimary}44 100%)`,
            pointerEvents: 'none',
          }}
        />

        {/* "LIVE DEMO" badge */}
        <div
          style={{
            position: 'absolute',
            top: 40,
            left: demoOnLeft ? 40 : undefined,
            right: demoOnLeft ? undefined : 40,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '10px 20px',
            background: `${colors.dark.bgPrimary}dd`,
            borderRadius: 8,
            border: `1px solid ${accentColor}66`,
            boxShadow: `0 0 20px ${accentColor}33`,
          }}
        >
          {/* Recording dot */}
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              background: colors.accentHot,
              boxShadow: `0 0 10px ${colors.accentHot}`,
              opacity: 0.5 + glowPulse * 0.5,
            }}
          />
          <span
            style={{
              fontFamily: typography.fonts.mono,
              fontSize: 14,
              fontWeight: typography.weights.semibold,
              color: colors.dark.textPrimary,
              letterSpacing: '0.15em',
              textTransform: 'uppercase',
            }}
          >
            Live Demo
          </span>
        </div>
      </div>

      {/* Motion Graphics Side */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          clipPath: graphicsClipPath,
          transform: `translateX(${graphicsTranslateX}px)`,
          overflow: 'hidden',
        }}
      >
        {/* Background gradient */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: backgroundVariant === 'aurora'
              ? gradients.auroraRadial
              : backgroundVariant === 'particles'
              ? gradients.darkPurple
              : gradients.darkSpace,
          }}
        />

        {/* Subtle grid pattern */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundImage: `linear-gradient(${colors.dark.border}11 1px, transparent 1px), linear-gradient(90deg, ${colors.dark.border}11 1px, transparent 1px)`,
            backgroundSize: '40px 40px',
            opacity: 0.5,
          }}
        />

        {/* Content container */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: demoOnLeft ? demoWidthPx + 60 : 80,
            right: demoOnLeft ? 80 : demoWidthPx + 60,
            bottom: 0,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            padding: '60px 40px',
          }}
        >
          {/* Accent line */}
          <div
            style={{
              width: interpolate(sceneFrame, [fps * 0.3, fps * 0.7], [0, 100], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
                easing: Easing.out(Easing.cubic),
              }),
              height: 4,
              background: `linear-gradient(90deg, ${accentColor}, ${colors.accentSecondary})`,
              borderRadius: 2,
              marginBottom: 24,
              boxShadow: `0 0 20px ${accentColor}66`,
            }}
          />

          {/* Title */}
          {title && (
            <h2
              style={{
                fontFamily: typography.fonts.heading,
                fontSize: typography.sizes.h2,
                fontWeight: typography.weights.bold,
                color: colors.dark.textPrimary,
                margin: 0,
                marginBottom: 20,
                opacity: titleOpacity,
                transform: `translateY(${titleY}px)`,
                lineHeight: 1.2,
              }}
            >
              {title}
            </h2>
          )}

          {/* Description text */}
          {text && (
            <p
              style={{
                fontFamily: typography.fonts.body,
                fontSize: typography.sizes.h4,
                fontWeight: typography.weights.normal,
                color: colors.dark.textSecondary,
                margin: 0,
                marginBottom: 30,
                opacity: textOpacity,
                lineHeight: 1.6,
                maxWidth: 500,
              }}
            >
              {text}
            </p>
          )}

          {/* Bullet points */}
          {bullets.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {bullets.map((bullet, index) => {
                const bulletDelay = fps * 0.8 + index * 8;
                const bulletOpacity = interpolate(
                  sceneFrame - bulletDelay,
                  [0, 15],
                  [0, 1],
                  { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
                );
                const bulletX = interpolate(
                  sceneFrame - bulletDelay,
                  [0, 20],
                  [-20, 0],
                  { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
                );

                return (
                  <div
                    key={index}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 16,
                      opacity: bulletOpacity,
                      transform: `translateX(${bulletX}px)`,
                    }}
                  >
                    {/* Bullet marker */}
                    <div
                      style={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        background: accentColor,
                        boxShadow: `0 0 12px ${accentColor}`,
                        flexShrink: 0,
                      }}
                    />
                    <span
                      style={{
                        fontFamily: typography.fonts.body,
                        fontSize: typography.sizes.body,
                        color: colors.dark.textPrimary,
                      }}
                    >
                      {bullet}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Accent glow orb */}
        <div
          style={{
            position: 'absolute',
            width: 400,
            height: 400,
            borderRadius: '50%',
            background: `radial-gradient(circle, ${accentColor}22 0%, transparent 70%)`,
            filter: 'blur(60px)',
            top: '50%',
            left: demoOnLeft ? '70%' : '30%',
            transform: 'translate(-50%, -50%)',
            opacity: glowPulse,
          }}
        />
      </div>

      {/* Diagonal Split Edge Glow */}
      <svg
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          pointerEvents: 'none',
        }}
      >
        <defs>
          <linearGradient id="splitGlow" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor={accentColor} stopOpacity={0.8 * glowPulse} />
            <stop offset="50%" stopColor={colors.accentSecondary} stopOpacity={0.6 * glowPulse} />
            <stop offset="100%" stopColor={accentColor} stopOpacity={0.8 * glowPulse} />
          </linearGradient>
          <filter id="glowFilter">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <line
          x1={demoOnLeft ? demoWidthPx + skewOffset : width - demoWidthPx - skewOffset}
          y1={0}
          x2={demoOnLeft ? demoWidthPx - skewOffset : width - demoWidthPx + skewOffset}
          y2={height}
          stroke="url(#splitGlow)"
          strokeWidth={3}
          filter="url(#glowFilter)"
        />
      </svg>
    </AbsoluteFill>
  );
};

export default SplitScreenDemo;
