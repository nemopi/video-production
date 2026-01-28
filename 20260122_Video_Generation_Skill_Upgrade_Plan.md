# 動画生成スキル・アップデート計画書 (Video Generation Skill Upgrade Plan)
**Date**: 2026-01-22
**Project**: Legendary AI Team Evolution
**Author**: Antigravity

## 1. 目的と概要
現在の「巨匠AIチーム（Persona Skills）」は、静止画生成（T2I）において高い演出能力を発揮していますが、動画生成（I2V/T2V）においては、AIモデル（Sora, Hailuo等）のデフォルトの挙動に依存する部分が大きく、「意図した通りの動き」を制御しきれていない課題があります。

本計画は、ユーザーから提供される**専門書籍（PDF等）**や**リファレンス動画**を解析し、それを「Antigravityが実行可能なルールセット（SKILLファイル）」として体系的に実装することで、巨匠たちを**「静止画の画家」から「時間を操る映画監督」へと進化させる**ことを目的とします。

---

## 2. 重点強化領域 (3つの柱)

動画生成AI（Sora, Hailuo, Kling等）に対する「翻訳辞書」を構築し、各スキルにインストールします。

### ① カメラワークの言語化定義 (Cinematography Translation)
「ダイナミックに」等の抽象語ではなく、撮影技法を物理的な挙動記述に変換する辞書を構築します。

*   **定義すべき項目**:
    *   **移動**: Dolly, Truck, Pan, Tilt, Pedestal, Crane, Arc
    *   **レンズ**: Rack Focus（ピント送り）, Vertigo Effect（ドリー・ズーム）
    *   **歪み**: 広角(14-24mm)のパース強調 vs 望遠(85mm+)の圧縮効果
*   **実装イメージ**:
    > **User**: 「ヒッチコック的な不安なズームで」
    > **Agent**: `Dolly Zoom (Vertigo Effect): Camera moves backward speed 2.0 while zooming in lens focal length, keeping subject size constant, background perspective expands distortion.`

### ② 動きの物理法則と演技指導 (Physics & Acting Guide)
「不自然なAI動画」からの脱却を目指し、質量と感情を伴う動きを定義します。

*   **Motion Quality (動きの質)**:
    *   **重量感**: Mass, Inertia（慣性）, Gravity influence
    *   **カメラの揺れ**: Handheld shake (Organic/Chaos) vs Steadicam (Fluid/Smooth)
*   **Acting Guide (演技指導)**:
    *   **Micro-expressions**: 瞬き、視線の微細な泳ぎ、口元の震え
    *   **Timing**: 「5秒のうち、最初の2秒は静止、ラスト1秒で振り返る」といったタイムライン制御

### ③ 構造化された演出理論 (Structural Directing Rules)
書籍資料から抽出した「セオリー」を、構成のテンプレートとして組み込みます。

*   **Composition**: 三分割法、リーディングライン、ネガティブスペースの活用
*   **Editing Rhythm**: カッティングのテンポ、ショック・カット、マッチ・カットの指定

---

## 3. 各巨匠スキルへの適用イメージ (Persona 2.0)

### 🎥 Persona-Shinkai (新海誠) 2.0
*   **強化ポイント**: 「光と空気の流動」
*   **動画プロンプト辞書**:
    *   `Particle System`: 埃、雨、花びらの軌道を風速・風向で制御。
    *   `Lighting Bloom`: 逆光時のフレアの動き、雲の影（God Rays）の移動。
    *   `Focus Pull`: 雨粒（手前）からキャラクター（奥）へのピント移動。

### 🎬 Persona-Fincher (フィンチャー) 2.0
*   **強化ポイント**: 「完全制御されたカメラワーク」
*   **動画プロンプト辞書**:
    *   `Locked-down Camera`: 三脚固定のような絶対的な静止。
    *   `Machinery Precision`: 人間味を排した、ロボットアームのような正確なトラッキング。
    *   `Color Grading Consistency`: 時間経過でも崩れない冷徹な色調維持。

### 🔮 Persona-Gondry (ゴンドリー) / Yuasa (湯浅) 2.0
*   **強化ポイント**: 「物理法則の無視とループ」
*   **動画プロンプト辞書**:
    *   `Morphing`: オブジェクト形式の変化、液状化。
    *   `Loop Logic`: 夢のように繰り返されるリズム。
    *   `Perspective Distortion`: 魚眼レンズや非現実的なパース変化。

---

## 4. 今後の運用フロー (Update Workflow)

この計画を実行するために、以下のフローで開発を進めます。

1.  **Input (User)**
    *   映像制作関連の書籍PDF、技術書、または「この映画のこのシーン」というリファレンスURLを提示。
    *   「この資料から『カメラワークの章』を解析して」と指示。

2.  **Analyze (Antigravity)**
    *   資料を読み込み、AIが理解可能なプロンプトパターン（Prompt Patterns）やパラメータ設定（Parameters）を抽出。

3.  **Install (Updates)**
    *   抽出したルールを `SKILL.md`（例：`persona-shinkai/SKILL.md`）の `## Video Generation Rules` セクションに追記。
    *   または、共通スキル `skill-cinematography` を新規作成し、全ペルソナから参照させる。

4.  **Execute (Creation)**
    *   アップデートされたスキルを用いて、KamuiMCP (Sora/Hailuo) での実践テストを行う。

---

**Next Action**:
お手持ちの資料（PDFやURL）が揃いましたら、いつでもご共有ください。即座に解析と実装を開始します。
