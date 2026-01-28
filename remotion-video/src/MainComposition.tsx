import { Audio, Video } from "@remotion/media";
import {
  AbsoluteFill,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

const VIDEO_SOURCE = staticFile("tokyo_weather_2026-01-10_weathernews.mp4");
const AUDIO_SOURCE = staticFile("Control_Interlude_Songstarter_Cmin_120bpm.wav");

export const MainComposition = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // BPM 120 = 2 beats per second = every 15 frames at 30fps
  // Beat logic: Create a pulse every 15 frames
  const beatDuration = 15;
  const currentBeat = Math.floor(frame / beatDuration);
  const frameInBeat = frame % beatDuration;

  // Spring animation for the beat
  // It triggers at the start of every beat
  const beatSpring = spring({
    frame: frameInBeat,
    fps,
    config: {
      damping: 10,
      stiffness: 100,
    },
    durationInFrames: beatDuration,
  });

  // Calculate scale based on the spring
  // Base scale 1, pulses up to ~1.05 and back
  const scale = interpolate(beatSpring, [0, 1], [1, 1.05]);

  // Opacity effect: subtle flash on beat
  const opacity = interpolate(
    frameInBeat,
    [0, 3, beatDuration],
    [1, 0.8, 1],
    { extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <AbsoluteFill
        style={{
          transform: `scale(${scale})`,
          opacity: opacity,
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <Video
          src={VIDEO_SOURCE}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
          }}
          startFrom={0}
          // Loop the video if it's shorter than the composition
          loop
        />
      </AbsoluteFill>

      <Audio src={AUDIO_SOURCE} />
    </AbsoluteFill>
  );
};
