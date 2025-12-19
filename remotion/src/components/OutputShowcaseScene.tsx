/**
 * Output Showcase Scene - "What You Get"
 *
 * Shows the variety of outputs Media Engine produces:
 * - Animated file format icons that expand into real screenshots
 * - Ken Burns motion on each output type
 * - Theme-consistent styling throughout
 *
 * Segments:
 * 0-3s: HTML Documents (proposal with code blocks)
 * 3-6s: Interactive Demos (calculator, playground)
 * 6-9s: Dashboard Views (insights, build)
 * 9-12s: All formats summary with icons
 */

import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Img,
  staticFile,
  Easing,
  Sequence,
} from 'remotion';
import { Background } from './Background';
import { Vignette, ProgressIndicator, ScreenChrome } from './overlays';
import { interpolateKeyframes, transformToStyle, type Keyframe } from '../lib/motion';
import { colors, typography, glows } from '../lib/theme';

// ============================================================================
// Types
// ============================================================================

interface OutputShowcaseSceneProps {
  durationFrames: number;
}

interface OutputSegment {
  id: string;
  title: string;
  subtitle: string;
  icon: string;
  color: string;
  screenshots: string[];
  startFrame: number;
  endFrame: number;
}

// ============================================================================
// Segment Configuration
// ============================================================================

const createSegments = (totalFrames: number): OutputSegment[] => {
  const segmentDuration = totalFrames / 4;

  return [
    {
      id: 'html',
      title: 'HTML Documents',
      subtitle: 'Styled, responsive, print-ready',
      icon: 'HTML',
      color: colors.accent,
      screenshots: ['html-proposal-content.png', 'html-proposal-code.png'],
      startFrame: 0,
      endFrame: segmentDuration,
    },
    {
      id: 'demos',
      title: 'Interactive Demos',
      subtitle: 'Calculators, playgrounds, showcases',
      icon: 'DEMO',
      color: colors.success,
      screenshots: ['demo-pricing-calculator.png', 'demo-code-playground.png'],
      startFrame: segmentDuration,
      endFrame: segmentDuration * 2,
    },
    {
      id: 'dashboard',
      title: 'Dashboard & Analytics',
      subtitle: 'Health scores, insights, build controls',
      icon: 'DASH',
      color: colors.accentSecondary,
      screenshots: ['dashboard-insights.png', 'dashboard-build.png'],
      startFrame: segmentDuration * 2,
      endFrame: segmentDuration * 3,
    },
    {
      id: 'summary',
      title: 'One Source, Many Outputs',
      subtitle: 'PDF • PPTX • XLSX • HTML • MP4',
      icon: 'ALL',
      color: colors.accentHot,
      screenshots: ['dashboard-overview-full.png'],
      startFrame: segmentDuration * 3,
      endFrame: totalFrames,
    },
  ];
};

// ============================================================================
// File Icon Component
// ============================================================================

interface FileIconProps {
  format: string;
  color: string;
  scale: number;
  opacity: number;
  x?: number;
  y?: number;
}

const FileIcon: React.FC<FileIconProps> = ({ format, color, scale, opacity, x = 0, y = 0 }) => {
  return (
    <div
      style={{
        position: 'absolute',
        transform: `translate(${x}px, ${y}px) scale(${scale})`,
        opacity,
        transition: 'transform 0.1s ease-out',
      }}
    >
      <div
        style={{
          width: 80,
          height: 100,
          background: `linear-gradient(135deg, ${colors.dark.bgSecondary}, ${colors.dark.bgTertiary})`,
          borderRadius: 12,
          border: `2px solid ${color}`,
          boxShadow: `0 0 20px ${color}44, 0 8px 30px rgba(0,0,0,0.4)`,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 8,
        }}
      >
        {/* Document fold */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            right: 0,
            width: 20,
            height: 20,
            background: color,
            clipPath: 'polygon(100% 0, 100% 100%, 0 100%)',
            borderRadius: '0 12px 0 0',
          }}
        />

        {/* Format label */}
        <span
          style={{
            fontFamily: typography.fonts.mono,
            fontSize: 16,
            fontWeight: typography.weights.bold,
            color: color,
            textShadow: `0 0 10px ${color}`,
          }}
        >
          {format}
        </span>

        {/* Checkmark */}
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path
            d="M5 12L10 17L19 8"
            stroke={colors.success}
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
    </div>
  );
};

// ============================================================================
// Format Icons Row (for summary segment)
// ============================================================================

const FormatIconsRow: React.FC<{ progress: number }> = ({ progress }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const formats = [
    { name: 'PDF', color: colors.accentHot },
    { name: 'PPTX', color: colors.warning },
    { name: 'XLSX', color: colors.success },
    { name: 'HTML', color: colors.accent },
    { name: 'MP4', color: colors.accentSecondary },
  ];

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 200,
        left: 0,
        right: 0,
        display: 'flex',
        justifyContent: 'center',
        gap: 40,
      }}
    >
      {formats.map((format, index) => {
        const delay = index * 4;
        const iconScale = spring({
          frame: Math.max(0, frame - delay),
          fps,
          config: { damping: 10, stiffness: 150, mass: 0.5 },
        });

        const iconOpacity = interpolate(progress, [0, 0.3], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });

        return (
          <FileIcon
            key={format.name}
            format={format.name}
            color={format.color}
            scale={Math.max(0, iconScale)}
            opacity={iconOpacity}
          />
        );
      })}
    </div>
  );
};

