import { Composition } from "remotion";
import { Video } from "./Video";
import { ProfessionalHookScene } from "./components/ProfessionalHookScene";
import { OutputShowcaseScene } from "./components/OutputShowcaseScene";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Main"
        component={Video}
        durationInFrames={300}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title: "Video",
          scenes: [],
        }}
        calculateMetadata={async ({ props }) => {
          const totalFrames = props.scenes?.reduce(
            (acc: number, scene: any) => Math.max(acc, scene.endFrame || 0),
            300
          );
          return {
            durationInFrames: totalFrames,
            fps: props.fps || 30,
            width: props.width || 1920,
            height: props.height || 1080,
          };
        }}
      />

      {/* Professional Hook Scene - Proof of Concept */}
      <Composition
        id="ProfessionalHook"
        component={ProfessionalHookScene}
        durationInFrames={240}  // 8 seconds at 30fps
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          durationFrames: 240,
        }}
      />

      {/* Output Showcase Scene - What You Get */}
      <Composition
        id="OutputShowcase"
        component={OutputShowcaseScene}
        durationInFrames={360}  // 12 seconds at 30fps
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          durationFrames: 360,
        }}
      />
    </>
  );
};
