/**
 * Video Component - Enhanced Motion Graphics Renderer
 *
 * Renders rich, animated scenes using all available motion graphics components.
 * Supports multiple scene types, transitions, overlays, and data-driven animations.
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
import { TextReveal, HighlightText, Typewriter } from "./components/TextReveal";
import { Transition } from "./components/Transition";
import { StatCounter, StatGrid } from "./components/StatCounter";
import { FeatureCard, FeatureList } from "./components/FeatureCard";
import { Overlay } from "./components/Overlay";
import { colors, typography, gradients, icons } from "./lib/theme";

// ============================================================================
// Types
// ============================================================================

interface StatData {
  value: number;
  label: string;
  suffix?: string;
  prefix?: string;
}

interface FeatureCardData {
  icon?: keyof typeof icons;
  highlight?: string;
}

interface OverlayData {
  type: "stat" | "callout" | "lower_third";
  text: string;
  label?: string;
  position?: "center" | "bottom" | "bottom-right" | "top-right" | "top-left";
  animation?: "scale" | "slide_up" | "fade_in" | "word-by-word";
  delay?: number;
  duration?: number;
}

interface CodeBlock {
  command: string;
  label?: string;
}

interface SceneVisual {
  background?: "dark" | "gradient" | "grid" | "particles";
  animation?: string;
  show_logo?: boolean;
  text_reveal?: string;
  stat_grid?: {
    stats: StatData[];
    animation?: string;
    stagger_delay?: number;
  };
  feature_card?: FeatureCardData;
  overlay?: OverlayData;
  code_blocks?: CodeBlock[];
  cta?: string;
}

interface Scene {
  id: string;
  type: "intro" | "content" | "feature" | "demo" | "section" | "cta" | "outro";
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
  fps?: number;
  width?: number;
  height?: number;
}

// ============================================================================
// Scene Renderers
// ============================================================================

/**
 * Intro Scene - Logo reveal, title card with spring animation
 */
const IntroScene: React.FC<{
  scene: Scene;
  sceneFrame: number;
  sceneProgress: number;
}> = ({ scene, sceneFrame, sceneProgress }) => {
  const { fps } = useVideoConfig();

  const showLogo = scene.visual?.show_logo;
  const textRevealStyle = scene.visual?.text_reveal;

  // If it's a logo reveal scene
  if (showLogo) {
    return (
      <TitleCard
        title={scene.title || ""}
        tagline={scene.text || ""}
        variant="intro"
      />
    );
  }

  // Text-focused intro (like "The Problem" hook)
  const titleOpacity = interpolate(
    sceneFrame,
    [0, 20, scene.durationFrames - 20, scene.durationFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const titleScale = spring({
    frame: sceneFrame,
    fps,
    config: { damping: 15, stiffness: 80, mass: 0.8 },
  });

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: 100,
      }}
    >
      {scene.title && scene.title !== "The Hook" && (
        <h2
          style={{
            fontFamily: typography.fonts.body,
            fontSize: typography.sizes.h3,
            fontWeight: typography.weights.medium,
            color: colors.accent,
            marginBottom: 30,
            textTransform: "uppercase",
            letterSpacing: "0.2em",
            opacity: titleOpacity,
          }}
        >
          {scene.title}
        </h2>
      )}

      <div
        style={{
          transform: `scale(${titleScale})`,
          opacity: titleOpacity,
          maxWidth: 1400,
        }}
      >
        {textRevealStyle === "word-by-word" ? (
          <TextReveal
            text={scene.text || ""}
            variant="heading"
            framesPerWord={8}
            delay={15}
          />
        ) : (
          <h1
            style={{
              fontFamily: typography.fonts.heading,
              fontSize: typography.sizes.display,
              fontWeight: typography.weights.bold,
              color: colors.dark.textPrimary,
              textAlign: "center",
              lineHeight: 1.2,
              textShadow: `0 4px 40px ${colors.accent}33`,
            }}
          >
            {scene.text}
          </h1>
        )}
      </div>
    </AbsoluteFill>
  );
};

/**
 * Content Scene - Text reveals, stats, code blocks
 */
