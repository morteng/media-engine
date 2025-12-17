/**
 * TextReveal Components - Electric Aurora Edition
 *
 * Kinetic typography with bounce, wave, elastic, and split effects.
 * Dynamic text animations that grab attention and engage viewers.
 */

import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, Easing, spring } from 'remotion';
import { colors, typography, gradients, glows } from '../lib/theme';

type RevealEffect = 'fade-up' | 'bounce' | 'elastic' | 'wave' | 'split' | 'scale-pop' | 'rotate' | 'glitch';

interface TextRevealProps {
  text: string;
  delay?: number;
  framesPerWord?: number;
  variant?: 'display' | 'heading' | 'tagline' | 'body';
  effect?: RevealEffect;
  color?: string;
  gradient?: boolean;
  align?: 'left' | 'center' | 'right';
  maxWidth?: number;
  glow?: boolean;
}

export const TextReveal: React.FC<TextRevealProps> = ({
  text,
  delay = 0,
  framesPerWord = 5,
  variant = 'heading',
  effect = 'bounce',
  color,
  gradient = false,
  align = 'center',
  maxWidth,
  glow = false,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const words = text.split(' ');

  // Style configurations with new fonts
  const styles = {
    display: {
      fontFamily: typography.fonts.display,
      fontSize: typography.sizes.display,
      fontWeight: typography.weights.heavy,
      color: color || colors.dark.textPrimary,
      lineHeight: 1.1,
      letterSpacing: '0.02em',
    },
    heading: {
      fontFamily: typography.fonts.heading,
      fontSize: typography.sizes.h1,
      fontWeight: typography.weights.bold,
      color: color || colors.dark.textPrimary,
      lineHeight: 1.2,
    },
    tagline: {
      fontFamily: typography.fonts.body,
      fontSize: typography.sizes.h3,
      fontWeight: typography.weights.medium,
      color: color || colors.dark.textSecondary,
      letterSpacing: '0.15em',
      textTransform: 'uppercase' as const,
      lineHeight: 1.4,
    },
    body: {
      fontFamily: typography.fonts.body,
      fontSize: typography.sizes.body,
      fontWeight: typography.weights.normal,
      color: color || colors.dark.textSecondary,
      lineHeight: 1.6,
    },
  };

  const style = styles[variant];

  // Gradient text style
  const gradientStyle = gradient ? {
    background: gradients.textAurora,
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
  } : {};

  // Glow effect
  const glowStyle = glow ? {
    textShadow: glows.cyan,
  } : {};

  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: align === 'center' ? 'center' : align === 'right' ? 'flex-end' : 'flex-start',
        gap: variant === 'display' ? '0.25em' : '0.2em',
        maxWidth: maxWidth || 'none',
        ...style,
        ...gradientStyle,
        ...glowStyle,
      }}
    >
      {words.map((word, index) => (
        <AnimatedWord
          key={index}
          word={word}
          index={index}
          delay={delay}
          framesPerWord={framesPerWord}
          effect={effect}
          fps={fps}
          frame={frame}
        />
      ))}
    </div>
  );
};

