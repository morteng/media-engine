/**
 * Background Components - Electric Aurora Edition
 *
 * Dynamic, vibrant backgrounds with aurora effects, particles,
 * pulsing grids, and animated gradients.
 */

import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, random } from 'remotion';
import { colors, gradients, particles as particleConfig } from '../lib/theme';

type BackgroundVariant = 'dark' | 'aurora' | 'grid' | 'particles' | 'pulse' | 'cyber' | 'waves';

interface BackgroundProps {
  variant?: BackgroundVariant;
  animate?: boolean;
  intensity?: 'low' | 'medium' | 'high';
}

export const Background: React.FC<BackgroundProps> = ({
  variant = 'dark',
  animate = true,
  intensity = 'medium',
}) => {
  switch (variant) {
    case 'aurora':
      return <AuroraBackground animate={animate} intensity={intensity} />;
    case 'grid':
      return <GridBackground animate={animate} intensity={intensity} />;
    case 'particles':
      return <ParticleBackground intensity={intensity} />;
    case 'pulse':
      return <PulseBackground animate={animate} intensity={intensity} />;
    case 'cyber':
      return <CyberBackground animate={animate} intensity={intensity} />;
    case 'waves':
      return <WaveBackground animate={animate} intensity={intensity} />;
    case 'dark':
    default:
      return <DarkBackground animate={animate} intensity={intensity} />;
  }
};

// Intensity multipliers
const getIntensity = (intensity: 'low' | 'medium' | 'high') => ({
  low: 0.5,
  medium: 1,
  high: 1.5,
}[intensity]);

// Deep space background with aurora glow
const DarkBackground: React.FC<{ animate: boolean; intensity: 'low' | 'medium' | 'high' }> = ({ animate, intensity }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const mult = getIntensity(intensity);

  // Animated glow positions
  const glow1X = animate ? 30 + Math.sin(frame / (fps * 3)) * 10 : 30;
  const glow1Y = animate ? 40 + Math.cos(frame / (fps * 4)) * 10 : 40;
  const glow2X = animate ? 70 + Math.cos(frame / (fps * 2.5)) * 15 : 70;
  const glow2Y = animate ? 60 + Math.sin(frame / (fps * 3.5)) * 10 : 60;

  // Pulsing opacity
  const pulseOpacity = animate
    ? interpolate(Math.sin(frame / (fps * 1.5)), [-1, 1], [0.3 * mult, 0.6 * mult])
    : 0.4 * mult;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: gradients.darkSpace,
        overflow: 'hidden',
      }}
    >
      {/* Noise texture */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
          opacity: 0.04,
          mixBlendMode: 'overlay',
        }}
      />

      {/* Primary cyan glow */}
      <div
        style={{
          position: 'absolute',
          left: `${glow1X}%`,
          top: `${glow1Y}%`,
          transform: 'translate(-50%, -50%)',
          width: '600px',
          height: '600px',
          borderRadius: '50%',
          background: `radial-gradient(circle, ${colors.accent}25 0%, transparent 70%)`,
          filter: 'blur(80px)',
          opacity: pulseOpacity,
        }}
      />

      {/* Secondary purple glow */}
      <div
        style={{
          position: 'absolute',
          left: `${glow2X}%`,
          top: `${glow2Y}%`,
          transform: 'translate(-50%, -50%)',
          width: '500px',
          height: '500px',
          borderRadius: '50%',
          background: `radial-gradient(circle, ${colors.accentSecondary}20 0%, transparent 70%)`,
          filter: 'blur(100px)',
          opacity: pulseOpacity * 0.8,
        }}
      />

      {/* Pink accent bottom */}
      <div
        style={{
          position: 'absolute',
          bottom: '-10%',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '120%',
          height: '300px',
          background: `radial-gradient(ellipse at center, ${colors.accentHot}15 0%, transparent 70%)`,
          filter: 'blur(60px)',
          opacity: pulseOpacity * 0.6,
        }}
      />
    </div>
  );
};