const ContentScene: React.FC<{
  scene: Scene;
  sceneFrame: number;
  sceneProgress: number;
}> = ({ scene, sceneFrame, sceneProgress }) => {
  const { fps } = useVideoConfig();

  const statGrid = scene.visual?.stat_grid;
  const codeBlocks = scene.visual?.code_blocks;

  // Fade in/out
  const opacity = interpolate(
    sceneFrame,
    [0, 20, scene.durationFrames - 15, scene.durationFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Stats scene
  if (statGrid) {
    return (
      <AbsoluteFill
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          opacity,
        }}
      >
        {scene.title && (
          <h2
            style={{
              fontFamily: typography.fonts.heading,
              fontSize: typography.sizes.h2,
              fontWeight: typography.weights.bold,
              color: colors.dark.textPrimary,
              marginBottom: 80,
              textAlign: "center",
            }}
          >
            {scene.title}
          </h2>
        )}
        <StatGrid
          stats={statGrid.stats}
          staggerDelay={statGrid.stagger_delay || 15}
        />
      </AbsoluteFill>
    );
  }

  // Code blocks scene (like "Get Started")
  if (codeBlocks && codeBlocks.length > 0) {
    return (
      <AbsoluteFill
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: 100,
          opacity,
        }}
      >
        {scene.title && (
          <h2
            style={{
              fontFamily: typography.fonts.heading,
              fontSize: typography.sizes.h1,
              fontWeight: typography.weights.bold,
              color: colors.dark.textPrimary,
              marginBottom: 60,
            }}
          >
            {scene.title}
          </h2>
        )}

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 24,
            width: "100%",
            maxWidth: 900,
          }}
        >
          {codeBlocks.map((block, index) => {
            const blockDelay = index * 25;
            const blockOpacity = interpolate(
              sceneFrame - blockDelay,
              [0, 15],
              [0, 1],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
            );
            const blockX = interpolate(
              sceneFrame - blockDelay,
              [0, 20],
              [-30, 0],
              {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
                easing: Easing.out(Easing.cubic),
              }
            );

            return (
              <div
                key={index}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 24,
                  opacity: blockOpacity,
                  transform: `translateX(${blockX}px)`,
                }}
              >
                {block.label && (
                  <span
                    style={{
                      fontFamily: typography.fonts.body,
                      fontSize: typography.sizes.body,
                      fontWeight: typography.weights.medium,
                      color: colors.accent,
                      textTransform: "uppercase",
                      letterSpacing: "0.1em",
                      width: 100,
                    }}
                  >
                    {block.label}
                  </span>
                )}
                <div
                  style={{
                    flex: 1,
                    background: colors.dark.bgSecondary,
                    borderRadius: 12,
                    padding: "20px 28px",
                    border: `1px solid ${colors.dark.border}`,
                  }}
                >
                  <Typewriter
                    text={block.command}
                    delay={blockDelay + 10}
                    charsPerFrame={2}
                  />
                </div>
              </div>
            );
          })}
        </div>

        {scene.text && (
          <p
            style={{
              fontFamily: typography.fonts.body,
              fontSize: typography.sizes.h4,
              color: colors.dark.textSecondary,
              marginTop: 50,
              textAlign: "center",
              maxWidth: 800,
              opacity: interpolate(sceneFrame, [60, 80], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
            }}
          >
            {scene.text}
          </p>
        )}
      </AbsoluteFill>
    );
  }

  // Default content scene with text reveal
  return (
    <AbsoluteFill
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: 100,
        opacity,
      }}
    >
      {scene.title && (
        <h2
          style={{
            fontFamily: typography.fonts.heading,
            fontSize: typography.sizes.h1,
            fontWeight: typography.weights.bold,
            color: colors.dark.textPrimary,
            marginBottom: 50,
            textAlign: "center",
          }}
        >
          {scene.title}
        </h2>
      )}
      <TextReveal
        text={scene.text || ""}
        variant="body"
        framesPerWord={5}
        maxWidth={1200}
        delay={scene.title ? 20 : 0}
      />
    </AbsoluteFill>
  );
};

