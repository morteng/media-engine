/**
 * TitleCard Component
 *
 * Animated title card with the ROP logo and tagline.
 * Features elegant fade-in, text reveal, and copper accent animations.
 */

import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, Easing, spring } from 'remotion';
import { colors, typography, gradients } from '../lib/theme';

interface TitleCardProps {
  title?: string;
  tagline?: string;
  variant?: 'intro' | 'section' | 'outro';
}

export const TitleCard: React.FC<TitleCardProps> = ({
  title = 'ROP',
  tagline = 'AI-First Restaurant Operations',
  variant = 'intro',
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Animation phases
  const logoRevealDuration = fps * 1.2; // 1.2 seconds
  const taglineDelay = fps * 0.8;
  const taglineRevealDuration = fps * 1;

  // Background opacity
  const bgOpacity = interpolate(
    frame,
    [0, fps * 0.3],
    [0, 1],
    { extrapolateRight: 'clamp' }
  );

  // Logo animation using spring
  const logoScale = spring({
    frame,
    fps,
    config: {
      damping: 12,
      stiffness: 100,
      mass: 0.5,
    },
  });

  const logoOpacity = interpolate(
    frame,
    [0, logoRevealDuration * 0.4],
    [0, 1],
    { extrapolateRight: 'clamp' }
  );

  // Copper accent line animation
  const accentLineWidth = interpolate(
    frame,
    [fps * 0.5, fps * 1.2],
    [0, 200],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

  // Tagline word-by-word reveal
  const taglineOpacity = interpolate(
    frame - taglineDelay,
    [0, taglineRevealDuration * 0.3],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const taglineY = interpolate(
    frame - taglineDelay,
    [0, taglineRevealDuration],
    [20, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

  // Subtle background grain/texture effect
  const grainOpacity = 0.03;

  return (
    <div
      style={{
        position: 'absolute',
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: gradients.darkRadial,
        opacity: bgOpacity,
        overflow: 'hidden',
      }}
    >
      {/* Subtle texture overlay */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
          opacity: grainOpacity,
          mixBlendMode: 'overlay',
        }}
      />

      {/* Copper glow accent in background */}
      <div
        style={{
          position: 'absolute',
          width: '600px',
          height: '600px',
          borderRadius: '50%',
          background: `radial-gradient(circle, ${colors.accent}22 0%, transparent 70%)`,
          filter: 'blur(100px)',
          opacity: interpolate(frame, [fps * 0.5, fps * 1.5], [0, 0.6], {
            extrapolateRight: 'clamp',
          }),
        }}
      />

      {/* Main title */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          transform: `scale(${logoScale})`,
          opacity: logoOpacity,
        }}
      >
        <h1
          style={{
            fontFamily: typography.fonts.heading,
            fontSize: variant === 'intro' ? 160 : 120,
            fontWeight: typography.weights.bold,
            color: colors.dark.textPrimary,
            margin: 0,
            letterSpacing: '0.05em',
            textShadow: `0 4px 30px ${colors.accent}44`,
          }}
        >
          {title}
        </h1>

        {/* Copper accent line */}
        <div
          style={{
            width: `${accentLineWidth}px`,
            height: 4,
            background: gradients.copperGlow,
            borderRadius: 2,
            marginTop: 20,
            boxShadow: `0 0 20px ${colors.accent}66`,
          }}
        />
      </div>

      {/* Tagline */}
      <p
        style={{
          fontFamily: typography.fonts.body,
          fontSize: typography.sizes.h3,
          fontWeight: typography.weights.light,
          color: colors.dark.textSecondary,
          margin: 0,
          marginTop: 40,
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
          opacity: taglineOpacity,
          transform: `translateY(${taglineY}px)`,
        }}
      >
        {tagline}
      </p>

      {/* Subtle corner accents */}
      <CornerAccent position="top-left" frame={frame} fps={fps} />
      <CornerAccent position="bottom-right" frame={frame} fps={fps} />
    </div>
  );
};

// Corner accent decoration
const CornerAccent: React.FC<{
  position: 'top-left' | 'bottom-right';
  frame: number;
  fps: number;
}> = ({ position, frame, fps }) => {
  const delay = position === 'top-left' ? fps * 0.8 : fps * 1;

  const opacity = interpolate(
    frame - delay,
    [0, fps * 0.5],
    [0, 0.3],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const scale = interpolate(
    frame - delay,
    [0, fps * 0.8],
    [0.5, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

  const positionStyles = position === 'top-left'
    ? { top: 60, left: 60 }
    : { bottom: 60, right: 60 };

  const rotation = position === 'top-left' ? 0 : 180;

  return (
    <div
      style={{
        position: 'absolute',
        ...positionStyles,
        opacity,
        transform: `scale(${scale}) rotate(${rotation}deg)`,
      }}
    >
      <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
        <path
          d="M0 0 L80 0 L80 8 L8 8 L8 80 L0 80 Z"
          fill={colors.accent}
          opacity={0.5}
        />
      </svg>
    </div>
  );
};

export default TitleCard;
