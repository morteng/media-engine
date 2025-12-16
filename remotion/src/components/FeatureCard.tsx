/**
 * FeatureCard Component
 *
 * Animated feature showcase card with icon, title, and description.
 * Designed for the MVP features section.
 */

import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, Easing } from 'remotion';
import { colors, typography, icons } from '../lib/theme';

interface FeatureCardProps {
  icon: keyof typeof icons;
  title: string;
  description: string;
  delay?: number;
  index?: number;
}

export const FeatureCard: React.FC<FeatureCardProps> = ({
  icon,
  title,
  description,
  delay = 0,
  index = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Card entrance animation
  const cardOpacity = interpolate(
    frame - delay,
    [0, fps * 0.4],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const cardX = interpolate(
    frame - delay,
    [0, fps * 0.6],
    [-40, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

  const cardScale = interpolate(
    frame - delay,
    [0, fps * 0.5],
    [0.95, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

  // Icon animation (bounce in)
  const iconScale = interpolate(
    frame - delay - fps * 0.1,
    [0, fps * 0.3, fps * 0.45],
    [0, 1.15, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const iconRotation = interpolate(
    frame - delay - fps * 0.1,
    [0, fps * 0.4],
    [-10, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

  // Title animation
  const titleOpacity = interpolate(
    frame - delay - fps * 0.2,
    [0, fps * 0.3],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const titleX = interpolate(
    frame - delay - fps * 0.2,
    [0, fps * 0.4],
    [20, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

  // Description animation (word by word feel through opacity)
  const descOpacity = interpolate(
    frame - delay - fps * 0.4,
    [0, fps * 0.5],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Accent line animation
  const lineWidth = interpolate(
    frame - delay - fps * 0.3,
    [0, fps * 0.5],
    [0, 60],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

  const iconPath = icons[icon] || icons.check;

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: 32,
        padding: 40,
        background: `${colors.dark.bgSecondary}cc`,
        borderRadius: 20,
        border: `1px solid ${colors.dark.border}`,
        backdropFilter: 'blur(10px)',
        opacity: cardOpacity,
        transform: `translateX(${cardX}px) scale(${cardScale})`,
        width: 580,
      }}
    >
      {/* Icon container */}
      <div
        style={{
          width: 80,
          height: 80,
          borderRadius: 20,
          background: `linear-gradient(135deg, ${colors.accent}22 0%, ${colors.accent}11 100%)`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          transform: `scale(${iconScale}) rotate(${iconRotation}deg)`,
        }}
      >
        <svg
          width="40"
          height="40"
          viewBox="0 0 24 24"
          fill="none"
          stroke={colors.accent}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d={iconPath} />
        </svg>
      </div>

      {/* Content */}
      <div style={{ flex: 1 }}>
        <h3
          style={{
            fontFamily: typography.fonts.heading,
            fontSize: typography.sizes.h3,
            fontWeight: typography.weights.semibold,
            color: colors.dark.textPrimary,
            margin: 0,
            marginBottom: 12,
            opacity: titleOpacity,
            transform: `translateX(${titleX}px)`,
          }}
        >
          {title}
        </h3>

        {/* Accent line */}
        <div
          style={{
            width: lineWidth,
            height: 3,
            background: colors.accent,
            borderRadius: 2,
            marginBottom: 16,
          }}
        />

        <p
          style={{
            fontFamily: typography.fonts.body,
            fontSize: typography.sizes.h4,
            fontWeight: typography.weights.normal,
            color: colors.dark.textSecondary,
            margin: 0,
            lineHeight: 1.6,
            opacity: descOpacity,
          }}
        >
          {description}
        </p>
      </div>
    </div>
  );
};

// Feature list with staggered animations
interface FeatureListProps {
  features: Array<{
    icon: keyof typeof icons;
    title: string;
    description: string;
  }>;
  staggerDelay?: number;
}

export const FeatureList: React.FC<FeatureListProps> = ({
  features,
  staggerDelay = 15,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 24,
      }}
    >
      {features.map((feature, index) => (
        <FeatureCard
          key={feature.title}
          {...feature}
          delay={index * staggerDelay}
          index={index}
        />
      ))}
    </div>
  );
};

export default FeatureCard;