/**
 * Feature Scene - Feature cards with icons and descriptions
 */
const FeatureScene: React.FC<{
  scene: Scene;
  sceneFrame: number;
  sceneProgress: number;
}> = ({ scene, sceneFrame, sceneProgress }) => {
  const { fps } = useVideoConfig();

  const featureCard = scene.visual?.feature_card;
  const iconName = featureCard?.icon || "check";

  // Map scene icons to available theme icons
  const iconMapping: Record<string, keyof typeof icons> = {
    document: "menu",
    build: "sync",
    video: "clock",
    globe: "locations",
    check: "check",
    shield: "shield",
    audit: "calendar",
    ai: "ai",
  };

  const mappedIcon = iconMapping[iconName] || "check";

  const opacity = interpolate(
    sceneFrame,
    [0, 20, scene.durationFrames - 20, scene.durationFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 80,
        opacity,
      }}
    >
      <div
        style={{
          display: "flex",
          gap: 80,
          alignItems: "center",
          maxWidth: 1600,
        }}
      >
        {/* Feature Card */}
        <div style={{ flex: "0 0 auto" }}>
          <FeatureCard
            icon={mappedIcon}
            title={scene.title || ""}
            description=""
            delay={0}
          />
        </div>

        {/* Description */}
        <div style={{ flex: 1 }}>
          <TextReveal
            text={scene.text || ""}
            variant="body"
            framesPerWord={4}
            align="left"
            delay={15}
          />
        </div>
      </div>
    </AbsoluteFill>
  );
};

/**
 * Demo Scene - Screen recordings, terminal output, overlays
 */
