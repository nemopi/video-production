# Remotion リップシンク動画制作報告
**作成日**: 2026年1月22日
**技術**: Remotion Agent Skills + 音声波形解析

---

## 成果物 (Lip Sync Animation)

**プロジェクトパス**: `/Users/takayukinemoto/Desktop/映像制作/remotion-video`
**最終出力**: `/Users/takayukinemoto/Desktop/映像制作/remotion-video/out/LipSync.mp4`
**音声ファイル**: `/Users/takayukinemoto/Desktop/映像制作/remotion-video/public/voice.mp3`
**画像素材**:
- `/Users/takayukinemoto/Desktop/映像制作/remotion-video/public/mouth-open.png` (口を開けた状態)
- `/Users/takayukinemoto/Desktop/映像制作/remotion-video/public/mouth-half.png` (口を半分開けた状態)
- `/Users/takayukinemoto/Desktop/映像制作/remotion-video/public/mouth-closed.png` (口を閉じた状態)

**動画尺**: 約7.15秒 (音声の長さに自動対応)
**解像度**: 1920x1080 (Full HD)
**フレームレート**: 30fps

---

## ユーザーからの依頼

> Remotionスキルを使って、/Users/takayukinemoto/Desktop/映像制作/20260121 にある画像ファイル3点（口開けてる画像、口を半分開けている画像、口をとじたもの）と、台詞音声ファイルから、リップシンク動画を作成してください。尺は音声ファイルベースで台詞が終わるところまで。

---

## 実装プロセス

### Phase 1: 素材の準備と環境構築

#### 1.1 素材ファイルの確認
元の素材は以下のパスに配置されていました：
```
/Users/takayukinemoto/Desktop/映像制作/20260121/
├── hf_20260121_042715_fab8b8d3-2ba2-4075-ab50-9528c4ed5109.png (口を開けた画像)
├── hf_20260121_061355_e2d75691-5cbd-4ae6-b879-cf5964ca4d36.png (口を半分開けた画像)
├── hf_20260121_061408_ca5df59d-5347-4092-bc14-8043ebf3e20d.png (口を閉じた画像)
└── ElevenLabs_2026-01-21T06_19_22_Zakira_pvc_sp87_s74_sb91_v3.mp3 (音声)
```

#### 1.2 ファイルのコピーとリネーム
Remotionプロジェクトの`public`フォルダに、わかりやすい名前でコピー：
```bash
cp "/Users/takayukinemoto/Desktop/映像制作/20260121/hf_20260121_042715_fab8b8d3-2ba2-4075-ab50-9528c4ed5109.png" \
   "/Users/takayukinemoto/Desktop/映像制作/remotion-video/public/mouth-open.png"

cp "/Users/takayukinemoto/Desktop/映像制作/20260121/hf_20260121_061355_e2d75691-5cbd-4ae6-b879-cf5964ca4d36.png" \
   "/Users/takayukinemoto/Desktop/映像制作/remotion-video/public/mouth-half.png"

cp "/Users/takayukinemoto/Desktop/映像制作/20260121/hf_20260121_061408_ca5df59d-5347-4092-bc14-8043ebf3e20d.png" \
   "/Users/takayukinemoto/Desktop/映像制作/remotion-video/public/mouth-closed.png"

cp "/Users/takayukinemoto/Desktop/映像制作/20260121/ElevenLabs_2026-01-21T06_19_22_Zakira_pvc_sp87_s74_sb91_v3.mp3" \
   "/Users/takayukinemoto/Desktop/映像制作/remotion-video/public/voice.mp3"
```

**設計判断**: ファイル名を簡潔にすることで、コード内での参照を容易にし、保守性を向上。

---

### Phase 2: コンポーネント実装

#### 2.1 音声の長さ取得関数の作成
**ファイルパス**: `/Users/takayukinemoto/Desktop/映像制作/remotion-video/src/getAudioDuration.ts`

音声ファイルの長さを動的に取得し、動画の尺を自動調整するための関数を作成。

```typescript
import { staticFile } from "remotion";

export const getAudioDuration = async (audioPath: string): Promise<number> => {
  return new Promise((resolve, reject) => {
    const audio = new Audio(staticFile(audioPath));

    audio.addEventListener("loadedmetadata", () => {
      resolve(audio.duration);
    });

    audio.addEventListener("error", (error) => {
      reject(error);
    });

    audio.load();
  });
};
```

**設計判断**: ブラウザの`Audio` APIを使用し、シンプルかつ確実に音声の長さを取得。

#### 2.2 リップシンクコンポーネントの初期実装
**ファイルパス**: `/Users/takayukinemoto/Desktop/映像制作/remotion-video/src/LipSync.tsx`

最初のアプローチは、周期的なアニメーションで口を動かす実装：

