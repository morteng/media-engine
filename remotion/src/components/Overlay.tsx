/**
 * Overlay Components
 *
 * Text overlays for video: stat counters, callouts, lower thirds.
 * Designed to layer on top of demo footage or motion graphics.
 */

import React from 'react';
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Easing,
  spring,
} from 'remotion';
import { colors, typography, gradients } from '../lib/theme';

type OverlayType = 'stat' | 'callout' | 'lower_third';
type OverlayPosition = 'center' | 'bottom' | 'bottom-right' | 'top-right' | 'top-left';
type OverlayAnimation = 'scale' | 'slide_up' | 'fade_in' | 'word-by-word';
type OverlayColor = 'copper' | 'cream' | 'espresso';

interface OverlayProps {
  type: OverlayType;
  text: string;
  label?: string;
  position?: OverlayPosition;
  animation?: OverlayAnimation;
  delay?: number; // frames
  duration?: number; // frames
  fontSize?: number;
  color?: OverlayColor;
}

const colorMap: Record<OverlayColor, string> = {
  copper: colors.accent,
  cream: colors.bgPrimary,
  espresso: colors.primary,
};

const positionStyles: Record<OverlayPosition, React.CSSProperties> = {
  center: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    textAlign: 'center',
  },
  bottom: {
    position: 'absolute',
    bottom: 80,
    left: '50%',
    transform: 'translateX(-50%)',
    textAlign: 'center',
  },
  'bottom-right': {
    position: 'absolute',
    bottom: 80,
    right: 80,
    textAlign: 'right',
  },
  'top-right': {
    position: 'absolute',
    top: 80,
    right: 80,
    textAlign: 'right',
  },
  'top-left': {
    position: 'absolute',
    top: 80,
    left: 80,
    textAlign: 'left',
  },
};