// ============================================================================
// Screenshot with Motion
// ============================================================================

interface ScreenshotDisplayProps {
  src: string;
  progress: number;
  title?: string;
}

const ScreenshotDisplay: React.FC<ScreenshotDisplayProps> = ({ src, progress, title }) => {
  // Ken Burns motion
  const keyframes: Keyframe[] = [
    { at: 0, scale: 1.15, x: 0, y: 0, opacity: 0 },
    { at: 0.15, scale: 1.15, x: 0, y: 0, opacity: 1 },
    { at: 0.5, scale: 1.25, x: -30, y: -20, opacity: 1 },
    { at: 0.85, scale: 1.25, x: -30, y: -20, opacity: 1 },
    { at: 1, scale: 1.3, x: -50, y: -30, opacity: 0 },
  ];

  const transform = interpolateKeyframes(keyframes, progress);

  return (
    <AbsoluteFill
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <div
        style={{
          width: '80%',
          height: '70%',
          position: 'relative',
          ...transformToStyle(transform),
        }}
      >
        <ScreenChrome title={title || 'Media Engine'}>
          <Img
            src={staticFile(`assets/captures/${src}`)}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
            }}
          />
        </ScreenChrome>
      </div>
    </AbsoluteFill>
  );
};

// ============================================================================
// Segment Title Overlay
// ============================================================================

interface SegmentTitleProps {
  title: string;
  subtitle: string;
  color: string;
  progress: number;
}

const SegmentTitle: React.FC<SegmentTitleProps> = ({ title, subtitle, color, progress }) => {
  const opacity = interpolate(progress, [0, 0.1, 0.8, 1], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const y = interpolate(progress, [0, 0.1, 0.8, 1], [20, 0, 0, -20], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  return (
    <div
      style={{
        position: 'absolute',
        top: 80,
        left: 0,
        right: 0,
        textAlign: 'center',
        opacity,
        transform: `translateY(${y}px)`,
      }}
    >
      <h2
        style={{
          fontFamily: typography.fonts.heading,
          fontSize: typography.sizes.h1,
          fontWeight: typography.weights.bold,
          color: colors.dark.textPrimary,
          margin: 0,
          textShadow: `0 0 30px ${color}66`,
        }}
      >
        {title}
      </h2>
      <p
        style={{
          fontFamily: typography.fonts.body,
          fontSize: typography.sizes.h3,
          fontWeight: typography.weights.medium,
          color: color,
          margin: '10px 0 0 0',
        }}
      >
        {subtitle}
      </p>
    </div>
  );
};

// ============================================================================
// Main Component
// ============================================================================

export const OutputShowcaseScene: React.FC<OutputShowcaseSceneProps> = ({
  durationFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const segments = createSegments(durationFrames);
  const progress = frame / durationFrames;

  // Find current segment
  const currentSegment = segments.find(
    s => frame >= s.startFrame && frame < s.endFrame
  ) || segments[segments.length - 1];

  // Calculate local progress within segment
  const segmentDuration = currentSegment.endFrame - currentSegment.startFrame;
  const segmentProgress = (frame - currentSegment.startFrame) / segmentDuration;

  // Determine which screenshot to show (alternate between two)
  const screenshotIndex = segmentProgress < 0.5 ? 0 : 1;
  const screenshotProgress = segmentProgress < 0.5
    ? segmentProgress * 2
    : (segmentProgress - 0.5) * 2;

  const currentScreenshot = currentSegment.screenshots[
    Math.min(screenshotIndex, currentSegment.screenshots.length - 1)
  ];

  return (
    <AbsoluteFill style={{ backgroundColor: colors.dark.bgPrimary }}>
      {/* Layer 1: Animated Background */}
      <Background variant="cyber" intensity="low" />

      {/* Layer 2: Screenshot Display */}
      {currentSegment.id !== 'summary' && (
        <ScreenshotDisplay
          src={currentScreenshot}
          progress={screenshotProgress}
          title={currentSegment.title}
        />
      )}

      {/* Layer 3: Summary Icons */}
      {currentSegment.id === 'summary' && (
        <>
          <ScreenshotDisplay
            src={currentSegment.screenshots[0]}
            progress={segmentProgress}
            title="Media Engine Dashboard"
          />
          <FormatIconsRow progress={segmentProgress} />
        </>
      )}

      {/* Layer 4: Vignette */}
      <Vignette intensity={0.3} />

      {/* Layer 5: Title Overlay */}
      <SegmentTitle
        title={currentSegment.title}
        subtitle={currentSegment.subtitle}
        color={currentSegment.color}
        progress={segmentProgress}
      />

      {/* Layer 6: Progress Indicator */}
      <ProgressIndicator
        progress={progress}
        segments={segments.length}
        currentSegment={segments.indexOf(currentSegment)}
      />

      {/* Fade in/out */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: colors.dark.bgPrimary,
          opacity: interpolate(frame, [0, 15, durationFrames - 15, durationFrames], [1, 0, 0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          }),
          pointerEvents: 'none',
        }}
      />
    </AbsoluteFill>
  );
};

export default OutputShowcaseScene;
