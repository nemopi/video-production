import { AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Audio } from "@remotion/media";

export const LipSync: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 音声解析に基づく台詞区間の定義（秒単位）
  // 無音区間を除外して、実際に台詞がある区間のみ口を動かす
  const speechSegments = [
    { start: 0.00, end: 0.29 },   // 最初の台詞
    { start: 0.74, end: 1.28 },   // 2番目の台詞
    { start: 1.75, end: 3.49 },   // 3番目の台詞
    { start: 4.38, end: 5.66 },   // 4番目の台詞
  ];

  // 現在のフレームの時間を計算（秒）
  const currentTime = frame / fps;

  // 現在のフレームが台詞区間内かチェック
  const isSpeaking = speechSegments.some(
    (segment) => currentTime >= segment.start && currentTime <= segment.end
  );

  let mouthImage = "mouth-closed.png";

  if (isSpeaking) {
    // 台詞中: 周期的に口を動かす
    const cycle = Math.floor(frame / 6) % 5;
    const microCycle = frame % 6;

    if (cycle === 0 || cycle === 1) {
      // 大きく開く
      mouthImage = microCycle < 3 ? "mouth-open.png" : "mouth-half.png";
    } else if (cycle === 2) {
      // 半分開く
      mouthImage = "mouth-half.png";
    } else if (cycle === 3) {
      // 小さく開く
      mouthImage = microCycle < 3 ? "mouth-half.png" : "mouth-closed.png";
    } else {
      // 閉じる
      mouthImage = microCycle < 2 ? "mouth-closed.png" : "mouth-half.png";
    }
  } else {
    // 台詞がない区間: 口を閉じる
    mouthImage = "mouth-closed.png";
  }

  return (
    <AbsoluteFill style={{ backgroundColor: "#1a1a1a" }}>
      {/* 音声 */}
      <Audio src={staticFile("voice.mp3")} />

      {/* 口の画像 - 中央に配置 */}
      <AbsoluteFill
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <Img
          src={staticFile(mouthImage)}
          style={{
            maxWidth: "80%",
            maxHeight: "80%",
            objectFit: "contain",
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
