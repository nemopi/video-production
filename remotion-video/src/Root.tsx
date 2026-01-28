import { Composition, CalculateMetadataFunction } from "remotion";
import { MainComposition } from "./MainComposition";
import { AgentSkillsPromo } from "./AgentSkillsPromo";
import { LipSync } from "./LipSync";
import { getAudioDuration } from "./getAudioDuration";
import "./index.css";

const calculateLipSyncMetadata: CalculateMetadataFunction<Record<string, unknown>> = async () => {
  const audioDuration = await getAudioDuration("voice.mp3");
  const fps = 30;

  return {
    durationInFrames: Math.ceil(audioDuration * fps),
  };
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="MainComposition"
        component={MainComposition}
        durationInFrames={900} // 30 seconds * 30 fps
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="AgentSkillsPromo"
        component={AgentSkillsPromo}
        durationInFrames={450} // 15 seconds * 30 fps
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="LipSync"
        component={LipSync}
        durationInFrames={300} // デフォルト値、calculateMetadataで上書きされる
        fps={30}
        width={1920}
        height={1080}
        calculateMetadata={calculateLipSyncMetadata}
      />
    </>
  );
};
