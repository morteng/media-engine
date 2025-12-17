/**
 * Transition Components - Electric Aurora Edition
 *
 * Dynamic, eye-catching transitions between scenes.
 * Features: glitch, slice, zoom, diagonal, liquid, and more!
 */

import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, Easing, random } from 'remotion';
import { colors, gradients } from '../lib/theme';

export type TransitionType =
  | 'aurora-sweep'    // Multi-color diagonal sweep
  | 'glitch'          // Digital glitch effect
  | 'slice'           // Horizontal slices
  | 'zoom-burst'      // Zoom out with blur
  | 'diagonal-split'  // Diagonal split reveal
  | 'liquid'          // Wavy liquid motion
  | 'pixel-dissolve'  // Pixel scatter
  | 'rotate-wipe'     // Rotating wipe
  | 'flash'           // Quick flash transition
  | 'grid-reveal'     // Grid squares reveal
  | 'fade'            // Simple fade
  | 'wipe'            // Horizontal wipe
  | 'radial';         // Circle reveal

interface TransitionProps {
  type?: TransitionType;
  direction?: 'in' | 'out';
  delay?: number;
  duration?: number;
}

export const Transition: React.FC<TransitionProps> = ({
  type = 'aurora-sweep',
  direction = 'in',
  delay = 0,
  duration,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const transitionDuration = duration || fps * 0.6;

  const props = { frame, delay, duration: transitionDuration, direction };

  switch (type) {
    case 'aurora-sweep':
      return <AuroraSweep {...props} />;
    case 'glitch':
      return <GlitchTransition {...props} />;
    case 'slice':
      return <SliceTransition {...props} />;
    case 'zoom-burst':
      return <ZoomBurst {...props} />;
    case 'diagonal-split':
      return <DiagonalSplit {...props} />;
    case 'liquid':
      return <LiquidTransition {...props} />;
    case 'pixel-dissolve':
      return <PixelDissolve {...props} />;
    case 'rotate-wipe':
      return <RotateWipe {...props} />;
    case 'flash':
      return <FlashTransition {...props} />;
    case 'grid-reveal':
      return <GridReveal {...props} />;
    case 'fade':
      return <FadeTransition {...props} />;
    case 'wipe':
      return <WipeTransition {...props} />;
    case 'radial':
      return <RadialTransition {...props} />;
    default:
      return null;
  }
};

interface TransitionInternalProps {
  frame: number;
  delay: number;
  duration: number;
  direction: 'in' | 'out';
}

// Aurora Sweep - Multi-color diagonal bars with glow
const AuroraSweep: React.FC<TransitionInternalProps> = ({ frame, delay, duration, direction }) => {
  const progress = interpolate(
    frame - delay,
    [0, duration],
    direction === 'in' ? [0, 1] : [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic) }
  );

  const bar1X = interpolate(progress, [0, 1], [-100, 120]);
  const bar2X = interpolate(progress, [0, 1], [-100, 125]);
  const bar3X = interpolate(progress, [0, 1], [-100, 130]);
  const bar4X = interpolate(progress, [0, 1], [-100, 115]);

  if (progress <= 0 || progress >= 1) return null;

  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
      {/* Dark base bar */}
      <div style={{
        position: 'absolute',
        top: '-20%',
        left: `${bar4X}%`,
        width: '40%',
        height: '140%',
        background: colors.dark.bgPrimary,
        transform: 'skewX(-20deg)',
      }} />

      {/* Cyan bar with glow */}
      <div style={{
        position: 'absolute',
        top: '-20%',
        left: `${bar3X}%`,
        width: '25%',
        height: '140%',
        background: gradients.electricCyan,
        transform: 'skewX(-20deg)',
        boxShadow: `0 0 80px ${colors.accent}88, 0 0 120px ${colors.accent}44`,
      }} />

      {/* Purple bar with glow */}
      <div style={{
        position: 'absolute',
        top: '-20%',
        left: `${bar2X}%`,
        width: '15%',
        height: '140%',
        background: gradients.electricPurple,
        transform: 'skewX(-20deg)',
        boxShadow: `0 0 60px ${colors.accentSecondary}88`,
      }} />

      {/* Pink accent bar */}
      <div style={{
        position: 'absolute',
        top: '-20%',
        left: `${bar1X}%`,
        width: '8%',
        height: '140%',
        background: gradients.electricPink,
        transform: 'skewX(-20deg)',
        boxShadow: `0 0 40px ${colors.accentHot}88`,
      }} />
    </div>
  );
};