// Full aurora animated background
const AuroraBackground: React.FC<{ animate: boolean; intensity: 'low' | 'medium' | 'high' }> = ({ animate, intensity }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const mult = getIntensity(intensity);

  // Multiple aurora waves with different speeds
  const wave1 = animate ? Math.sin(frame / (fps * 2)) * 30 : 0;
  const wave2 = animate ? Math.cos(frame / (fps * 1.5)) * 25 : 0;
  const wave3 = animate ? Math.sin(frame / (fps * 3) + 1) * 20 : 0;

  // Color cycling
  const colorShift = (frame / fps) * 20;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: colors.dark.bgPrimary,
        overflow: 'hidden',
      }}
    >
      {/* Aurora layer 1 - Cyan */}
      <div
        style={{
          position: 'absolute',
          top: `${20 + wave1}%`,
          left: '-10%',
          width: '120%',
          height: '40%',
          background: `linear-gradient(90deg,
            transparent 0%,
            ${colors.accent}${Math.floor(30 * mult).toString(16).padStart(2, '0')} 20%,
            ${colors.accent}${Math.floor(50 * mult).toString(16).padStart(2, '0')} 50%,
            ${colors.accent}${Math.floor(30 * mult).toString(16).padStart(2, '0')} 80%,
            transparent 100%
          )`,
          filter: 'blur(60px)',
          transform: `skewY(-5deg) translateX(${wave2}px)`,
        }}
      />

      {/* Aurora layer 2 - Purple */}
      <div
        style={{
          position: 'absolute',
          top: `${35 + wave2}%`,
          left: '-10%',
          width: '120%',
          height: '35%',
          background: `linear-gradient(90deg,
            transparent 0%,
            ${colors.accentSecondary}${Math.floor(25 * mult).toString(16).padStart(2, '0')} 30%,
            ${colors.accentSecondary}${Math.floor(40 * mult).toString(16).padStart(2, '0')} 50%,
            ${colors.accentSecondary}${Math.floor(25 * mult).toString(16).padStart(2, '0')} 70%,
            transparent 100%
          )`,
          filter: 'blur(80px)',
          transform: `skewY(3deg) translateX(${-wave1}px)`,
        }}
      />

      {/* Aurora layer 3 - Pink */}
      <div
        style={{
          position: 'absolute',
          top: `${50 + wave3}%`,
          left: '-10%',
          width: '120%',
          height: '30%',
          background: `linear-gradient(90deg,
            transparent 0%,
            ${colors.accentHot}${Math.floor(20 * mult).toString(16).padStart(2, '0')} 25%,
            ${colors.accentHot}${Math.floor(35 * mult).toString(16).padStart(2, '0')} 50%,
            ${colors.accentHot}${Math.floor(20 * mult).toString(16).padStart(2, '0')} 75%,
            transparent 100%
          )`,
          filter: 'blur(70px)',
          transform: `skewY(-2deg) translateX(${wave1 * 0.5}px)`,
        }}
      />

      {/* Star field overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `radial-gradient(2px 2px at 20px 30px, ${colors.primary}88, transparent),
                        radial-gradient(2px 2px at 40px 70px, ${colors.accent}66, transparent),
                        radial-gradient(1px 1px at 90px 40px, ${colors.primary}66, transparent),
                        radial-gradient(2px 2px at 130px 80px, ${colors.accentSecondary}66, transparent),
                        radial-gradient(1px 1px at 160px 30px, ${colors.primary}88, transparent)`,
          backgroundSize: '200px 100px',
        }}
      />
    </div>
  );
};

// Cyber grid with perspective and scanning line
const GridBackground: React.FC<{ animate: boolean; intensity: 'low' | 'medium' | 'high' }> = ({ animate, intensity }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const mult = getIntensity(intensity);

  // Grid animation
  const gridOpacity = animate
    ? interpolate(Math.sin(frame / (fps * 2)), [-1, 1], [0.08 * mult, 0.15 * mult])
    : 0.1 * mult;

  // Continuous grid scroll
  const gridY = animate ? (frame * 0.5) % 60 : 0;

  // Scan line position
  const scanY = animate ? ((frame * 3) % 120) - 10 : -10;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: colors.dark.bgPrimary,
        overflow: 'hidden',
      }}
    >
      {/* Perspective grid */}
      <div
        style={{
          position: 'absolute',
          inset: '-100%',
          backgroundImage: `
            linear-gradient(${colors.accent}${Math.floor(gridOpacity * 255).toString(16).padStart(2, '0')} 1px, transparent 1px),
            linear-gradient(90deg, ${colors.accent}${Math.floor(gridOpacity * 255).toString(16).padStart(2, '0')} 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
          backgroundPosition: `0 ${gridY}px`,
          transform: 'perspective(500px) rotateX(60deg)',
          transformOrigin: 'center 100%',
        }}
      />

      {/* Horizontal grid lines for variety */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `linear-gradient(0deg, ${colors.accentSecondary}08 1px, transparent 1px)`,
          backgroundSize: '100% 80px',
        }}
      />

      {/* Scan line */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: `${scanY}%`,
          height: '2px',
          background: gradients.aurora,
          boxShadow: `0 0 20px ${colors.accent}, 0 0 40px ${colors.accent}`,
          opacity: 0.8,
        }}
      />

      {/* Depth gradient */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `linear-gradient(180deg,
            ${colors.dark.bgPrimary} 0%,
            transparent 20%,
            transparent 60%,
            ${colors.dark.bgPrimary} 100%
          )`,
        }}
      />

      {/* Center glow */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: '50%',
          transform: 'translateX(-50%)',
          width: '100%',
          height: '50%',
          background: `radial-gradient(ellipse at center bottom, ${colors.accent}15 0%, transparent 70%)`,
          filter: 'blur(40px)',
        }}
      />
    </div>
  );
};

// Dynamic particle system
const ParticleBackground: React.FC<{ intensity: 'low' | 'medium' | 'high' }> = ({ intensity }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const mult = getIntensity(intensity);

  const particleCount = Math.floor(particleConfig.count * mult);

  // Generate particles with deterministic random
  const particles = React.useMemo(() => {
    const result = [];
    for (let i = 0; i < particleCount; i++) {
      const seed = `particle-${i}`;
      result.push({
        id: i,
        x: random(seed + '-x') * 100,
        y: random(seed + '-y') * 100,
        size: particleConfig.sizeRange[0] + random(seed + '-size') * (particleConfig.sizeRange[1] - particleConfig.sizeRange[0]),
        speed: particleConfig.speedRange[0] + random(seed + '-speed') * (particleConfig.speedRange[1] - particleConfig.speedRange[0]),
        color: particleConfig.colors[Math.floor(random(seed + '-color') * particleConfig.colors.length)],
        opacity: particleConfig.opacityRange[0] + random(seed + '-opacity') * (particleConfig.opacityRange[1] - particleConfig.opacityRange[0]),
        oscillation: random(seed + '-osc') * 3,
      });
    }
    return result;
  }, [particleCount]);

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: gradients.darkPurple,
        overflow: 'hidden',
      }}
    >
      {particles.map((particle) => {
        // Continuous upward movement with wrap
        const baseY = (particle.y + (frame * particle.speed) / fps * 15) % 120 - 10;
        // Horizontal oscillation
        const xOffset = Math.sin((frame / fps) * particle.oscillation + particle.id) * 20;

        const opacity = interpolate(
          baseY,
          [-10, 15, 85, 110],
          [0, particle.opacity, particle.opacity, 0],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );

        return (
          <div
            key={particle.id}
            style={{
              position: 'absolute',
              left: `calc(${particle.x}% + ${xOffset}px)`,
              top: `${baseY}%`,
              width: particle.size,
              height: particle.size,
              borderRadius: '50%',
              background: particle.color,
              boxShadow: `0 0 ${particle.size * 2}px ${particle.color}`,
              opacity,
            }}
          />
        );
      })}

      {/* Gradient overlay for depth */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `radial-gradient(ellipse at center, transparent 0%, ${colors.dark.bgPrimary}60 100%)`,
        }}
      />
    </div>
  );
};

// Pulsing concentric circles
const PulseBackground: React.FC<{ animate: boolean; intensity: 'low' | 'medium' | 'high' }> = ({ animate, intensity }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const mult = getIntensity(intensity);

  const rings = 5;
  const ringElements = [];

  for (let i = 0; i < rings; i++) {
    const delay = i * (fps * 0.3);
    const progress = animate ? ((frame - delay) / (fps * 2)) % 1 : 0;
    const scale = progress * 3;
    const opacity = interpolate(progress, [0, 0.2, 0.8, 1], [0, 0.5 * mult, 0.3 * mult, 0]);

    if (progress > 0) {
      ringElements.push(
        <div
          key={i}
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: `translate(-50%, -50%) scale(${scale})`,
            width: '400px',
            height: '400px',
            borderRadius: '50%',
            border: `2px solid ${[colors.accent, colors.accentSecondary, colors.accentHot][i % 3]}`,
            boxShadow: `0 0 20px ${[colors.accent, colors.accentSecondary, colors.accentHot][i % 3]}44`,
            opacity,
          }}
        />
      );
    }
  }

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: colors.dark.bgPrimary,
        overflow: 'hidden',
      }}
    >
      {ringElements}

      {/* Center glow */}
      <div
        style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '200px',
          height: '200px',
          borderRadius: '50%',
          background: `radial-gradient(circle, ${colors.accent}40 0%, transparent 70%)`,
          filter: 'blur(30px)',
        }}
      />
    </div>
  );
};

// Cyberpunk style with hex grid and glowing lines
const CyberBackground: React.FC<{ animate: boolean; intensity: 'low' | 'medium' | 'high' }> = ({ animate, intensity }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const mult = getIntensity(intensity);

  // Scanning beam
  const beamX = animate ? ((frame * 2) % 140) - 20 : -20;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: colors.dark.bgPrimary,
        overflow: 'hidden',
      }}
    >
      {/* Hex pattern */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='28' height='49'%3E%3Cpath d='M14 0l14 24.5L14 49 0 24.5z' fill='none' stroke='%23${colors.accent.slice(1)}22' stroke-width='0.5'/%3E%3C/svg%3E")`,
          backgroundSize: '28px 49px',
          opacity: 0.5 * mult,
        }}
      />

      {/* Diagonal lines */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `repeating-linear-gradient(
            45deg,
            transparent,
            transparent 100px,
            ${colors.accentSecondary}08 100px,
            ${colors.accentSecondary}08 101px
          )`,
        }}
      />

      {/* Vertical beam */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          bottom: 0,
          left: `${beamX}%`,
          width: '3px',
          background: gradients.aurora,
          boxShadow: `0 0 30px ${colors.accent}, 0 0 60px ${colors.accentSecondary}`,
          opacity: 0.7,
        }}
      />

      {/* Corner accents */}
      <div
        style={{
          position: 'absolute',
          top: 40,
          left: 40,
          width: '100px',
          height: '100px',
          borderLeft: `2px solid ${colors.accent}`,
          borderTop: `2px solid ${colors.accent}`,
          boxShadow: `-5px -5px 20px ${colors.accent}44`,
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: 40,
          right: 40,
          width: '100px',
          height: '100px',
          borderRight: `2px solid ${colors.accentHot}`,
          borderBottom: `2px solid ${colors.accentHot}`,
          boxShadow: `5px 5px 20px ${colors.accentHot}44`,
        }}
      />

      {/* Bottom glow */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: '200px',
          background: `linear-gradient(0deg, ${colors.accentSecondary}20 0%, transparent 100%)`,
        }}
      />
    </div>
  );
};