const DemoScene: React.FC<{
  scene: Scene;
  sceneFrame: number;
  sceneProgress: number;
}> = ({ scene, sceneFrame, sceneProgress }) => {
  const { fps } = useVideoConfig();

  const overlay = scene.visual?.overlay;

  const opacity = interpolate(
    sceneFrame,
    [0, 15, scene.durationFrames - 15, scene.durationFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Simulated terminal/demo area
  const terminalScale = interpolate(
    sceneFrame,
    [0, 25],
    [0.95, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) }
  );

  return (
    <AbsoluteFill style={{ opacity }}>
      {/* Title */}
      <div
        style={{
          position: "absolute",
          top: 80,
          left: 100,
          right: 100,
        }}
      >
        <h2
          style={{
            fontFamily: typography.fonts.heading,
            fontSize: typography.sizes.h2,
            fontWeight: typography.weights.bold,
            color: colors.dark.textPrimary,
            marginBottom: 20,
          }}
        >
          {scene.title}
        </h2>
        <div
          style={{
            width: 120,
            height: 4,
            background: gradients.copperGlow,
            borderRadius: 2,
          }}
        />
      </div>

      {/* Demo content area */}
      <AbsoluteFill
        style={{
          top: 200,
          bottom: 150,
          left: 100,
          right: 100,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div
          style={{
            width: "100%",
            height: "100%",
            background: colors.dark.bgSecondary,
            borderRadius: 20,
            border: `1px solid ${colors.dark.border}`,
            transform: `scale(${terminalScale})`,
            display: "flex",
            flexDirection: "column",
            padding: 40,
            overflow: "hidden",
          }}
        >
          {/* Terminal header */}
          <div
            style={{
              display: "flex",
              gap: 8,
              marginBottom: 30,
            }}
          >
            <div
              style={{
                width: 14,
                height: 14,
                borderRadius: "50%",
                background: "#ff5f57",
              }}
            />
            <div
              style={{
                width: 14,
                height: 14,
                borderRadius: "50%",
                background: "#febc2e",
              }}
            />
            <div
              style={{
                width: 14,
                height: 14,
                borderRadius: "50%",
                background: "#28c840",
              }}
            />
          </div>

          {/* Terminal content */}
          <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <div
              style={{
                fontFamily: typography.fonts.mono,
                fontSize: 28,
                color: colors.dark.textPrimary,
                textAlign: "center",
                maxWidth: 1000,
                lineHeight: 1.6,
              }}
            >
              <Typewriter
                text={scene.text || ""}
                delay={20}
                charsPerFrame={1.5}
              />
            </div>
          </div>
        </div>
      </AbsoluteFill>

      {/* Overlay */}
      {overlay && (
        <Overlay
          type={overlay.type}
          text={overlay.text}
          label={overlay.label}
          position={overlay.position || "bottom-right"}
          animation={overlay.animation || "slide_up"}
          delay={30}
          duration={scene.durationFrames - 60}
        />
      )}
    </AbsoluteFill>
  );
};

/**
 * Section Scene - Transition/header scenes between major sections
 */
const SectionScene: React.FC<{
  scene: Scene;
  sceneFrame: number;
  sceneProgress: number;
}> = ({ scene, sceneFrame, sceneProgress }) => {
  const { fps } = useVideoConfig();

  const titleScale = spring({
    frame: sceneFrame,
    fps,
    config: { damping: 12, stiffness: 100, mass: 0.5 },
  });

  const opacity = interpolate(
    sceneFrame,
    [0, 15, scene.durationFrames - 10, scene.durationFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const lineWidth = interpolate(
    sceneFrame,
    [10, 35],
    [0, 300],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) }
  );

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        opacity,
      }}
    >
      <h1
        style={{
          fontFamily: typography.fonts.heading,
          fontSize: typography.sizes.display,
          fontWeight: typography.weights.bold,
          color: colors.dark.textPrimary,
          transform: `scale(${titleScale})`,
          textShadow: `0 4px 30px ${colors.accent}44`,
        }}
      >
        {scene.title}
      </h1>

      <div
        style={{
          width: lineWidth,
          height: 4,
          background: gradients.copperGlow,
          borderRadius: 2,
          marginTop: 30,
          boxShadow: `0 0 20px ${colors.accent}66`,
        }}
      />

      {scene.text && (
        <p
          style={{
            fontFamily: typography.fonts.body,
            fontSize: typography.sizes.h3,
            fontWeight: typography.weights.light,
            color: colors.dark.textSecondary,
            marginTop: 40,
            opacity: interpolate(sceneFrame, [20, 40], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        >
          {scene.text}
        </p>
      )}
    </AbsoluteFill>
  );
};

/**
 * Outro Scene - CTA, logo, closing
 */
const OutroScene: React.FC<{
  scene: Scene;
  sceneFrame: number;
  sceneProgress: number;
}> = ({ scene, sceneFrame, sceneProgress }) => {
  const { fps } = useVideoConfig();

  const cta = scene.visual?.cta;

  const logoScale = spring({
    frame: sceneFrame,
    fps,
    config: { damping: 10, stiffness: 80, mass: 0.6 },
  });

  const opacity = interpolate(
    sceneFrame,
    [0, 20, scene.durationFrames - 30, scene.durationFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const ctaOpacity = interpolate(
    sceneFrame,
    [30, 50],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const ctaY = interpolate(
    sceneFrame,
    [30, 55],
    [30, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) }
  );

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        opacity,
      }}
    >
      {/* Logo/Title */}
      <h1
        style={{
          fontFamily: typography.fonts.heading,
          fontSize: 140,
          fontWeight: typography.weights.bold,
          color: colors.dark.textPrimary,
          transform: `scale(${logoScale})`,
          textShadow: `0 4px 40px ${colors.accent}44`,
          marginBottom: 30,
        }}
      >
        {scene.title}
      </h1>

      {/* Copper accent line */}
      <div
        style={{
          width: interpolate(sceneFrame, [10, 30], [0, 250], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
          height: 4,
          background: gradients.copperGlow,
          borderRadius: 2,
          marginBottom: 50,
          boxShadow: `0 0 25px ${colors.accent}66`,
        }}
      />

      {/* Tagline */}
      {scene.text && (
        <TextReveal
          text={scene.text}
          variant="tagline"
          framesPerWord={6}
          delay={20}
          maxWidth={1000}
        />
      )}

      {/* CTA */}
      {cta && (
        <div
          style={{
            marginTop: 60,
            opacity: ctaOpacity,
            transform: `translateY(${ctaY}px)`,
          }}
        >
          <div
            style={{
              background: `${colors.dark.bgSecondary}ee`,
              borderRadius: 16,
              padding: "24px 48px",
              border: `2px solid ${colors.accent}`,
              boxShadow: `0 0 30px ${colors.accent}33`,
            }}
          >
            <span
              style={{
                fontFamily: typography.fonts.mono,
                fontSize: typography.sizes.h3,
                fontWeight: typography.weights.medium,
                color: colors.accent,
              }}
            >
              {cta}
            </span>
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};

// ============================================================================
// Main Video Component
// ============================================================================

export const Video: React.FC<VideoProps> = ({ title, scenes }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Find current scene
  const currentSceneIndex = scenes.findIndex(
    (scene) => frame >= scene.startFrame && frame < scene.endFrame
  );
  const currentScene = scenes[currentSceneIndex];

  // Get next scene for transitions
  const nextScene = scenes[currentSceneIndex + 1];
  const prevScene = scenes[currentSceneIndex - 1];

  // No scene found - show default background
  if (!currentScene) {
    return (
      <AbsoluteFill style={{ backgroundColor: colors.dark.bgPrimary }}>
        <Background variant="gradient" />
      </AbsoluteFill>
    );
  }

  const sceneFrame = frame - currentScene.startFrame;
  const sceneProgress = sceneFrame / currentScene.durationFrames;

  // Determine background variant
  const bgVariant = (currentScene.visual?.background || "dark") as
    | "dark"
    | "gradient"
    | "grid"
    | "particles";

  // Determine transition type based on scene animation property
  const getTransitionType = (animation?: string): "copper-sweep" | "fade" | "wipe" | "radial" => {
    switch (animation) {
      case "copper-sweep":
        return "copper-sweep";
      case "wipe":
        return "wipe";
      case "radial":
        return "radial";
      default:
        return "fade";
    }
  };

  // Check if we need a transition in (first 20 frames of scene, except first scene)
  const showTransitionIn = currentSceneIndex > 0 && sceneFrame < fps * 0.7;
  const transitionInType = getTransitionType(currentScene.visual?.animation);

  // Check if we need a transition out (last 20 frames of scene, except last scene)
  const framesUntilEnd = currentScene.durationFrames - sceneFrame;
  const showTransitionOut = currentSceneIndex < scenes.length - 1 && framesUntilEnd < fps * 0.5;

  // Render scene content based on type
  const renderScene = () => {
    switch (currentScene.type) {
      case "intro":
        return (
          <IntroScene
            scene={currentScene}
            sceneFrame={sceneFrame}
            sceneProgress={sceneProgress}
          />
        );
      case "content":
        return (
          <ContentScene
            scene={currentScene}
            sceneFrame={sceneFrame}
            sceneProgress={sceneProgress}
          />
        );
      case "feature":
        return (
          <FeatureScene
            scene={currentScene}
            sceneFrame={sceneFrame}
            sceneProgress={sceneProgress}
          />
        );
      case "demo":
        return (
          <DemoScene
            scene={currentScene}
            sceneFrame={sceneFrame}
            sceneProgress={sceneProgress}
          />
        );
      case "section":
        return (
          <SectionScene
            scene={currentScene}
            sceneFrame={sceneFrame}
            sceneProgress={sceneProgress}
          />
        );
      case "cta":
      case "outro":
        return (
          <OutroScene
            scene={currentScene}
            sceneFrame={sceneFrame}
            sceneProgress={sceneProgress}
          />
        );
      default:
        // Fallback for unknown scene types
        return (
          <ContentScene
            scene={currentScene}
            sceneFrame={sceneFrame}
            sceneProgress={sceneProgress}
          />
        );
    }
  };

  return (
    <AbsoluteFill style={{ backgroundColor: colors.dark.bgPrimary }}>
      {/* Background layer */}
      <Background variant={bgVariant} />

      {/* Scene content */}
      {renderScene()}

      {/* Transition overlays */}
      {showTransitionIn && (
        <Transition
          type={transitionInType}
          direction="in"
          delay={0}
          duration={fps * 0.6}
        />
      )}
    </AbsoluteFill>
  );
};

export default Video;