```typescript
// 初期実装（後に修正）
const getMouthState = (currentFrame: number): number => {
  const cycle = Math.floor(currentFrame / 8) % 4;
  const microCycle = currentFrame % 8;
  const noise = Math.sin(currentFrame * 0.3) * 0.2;

  let baseState = 0;

  if (cycle === 1 || cycle === 2) {
    baseState = microCycle < 4 ? 2 : 1;
  } else if (cycle === 3) {
    baseState = 1;
  } else {
    baseState = microCycle < 2 ? 1 : 0;
  }

  return Math.max(0, Math.min(2, baseState + noise));
};
```

**問題点**: この方法では、音声の実際の内容とは無関係に口が動いてしまう。

#### 2.3 Root.tsxへのコンポジション追加
**ファイルパス**: `/Users/takayukinemoto/Desktop/映像制作/remotion-video/src/Root.tsx`

`calculateMetadata`を使用して、音声の長さに合わせて動画の尺を自動調整：

```typescript
import { Composition, CalculateMetadataFunction } from "remotion";
import { LipSync } from "./LipSync";
import { getAudioDuration } from "./getAudioDuration";

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
      {/* 既存のコンポジション... */}
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
```

**設計判断**: 動画の尺をハードコードせず、音声の長さに自動的に合わせることで、汎用性を確保。

---

### Phase 3: 問題の発見と解決

#### 3.1 問題1: 台詞がない区間でも口が動いてしまう

**ユーザーからのフィードバック**:
> リップシンクは上手くいってる、ありがとう、でも、なんか無音のときにパクパクしてたり、終わってからも台詞がないのに話してるよ、調整できる？

**原因分析**:
周期的なアニメーションでは、音声の実際の内容（台詞のある/なし）を考慮できていなかった。

**解決アプローチ**:
音声ファイルの波形を解析し、実際に台詞がある区間だけ口を動かすように修正。

#### 3.2 音声波形の解析

ffmpegの`silencedetect`フィルターを使用して、無音区間を検出：

```bash
ffmpeg -i /Users/takayukinemoto/Desktop/映像制作/remotion-video/public/voice.mp3 \
       -af silencedetect=noise=-30dB:d=0.3 \
       -f null - 2>&1 | grep silence
```

**解析結果**:
```
[silencedetect] silence_start: 0.289478
[silencedetect] silence_end: 0.740227 | silence_duration: 0.450748
[silencedetect] silence_start: 1.278844
[silencedetect] silence_end: 1.754626 | silence_duration: 0.475782
[silencedetect] silence_start: 3.493152
[silencedetect] silence_end: 4.378526 | silence_duration: 0.885374
[silencedetect] silence_start: 5.66263
[silencedetect] silence_end: 7.157551 | silence_duration: 1.494921
```

**台詞区間の特定**:
- **0.00秒～0.29秒**: 台詞
- **0.74秒～1.28秒**: 台詞
- **1.75秒～3.49秒**: 台詞
- **4.38秒～5.66秒**: 台詞

**無音区間**:
- 0.29秒～0.74秒
- 1.28秒～1.75秒
- 3.49秒～4.38秒
- 5.66秒～7.15秒（終了まで）

#### 3.3 最終実装: 音声解析ベースのリップシンク

**ファイルパス**: `/Users/takayukinemoto/Desktop/映像制作/remotion-video/src/LipSync.tsx`

音声解析の結果を元に、台詞区間を定義して実装：

```typescript
import { AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Audio } from "@remotion/media";

export const LipSync: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 音声解析に基づく台詞区間の定義（秒単位）
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
      mouthImage = microCycle < 3 ? "mouth-open.png" : "mouth-half.png";
    } else if (cycle === 2) {
      mouthImage = "mouth-half.png";
    } else if (cycle === 3) {
      mouthImage = microCycle < 3 ? "mouth-half.png" : "mouth-closed.png";
    } else {
      mouthImage = microCycle < 2 ? "mouth-closed.png" : "mouth-half.png";
    }
  } else {
    // 台詞がない区間: 口を閉じる
    mouthImage = "mouth-closed.png";
  }

  return (
    <AbsoluteFill style={{ backgroundColor: "#1a1a1a" }}>
      <Audio src={staticFile("voice.mp3")} />

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
```

**設計判断のポイント**:
1. **台詞区間の配列管理**: 複数の台詞区間を配列で定義し、`some()`メソッドで現在のフレームが該当するかチェック
2. **時間ベースの判定**: フレーム数を秒に変換し、音声解析結果と直接比較
3. **周期的な口パク**: 台詞区間内では、6フレームごとに口の状態を変化させることで、自然な口パクを実現
4. **状態の多様性**: Open/Half/Closedの3状態を組み合わせることで、単調にならない動きを生成

---

## 技術的な詳細

### リップシンク制御のロジック

**口の状態決定アルゴリズム**:
```
IF 現在時刻が台詞区間内:
  cycle = floor(frame / 6) % 5
  microCycle = frame % 6

  IF cycle == 0 or 1:
    → microCycle < 3 ? Open : Half
  ELSE IF cycle == 2:
    → Half
  ELSE IF cycle == 3:
    → microCycle < 3 ? Half : Closed
  ELSE:
    → microCycle < 2 ? Closed : Half
ELSE:
  → Closed (無音区間は常に口を閉じる)
```

