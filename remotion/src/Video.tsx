import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";
import { TitleCard } from "./components/TitleCard";
import { Background } from "./components/Background";
import { TextReveal } from "./components/TextReveal";
import { Transition } from "./components/Transition";

interface Scene {
  id: string;
  type: string;
  title?: string;
  text?: string;
  startFrame: number;
  endFrame: number;
  durationFrames: number;
  visual?: {
    background?: string;
    animation?: string;
    show_logo?: boolean;
    text_reveal?: string;
  };
}

interface VideoProps {
  title: string;
  scenes: Scene[];
  fps?: number;
  width?: number;
  height?: number;
}

export const Video: React.FC<VideoProps> = ({ title, scenes }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Find current scene
  const currentScene = scenes.find(
    (scene) => frame >= scene.startFrame && frame < scene.endFrame
  );

  if (!currentScene) {
    return (
      <AbsoluteFill style={{ backgroundColor: "#0f172a" }}>
        <Background variant="gradient" />
      </AbsoluteFill>
    );
  }

  const sceneFrame = frame - currentScene.startFrame;
  const sceneProgress = sceneFrame / currentScene.durationFrames;

  // Fade in/out
  const opacity = interpolate(
    sceneFrame,
    [0, 15, currentScene.durationFrames - 15, currentScene.durationFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const bgVariant = currentScene.visual?.background || "gradient";

  return (
    <AbsoluteFill style={{ backgroundColor: "#0f172a" }}>
      <Background variant={bgVariant as any} />

      <AbsoluteFill style={{ opacity }}>
        {currentScene.type === "intro" && (
          <TitleCard
            title={currentScene.title || ""}
            tagline={currentScene.text || ""}
            showLogo={currentScene.visual?.show_logo}
          />
        )}

        {currentScene.type === "content" && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              height: "100%",
              padding: "80px",
            }}
          >
            {currentScene.title && (
              <h2
                style={{
                  fontSize: 64,
                  fontWeight: 700,
                  color: "#f8fafc",
                  marginBottom: 40,
                  textAlign: "center",
                }}
              >
                {currentScene.title}
              </h2>
            )}
            <TextReveal
              text={currentScene.text || ""}
              progress={sceneProgress}
            />
          </div>
        )}

        {(currentScene.type === "demo" || currentScene.type === "feature") && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              height: "100%",
              padding: "80px",
            }}
          >
            <h2
              style={{
                fontSize: 56,
                fontWeight: 700,
                color: "#f8fafc",
                marginBottom: 30,
                textAlign: "center",
              }}
            >
              {currentScene.title}
            </h2>
            <p
              style={{
                fontSize: 32,
                color: "#94a3b8",
                textAlign: "center",
                maxWidth: 1200,
                lineHeight: 1.5,
              }}
            >
              {currentScene.text}
            </p>
          </div>
        )}

        {(currentScene.type === "cta" || currentScene.type === "outro") && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              height: "100%",
            }}
          >
            <h1
              style={{
                fontSize: 80,
                fontWeight: 800,
                color: "#f8fafc",
                marginBottom: 20,
              }}
            >
              {currentScene.title}
            </h1>
            <p
              style={{
                fontSize: 36,
                color: "#3b82f6",
              }}
            >
              {currentScene.text}
            </p>
          </div>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