// Glitch Transition - Digital artifact effect
const GlitchTransition: React.FC<TransitionInternalProps> = ({ frame, delay, duration, direction }) => {
  const progress = interpolate(
    frame - delay,
    [0, duration],
    direction === 'in' ? [0, 1] : [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  if (progress <= 0 || progress >= 1) return null;

  const glitchIntensity = Math.sin(progress * Math.PI) * 100;
  const slices = 12;

  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
      {Array.from({ length: slices }).map((_, i) => {
        const offsetX = random(`glitch-x-${i}`) * glitchIntensity - glitchIntensity / 2;
        const sliceHeight = 100 / slices;
        const color = [colors.accent, colors.accentSecondary, colors.accentHot][i % 3];
        const opacity = random(`glitch-o-${i}`) * 0.8 + 0.2;

        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: `${offsetX}%`,
              top: `${i * sliceHeight}%`,
              width: '100%',
              height: `${sliceHeight + 0.5}%`,
              background: color,
              opacity: opacity * (1 - progress),
              mixBlendMode: 'screen',
            }}
          />
        );
      })}

      {/* Scanlines */}
      <div style={{
        position: 'absolute',
        inset: 0,
        background: `repeating-linear-gradient(
          0deg,
          transparent,
          transparent 2px,
          ${colors.dark.bgPrimary}22 2px,
          ${colors.dark.bgPrimary}22 4px
        )`,
        opacity: 1 - progress,
      }} />
    </div>
  );
};

// Slice Transition - Horizontal slices slide in/out
const SliceTransition: React.FC<TransitionInternalProps> = ({ frame, delay, duration, direction }) => {
  const progress = interpolate(
    frame - delay,
    [0, duration],
    direction === 'in' ? [0, 1] : [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic) }
  );

  if (progress <= 0 || progress >= 1) return null;

  const sliceCount = 8;
  const sliceHeight = 100 / sliceCount;

  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
      {Array.from({ length: sliceCount }).map((_, i) => {
        const sliceDelay = i * 0.08;
        const sliceProgress = interpolate(
          progress,
          [sliceDelay, sliceDelay + 0.4],
          [0, 100],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );
        const fromLeft = i % 2 === 0;

        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              top: `${i * sliceHeight}%`,
              left: fromLeft ? 0 : undefined,
              right: fromLeft ? undefined : 0,
              width: `${100 - sliceProgress}%`,
              height: `${sliceHeight + 0.5}%`,
              background: colors.dark.bgPrimary,
            }}
          />
        );
      })}
    </div>
  );
};

// Zoom Burst - Explosive zoom out
const ZoomBurst: React.FC<TransitionInternalProps> = ({ frame, delay, duration, direction }) => {
  const progress = interpolate(
    frame - delay,
    [0, duration],
    direction === 'in' ? [0, 1] : [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.exp) }
  );

  if (progress <= 0 || progress >= 1) return null;

  const scale = interpolate(progress, [0, 1], [5, 1]);
  const opacity = interpolate(progress, [0, 0.5, 1], [1, 0.8, 0]);

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: gradients.darkRadial,
        opacity,
        transform: `scale(${scale})`,
        pointerEvents: 'none',
      }}
    >
      {/* Radial burst lines */}
      <div style={{
        position: 'absolute',
        inset: 0,
        background: `conic-gradient(
          from 0deg,
          ${colors.accent}22 0deg,
          transparent 30deg,
          ${colors.accentSecondary}22 60deg,
          transparent 90deg,
          ${colors.accentHot}22 120deg,
          transparent 150deg,
          ${colors.accent}22 180deg,
          transparent 210deg,
          ${colors.accentSecondary}22 240deg,
          transparent 270deg,
          ${colors.accentHot}22 300deg,
          transparent 330deg,
          ${colors.accent}22 360deg
        )`,
      }} />
    </div>
  );
};

