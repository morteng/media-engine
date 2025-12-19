/**
 * Overlay Components - Professional video overlays
 *
 * Vignette, highlights, callouts, and focus effects for
 * directing viewer attention.
 */

import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';
import { colors, gradients, glows, typography } from '../../lib/theme';

// ============================================================================
// Vignette - Darken edges to focus attention
// ============================================================================

interface VignetteProps {
  intensity?: number;  // 0-1
  color?: string;
  style?: 'soft' | 'hard' | 'oval';
}

export const Vignette: React.FC<VignetteProps> = ({
  intensity = 0.5,
  color = 'black',
  style = 'soft',
}) => {
  const spread = style === 'hard' ? '40%' : style === 'oval' ? '60%' : '50%';
  const blur = style === 'hard' ? '20%' : '30%';

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: `radial-gradient(ellipse at center, transparent ${spread}, ${color} 100%)`,
        opacity: intensity,
        pointerEvents: 'none',
      }}
    />
  );
};

// ============================================================================
// Highlight Box - Glow around a region
// ============================================================================

interface HighlightBoxProps {
  x: number;
  y: number;
  width: number;
  height: number;
  color?: string;
  style?: 'glow' | 'border' | 'pulse';
  delay?: number;
  borderRadius?: number;
}

export const HighlightBox: React.FC<HighlightBoxProps> = ({
  x,
  y,
  width,
  height,
  color = colors.accent,
  style = 'glow',
  delay = 0,
  borderRadius = 8,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
    frame: frame - delay,
    fps,
    config: { damping: 12, stiffness: 100, mass: 0.5 },
  });

  const opacity = interpolate(frame - delay, [0, 10], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const pulseOpacity = style === 'pulse'
    ? 0.5 + Math.sin((frame - delay) * 0.15) * 0.3
    : 1;

  const baseStyle: React.CSSProperties = {
    position: 'absolute',
    left: x,
    top: y,
    width,
    height,
    borderRadius,
    transform: `scale(${Math.max(0, scale)})`,
    opacity: opacity * pulseOpacity,
    pointerEvents: 'none',
  };

  if (style === 'glow') {
    return (
      <div
        style={{
          ...baseStyle,
          border: `3px solid ${color}`,
          boxShadow: `0 0 20px ${color}, 0 0 40px ${color}66, inset 0 0 20px ${color}33`,
        }}
      />
    );
  }

  if (style === 'border') {
    return (
      <div
        style={{
          ...baseStyle,
          border: `3px solid ${color}`,
        }}
      />
    );
  }

  // Pulse style
  return (
    <>
      <div
        style={{
          ...baseStyle,
          border: `2px solid ${color}`,
          boxShadow: `0 0 ${20 * pulseOpacity}px ${color}`,
        }}
      />
      <div
        style={{
          ...baseStyle,
          transform: `scale(${Math.max(0, scale) * (1 + (1 - pulseOpacity) * 0.1)})`,
          border: `1px solid ${color}44`,
        }}
      />
    </>
  );
};

// ============================================================================
// Callout - Annotation bubble
// ============================================================================

interface CalloutProps {
  text: string;
  x: number;
  y: number;
  position?: 'top' | 'bottom' | 'left' | 'right';
  color?: string;
  delay?: number;
}

export const Callout: React.FC<CalloutProps> = ({
  text,
  x,
  y,
  position = 'top',
  color = colors.accent,
  delay = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
    frame: frame - delay,
    fps,
    config: { damping: 10, stiffness: 150, mass: 0.4 },
  });

  const opacity = interpolate(frame - delay, [0, 15], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Calculate offset based on position
  const offsets = {
    top: { transform: 'translateX(-50%) translateY(-100%)', marginTop: -10 },
    bottom: { transform: 'translateX(-50%) translateY(0)', marginTop: 10 },
    left: { transform: 'translateX(-100%) translateY(-50%)', marginLeft: -10 },
    right: { transform: 'translateX(0) translateY(-50%)', marginLeft: 10 },
  };

  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        ...offsets[position],
        transform: `${offsets[position].transform} scale(${Math.max(0, scale)})`,
        opacity,
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          background: colors.dark.bgSecondary,
          border: `2px solid ${color}`,
          borderRadius: 12,
          padding: '12px 20px',
          boxShadow: `0 0 20px ${color}44, 0 4px 20px rgba(0,0,0,0.4)`,
        }}
      >
        <span
          style={{
            fontFamily: typography.fonts.body,
            fontSize: typography.sizes.body,
            fontWeight: typography.weights.medium,
            color: colors.dark.textPrimary,
            whiteSpace: 'nowrap',
          }}
        >
          {text}
        </span>
      </div>
    </div>
  );
};

// ============================================================================
// Focus Mask - Blur/dim everything except focus area
// ============================================================================

interface FocusMaskProps {
  focusX: number;
  focusY: number;
  focusWidth: number;
  focusHeight: number;
  blurAmount?: number;
  dimAmount?: number;
  borderRadius?: number;
}

