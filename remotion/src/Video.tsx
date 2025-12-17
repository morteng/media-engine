/**
 * Video Component - Electric Aurora Edition
 *
 * Dynamic, vibrant video renderer with kinetic typography,
 * aurora backgrounds, and exciting transitions.
 */

import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Easing,
} from "remotion";
import { Background } from "./components/Background";
import { TitleCard } from "./components/TitleCard";
import { TextReveal, HighlightText, Typewriter, GradientText, CharacterReveal, AnimatedCounter } from "./components/TextReveal";
import { Transition, TransitionType } from "./components/Transition";
import { StatCounter, StatGrid } from "./components/StatCounter";
import { FeatureCard } from "./components/FeatureCard";
import { Overlay } from "./components/Overlay";
import { colors, typography, gradients, glows, icons } from "./lib/theme";

// ============================================================================
// Types
// ============================================================================

type BackgroundVariant = 'dark' | 'aurora' | 'grid' | 'particles' | 'pulse' | 'cyber' | 'waves';
type TextEffect = 'fade-up' | 'bounce' | 'elastic' | 'wave' | 'split' | 'scale-pop' | 'rotate' | 'glitch';

interface StatData {
  value: number;
  label: string;
  suffix?: string;
  prefix?: string;
}

interface SceneVisual {
  background?: BackgroundVariant;
  intensity?: 'low' | 'medium' | 'high';
  transition_in?: TransitionType;
  transition_out?: TransitionType;
  text_effect?: TextEffect;
  show_logo?: boolean;
  glow?: boolean;
  gradient_text?: boolean;
  logo_glow?: boolean;
  logo_only?: boolean;
  fade_out?: boolean;
  pulse_animation?: boolean;
  stat_grid?: {
    stats: StatData[];
    animation?: string;
    stagger_delay?: number;
  };
  feature_card?: {
    icon?: string;
    highlight?: 'cyan' | 'purple' | 'hot' | 'neon';
  };
  terminal?: {
    commands?: string[];
  };
  pipeline?: string[];
  metrics?: string[];
  icons?: string[];
  code_preview?: string;
  cta?: {
    primary?: string;
    secondary?: string;
  } | string;
  // Two-line layout with emphasized subtitle
  two_line_layout?: boolean;
  subtitle_emphasis?: boolean;
  // Flying output icons for demo scenes
  flying_outputs?: boolean;
  output_icons?: string[];
  output_animation?: string;
}

interface Scene {
  id: string;
  type: 'intro' | 'content' | 'feature' | 'demo' | 'section' | 'outro';
  title?: string;
  text?: string;
  startFrame: number;
  endFrame: number;
  durationFrames: number;
  visual?: SceneVisual;
}

interface VideoProps {
  title: string;
  scenes: Scene[];
  theme?: string;
}

// ============================================================================
// Utility Functions
// ============================================================================

const getHighlightColor = (highlight?: string): string => {
  switch (highlight) {
    case 'cyan': return colors.accent;
    case 'purple': return colors.accentSecondary;
    case 'hot': return colors.accentHot;
    case 'neon': return colors.accentNeon;
    default: return colors.accent;
  }
};

// ============================================================================
// Scene Renderers
// ============================================================================

/**
 * Intro Scene - Dynamic title reveals with gradient text and glows
 */