// Diagonal Split - Split from corner
const DiagonalSplit: React.FC<TransitionInternalProps> = ({ frame, delay, duration, direction }) => {
  const progress = interpolate(
    frame - delay,
    [0, duration],
    direction === 'in' ? [0, 1] : [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic) }
  );

  if (progress <= 0 || progress >= 1) return null;

  const splitProgress = progress * 200;

  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
      {/* Top-left triangle */}
      <div style={{
        position: 'absolute',
        inset: 0,
        background: colors.dark.bgPrimary,
        clipPath: `polygon(0 0, ${splitProgress}% 0, 0 ${splitProgress}%)`,
      }} />

      {/* Bottom-right triangle */}
      <div style={{
        position: 'absolute',
        inset: 0,
        background: colors.dark.bgSecondary,
        clipPath: `polygon(100% 100%, ${100 - splitProgress}% 100%, 100% ${100 - splitProgress}%)`,
      }} />

      {/* Diagonal line accent */}
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        width: '200%',
        height: '4px',
        background: gradients.aurora,
        transform: `translate(-50%, -50%) rotate(-45deg) scaleX(${1 - progress})`,
        boxShadow: `0 0 30px ${colors.accent}`,
      }} />
    </div>
  );
};

// Liquid Transition - Wavy liquid motion
const LiquidTransition: React.FC<TransitionInternalProps> = ({ frame, delay, duration, direction }) => {
  const progress = interpolate(
    frame - delay,
    [0, duration],
    direction === 'in' ? [0, 1] : [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic) }
  );

  if (progress <= 0 || progress >= 1) return null;

  const waveOffset = frame * 3;
  const baseY = interpolate(progress, [0, 1], [100, -20]);

  // Create wavy clip path
  const points = [];
  for (let x = 0; x <= 100; x += 2) {
    const wave1 = Math.sin((x + waveOffset) * 0.1) * 8;
    const wave2 = Math.sin((x + waveOffset * 0.5) * 0.15) * 5;
    const y = baseY + wave1 + wave2;
    points.push(`${x}% ${y}%`);
  }
  points.push('100% 100%', '0% 100%');
  const clipPath = `polygon(${points.join(', ')})`;

  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
      <div style={{
        position: 'absolute',
        inset: 0,
        background: gradients.darkPurple,
        clipPath,
      }} />

      {/* Liquid highlight */}
      <div style={{
        position: 'absolute',
        inset: 0,
        background: `linear-gradient(180deg, ${colors.accent}44 0%, transparent 30%)`,
        clipPath,
      }} />
    </div>
  );
};

// Pixel Dissolve - Scattered pixel effect
const PixelDissolve: React.FC<TransitionInternalProps> = ({ frame, delay, duration, direction }) => {
  const progress = interpolate(
    frame - delay,
    [0, duration],
    direction === 'in' ? [0, 1] : [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  if (progress <= 0 || progress >= 1) return null;

  const gridSize = 16;
  const cellSize = 100 / gridSize;

  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
      {Array.from({ length: gridSize * gridSize }).map((_, i) => {
        const x = (i % gridSize) * cellSize;
        const y = Math.floor(i / gridSize) * cellSize;
        const cellDelay = random(`pixel-${i}`) * 0.7;
        const cellProgress = interpolate(
          progress,
          [cellDelay, cellDelay + 0.3],
          [0, 1],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );

        if (cellProgress >= 1) return null;

        const color = [colors.dark.bgPrimary, colors.dark.bgSecondary, colors.accent + '44'][
          Math.floor(random(`pixel-c-${i}`) * 3)
        ];

        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: `${x}%`,
              top: `${y}%`,
              width: `${cellSize + 0.5}%`,
              height: `${cellSize + 0.5}%`,
              background: color,
              opacity: 1 - cellProgress,
              transform: `scale(${1 - cellProgress * 0.5})`,
            }}
          />
        );
      })}
    </div>
  );
};

// Rotate Wipe - Rotating bar wipe
const RotateWipe: React.FC<TransitionInternalProps> = ({ frame, delay, duration, direction }) => {
  const progress = interpolate(
    frame - delay,
    [0, duration],
    direction === 'in' ? [0, 1] : [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic) }
  );

  if (progress <= 0 || progress >= 1) return null;

  const rotation = interpolate(progress, [0, 1], [-45, 45]);
  const width = interpolate(progress, [0, 0.5, 1], [300, 200, 0]);

  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        width: `${width}%`,
        height: '300%',
        background: colors.dark.bgPrimary,
        transform: `translate(-50%, -50%) rotate(${rotation}deg)`,
        transformOrigin: 'center center',
      }}>
        {/* Accent edge */}
        <div style={{
          position: 'absolute',
          right: 0,
          top: 0,
          width: '4px',
          height: '100%',
          background: gradients.aurora,
          boxShadow: `0 0 30px ${colors.accent}`,
        }} />
      </div>
    </div>
  );
};