// Animated wave background
const WaveBackground: React.FC<{ animate: boolean; intensity: 'low' | 'medium' | 'high' }> = ({ animate, intensity }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const mult = getIntensity(intensity);

  // Generate wave paths
  const generateWave = (offset: number, amplitude: number, frequency: number) => {
    const points = [];
    for (let x = 0; x <= 100; x += 2) {
      const y = 50 + Math.sin((x * frequency + (animate ? frame / fps * 30 : 0) + offset) * 0.1) * amplitude;
      points.push(`${x}% ${y}%`);
    }
    return `polygon(0% 100%, ${points.join(', ')}, 100% 100%)`;
  };

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: colors.dark.bgPrimary,
        overflow: 'hidden',
      }}
    >
      {/* Wave layer 1 */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `linear-gradient(180deg, ${colors.accent}30 0%, ${colors.accent}10 100%)`,
          clipPath: generateWave(0, 15 * mult, 1),
          opacity: 0.6,
        }}
      />

      {/* Wave layer 2 */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `linear-gradient(180deg, ${colors.accentSecondary}25 0%, ${colors.accentSecondary}08 100%)`,
          clipPath: generateWave(50, 12 * mult, 1.3),
          opacity: 0.5,
        }}
      />

      {/* Wave layer 3 */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `linear-gradient(180deg, ${colors.accentHot}20 0%, ${colors.accentHot}05 100%)`,
          clipPath: generateWave(100, 10 * mult, 1.6),
          opacity: 0.4,
        }}
      />

      {/* Top glow */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '300px',
          background: `radial-gradient(ellipse at center top, ${colors.accent}15 0%, transparent 70%)`,
          filter: 'blur(40px)',
        }}
      />
    </div>
  );
};

export default Background;
