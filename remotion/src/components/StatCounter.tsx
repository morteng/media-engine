/**
 * StatCounter Component
 *
 * Animated statistic counter with count-up effect.
 * Supports percentages, time, and multiplier formats.
 */

import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, Easing } from 'remotion';
import { colors, typography } from '../lib/theme';
import { animateCount } from '../lib/animations';

interface StatCounterProps {
  value: number;
  suffix?: string;
  prefix?: string;
  label: string;
  delay?: number;
  duration?: number;
  size?: 'small' | 'medium' | 'large';
  color?: string;
}

export const StatCounter: React.FC<StatCounterProps> = ({
  value,
  suffix = '',
  prefix = '',
  label,
  delay = 0,
  duration,
  size = 'large',
  color = colors.accent,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const countDuration = duration || fps * 1.5; // 1.5 seconds default

  // Animated value
  const displayValue = animateCount(frame, delay, countDuration, value);

  // Container animation
  const containerOpacity = interpolate(
    frame - delay,
    [0, fps * 0.3],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const containerY = interpolate(
    frame - delay,
    [0, fps * 0.5],
    [30, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

  // Scale pop effect when count completes
  const countProgress = interpolate(
    frame - delay,
    [0, countDuration],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const scale = countProgress >= 1
    ? interpolate(
        frame - delay - countDuration,
        [0, fps * 0.2, fps * 0.4],
        [1, 1.05, 1],
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
      )
    : 1;

  // Label animation (delayed)
  const labelOpacity = interpolate(
    frame - delay - fps * 0.3,
    [0, fps * 0.3],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const labelY = interpolate(
    frame - delay - fps * 0.3,
    [0, fps * 0.4],
    [10, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

  // Size configurations
  const sizes = {
    small: { number: 48, label: 14, gap: 8 },
    medium: { number: 72, label: 18, gap: 12 },
    large: { number: 120, label: 24, gap: 16 },
  };

  const sizeConfig = sizes[size];

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        opacity: containerOpacity,
        transform: `translateY(${containerY}px) scale(${scale})`,
      }}
    >
      {/* Number with suffix */}
      <div
        style={{
          display: 'flex',
          alignItems: 'baseline',
          gap: 8,
        }}
      >
        {prefix && (
          <span
            style={{
              fontFamily: typography.fonts.body,
              fontSize: sizeConfig.number * 0.5,
              fontWeight: typography.weights.light,
              color: colors.dark.textSecondary,
            }}
          >
            {prefix}
          </span>
        )}
        <span
          style={{
            fontFamily: typography.fonts.heading,
            fontSize: sizeConfig.number,
            fontWeight: typography.weights.bold,
            color,
            lineHeight: 1,
            textShadow: `0 4px 20px ${color}44`,
          }}
        >
          {displayValue}
        </span>
        <span
          style={{
            fontFamily: typography.fonts.body,
            fontSize: sizeConfig.number * 0.4,
            fontWeight: typography.weights.semibold,
            color,
            opacity: 0.9,
          }}
        >
          {suffix}
        </span>
      </div>

      {/* Label */}
      <span
        style={{
          fontFamily: typography.fonts.body,
          fontSize: sizeConfig.label,
          fontWeight: typography.weights.medium,
          color: colors.dark.textSecondary,
          marginTop: sizeConfig.gap,
          textTransform: 'uppercase',
          letterSpacing: '0.15em',
          opacity: labelOpacity,
          transform: `translateY(${labelY}px)`,
        }}
      >
        {label}
      </span>
    </div>
  );
};

// Grid of multiple stats
interface StatGridProps {
  stats: Array<{
    value: number;
    suffix?: string;
    prefix?: string;
    label: string;
  }>;
  staggerDelay?: number;
}

export const StatGrid: React.FC<StatGridProps> = ({
  stats,
  staggerDelay = 10,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Container fade in
  const containerOpacity = interpolate(
    frame,
    [0, fps * 0.3],
    [0, 1],
    { extrapolateRight: 'clamp' }
  );

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        gap: 100,
        opacity: containerOpacity,
      }}
    >
      {stats.map((stat, index) => (
        <StatCounter
          key={stat.label}
          {...stat}
          delay={index * staggerDelay}
          size="large"
        />
      ))}
    </div>
  );
};

export default StatCounter;