const IntroScene: React.FC<{
  scene: Scene;
  sceneFrame: number;
}> = ({ scene, sceneFrame }) => {
  const { fps } = useVideoConfig();
  const visual = scene.visual || {};

  // Logo reveal with title card
  if (visual.show_logo && visual.gradient_text) {
    const titleScale = spring({
      frame: sceneFrame,
      fps,
      config: { damping: 10, stiffness: 100, mass: 0.6 },
    });

    const glowPulse = Math.sin(sceneFrame * 0.1) * 0.3 + 0.7;

    return (
      <AbsoluteFill
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div style={{ transform: `scale(${titleScale})` }}>
          <GradientText
            text={scene.title || ''}
            size="display"
            delay={5}
          />
        </div>

        {/* Subtitle */}
        {scene.text && (
          <div
            style={{
              marginTop: 40,
              opacity: interpolate(sceneFrame, [20, 40], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
            }}
          >
            <TextReveal
              text={scene.text}
              variant="tagline"
              effect={visual.text_effect || 'bounce'}
              delay={25}
              framesPerWord={4}
              glow={visual.glow}
            />
          </div>
        )}

        {/* Glow ring */}
        {visual.glow && (
          <div
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: '600px',
              height: '600px',
              borderRadius: '50%',
              border: `2px solid ${colors.accent}`,
              boxShadow: glows.multi,
              opacity: glowPulse * 0.3,
            }}
          />
        )}
      </AbsoluteFill>
    );
  }

  // Text-focused intro (hook scene)
  const opacity = interpolate(
    sceneFrame,
    [0, 15, scene.durationFrames - 10, scene.durationFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  return (
    <AbsoluteFill
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 100,
        opacity,
      }}
    >
      {scene.title && scene.title !== scene.text && (
        <h2
          style={{
            fontFamily: typography.fonts.body,
            fontSize: typography.sizes.h3,
            fontWeight: typography.weights.medium,
            color: colors.accent,
            marginBottom: 30,
            textTransform: 'uppercase',
            letterSpacing: '0.2em',
            textShadow: `0 0 20px ${colors.accent}66`,
          }}
        >
          {scene.title}
        </h2>
      )}

      <TextReveal
        text={scene.text || ''}
        variant="heading"
        effect={visual.text_effect || 'bounce'}
        framesPerWord={6}
        delay={10}
        glow
        maxWidth={1400}
      />
    </AbsoluteFill>
  );
};

/**
 * Content Scene - Stats, text reveals, icons
 */
