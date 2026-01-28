import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

export const AgentSkillsPromo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // タイミング設定 (15秒 = 450フレーム)
  const introStart = 0;
  const introEnd = 2 * fps; // 0-2秒
  const titleStart = introEnd;
  const titleEnd = 4 * fps; // 2-4秒
  const feature1Start = titleEnd;
  const feature1End = 7 * fps; // 4-7秒
  const feature2Start = feature1End;
  const feature2End = 10 * fps; // 7-10秒
  const feature3Start = feature2End;
  const feature3End = 13 * fps; // 10-13秒
  const outroStart = feature3End;
  const outroEnd = 15 * fps; // 13-15秒

  // イントロアニメーション (0-2秒)
  const introOpacity = interpolate(
    frame,
    [introStart, introStart + 0.5 * fps, introEnd - 0.3 * fps, introEnd],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const introScale = interpolate(
    frame,
    [introStart, introStart + 0.5 * fps],
    [0.8, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // タイトルアニメーション (2-4秒) - 4秒でフェードアウト
  const titleOpacity = interpolate(
    frame,
    [titleStart, titleStart + 0.3 * fps, feature1Start - 0.3 * fps, feature1Start],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const titleY = interpolate(
    frame,
    [titleStart, titleStart + 0.5 * fps],
    [50, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // 機能1アニメーション (4-7秒) - 7秒でフェードアウト
  const feature1Opacity = interpolate(
    frame,
    [feature1Start, feature1Start + 0.3 * fps, feature2Start - 0.3 * fps, feature2Start],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const feature1X = interpolate(
    frame,
    [feature1Start, feature1Start + 0.5 * fps],
    [-100, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // 機能2アニメーション (7-10秒) - 10秒でフェードアウト
  const feature2Opacity = interpolate(
    frame,
    [feature2Start, feature2Start + 0.3 * fps, feature3Start - 0.3 * fps, feature3Start],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const feature2X = interpolate(
    frame,
    [feature2Start, feature2Start + 0.5 * fps],
    [-100, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // 機能3アニメーション (10-13秒) - 13秒でフェードアウト
  const feature3Opacity = interpolate(
    frame,
    [feature3Start, feature3Start + 0.3 * fps, outroStart - 0.3 * fps, outroStart],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const feature3X = interpolate(
    frame,
    [feature3Start, feature3Start + 0.5 * fps],
    [-100, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // アウトロアニメーション (13-15秒)
  const outroOpacity = interpolate(
    frame,
    [outroStart, outroStart + 0.3 * fps, outroEnd],
    [0, 1, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const outroScale = interpolate(
    frame,
    [outroStart, outroStart + 0.5 * fps],
    [0.9, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ backgroundColor: "#0f172a" }}>
      {/* イントロ: Remotionロゴ風 (0-2秒) */}
      {frame >= introStart && frame < introEnd && (
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: `translate(-50%, -50%) scale(${introScale})`,
            opacity: introOpacity,
            textAlign: "center",
          }}
        >
          <div
            style={{
              fontSize: 120,
              fontWeight: "bold",
              color: "#6366f1",
              letterSpacing: "-0.05em",
            }}
          >
            Remotion
          </div>
        </div>
      )}

      {/* タイトル: Agent Skills (2-4秒) */}
      {frame >= titleStart && (
        <div
          style={{
            position: "absolute",
            top: "20%",
            left: "50%",
            transform: `translate(-50%, ${titleY}px)`,
            opacity: titleOpacity,
            textAlign: "center",
          }}
        >
          <div
            style={{
              fontSize: 80,
              fontWeight: "bold",
              background: "linear-gradient(90deg, #6366f1, #a855f7)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              marginBottom: 20,
            }}
          >
            Agent Skills
          </div>
          <div
            style={{
              fontSize: 32,
              color: "#cbd5e1",
              fontWeight: 300,
            }}
          >
            Claude Codeで動画制作を革新
          </div>
        </div>
      )}

      {/* 機能1: プロンプトだけで動画作成 (4-7秒) */}
      {frame >= feature1Start && (
        <div
          style={{
            position: "absolute",
            top: "45%",
            left: "50%",
            transform: `translate(-50%, -50%) translateX(${feature1X}px)`,
            opacity: feature1Opacity,
            width: "80%",
            maxWidth: 1200,
          }}
        >
          <div
            style={{
              background: "rgba(99, 102, 241, 0.1)",
              border: "2px solid #6366f1",
              borderRadius: 20,
              padding: "30px 50px",
            }}
          >
            <div
              style={{
                fontSize: 40,
                color: "#6366f1",
                marginBottom: 15,
                fontWeight: "bold",
              }}
            >
              💬 プロンプトだけで制作
            </div>
            <div style={{ fontSize: 28, color: "#e2e8f0", lineHeight: 1.6 }}>
              コードを書かずに、自然言語で動画を作成
            </div>
          </div>
        </div>
      )}

      {/* 機能2: 簡単インストール (7-10秒) */}
      {frame >= feature2Start && (
        <div
          style={{
            position: "absolute",
            top: "45%",
            left: "50%",
            transform: `translate(-50%, -50%) translateX(${feature2X}px)`,
            opacity: feature2Opacity,
            width: "80%",
            maxWidth: 1200,
          }}
        >
          <div
            style={{
              background: "rgba(168, 85, 247, 0.1)",
              border: "2px solid #a855f7",
              borderRadius: 20,
              padding: "30px 50px",
            }}
          >
            <div
              style={{
                fontSize: 40,
                color: "#a855f7",
                marginBottom: 15,
                fontWeight: "bold",
              }}
            >
              🚀 簡単セットアップ
            </div>
            <div style={{ fontSize: 28, color: "#e2e8f0", lineHeight: 1.6 }}>
              <code
                style={{
                  background: "rgba(15, 23, 42, 0.6)",
                  padding: "5px 15px",
                  borderRadius: 8,
                  fontFamily: "monospace",
                }}
              >
                npx skills add remotion-dev/skills
              </code>
            </div>
          </div>
        </div>
      )}

      {/* 機能3: Claude Code統合 (10-13秒) */}
      {frame >= feature3Start && (
        <div
          style={{
            position: "absolute",
            top: "45%",
            left: "50%",
            transform: `translate(-50%, -50%) translateX(${feature3X}px)`,
            opacity: feature3Opacity,
            width: "80%",
            maxWidth: 1200,
          }}
        >
          <div
            style={{
              background: "rgba(34, 197, 94, 0.1)",
              border: "2px solid #22c55e",
              borderRadius: 20,
              padding: "30px 50px",
            }}
          >
            <div
              style={{
                fontSize: 40,
                color: "#22c55e",
                marginBottom: 15,
                fontWeight: "bold",
              }}
            >
              🤖 AI駆動のワークフロー
            </div>
            <div style={{ fontSize: 28, color: "#e2e8f0", lineHeight: 1.6 }}>
              Claude Codeが自動でコードを生成・調整
            </div>
          </div>
        </div>
      )}

      {/* アウトロ: CTA (13-15秒) */}
      {frame >= outroStart && (
        <div
          style={{
            position: "absolute",
            bottom: "15%",
            left: "50%",
            transform: `translate(-50%, 0) scale(${outroScale})`,
            opacity: outroOpacity,
            textAlign: "center",
          }}
        >
          <div
            style={{
              fontSize: 48,
              fontWeight: "bold",
              color: "#fff",
              marginBottom: 20,
            }}
          >
            今すぐ始めよう！
          </div>
          <div
            style={{
              fontSize: 32,
              color: "#94a3b8",
              fontFamily: "monospace",
            }}
          >
            remotion.dev/skills
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
