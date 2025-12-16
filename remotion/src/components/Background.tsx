/**
 * Background Components
 *
 * Animated backgrounds for different scenes.
 * Includes gradient, particles, and grid effects.
 */

import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { colors, gradients } from '../lib/theme';

interface BackgroundProps {
  variant?: 'dark' | 'gradient' | 'grid' | 'particles';
  animate?: boolean;
}

export const Background: React.FC<BackgroundProps> = ({
  variant = 'dark',
  animate = true,
}) => {
  switch (variant) {
    case 'gradient':
      return <GradientBackground animate={animate} />;
    case 'grid':
      return <GridBackground animate={animate} />;
    case 'particles':
      return <ParticleBackground />;
    case 'dark':
    default:
      return <DarkBackground animate={animate} />;
  }
};

// Dark warm background with subtle animation
const DarkBackground: React.FC<{ animate: boolean }> = ({ animate }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Subtle pulsing glow
  const glowOpacity = animate
    ? interpolate(
        Math.sin(frame / (fps * 2)),
        [-1, 1],
        [0.3, 0.5]
      )
    : 0.4;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: gradients.darkRadial,
      }}
    >
      {/* Subtle texture */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
          opacity: 0.03,
          mixBlendMode: 'overlay',
        }}
      />

      {/* Copper glow accent */}
      <div
        style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '800px',
          height: '800px',
          borderRadius: '50%',
          background: `radial-gradient(circle, ${colors.accent}15 0%, transparent 70%)`,
          filter: 'blur(80px)',
          opacity: glowOpacity,
        }}
      />
    </div>
  );
};

// Animated gradient background
const GradientBackground: React.FC<{ animate: boolean }> = ({ animate }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Slow rotation of gradient
  const rotation = animate ? (frame / fps) * 10 : 0;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: colors.dark.bgPrimary,
        overflow: 'hidden',
      }}
    >
      {/* Rotating gradient orbs */}
      <div
        style={{
          position: 'absolute',
          top: '-20%',
          left: '-20%',
          width: '140%',
          height: '140%',
          transform: `rotate(${rotation}deg)`,
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: '10%',
            left: '10%',
            width: '500px',
            height: '500px',
            borderRadius: '50%',
            background: `radial-gradient(circle, ${colors.accent}20 0%, transparent 70%)`,
            filter: 'blur(100px)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            bottom: '20%',
            right: '15%',
            width: '400px',
            height: '400px',
            borderRadius: '50%',
            background: `radial-gradient(circle, ${colors.dark.accent}15 0%, transparent 70%)`,
            filter: 'blur(80px)',
          }}
        />
      </div>
    </div>
  );
};

// Grid background for tech feel
const GridBackground: React.FC<{ animate: boolean }> = ({ animate }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Grid animation - subtle pulse on lines
  const gridOpacity = animate
    ? interpolate(
        Math.sin(frame / (fps * 3)),
        [-1, 1],
        [0.05, 0.1]
      )
    : 0.08;

  // Perspective shift
  const perspectiveY = animate
    ? interpolate(frame, [0, fps * 10], [0, -50], { extrapolateRight: 'extend' })
    : 0;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: colors.dark.bgPrimary,
        overflow: 'hidden',
      }}
    >
      {/* Grid pattern */}
      <div
        style={{
          position: 'absolute',
          inset: '-50%',
          backgroundImage: `
            linear-gradient(${colors.dark.border}40 1px, transparent 1px),
            linear-gradient(90deg, ${colors.dark.border}40 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
          opacity: gridOpacity,
          transform: `perspective(1000px) rotateX(60deg) translateY(${perspectiveY}px)`,
          transformOrigin: 'center center',
        }}
      />

      {/* Gradient overlay for depth */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `linear-gradient(180deg, ${colors.dark.bgPrimary} 0%, transparent 30%, transparent 70%, ${colors.dark.bgPrimary} 100%)`,
        }}
      />

      {/* Copper accent glow */}
      <div
        style={{
          position: 'absolute',
          bottom: '-20%',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '100%',
          height: '400px',
          background: `radial-gradient(ellipse at center, ${colors.accent}15 0%, transparent 70%)`,
          filter: 'blur(60px)',
        }}
      />
    </div>
  );
};

// Floating particles background
const ParticleBackground: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Generate deterministic particles
  const particles = React.useMemo(() => {
    const result = [];
    for (let i = 0; i < 30; i++) {
      result.push({
        id: i,
        x: (i * 37) % 100,
        y: (i * 53) % 100,
        size: 2 + (i % 4),
        speed: 0.3 + (i % 5) * 0.1,
        delay: i * 10,
      });
    }
    return result;
  }, []);

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: colors.dark.bgPrimary,
        overflow: 'hidden',
      }}
    >
      {particles.map((particle) => {
        const y = (particle.y + (frame * particle.speed) / fps * 10) % 120 - 10;
        const opacity = interpolate(
          y,
          [-10, 20, 80, 110],
          [0, 0.6, 0.6, 0],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );

        return (
          <div
            key={particle.id}
            style={{
              position: 'absolute',
              left: `${particle.x}%`,
              top: `${y}%`,
              width: particle.size,
              height: particle.size,
              borderRadius: '50%',
              background: particle.id % 3 === 0 ? colors.accent : colors.dark.textMuted,
              opacity: opacity * (particle.id % 3 === 0 ? 0.8 : 0.3),
            }}
          />
        );
      })}

      {/* Gradient overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `radial-gradient(ellipse at center, transparent 0%, ${colors.dark.bgPrimary}80 100%)`,
        }}
      />
    </div>
  );
};

export default Background;
