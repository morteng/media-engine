/**
 * Transition Components
 *
 * Animated transitions between scenes.
 * Includes copper sweep, fade, and wipe effects.
 */

import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, Easing } from 'remotion';
import { colors, gradients } from '../lib/theme';

interface TransitionProps {
  type?: 'copper-sweep' | 'fade' | 'wipe' | 'radial';
  direction?: 'in' | 'out';
  delay?: number;
  duration?: number;
}

export const Transition: React.FC<TransitionProps> = ({
  type = 'copper-sweep',
  direction = 'in',
  delay = 0,
  duration,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const transitionDuration = duration || fps * 0.8;

  switch (type) {
    case 'copper-sweep':
      return <CopperSweep frame={frame} delay={delay} duration={transitionDuration} direction={direction} />;
    case 'fade':
      return <FadeTransition frame={frame} delay={delay} duration={transitionDuration} direction={direction} />;
    case 'wipe':
      return <WipeTransition frame={frame} delay={delay} duration={transitionDuration} direction={direction} />;
    case 'radial':
      return <RadialTransition frame={frame} delay={delay} duration={transitionDuration} direction={direction} />;
    default:
      return null;
  }
};

// Copper sweep transition - signature ROP transition
const CopperSweep: React.FC<{
  frame: number;
  delay: number;
  duration: number;
  direction: 'in' | 'out';
}> = ({ frame, delay, duration, direction }) => {
  const progress = interpolate(
    frame - delay,
    [0, duration],
    direction === 'in' ? [0, 1] : [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic) }
  );

  // Three diagonal bars sweeping across
  const bar1X = interpolate(progress, [0, 1], [-100, 110]);
  const bar2X = interpolate(progress, [0, 1], [-100, 115]);
  const bar3X = interpolate(progress, [0, 1], [-100, 120]);

  if (progress <= 0 || progress >= 1) return null;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        pointerEvents: 'none',
      }}
    >
      {/* Dark bar */}
      <div
        style={{
          position: 'absolute',
          top: '-10%',
          left: `${bar3X}%`,
          width: '30%',
          height: '120%',
          background: colors.dark.bgPrimary,
          transform: 'skewX(-15deg)',
        }}
      />

      {/* Copper bar */}
      <div
        style={{
          position: 'absolute',
          top: '-10%',
          left: `${bar2X}%`,
          width: '20%',
          height: '120%',
          background: gradients.copperGlow,
          transform: 'skewX(-15deg)',
          boxShadow: `0 0 60px ${colors.accent}88`,
        }}
      />

      {/* Light accent bar */}
      <div
        style={{
          position: 'absolute',
          top: '-10%',
          left: `${bar1X}%`,
          width: '8%',
          height: '120%',
          background: colors.dark.bgSecondary,
          transform: 'skewX(-15deg)',
        }}
      />
    </div>
  );
};

// Simple fade transition
const FadeTransition: React.FC<{
  frame: number;
  delay: number;
  duration: number;
  direction: 'in' | 'out';
}> = ({ frame, delay, duration, direction }) => {
  const opacity = interpolate(
    frame - delay,
    [0, duration],
    direction === 'in' ? [1, 0] : [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  if (opacity <= 0) return null;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: colors.dark.bgPrimary,
        opacity,
        pointerEvents: 'none',
      }}
    />
  );
};

// Horizontal wipe transition
const WipeTransition: React.FC<{
  frame: number;
  delay: number;
  duration: number;
  direction: 'in' | 'out';
}> = ({ frame, delay, duration, direction }) => {
  const progress = interpolate(
    frame - delay,
    [0, duration],
    direction === 'in' ? [0, 100] : [100, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic) }
  );

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: colors.dark.bgPrimary,
        clipPath: `inset(0 ${100 - progress}% 0 0)`,
        pointerEvents: 'none',
      }}
    />
  );
};

// Radial/circle transition
const RadialTransition: React.FC<{
  frame: number;
  delay: number;
  duration: number;
  direction: 'in' | 'out';
}> = ({ frame, delay, duration, direction }) => {
  const progress = interpolate(
    frame - delay,
    [0, duration],
    direction === 'in' ? [0, 150] : [150, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic) }
  );

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: colors.dark.bgPrimary,
        clipPath: `circle(${progress}% at 50% 50%)`,
        pointerEvents: 'none',
      }}
    />
  );
};

// Scene wrapper with automatic transitions
interface SceneProps {
  children: React.ReactNode;
  transitionIn?: TransitionProps['type'];
  transitionOut?: TransitionProps['type'];
  transitionDuration?: number;
}

export const Scene: React.FC<SceneProps> = ({
  children,
  transitionIn = 'fade',
  transitionOut,
  transitionDuration,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const duration = transitionDuration || fps * 0.5;

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      {children}

      {/* Transition in (overlay that fades away) */}
      {transitionIn && (
        <Transition
          type={transitionIn}
          direction="in"
          delay={0}
          duration={duration}
        />
      )}

      {/* Transition out (overlay that appears) */}
      {transitionOut && (
        <Transition
          type={transitionOut}
          direction="out"
          delay={durationInFrames - duration}
          duration={duration}
        />
      )}
    </div>
  );
};

export default Transition;