// Animated word component with various effects
const AnimatedWord: React.FC<{
  word: string;
  index: number;
  delay: number;
  framesPerWord: number;
  effect: RevealEffect;
  fps: number;
  frame: number;
}> = ({ word, index, delay, framesPerWord, effect, fps, frame }) => {
  const wordDelay = delay + index * framesPerWord;

  // Common interpolations
  const progress = interpolate(
    frame - wordDelay,
    [0, framesPerWord],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const opacity = interpolate(progress, [0, 0.5], [0, 1], { extrapolateRight: 'clamp' });

  // Effect-specific transforms
  let transform = '';
  let filter = '';

  switch (effect) {
    case 'fade-up':
      const fadeY = interpolate(progress, [0, 1], [30, 0], { easing: Easing.out(Easing.cubic) });
      const fadeBlur = interpolate(progress, [0, 0.5], [8, 0], { extrapolateRight: 'clamp' });
      transform = `translateY(${fadeY}px)`;
      filter = `blur(${fadeBlur}px)`;
      break;

    case 'bounce':
      // Spring-like bounce effect
      const bounceY = interpolate(
        progress,
        [0, 0.4, 0.6, 0.8, 1],
        [60, -15, 8, -4, 0],
        { easing: Easing.out(Easing.cubic) }
      );
      const bounceScale = interpolate(
        progress,
        [0, 0.4, 0.6, 0.8, 1],
        [0.5, 1.1, 0.95, 1.02, 1]
      );
      transform = `translateY(${bounceY}px) scale(${bounceScale})`;
      break;

    case 'elastic':
      // Elastic stretch effect
      const elasticX = interpolate(
        progress,
        [0, 0.3, 0.5, 0.7, 0.85, 1],
        [-100, 20, -10, 5, -2, 0],
        { easing: Easing.out(Easing.quad) }
      );
      const scaleX = interpolate(
        progress,
        [0, 0.3, 0.5, 0.7, 1],
        [0.3, 1.3, 0.9, 1.1, 1]
      );
      transform = `translateX(${elasticX}px) scaleX(${scaleX})`;
      break;

    case 'wave':
      // Wave motion effect
      const waveY = Math.sin((frame - wordDelay) * 0.15 + index * 0.5) * 10 * (1 - progress * 0.8);
      const waveRotate = Math.sin((frame - wordDelay) * 0.1 + index * 0.3) * 5 * (1 - progress * 0.9);
      const waveScale = interpolate(progress, [0, 0.5, 1], [0, 1.1, 1]);
      transform = `translateY(${waveY}px) rotate(${waveRotate}deg) scale(${waveScale})`;
      break;

    case 'split':
      // Split from center effect
      const splitY = interpolate(
        progress,
        [0, 1],
        [index % 2 === 0 ? -80 : 80, 0],
        { easing: Easing.out(Easing.cubic) }
      );
      const splitRotate = interpolate(
        progress,
        [0, 1],
        [index % 2 === 0 ? -30 : 30, 0],
        { easing: Easing.out(Easing.cubic) }
      );
      transform = `translateY(${splitY}px) rotate(${splitRotate}deg)`;
      break;

    case 'scale-pop':
      // Pop in with overshoot
      const popScale = interpolate(
        progress,
        [0, 0.5, 0.75, 1],
        [0, 1.4, 0.9, 1],
        { easing: Easing.out(Easing.cubic) }
      );
      const popRotate = interpolate(
        progress,
        [0, 0.5, 1],
        [index % 2 === 0 ? -15 : 15, index % 2 === 0 ? 5 : -5, 0]
      );
      transform = `scale(${popScale}) rotate(${popRotate}deg)`;
      break;

    case 'rotate':
      // Rotate in from 3D
      const rotateY = interpolate(
        progress,
        [0, 1],
        [90, 0],
        { easing: Easing.out(Easing.cubic) }
      );
      const rotateZ = interpolate(
        progress,
        [0, 0.5, 1],
        [45, -10, 0],
        { easing: Easing.out(Easing.cubic) }
      );
      transform = `perspective(800px) rotateY(${rotateY}deg) rotateZ(${rotateZ}deg)`;
      break;

    case 'glitch':
      // Glitch/distortion effect
      const glitchOffset = Math.random() > 0.7 ? (Math.random() - 0.5) * 10 * (1 - progress) : 0;
      const glitchSkew = Math.random() > 0.8 ? (Math.random() - 0.5) * 10 * (1 - progress) : 0;
      const glitchScale = interpolate(progress, [0, 0.5, 1], [1.5, 1, 1]);
      transform = `translateX(${glitchOffset}px) skewX(${glitchSkew}deg) scale(${glitchScale})`;
      break;
  }

  return (
    <span
      style={{
        display: 'inline-block',
        opacity,
        transform,
        filter,
        transformOrigin: 'center center',
      }}
    >
      {word}
    </span>
  );
};

// Gradient text with animated highlight sweep
interface GradientTextProps {
  text: string;
  delay?: number;
  size?: 'display' | 'h1' | 'h2' | 'h3';
}

export const GradientText: React.FC<GradientTextProps> = ({
  text,
  delay = 0,
  size = 'h1',
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = interpolate(
    frame - delay,
    [0, fps * 0.5],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const scale = interpolate(progress, [0, 0.5, 1], [0.8, 1.05, 1]);
  const opacity = interpolate(progress, [0, 0.3], [0, 1], { extrapolateRight: 'clamp' });

  // Animated gradient position for shimmer effect
  const shimmerPos = interpolate(
    (frame - delay) % (fps * 2),
    [0, fps * 2],
    [-100, 200]
  );

  return (
    <div
      style={{
        fontFamily: size === 'display' ? typography.fonts.display : typography.fonts.heading,
        fontSize: typography.sizes[size],
        fontWeight: typography.weights.bold,
        background: `linear-gradient(90deg,
          ${colors.accent} 0%,
          ${colors.accentSecondary} 25%,
          ${colors.accentHot} 50%,
          ${colors.accentSecondary} 75%,
          ${colors.accent} 100%
        )`,
        backgroundSize: '200% 100%',
        backgroundPosition: `${shimmerPos}% 0`,
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        backgroundClip: 'text',
        transform: `scale(${scale})`,
        opacity,
        textShadow: `0 0 60px ${colors.accent}44`,
      }}
    >
      {text}
    </div>
  );
};

// Highlight text with neon accent
interface HighlightTextProps {
  text: string;
  highlight: string;
  delay?: number;
  highlightColor?: string;
}

export const HighlightText: React.FC<HighlightTextProps> = ({
  text,
  highlight,
  delay = 0,
  highlightColor,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Split text around highlight
  const parts = text.split(highlight);

  // Container animation
  const containerOpacity = interpolate(
    frame - delay,
    [0, fps * 0.3],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Highlight animation (appears after main text)
  const highlightDelay = delay + fps * 0.4;
  const highlightProgress = interpolate(
    frame - highlightDelay,
    [0, fps * 0.4],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const highlightScale = interpolate(
    highlightProgress,
    [0, 0.5, 0.7, 1],
    [0.5, 1.2, 0.95, 1]
  );

  const highlightY = interpolate(
    highlightProgress,
    [0, 0.5, 1],
    [20, -5, 0]
  );

  // Animated glow pulse
  const glowPulse = Math.sin((frame - highlightDelay) * 0.1) * 0.3 + 0.7;
  const accentColor = highlightColor || colors.accent;

  return (
    <div
      style={{
        fontFamily: typography.fonts.heading,
        fontSize: typography.sizes.h2,
        fontWeight: typography.weights.semibold,
        color: colors.dark.textPrimary,
        opacity: containerOpacity,
        display: 'inline-flex',
        alignItems: 'center',
        flexWrap: 'wrap',
        justifyContent: 'center',
        gap: '0.25em',
      }}
    >
      {parts[0]}
      <span
        style={{
          color: accentColor,
          display: 'inline-block',
          transform: `scale(${highlightScale}) translateY(${highlightY}px)`,
          opacity: highlightProgress,
          position: 'relative',
          textShadow: `0 0 ${30 * glowPulse}px ${accentColor}88, 0 0 ${60 * glowPulse}px ${accentColor}44`,
        }}
      >
        {/* Underline accent */}
        <span
          style={{
            position: 'absolute',
            bottom: '-4px',
            left: 0,
            right: 0,
            height: '3px',
            background: gradients.aurora,
            borderRadius: '2px',
            transform: `scaleX(${highlightProgress})`,
            transformOrigin: 'left',
            boxShadow: `0 0 10px ${accentColor}`,
          }}
        />
        {highlight}
      </span>
      {parts[1]}
    </div>
  );
};

// Typewriter effect with enhanced cursor and colors
interface TypewriterProps {
  text: string;
  delay?: number;
  charsPerFrame?: number;
  cursor?: boolean;
  variant?: 'terminal' | 'code' | 'chat';
}

export const Typewriter: React.FC<TypewriterProps> = ({
  text,
  delay = 0,
  charsPerFrame = 2,
  cursor = true,
  variant = 'terminal',
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const elapsed = Math.max(0, frame - delay);
  const charsToShow = Math.min(Math.floor(elapsed * charsPerFrame), text.length);
  const displayText = text.slice(0, charsToShow);

  // Cursor blink (faster for more energy)
  const cursorOpacity = cursor
    ? Math.floor((frame - delay) / (fps * 0.3)) % 2 === 0 ? 1 : 0.3
    : 0;

  const isComplete = charsToShow >= text.length;

  // Variant styles
  const variantStyles = {
    terminal: {
      fontFamily: typography.fonts.mono,
      fontSize: typography.sizes.body,
      color: colors.accentNeon,
      textShadow: `0 0 10px ${colors.accentNeon}88`,
    },
    code: {
      fontFamily: typography.fonts.mono,
      fontSize: typography.sizes.small,
      color: colors.accent,
    },
    chat: {
      fontFamily: typography.fonts.body,
      fontSize: typography.sizes.body,
      color: colors.dark.textPrimary,
    },
  };

  return (
    <span style={variantStyles[variant]}>
      {displayText}
      {cursor && (
        <span
          style={{
            opacity: isComplete ? (cursorOpacity * 0.5) : cursorOpacity,
            color: colors.accentHot,
            textShadow: `0 0 5px ${colors.accentHot}`,
            fontWeight: 'bold',
          }}
        >
          {variant === 'terminal' ? '_' : '|'}
        </span>
      )}
    </span>
  );
};

// Character-by-character reveal with stagger
interface CharacterRevealProps {
  text: string;
  delay?: number;
  framesPerChar?: number;
  effect?: 'drop' | 'zoom' | 'spin';
}

export const CharacterReveal: React.FC<CharacterRevealProps> = ({
  text,
  delay = 0,
  framesPerChar = 2,
  effect = 'drop',
}) => {
  const frame = useCurrentFrame();

  return (
    <span style={{
      fontFamily: typography.fonts.display,
      fontSize: typography.sizes.display,
      fontWeight: typography.weights.heavy,
      display: 'inline-flex',
    }}>
      {text.split('').map((char, i) => {
        const charDelay = delay + i * framesPerChar;
        const progress = interpolate(
          frame - charDelay,
          [0, framesPerChar * 3],
          [0, 1],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );

        let transform = '';
        const opacity = interpolate(progress, [0, 0.3], [0, 1], { extrapolateRight: 'clamp' });

        switch (effect) {
          case 'drop':
            const dropY = interpolate(progress, [0, 0.5, 0.7, 1], [-80, 10, -5, 0]);
            const dropScale = interpolate(progress, [0, 0.5, 1], [0.5, 1.1, 1]);
            transform = `translateY(${dropY}px) scale(${dropScale})`;
            break;
          case 'zoom':
            const zoomScale = interpolate(progress, [0, 0.5, 1], [3, 0.9, 1]);
            const zoomRotate = interpolate(progress, [0, 1], [180, 0]);
            transform = `scale(${zoomScale}) rotate(${zoomRotate}deg)`;
            break;
          case 'spin':
            const spinRotate = interpolate(progress, [0, 1], [720, 0]);
            const spinScale = interpolate(progress, [0, 0.5, 1], [0, 1.2, 1]);
            transform = `rotate(${spinRotate}deg) scale(${spinScale})`;
            break;
        }

        return (
          <span
            key={i}
            style={{
              display: 'inline-block',
              opacity,
              transform,
              color: i % 3 === 0 ? colors.accent : i % 3 === 1 ? colors.accentSecondary : colors.accentHot,
              textShadow: `0 0 20px currentColor`,
              minWidth: char === ' ' ? '0.3em' : 'auto',
            }}
          >
            {char}
          </span>
        );
      })}
    </span>
  );
};

// Counter animation for numbers
interface AnimatedCounterProps {
  value: number;
  delay?: number;
  duration?: number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
}

export const AnimatedCounter: React.FC<AnimatedCounterProps> = ({
  value,
  delay = 0,
  duration = 45,
  prefix = '',
  suffix = '',
  decimals = 0,
}) => {
  const frame = useCurrentFrame();

  const progress = interpolate(
    frame - delay,
    [0, duration],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

  const currentValue = value * progress;
  const displayValue = decimals > 0
    ? currentValue.toFixed(decimals)
    : Math.floor(currentValue).toLocaleString();

  const scale = interpolate(progress, [0.9, 1], [1, 1.05], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  return (
    <span
      style={{
        fontFamily: typography.fonts.display,
        fontSize: typography.sizes.display,
        fontWeight: typography.weights.heavy,
        color: colors.accent,
        textShadow: glows.cyan,
        display: 'inline-block',
        transform: `scale(${scale})`,
      }}
    >
      {prefix}{displayValue}{suffix}
    </span>
  );
};

export default TextReveal;