export const Overlay: React.FC<OverlayProps> = ({
  type,
  text,
  label,
  position = 'center',
  animation = 'fade_in',
  delay = 0,
  duration,
  fontSize,
  color = 'copper',
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const effectiveDuration = duration ?? durationInFrames;
  const adjustedFrame = frame - delay;

  // Calculate opacity for fade in/out
  const fadeInDuration = fps * 0.4;
  const fadeOutDuration = fps * 0.3;

  const opacity = interpolate(
    adjustedFrame,
    [0, fadeInDuration, effectiveDuration - fadeOutDuration, effectiveDuration],
    [0, 1, 1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  if (adjustedFrame < 0 || adjustedFrame > effectiveDuration) {
    return null;
  }

  switch (type) {
    case 'stat':
      return (
        <StatOverlay
          text={text}
          label={label}
          position={position}
          animation={animation}
          adjustedFrame={adjustedFrame}
          opacity={opacity}
          fontSize={fontSize}
          color={colorMap[color]}
        />
      );
    case 'callout':
      return (
        <CalloutOverlay
          text={text}
          position={position}
          animation={animation}
          adjustedFrame={adjustedFrame}
          opacity={opacity}
          fontSize={fontSize}
          color={colorMap[color]}
        />
      );
    case 'lower_third':
      return (
        <LowerThirdOverlay
          text={text}
          label={label}
          position={position}
          adjustedFrame={adjustedFrame}
          opacity={opacity}
          fontSize={fontSize}
          color={colorMap[color]}
        />
      );
    default:
      return null;
  }
};

// Stat overlay - big number with optional label
interface StatOverlayProps {
  text: string;
  label?: string;
  position: OverlayPosition;
  animation: OverlayAnimation;
  adjustedFrame: number;
  opacity: number;
  fontSize?: number;
  color: string;
}

const StatOverlay: React.FC<StatOverlayProps> = ({
  text,
  label,
  position,
  animation,
  adjustedFrame,
  opacity,
  fontSize = 120,
  color,
}) => {
  const { fps } = useVideoConfig();

  // Scale animation
  const scale = animation === 'scale'
    ? spring({
        frame: adjustedFrame,
        fps,
        config: {
          damping: 12,
          stiffness: 100,
          mass: 0.5,
        },
      })
    : 1;

  // Slide up animation
  const translateY = animation === 'slide_up'
    ? interpolate(
        adjustedFrame,
        [0, fps * 0.4],
        [40, 0],
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
      )
    : 0;

  return (
    <div
      style={{
        ...positionStyles[position],
        opacity,
        transform: `${positionStyles[position].transform ?? ''} scale(${scale}) translateY(${translateY}px)`,
        zIndex: 100,
      }}
    >
      {/* Glow effect behind stat */}
      <div
        style={{
          position: 'absolute',
          inset: -40,
          background: `radial-gradient(ellipse at center, ${color}22 0%, transparent 70%)`,
          filter: 'blur(20px)',
        }}
      />

      {/* Stat number */}
      <div
        style={{
          fontFamily: typography.fonts.heading,
          fontSize,
          fontWeight: typography.weights.bold,
          color,
          textShadow: `0 4px 20px ${color}44`,
          position: 'relative',
        }}
      >
        {text}
      </div>

      {/* Label below */}
      {label && (
        <div
          style={{
            fontFamily: typography.fonts.body,
            fontSize: fontSize * 0.2,
            fontWeight: typography.weights.medium,
            color: colors.dark.textSecondary,
            marginTop: 8,
            textTransform: 'uppercase',
            letterSpacing: '0.15em',
            opacity: interpolate(
              adjustedFrame,
              [fps * 0.3, fps * 0.6],
              [0, 1],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
            ),
          }}
        >
          {label}
        </div>
      )}
    </div>
  );
};

// Callout overlay - emphasized text
interface CalloutOverlayProps {
  text: string;
  position: OverlayPosition;
  animation: OverlayAnimation;
  adjustedFrame: number;
  opacity: number;
  fontSize?: number;
  color: string;
}

const CalloutOverlay: React.FC<CalloutOverlayProps> = ({
  text,
  position,
  animation,
  adjustedFrame,
  opacity,
  fontSize = 48,
  color,
}) => {
  const { fps } = useVideoConfig();

  // Word by word reveal
  const words = text.split(' ');
  const framesPerWord = Math.floor(fps * 0.15);

  // Slide up animation
  const translateY = animation === 'slide_up'
    ? interpolate(
        adjustedFrame,
        [0, fps * 0.4],
        [30, 0],
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
      )
    : 0;

  return (
    <div
      style={{
        ...positionStyles[position],
        opacity,
        transform: `${positionStyles[position].transform ?? ''} translateY(${translateY}px)`,
        zIndex: 100,
        padding: '24px 48px',
        background: position === 'bottom' || position.includes('right')
          ? `linear-gradient(135deg, ${colors.dark.bgPrimary}ee 0%, ${colors.dark.bgSecondary}dd 100%)`
          : 'transparent',
        borderRadius: 12,
        backdropFilter: position !== 'center' ? 'blur(10px)' : undefined,
        borderLeft: position !== 'center' ? `4px solid ${color}` : undefined,
      }}
    >
      <div
        style={{
          fontFamily: typography.fonts.heading,
          fontSize,
          fontWeight: typography.weights.semibold,
          color,
          display: 'flex',
          flexWrap: 'wrap',
          gap: '0.3em',
          justifyContent: position === 'center' ? 'center' : 'flex-start',
        }}
      >
        {animation === 'word-by-word' ? (
          words.map((word, i) => {
            const wordOpacity = interpolate(
              adjustedFrame - i * framesPerWord,
              [0, framesPerWord],
              [0, 1],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
            );
            const wordY = interpolate(
              adjustedFrame - i * framesPerWord,
              [0, framesPerWord],
              [20, 0],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
            );
            return (
              <span
                key={i}
                style={{
                  opacity: wordOpacity,
                  transform: `translateY(${wordY}px)`,
                }}
              >
                {word}
              </span>
            );
          })
        ) : (
          text
        )}
      </div>
    </div>
  );
};

// Lower third overlay - subtitle style
interface LowerThirdOverlayProps {
  text: string;
  label?: string;
  position: OverlayPosition;
  adjustedFrame: number;
  opacity: number;
  fontSize?: number;
  color: string;
}

const LowerThirdOverlay: React.FC<LowerThirdOverlayProps> = ({
  text,
  label,
  position,
  adjustedFrame,
  opacity,
  fontSize = 32,
  color,
}) => {
  const { fps } = useVideoConfig();

  // Slide in from left
  const slideX = interpolate(
    adjustedFrame,
    [0, fps * 0.5],
    [-100, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

  // Line reveal
  const lineWidth = interpolate(
    adjustedFrame,
    [fps * 0.2, fps * 0.6],
    [0, 100],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
  );

  return (
    <div
      style={{
        ...positionStyles[position],
        opacity,
        transform: `${positionStyles[position].transform ?? ''} translateX(${slideX}px)`,
        zIndex: 100,
      }}
    >
      {/* Background bar */}
      <div
        style={{
          background: `linear-gradient(90deg, ${colors.dark.bgPrimary}ee 0%, ${colors.dark.bgPrimary}88 80%, transparent 100%)`,
          padding: '16px 48px 16px 24px',
          borderRadius: 4,
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Copper accent line */}
        <div
          style={{
            position: 'absolute',
            left: 0,
            top: 0,
            bottom: 0,
            width: 4,
            background: colors.accent,
          }}
        />

        {/* Animated underline */}
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            width: `${lineWidth}%`,
            height: 2,
            background: `linear-gradient(90deg, ${colors.accent} 0%, transparent 100%)`,
          }}
        />

        {/* Label */}
        {label && (
          <div
            style={{
              fontFamily: typography.fonts.body,
              fontSize: fontSize * 0.6,
              fontWeight: typography.weights.medium,
              color: colors.dark.textMuted,
              marginBottom: 4,
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
            }}
          >
            {label}
          </div>
        )}

        {/* Main text */}
        <div
          style={{
            fontFamily: typography.fonts.body,
            fontSize,
            fontWeight: typography.weights.semibold,
            color,
          }}
        >
          {text}
        </div>
      </div>
    </div>
  );
};

export default Overlay;