// Flash Transition - Quick bright flash
const FlashTransition: React.FC<TransitionInternalProps> = ({ frame, delay, duration, direction }) => {
  const progress = interpolate(
    frame - delay,
    [0, duration],
    direction === 'in' ? [0, 1] : [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  if (progress <= 0 || progress >= 1) return null;

  // Flash peaks in the middle
  const flashIntensity = Math.sin(progress * Math.PI);

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: `linear-gradient(135deg, ${colors.primary}, ${colors.accent}44)`,
        opacity: flashIntensity,
        mixBlendMode: 'overlay',
        pointerEvents: 'none',
      }}
    />
  );
};

// Grid Reveal - Grid squares reveal one by one
const GridReveal: React.FC<TransitionInternalProps> = ({ frame, delay, duration, direction }) => {
  const progress = interpolate(
    frame - delay,
    [0, duration],
    direction === 'in' ? [0, 1] : [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  if (progress <= 0 || progress >= 1) return null;

  const gridSize = 6;
  const cellSize = 100 / gridSize;

  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
      {Array.from({ length: gridSize * gridSize }).map((_, i) => {
        const x = i % gridSize;
        const y = Math.floor(i / gridSize);
        // Reveal from center outward
        const distFromCenter = Math.sqrt(Math.pow(x - gridSize / 2, 2) + Math.pow(y - gridSize / 2, 2));
        const maxDist = Math.sqrt(2) * gridSize / 2;
        const cellDelay = (distFromCenter / maxDist) * 0.6;
        const cellProgress = interpolate(
          progress,
          [cellDelay, cellDelay + 0.4],
          [0, 1],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );

        if (cellProgress >= 1) return null;

        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: `${x * cellSize}%`,
              top: `${y * cellSize}%`,
              width: `${cellSize + 0.5}%`,
              height: `${cellSize + 0.5}%`,
              background: colors.dark.bgPrimary,
              opacity: 1 - cellProgress,
              transform: `scale(${1 - cellProgress * 0.3})`,
              borderRadius: `${cellProgress * 50}%`,
            }}
          />
        );
      })}
    </div>
  );
};

// Simple fade transition
const FadeTransition: React.FC<TransitionInternalProps> = ({ frame, delay, duration, direction }) => {
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
const WipeTransition: React.FC<TransitionInternalProps> = ({ frame, delay, duration, direction }) => {
  const progress = interpolate(
    frame - delay,
    [0, duration],
    direction === 'in' ? [0, 100] : [100, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic) }
  );

  if (progress >= 100) return null;

  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
      <div style={{
        position: 'absolute',
        inset: 0,
        background: colors.dark.bgPrimary,
        clipPath: `inset(0 ${progress}% 0 0)`,
      }} />
      {/* Glowing edge */}
      <div style={{
        position: 'absolute',
        top: 0,
        bottom: 0,
        left: `${100 - progress}%`,
        width: '4px',
        background: gradients.aurora,
        boxShadow: `0 0 20px ${colors.accent}, 0 0 40px ${colors.accentSecondary}`,
      }} />
    </div>
  );
};

// Radial/circle transition
const RadialTransition: React.FC<TransitionInternalProps> = ({ frame, delay, duration, direction }) => {
  const progress = interpolate(
    frame - delay,
    [0, duration],
    direction === 'in' ? [0, 150] : [150, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic) }
  );

  if (progress >= 150) return null;

  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
      <div style={{
        position: 'absolute',
        inset: 0,
        background: colors.dark.bgPrimary,
        clipPath: `circle(${150 - progress}% at 50% 50%)`,
      }} />
      {/* Glowing ring */}
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        width: `${(150 - progress) * 2}%`,
        height: `${(150 - progress) * 2}%`,
        transform: 'translate(-50%, -50%)',
        borderRadius: '50%',
        border: `3px solid ${colors.accent}`,
        boxShadow: `0 0 20px ${colors.accent}, inset 0 0 20px ${colors.accent}44`,
        pointerEvents: 'none',
      }} />
    </div>
  );
};

// Scene wrapper with automatic transitions
interface SceneProps {
  children: React.ReactNode;
  transitionIn?: TransitionType;
  transitionOut?: TransitionType;
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
