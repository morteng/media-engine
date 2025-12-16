/**
 * TextReveal Component
 *
 * Animated text with word-by-word or character reveal effects.
 * Perfect for taglines and key messages.
 */

import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, Easing } from 'remotion';
import { colors, typography } from '../lib/theme';

interface TextRevealProps {
  text: string;
  delay?: number;
  framesPerWord?: number;
  variant?: 'heading' | 'tagline' | 'body';
  color?: string;
  align?: 'left' | 'center' | 'right';
  maxWidth?: number;
}

export const TextReveal: React.FC<TextRevealProps> = ({
  text,
  delay = 0,
  framesPerWord = 6,
  variant = 'heading',
  color,
  align = 'center',
  maxWidth,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const words = text.split(' ');

  // Style configurations
  const styles = {
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
      fontWeight: typography.weights.light,
      color: color || colors.dark.textSecondary,
      letterSpacing: '0.1em',
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

  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: align === 'center' ? 'center' : align === 'right' ? 'flex-end' : 'flex-start',
        gap: variant === 'heading' ? '0.3em' : '0.25em',
        maxWidth: maxWidth || 'none',
        ...style,
      }}
    >
      {words.map((word, index) => {
        const wordDelay = delay + index * framesPerWord;

        const opacity = interpolate(
          frame - wordDelay,
          [0, framesPerWord * 0.8],
          [0, 1],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );

        const y = interpolate(
          frame - wordDelay,
          [0, framesPerWord],
          [20, 0],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
        );

        const blur = interpolate(
          frame - wordDelay,
          [0, framesPerWord * 0.5],
          [4, 0],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );

        return (
          <span
            key={index}
            style={{
              display: 'inline-block',
              opacity,
              transform: `translateY(${y}px)`,
              filter: `blur(${blur}px)`,
            }}
          >
            {word}
          </span>
        );
      })}
    </div>
  );
};

// Highlight text with copper accent
interface HighlightTextProps {
  text: string;
  highlight: string;
  delay?: number;
}

export const HighlightText: React.FC<HighlightTextProps> = ({
  text,
  highlight,
  delay = 0,
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
  const highlightDelay = delay + fps * 0.5;
  const highlightScale = interpolate(
    frame - highlightDelay,
    [0, fps * 0.3, fps * 0.5],
    [0.8, 1.05, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const highlightOpacity = interpolate(
    frame - highlightDelay,
    [0, fps * 0.2],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Background glow on highlight
  const glowOpacity = interpolate(
    frame - highlightDelay,
    [0, fps * 0.3, fps * 0.8],
    [0, 0.3, 0.15],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

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
        gap: '0.2em',
      }}
    >
      {parts[0]}
      <span
        style={{
          color: colors.accent,
          display: 'inline-block',
          transform: `scale(${highlightScale})`,
          opacity: highlightOpacity,
          position: 'relative',
        }}
      >
        {/* Glow effect */}
        <span
          style={{
            position: 'absolute',
            inset: '-8px -16px',
            background: colors.accent,
            borderRadius: 8,
            opacity: glowOpacity,
            filter: 'blur(20px)',
            zIndex: -1,
          }}
        />
        {highlight}
      </span>
      {parts[1]}
    </div>
  );
};

// Typewriter effect
interface TypewriterProps {
  text: string;
  delay?: number;
  charsPerFrame?: number;
  cursor?: boolean;
}

export const Typewriter: React.FC<TypewriterProps> = ({
  text,
  delay = 0,
  charsPerFrame = 1.5,
  cursor = true,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const elapsed = Math.max(0, frame - delay);
  const charsToShow = Math.min(Math.floor(elapsed * charsPerFrame), text.length);
  const displayText = text.slice(0, charsToShow);

  // Cursor blink
  const cursorOpacity = cursor
    ? Math.floor((frame - delay) / (fps * 0.4)) % 2 === 0 ? 1 : 0
    : 0;

  const isComplete = charsToShow >= text.length;

  return (
    <span
      style={{
        fontFamily: typography.fonts.mono,
        fontSize: typography.sizes.body,
        color: colors.dark.textPrimary,
      }}
    >
      {displayText}
      {cursor && !isComplete && (
        <span
          style={{
            opacity: cursorOpacity,
            color: colors.accent,
          }}
        >
          |
        </span>
      )}
    </span>
  );
};

export default TextReveal;