**周期の設定理由**:
- 6フレーム（0.2秒）: 人間の自然な発話における音節の平均的な長さに近い
- 5つのサイクル: 口の開閉パターンに変化をつけ、機械的な印象を軽減

### 音声解析のパラメータ

ffmpegの`silencedetect`フィルター設定：
```
noise=-30dB    # -30dB以下を無音として検出
d=0.3          # 0.3秒以上の無音を検出
```

**パラメータ選定の理由**:
- `-30dB`: 台詞の合間にある短い息継ぎを無音として検出しすぎないための閾値
- `0.3秒`: 明確な無音区間（言葉と言葉の間）だけを検出するための最小時間

---

## エラー対応履歴

### エラー1: TypeScript型エラー
**エラー内容**:
```
ジェネリック型 'CalculateMetadataFunction' には 1 個の型引数が必要です。
```

**原因**: `CalculateMetadataFunction`に型引数を指定していなかった。

**解決策**:
```typescript
// 修正前
const calculateLipSyncMetadata: CalculateMetadataFunction = async () => {

// 修正後
const calculateLipSyncMetadata: CalculateMetadataFunction<Record<string, unknown>> = async () => {
```

### エラー2: useAudioDataのインポートエラー
**エラー内容**:
```
モジュール '@remotion/media' にエクスポートされたメンバー 'useAudioData' がありません。
```

**原因**: Remotionのバージョンにより、音声データ取得のAPIが異なる。当初、`useAudioData`を使った実装を試みたが、利用可能なAPIではなかった。

**解決策**: 音声の波形解析ではなく、ffmpegによる事前解析結果を使用する方式に変更。これにより、より正確な台詞区間の特定が可能になった。

---

## 成果と学び

### 達成したこと
✅ 音声ファイルの長さに自動対応する動画生成
✅ 台詞区間のみで口を動かす正確なリップシンク
✅ Open/Half/Closedの3状態による自然な口パク
✅ 再利用可能なコンポーネント設計

### 技術的な学び
1. **音声解析の重要性**: 単純な周期的アニメーションではなく、実際の音声内容に基づいた制御が必要
2. **ffmpegの活用**: silencedetectフィルターによる無音区間検出が、正確なリップシンクの実現に不可欠
3. **calculateMetadataの活用**: 動的なメタデータ設定により、汎用性の高いコンポーネントを実現
4. **状態管理の工夫**: 複数の台詞区間を配列で管理し、時間ベースで判定することで、保守性を向上

---

## 確認方法

### プレビュー
```bash
cd /Users/takayukinemoto/Desktop/映像制作/remotion-video
npm run dev
```
ブラウザで http://localhost:3000 にアクセスし、「LipSync」コンポジションを選択。

### レンダリング
```bash
cd /Users/takayukinemoto/Desktop/映像制作/remotion-video
npx remotion render LipSync out/LipSync.mp4
```

---

## 今後の拡張可能性

### より高度なリップシンク
1. **音素解析**: Web Speech APIや音声認識を使用し、「あ・い・う・え・お」など母音に応じた口の形を切り替え
2. **音量ベースの制御**: Web Audio APIで実際の音量を取得し、声の大きさに応じて口の開き具合を動的に調整
3. **機械学習**: 音声からリップシンクを自動生成するモデル（例: Wav2Lip）との統合

### ワークフローの改善
1. **自動音声解析**: ffmpegの解析を`calculateMetadata`内で自動実行し、手動での区間設定を不要に
2. **リアルタイムプレビュー**: Remotion Studio上で台詞区間を視覚的に調整できるUI
3. **複数キャラクター対応**: 複数の音声トラックと画像セットを管理し、対話シーンを生成

---

## 関連ファイル一覧

### 実装ファイル
- `/Users/takayukinemoto/Desktop/映像制作/remotion-video/src/LipSync.tsx` - メインコンポーネント
- `/Users/takayukinemoto/Desktop/映像制作/remotion-video/src/getAudioDuration.ts` - 音声長取得関数
- `/Users/takayukinemoto/Desktop/映像制作/remotion-video/src/Root.tsx` - コンポジション定義

### 素材ファイル
- `/Users/takayukinemoto/Desktop/映像制作/remotion-video/public/voice.mp3` - 音声ファイル
- `/Users/takayukinemoto/Desktop/映像制作/remotion-video/public/mouth-open.png` - 口を開けた画像
- `/Users/takayukinemoto/Desktop/映像制作/remotion-video/public/mouth-half.png` - 口を半分開けた画像
- `/Users/takayukinemoto/Desktop/映像制作/remotion-video/public/mouth-closed.png` - 口を閉じた画像

### 出力ファイル
- `/Users/takayukinemoto/Desktop/映像制作/remotion-video/out/LipSync.mp4` - 最終動画

---

**制作者**: Claude Code (Remotion Agent Skills)
**制作日時**: 2026年1月22日
**総作業時間**: 約1時間（問題解決含む）
