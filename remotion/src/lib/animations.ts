/**
 * Animation utilities for Remotion
 *
 * Custom easing functions and interpolation helpers
 */

import { interpolate, Easing } from 'remotion';

// Custom easing functions
export const ease = {
  // Smooth professional easing
  smooth: (t: number) => {
    return t < 0.5
      ? 4 * t * t * t
      : 1 - Math.pow(-2 * t + 2, 3) / 2;
  },

  // Elegant ease out
  elegantOut: (t: number) => {
    return 1 - Math.pow(1 - t, 4);
  },

  // Subtle bounce for emphasis
  subtleBounce: (t: number) => {
    const c4 = (2 * Math.PI) / 3;
    return t === 0 ? 0
      : t === 1 ? 1
      : Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * c4) + 1;
  },

  // Spring-like motion
  spring: (t: number) => {
    return 1 - Math.cos(t * Math.PI * 0.5) * Math.exp(-t * 3);
  },
};

// Animation presets
export const presets = {
  // Fade in from bottom
  fadeInUp: (frame: number, delay: number = 0, duration: number = 20) => ({
    opacity: interpolate(
      frame - delay,
      [0, duration],
      [0, 1],
      { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
    ),
    transform: `translateY(${interpolate(
      frame - delay,
      [0, duration],
      [30, 0],
      { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
    )}px)`,
  }),

  // Fade in from left
  fadeInLeft: (frame: number, delay: number = 0, duration: number = 20) => ({
    opacity: interpolate(
      frame - delay,
      [0, duration],
      [0, 1],
      { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
    ),
    transform: `translateX(${interpolate(
      frame - delay,
      [0, duration],
      [-50, 0],
      { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
    )}px)`,
  }),

  // Scale in
  scaleIn: (frame: number, delay: number = 0, duration: number = 15) => ({
    opacity: interpolate(
      frame - delay,
      [0, duration * 0.5],
      [0, 1],
      { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
    ),
    transform: `scale(${interpolate(
      frame - delay,
      [0, duration],
      [0.8, 1],
      { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.back(1.5)) }
    )})`,
  }),

  // Fade out
  fadeOut: (frame: number, startFrame: number, duration: number = 15) => ({
    opacity: interpolate(
      frame,
      [startFrame, startFrame + duration],
      [1, 0],
      { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
    ),
  }),
};

// Count animation for stat counters
export function animateCount(
  frame: number,
  delay: number,
  duration: number,
  targetValue: number,
  startValue: number = 0
): number {
  const progress = interpolate(
    frame - delay,
    [0, duration],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

  return Math.round(startValue + (targetValue - startValue) * progress);
}

// Stagger animation helper
export function getStaggerDelay(index: number, baseDelay: number = 5): number {
  return index * baseDelay;
}

// Character-by-character reveal
export function revealText(
  text: string,
  frame: number,
  delay: number = 0,
  charsPerFrame: number = 2
): string {
  const charsToShow = Math.floor((frame - delay) * charsPerFrame);
  if (charsToShow <= 0) return '';
  if (charsToShow >= text.length) return text;
  return text.slice(0, charsToShow);
}

// Word-by-word reveal
export function revealWords(
  text: string,
  frame: number,
  delay: number = 0,
  framesPerWord: number = 8
): { words: string[]; visibleCount: number } {
  const words = text.split(' ');
  const elapsed = frame - delay;
  const visibleCount = Math.min(
    Math.floor(elapsed / framesPerWord) + 1,
    words.length
  );

  return { words, visibleCount: Math.max(0, visibleCount) };
}