const ContentScene: React.FC<{
  scene: Scene;
  sceneFrame: number;
}> = ({ scene, sceneFrame }) => {
  const { fps } = useVideoConfig();
  const visual = scene.visual || {};
  const statGrid = visual.stat_grid;
  const icons_list = visual.icons;

  const opacity = interpolate(
    sceneFrame,
    [0, 15, scene.durationFrames - 15, scene.durationFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Stats scene with animated counters
  if (statGrid) {
    return (
      <AbsoluteFill
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          opacity,
        }}
      >
        {scene.title && (
          <div style={{ marginBottom: 80 }}>
            <GradientText text={scene.title} size="h1" delay={0} />
          </div>
        )}

        <div
          style={{
            display: 'flex',
            gap: 100,
            justifyContent: 'center',
          }}
        >
          {statGrid.stats.map((stat, index) => {
            const delay = index * (statGrid.stagger_delay || 15);
            const statOpacity = interpolate(
              sceneFrame - delay,
              [0, 20],
              [0, 1],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
            );
            const statY = interpolate(
              sceneFrame - delay,
              [0, 25],
              [40, 0],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) }
            );

            return (
              <div
                key={index}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  opacity: statOpacity,
                  transform: `translateY(${statY}px)`,
                }}
              >
                <AnimatedCounter
                  value={stat.value}
                  delay={delay + 5}
                  duration={40}
                  suffix={stat.suffix}
                  prefix={stat.prefix}
                />
                <span
                  style={{
                    fontFamily: typography.fonts.body,
                    fontSize: typography.sizes.h4,
                    fontWeight: typography.weights.medium,
                    color: colors.dark.textSecondary,
                    marginTop: 16,
                    textTransform: 'uppercase',
                    letterSpacing: '0.15em',
                  }}
                >
                  {stat.label}
                </span>
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    );
  }

  // Two-line layout with emphasized subtitle (e.g., "Documentation... All by hand.")
  if (visual.two_line_layout) {
    return (
      <AbsoluteFill
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 100,
          opacity,
        }}
      >
        {/* Main title text */}
        {scene.title && (
          <div style={{ marginBottom: 40 }}>
            <TextReveal
              text={scene.title}
              variant="heading"
              effect={visual.text_effect || "elastic"}
              delay={0}
              framesPerWord={4}
              maxWidth={1400}
            />
          </div>
        )}

        {/* Emphasized subtitle on its own line */}
        {scene.text && (
          <div
            style={{
              opacity: interpolate(sceneFrame, [40, 60], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
              transform: `scale(${interpolate(sceneFrame, [40, 70], [0.8, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })})`,
            }}
          >
            <span
              style={{
                fontFamily: typography.fonts.heading,
                fontSize: typography.sizes.h1,
                fontWeight: typography.weights.heavy,
                color: colors.accentHot,
                textShadow: `0 0 40px ${colors.accentHot}88, 0 0 80px ${colors.accentHot}44`,
                letterSpacing: '0.05em',
              }}
            >
              {scene.text}
            </span>
          </div>
        )}

        {/* Icons below */}
        {icons_list && icons_list.length > 0 && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 30,
              marginTop: 60,
            }}
          >
            {icons_list.map((iconName, index) => {
              const iconDelay = 70 + index * 8;
              const iconScale = spring({
                frame: sceneFrame - iconDelay,
                fps,
                config: { damping: 8, stiffness: 150, mass: 0.5 },
              });

              return (
                <div
                  key={index}
                  style={{
                    transform: `scale(${Math.max(0, iconScale)})`,
                    opacity: interpolate(sceneFrame - iconDelay, [0, 10], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
                  }}
                >
                  <div
                    style={{
                      width: 70,
                      height: 70,
                      borderRadius: 14,
                      background: colors.dark.bgTertiary,
                      border: `2px solid ${[colors.accent, colors.accentSecondary, colors.accentHot, colors.accentNeon][index % 4]}`,
                      boxShadow: `0 0 20px ${[colors.accent, colors.accentSecondary, colors.accentHot, colors.accentNeon][index % 4]}44`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontFamily: typography.fonts.mono,
                      fontSize: 12,
                      fontWeight: typography.weights.bold,
                      color: colors.dark.textPrimary,
                      textTransform: 'uppercase',
                    }}
                  >
                    {iconName.slice(0, 4)}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </AbsoluteFill>
    );
  }

  // Icons showcase scene
  if (icons_list && icons_list.length > 0) {
    return (
      <AbsoluteFill
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 100,
          opacity,
        }}
      >
        {scene.title && (
          <div style={{ marginBottom: 50 }}>
            <TextReveal
              text={scene.title}
              variant="heading"
              effect="bounce"
              delay={0}
              framesPerWord={5}
              glow
            />
          </div>
        )}

        {scene.text && (
          <TextReveal
            text={scene.text}
            variant="tagline"
            effect="elastic"
            delay={20}
            framesPerWord={4}
          />
        )}

        {/* Icon flow visualization */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 30,
            marginTop: 60,
          }}
        >
          {icons_list.map((iconName, index) => {
            const iconDelay = 30 + index * 8;
            const iconScale = spring({
              frame: sceneFrame - iconDelay,
              fps,
              config: { damping: 8, stiffness: 150, mass: 0.5 },
            });
            const isArrow = iconName === 'arrow';

            return (
              <div
                key={index}
                style={{
                  transform: `scale(${Math.max(0, iconScale)})`,
                  opacity: interpolate(sceneFrame - iconDelay, [0, 10], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
                }}
              >
                {isArrow ? (
                  <div
                    style={{
                      width: 60,
                      height: 4,
                      background: gradients.aurora,
                      borderRadius: 2,
                      boxShadow: glows.cyan,
                    }}
                  />
                ) : (
                  <div
                    style={{
                      width: 80,
                      height: 80,
                      borderRadius: 16,
                      background: colors.dark.bgTertiary,
                      border: `2px solid ${[colors.accent, colors.accentSecondary, colors.accentHot, colors.accentNeon][index % 4]}`,
                      boxShadow: `0 0 20px ${[colors.accent, colors.accentSecondary, colors.accentHot, colors.accentNeon][index % 4]}44`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontFamily: typography.fonts.mono,
                      fontSize: 14,
                      fontWeight: typography.weights.bold,
                      color: colors.dark.textPrimary,
                      textTransform: 'uppercase',
                    }}
                  >
                    {iconName.slice(0, 4)}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    );
  }

  // Default content scene
  return (
    <AbsoluteFill
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 100,
        opacity,
      }}
    >
      {scene.title && (
        <div style={{ marginBottom: 50 }}>
          <TextReveal
            text={scene.title}
            variant="heading"
            effect={visual.text_effect || 'bounce'}
            delay={0}
            framesPerWord={5}
            glow
          />
        </div>
      )}
      {scene.text && (
        <TextReveal
          text={scene.text}
          variant="body"
          effect="fade-up"
          framesPerWord={4}
          maxWidth={1200}
          delay={scene.title ? 25 : 0}
        />
      )}
    </AbsoluteFill>
  );
};

/**
 * Feature Scene - Feature cards with pipeline visualizations
 */
const FeatureScene: React.FC<{
  scene: Scene;
  sceneFrame: number;
}> = ({ scene, sceneFrame }) => {
  const { fps } = useVideoConfig();
  const visual = scene.visual || {};
  const featureCard = visual.feature_card;
  const pipeline = visual.pipeline;
  const metrics = visual.metrics;

  const opacity = interpolate(
    sceneFrame,
    [0, 15, scene.durationFrames - 15, scene.durationFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const highlightColor = getHighlightColor(featureCard?.highlight);

  // Map icon names
  const iconMapping: Record<string, keyof typeof icons> = {
    video: 'play',
    shield: 'shield',
    ai: 'ai',
    check: 'check',
    document: 'document',
    code: 'code',
    chart: 'chart',
    sync: 'sync',
  };
  const mappedIcon = iconMapping[featureCard?.icon || 'check'] || 'check';

  return (
    <AbsoluteFill
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 80,
        opacity,
      }}
    >
      {/* Title with glow */}
      <div
        style={{
          marginBottom: 40,
          textAlign: 'center',
        }}
      >
        <h2
          style={{
            fontFamily: typography.fonts.heading,
            fontSize: typography.sizes.h1,
            fontWeight: typography.weights.bold,
            color: colors.dark.textPrimary,
            textShadow: `0 0 40px ${highlightColor}44`,
            marginBottom: 16,
          }}
        >
          {scene.title}
        </h2>
        <div
          style={{
            width: interpolate(sceneFrame, [10, 30], [0, 200], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
            height: 4,
            background: `linear-gradient(90deg, ${highlightColor}, ${colors.accentSecondary})`,
            borderRadius: 2,
            margin: '0 auto',
            boxShadow: `0 0 20px ${highlightColor}`,
          }}
        />
      </div>

      {/* Description */}
      <div style={{ marginBottom: 50, maxWidth: 1000 }}>
        <TextReveal
          text={scene.text || ''}
          variant="body"
          effect="fade-up"
          framesPerWord={4}
          delay={15}
        />
      </div>

      {/* Pipeline visualization */}
      {pipeline && pipeline.length > 0 && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 20,
          }}
        >
          {pipeline.map((step, index) => {
            const stepDelay = 30 + index * 12;
            const stepScale = spring({
              frame: sceneFrame - stepDelay,
              fps,
              config: { damping: 10, stiffness: 120, mass: 0.5 },
            });

            return (
              <React.Fragment key={index}>
                <div
                  style={{
                    padding: '20px 32px',
                    background: colors.dark.bgTertiary,
                    borderRadius: 12,
                    border: `2px solid ${[colors.accent, colors.accentSecondary, colors.accentHot, colors.accentNeon][index % 4]}`,
                    transform: `scale(${Math.max(0, stepScale)})`,
                    boxShadow: `0 0 20px ${[colors.accent, colors.accentSecondary, colors.accentHot, colors.accentNeon][index % 4]}44`,
                  }}
                >
                  <span
                    style={{
                      fontFamily: typography.fonts.mono,
                      fontSize: typography.sizes.body,
                      fontWeight: typography.weights.semibold,
                      color: colors.dark.textPrimary,
                    }}
                  >
                    {step}
                  </span>
                </div>
                {index < pipeline.length - 1 && (
                  <div
                    style={{
                      width: 40,
                      height: 3,
                      background: gradients.aurora,
                      borderRadius: 2,
                      opacity: interpolate(sceneFrame - stepDelay - 5, [0, 10], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
                    }}
                  />
                )}
              </React.Fragment>
            );
          })}
        </div>
      )}

      {/* Metrics visualization */}
      {metrics && metrics.length > 0 && (
        <div
          style={{
            display: 'flex',
            gap: 30,
            marginTop: 20,
          }}
        >
          {metrics.map((metric, index) => {
            const metricDelay = 30 + index * 10;
            const checkScale = spring({
              frame: sceneFrame - metricDelay,
              fps,
              config: { damping: 8, stiffness: 200, mass: 0.4 },
            });

            return (
              <div
                key={index}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  transform: `scale(${Math.max(0, checkScale)})`,
                }}
              >
                <div
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: '50%',
                    background: colors.success,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: `0 0 15px ${colors.success}66`,
                  }}
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3">
                    <path d={icons.check} />
                  </svg>
                </div>
                <span
                  style={{
                    fontFamily: typography.fonts.body,
                    fontSize: typography.sizes.body,
                    fontWeight: typography.weights.medium,
                    color: colors.dark.textPrimary,
                  }}
                >
                  {metric}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </AbsoluteFill>
  );
};

/**
 * Demo Scene - Terminal with neon styling and flying outputs
 */
const DemoScene: React.FC<{
  scene: Scene;
  sceneFrame: number;
}> = ({ scene, sceneFrame }) => {
  const { fps } = useVideoConfig();
  const visual = scene.visual || {};
  const terminal = visual.terminal;
  const flyingOutputs = visual.flying_outputs;
  const outputIcons = visual.output_icons || [];

  const opacity = interpolate(
    sceneFrame,
    [0, 15, scene.durationFrames - 15, scene.durationFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const terminalScale = spring({
    frame: sceneFrame,
    fps,
    config: { damping: 12, stiffness: 100, mass: 0.6 },
  });

  // Flying output icon positions (around the terminal)
  const flyingPositions = [
    { x: -300, y: -150, angle: -15 },
    { x: 350, y: -120, angle: 10 },
    { x: -350, y: 100, angle: -10 },
    { x: 380, y: 80, angle: 15 },
    { x: -200, y: 200, angle: -5 },
  ];

  return (
    <AbsoluteFill style={{ opacity }}>
      {/* Title */}
      <div
        style={{
          position: 'absolute',
          top: 80,
          left: 0,
          right: 0,
          textAlign: 'center',
        }}
      >
        <GradientText text={scene.title || ''} size="h2" delay={0} />
      </div>

      {/* Subtitle text */}
      {scene.text && (
        <div
          style={{
            position: 'absolute',
            top: 160,
            left: 0,
            right: 0,
            textAlign: 'center',
            opacity: interpolate(sceneFrame, [20, 40], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
          }}
        >
          <span
            style={{
              fontFamily: typography.fonts.body,
              fontSize: typography.sizes.h4,
              color: colors.dark.textSecondary,
            }}
          >
            {scene.text}
          </span>
        </div>
      )}

      {/* Flying output icons */}
      {flyingOutputs && outputIcons.length > 0 && (
        <AbsoluteFill
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {outputIcons.map((iconName, index) => {
            const iconDelay = 60 + index * 15;
            const iconProgress = interpolate(
              sceneFrame - iconDelay,
              [0, 30],
              [0, 1],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
            );
            const pos = flyingPositions[index % flyingPositions.length];
            const floatY = Math.sin((sceneFrame + index * 30) * 0.05) * 10;
            const iconColor = [colors.accent, colors.accentSecondary, colors.accentHot, colors.accentNeon, colors.success][index % 5];

            return (
              <div
                key={index}
                style={{
                  position: 'absolute',
                  transform: `translate(${pos.x}px, ${pos.y + floatY}px) rotate(${pos.angle}deg) scale(${iconProgress})`,
                  opacity: iconProgress,
                }}
              >
                <div
                  style={{
                    width: 90,
                    height: 110,
                    background: `linear-gradient(135deg, ${colors.dark.bgSecondary}, ${colors.dark.bgTertiary})`,
                    borderRadius: 12,
                    border: `2px solid ${iconColor}`,
                    boxShadow: `0 0 30px ${iconColor}66, 0 10px 40px rgba(0,0,0,0.4)`,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 8,
                  }}
                >
                  {/* Document icon top fold */}
                  <div
                    style={{
                      position: 'absolute',
                      top: 0,
                      right: 0,
                      width: 20,
                      height: 20,
                      background: iconColor,
                      clipPath: 'polygon(100% 0, 100% 100%, 0 100%)',
                      borderRadius: '0 12px 0 0',
                    }}
                  />
                  <span
                    style={{
                      fontFamily: typography.fonts.mono,
                      fontSize: 16,
                      fontWeight: typography.weights.bold,
                      color: iconColor,
                      textTransform: 'uppercase',
                      textShadow: `0 0 10px ${iconColor}`,
                    }}
                  >
                    {iconName.toUpperCase()}
                  </span>
                  {/* Mini content lines */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4, width: 50 }}>
                    <div style={{ height: 3, background: `${colors.dark.textMuted}44`, borderRadius: 2 }} />
                    <div style={{ height: 3, background: `${colors.dark.textMuted}44`, borderRadius: 2, width: '80%' }} />
                    <div style={{ height: 3, background: `${colors.dark.textMuted}44`, borderRadius: 2, width: '60%' }} />
                  </div>
                </div>
              </div>
            );
          })}
        </AbsoluteFill>
      )}

      {/* Terminal */}
      <AbsoluteFill
        style={{
          top: 200,
          bottom: 150,
          left: 250,
          right: 250,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div
          style={{
            width: '100%',
            maxWidth: 700,
            background: `${colors.dark.bgPrimary}ee`,
            borderRadius: 20,
            border: `2px solid ${colors.accent}`,
            boxShadow: glows.cyan,
            transform: `scale(${terminalScale})`,
            overflow: 'hidden',
          }}
        >
          {/* Terminal header */}
          <div
            style={{
              padding: '16px 24px',
              background: colors.dark.bgSecondary,
              borderBottom: `1px solid ${colors.dark.border}`,
              display: 'flex',
              gap: 10,
            }}
          >
            <div style={{ width: 14, height: 14, borderRadius: '50%', background: colors.accentHot }} />
            <div style={{ width: 14, height: 14, borderRadius: '50%', background: colors.warning }} />
            <div style={{ width: 14, height: 14, borderRadius: '50%', background: colors.success }} />
          </div>

          {/* Terminal content */}
          <div style={{ padding: 32 }}>
            {terminal?.commands ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {terminal.commands.map((cmd, index) => {
                  const cmdDelay = 15 + index * 20;
                  return (
                    <div key={index}>
                      <Typewriter
                        text={cmd}
                        delay={cmdDelay}
                        charsPerFrame={2.5}
                        variant="terminal"
                      />
                    </div>
                  );
                })}
              </div>
            ) : (
              <Typewriter
                text={scene.text || ''}
                delay={20}
                charsPerFrame={2}
                variant="terminal"
              />
            )}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/**
 * Outro Scene - CTA with glowing elements
 */
const OutroScene: React.FC<{
  scene: Scene;
  sceneFrame: number;
}> = ({ scene, sceneFrame }) => {
  const { fps } = useVideoConfig();
  const visual = scene.visual || {};
  const cta = visual.cta;

  const logoScale = spring({
    frame: sceneFrame,
    fps,
    config: { damping: 10, stiffness: 80, mass: 0.6 },
  });

  const opacity = interpolate(
    sceneFrame,
    [0, 20, scene.durationFrames - 30, scene.durationFrames],
    [0, 1, 1, visual.fade_out ? 0 : 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const glowPulse = visual.pulse_animation
    ? Math.sin(sceneFrame * 0.08) * 0.4 + 0.6
    : 1;

  // Logo only mode
  if (visual.logo_only) {
    return (
      <AbsoluteFill
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          opacity,
        }}
      >
        <div style={{ transform: `scale(${logoScale})` }}>
          <GradientText text="ME" size="display" delay={0} />
        </div>
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        opacity,
      }}
    >
      {/* Logo/Title */}
      <div style={{ transform: `scale(${logoScale})`, marginBottom: 30 }}>
        {visual.gradient_text ? (
          <GradientText text={scene.title || ''} size="display" delay={5} />
        ) : (
          <h1
            style={{
              fontFamily: typography.fonts.display,
              fontSize: typography.sizes.display,
              fontWeight: typography.weights.heavy,
              color: colors.dark.textPrimary,
              textShadow: visual.logo_glow ? glows.multi : undefined,
            }}
          >
            {scene.title}
          </h1>
        )}
      </div>

      {/* Accent line */}
      <div
        style={{
          width: interpolate(sceneFrame, [10, 30], [0, 300], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
          height: 4,
          background: gradients.aurora,
          borderRadius: 2,
          marginBottom: 40,
          boxShadow: glows.multi,
          opacity: glowPulse,
        }}
      />

      {/* Tagline */}
      {scene.text && (
        <TextReveal
          text={scene.text}
          variant="tagline"
          effect="wave"
          framesPerWord={5}
          delay={20}
          maxWidth={1000}
        />
      )}

      {/* CTA */}
      {cta && (
        <div
          style={{
            marginTop: 60,
            opacity: interpolate(sceneFrame, [40, 60], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
            transform: `translateY(${interpolate(sceneFrame, [40, 65], [30, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) })}px)`,
          }}
        >
          <div
            style={{
              background: `${colors.dark.bgSecondary}ee`,
              borderRadius: 16,
              padding: '24px 48px',
              border: `2px solid ${colors.accent}`,
              boxShadow: `0 0 ${30 * glowPulse}px ${colors.accent}66`,
            }}
          >
            <span
              style={{
                fontFamily: typography.fonts.mono,
                fontSize: typography.sizes.h3,
                fontWeight: typography.weights.medium,
                color: colors.accent,
                textShadow: `0 0 10px ${colors.accent}`,
              }}
            >
              {typeof cta === 'string' ? cta : cta.primary}
            </span>
          </div>

          {typeof cta !== 'string' && cta.secondary && (
            <div
              style={{
                marginTop: 20,
                textAlign: 'center',
              }}
            >
              <span
                style={{
                  fontFamily: typography.fonts.mono,
                  fontSize: typography.sizes.small,
                  color: colors.dark.textMuted,
                }}
              >
                {cta.secondary}
              </span>
            </div>
          )}
        </div>
      )}
    </AbsoluteFill>
  );
};

// ============================================================================
// Main Video Component
// ============================================================================

export const Video: React.FC<VideoProps> = ({ title, scenes, theme }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Find current scene
  const currentSceneIndex = scenes.findIndex(
    (scene) => frame >= scene.startFrame && frame < scene.endFrame
  );
  const currentScene = scenes[currentSceneIndex];

  if (!currentScene) {
    return (
      <AbsoluteFill style={{ backgroundColor: colors.dark.bgPrimary }}>
        <Background variant="aurora" />
      </AbsoluteFill>
    );
  }

  const sceneFrame = frame - currentScene.startFrame;
  const visual = currentScene.visual || {};

  // Background variant
  const bgVariant = (visual.background || 'dark') as BackgroundVariant;
  const bgIntensity = visual.intensity || 'medium';

  // Transition types
  const transitionIn = visual.transition_in || 'fade';
  const showTransitionIn = currentSceneIndex > 0 && sceneFrame < fps * 0.6;

  // Render scene based on type
  const renderScene = () => {
    switch (currentScene.type) {
      case 'intro':
        return <IntroScene scene={currentScene} sceneFrame={sceneFrame} />;
      case 'content':
        return <ContentScene scene={currentScene} sceneFrame={sceneFrame} />;
      case 'feature':
        return <FeatureScene scene={currentScene} sceneFrame={sceneFrame} />;
      case 'demo':
        return <DemoScene scene={currentScene} sceneFrame={sceneFrame} />;
      case 'section':
        return <ContentScene scene={currentScene} sceneFrame={sceneFrame} />;
      case 'outro':
        return <OutroScene scene={currentScene} sceneFrame={sceneFrame} />;
      default:
        return <ContentScene scene={currentScene} sceneFrame={sceneFrame} />;
    }
  };

  return (
    <AbsoluteFill style={{ backgroundColor: colors.dark.bgPrimary }}>
      {/* Background */}
      <Background variant={bgVariant} intensity={bgIntensity} />

      {/* Scene content */}
      {renderScene()}

      {/* Transition in */}
      {showTransitionIn && (
        <Transition
          type={transitionIn}
          direction="in"
          delay={0}
          duration={fps * 0.5}
        />
      )}
    </AbsoluteFill>
  );
};

export default Video;