export const FocusMask: React.FC<FocusMaskProps> = ({
  focusX,
  focusY,
  focusWidth,
  focusHeight,
  blurAmount = 8,
  dimAmount = 0.6,
  borderRadius = 16,
}) => {
  // Create a mask that shows the focus area clearly
  const maskId = `focus-mask-${focusX}-${focusY}`;

  return (
    <>
      {/* SVG mask definition */}
      <svg style={{ position: 'absolute', width: 0, height: 0 }}>
        <defs>
          <mask id={maskId}>
            <rect width="100%" height="100%" fill="white" />
            <rect
              x={focusX}
              y={focusY}
              width={focusWidth}
              height={focusHeight}
              rx={borderRadius}
              fill="black"
            />
          </mask>
        </defs>
      </svg>

      {/* Dimmed overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `rgba(0, 0, 0, ${dimAmount})`,
          mask: `url(#${maskId})`,
          WebkitMask: `url(#${maskId})`,
          pointerEvents: 'none',
        }}
      />

      {/* Focus border */}
      <div
        style={{
          position: 'absolute',
          left: focusX - 2,
          top: focusY - 2,
          width: focusWidth + 4,
          height: focusHeight + 4,
          borderRadius: borderRadius + 2,
          border: `2px solid ${colors.accent}44`,
          boxShadow: `0 0 30px ${colors.accent}22`,
          pointerEvents: 'none',
        }}
      />
    </>
  );
};

// ============================================================================
// Animated Cursor
// ============================================================================

interface CursorProps {
  x: number;
  y: number;
  clicking?: boolean;
  delay?: number;
}

export const Cursor: React.FC<CursorProps> = ({
  x,
  y,
  clicking = false,
  delay = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = interpolate(frame - delay, [0, 10], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const clickScale = clicking ? 0.9 : 1;
  const clickRing = clicking ? (
    <div
      style={{
        position: 'absolute',
        left: -15,
        top: -15,
        width: 50,
        height: 50,
        borderRadius: '50%',
        border: `2px solid ${colors.accent}`,
        opacity: 0.5,
        animation: 'pulse 0.3s ease-out',
      }}
    />
  ) : null;

  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        opacity,
        transform: `scale(${clickScale})`,
        pointerEvents: 'none',
        zIndex: 1000,
      }}
    >
      {clickRing}
      {/* Cursor SVG */}
      <svg
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        style={{ filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.5))' }}
      >
        <path
          d="M5 3L19 12L12 13L9 20L5 3Z"
          fill="white"
          stroke={colors.dark.bgPrimary}
          strokeWidth="2"
        />
      </svg>
    </div>
  );
};

// ============================================================================
// Progress Indicator
// ============================================================================

interface ProgressIndicatorProps {
  progress: number;  // 0-1
  segments?: number;
  currentSegment?: number;
  color?: string;
}

export const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
  progress,
  segments = 1,
  currentSegment = 0,
  color = colors.accent,
}) => {
  return (
    <div
      style={{
        position: 'absolute',
        bottom: 40,
        left: 80,
        right: 80,
        height: 4,
        background: colors.dark.bgTertiary,
        borderRadius: 2,
      }}
    >
      <div
        style={{
          height: '100%',
          width: `${progress * 100}%`,
          background: gradients.aurora,
          borderRadius: 2,
          boxShadow: glows.cyan,
          transition: 'width 0.1s linear',
        }}
      />

      {/* Segment markers */}
      {segments > 1 && Array.from({ length: segments - 1 }).map((_, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: `${((i + 1) / segments) * 100}%`,
            top: -2,
            width: 2,
            height: 8,
            background: colors.dark.textMuted,
            borderRadius: 1,
          }}
        />
      ))}
    </div>
  );
};

// ============================================================================
// Screen Chrome - Device frame
// ============================================================================

interface ScreenChromeProps {
  children: React.ReactNode;
  type?: 'browser' | 'desktop' | 'none';
  title?: string;
}

export const ScreenChrome: React.FC<ScreenChromeProps> = ({
  children,
  type = 'browser',
  title = 'Media Engine Dashboard',
}) => {
  if (type === 'none') {
    return <>{children}</>;
  }

  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        height: '100%',
        background: colors.dark.bgSecondary,
        borderRadius: 12,
        overflow: 'hidden',
        boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
      }}
    >
      {/* Title bar */}
      <div
        style={{
          height: 40,
          background: colors.dark.bgTertiary,
          display: 'flex',
          alignItems: 'center',
          padding: '0 16px',
          gap: 8,
        }}
      >
        {/* Traffic lights */}
        <div style={{ display: 'flex', gap: 8 }}>
          <div style={{ width: 12, height: 12, borderRadius: '50%', background: colors.accentHot }} />
          <div style={{ width: 12, height: 12, borderRadius: '50%', background: colors.warning }} />
          <div style={{ width: 12, height: 12, borderRadius: '50%', background: colors.success }} />
        </div>

        {/* Title */}
        <div
          style={{
            flex: 1,
            textAlign: 'center',
            fontFamily: typography.fonts.body,
            fontSize: 13,
            color: colors.dark.textMuted,
          }}
        >
          {title}
        </div>

        <div style={{ width: 60 }} />
      </div>

      {/* Content */}
      <div style={{ position: 'relative', height: 'calc(100% - 40px)', overflow: 'hidden' }}>
        {children}
      </div>
    </div>
  );
};

export default {
  Vignette,
  HighlightBox,
  Callout,
  FocusMask,
  Cursor,
  ProgressIndicator,
  ScreenChrome,
};
