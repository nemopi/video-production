# 巨匠AIチーム構築・要件定義書兼開発レポート

**作成日**: 2026年1月21日
**作成者**: Antigravity (with User)
**プロジェクト**: Legendary Creative Team Implementation

---

## 1. プロジェクト概要
本プロジェクトの目的は、映画・音楽・アニメーションにおける「伝説的な巨匠（Legendary Creators）」の人格とスキルをAIエージェントとして再現し、それらを指揮して高品質なクリエイティブを自動・半自動で生成するシステムを構築することである。

**核心コンセプト**:
> 「抽象的な巨匠の思考」を「具体的なエンジニアリングコード」に変換する階層構造を作る。

---

## 2. システムアーキテクチャ (System Architecture)

システムは以下の3層構造で成立している。

### Layer 1: The Director (翻訳エンジン)
- **Component**: `antigravity-core`
- **Role**: チームの総監督兼技術実装者。
- **Function**:
    - 巨匠たちの抽象的な言葉（「もっとエモく」「アナログな夢のように」）を、具体的な実行パラメータ（Pythonコード, ffmpeg引数, MCPツール引数）に翻訳する。
    - **Bridge the Gap**: `Emotional Adjective` -> `Technical Parameter`.

### Layer 2: The Cast (専門ペルソナ)
- **Component**: `.agent/skills/persona-*`
- **Role**: 特定の領域に特化したクリエイティブ・ディレクター。
- **Teams**:
    - **Team A: Visual & Storytelling** (映像、演出、物語)
        - **Hitchcock**: サスペンス、情報の非対称性、視線の演出。
        - **Yuasa (Masaaki)**: アニメーション、パースの歪み、サイケデリックな色彩。
        - **Shinkai (Makoto)**: 背景美術、光の解像度、距離と感情の同期。
        - **Fincher (David)**: 編集の精緻さ、カメラの安定性、冷徹なトーン。
    - **Team B: Sound & Groove** (音楽、リズム、同期)
        - **Nakata (Yasutaka)**: J-Pop構築、ボーカルチョップ、中毒性。
        - **Nujabes**: Lo-fi Hip Hop、サンプリングの温かみ、哀愁。
        - **Quincy (Jones)**: ポップスの王道、グルーヴの隙間、人間味。
        - **Gondry (Michel)**: アナログなギミック、幾何学的な同期、DIY精神。

### Layer 3: The Workbench (実行環境)
- **Tools**: Remotion (動画生成), ffmpeg (映像処理), Python (スクリプト), MCP (外部ツール連携)。
- **Workflow**: `.agent/workflows/` に定義された標準手順。

---

## 3. ペルソナ定義要件 (Persona Definition Requirements)

新しい巨匠ペルソナを追加（Add Member）する際は、以下のデータ構造を含むスキルファイルを作成する。

### 必須項目
1.  **Profile & Tone (人格・口調)**
    - 一人称、話し方の癖、絶対に言わないこと（NGワード）。
    - ユーザーをどう呼ぶか（「君」「相棒」「諸君」）。
2.  **Thought Algorithm (思考アルゴリズム)**
    - その巨匠が「無意識に行っている判断プロセス」を言語化したもの。
    - 例：Yuasaなら「水をゼリーとして描く」、Gondryなら「CGを段ボールに置き換える」。
3.  **Core Philosophy (核心的哲学)**
    - 美学の根源。何をもって「成功」とし、何を「失敗（駄作）」とするか。
4.  **Action Guidelines (具体的な翻訳辞書)**
    - Antigravityがコードに落とし込むための直接的な指示。
    - **Visual**: ライティング、カメラワーク、色使いの具体的指定。
    - **Audio**: BPM、楽器構成、ミキシングのバランス。

### ファイル形式
- パス: `.agent/skills/persona-[name]/SKILL.md`
- ヘッダー: YAML形式で `name` と `description` を定義。

---

## 4. 運用ワークフロー (Operational Workflow)

標準化された制作サイクルは以下の通り。

1.  **Summon (召喚)**: 
    - ユーザーが目的（例：「切ないリップシンク動画」）を提示し、担当ペルソナ（例：Shinkai）を指名。
2.  **Planning (構想)**: 
    - ペルソナスキルを読み込み、演出プラン（Atmosphere, Camera, Timing）を立案。
3.  **Translation (翻訳)**: 
    - `antigravity-core` スキルを使用し、演出プランをコード（Remotion, Python）に変換。
4.  **Execution (実行)**: 
    - コードを実行し、成果物を生成。
5.  **Critique (批評)**: 
    - ペルソナの視点で成果物をレビューし、ブラッシュアップ。

---

## 5. 実証実験レポート: Shinkai Lip Sync
**実施日**: 2026/01/21
**内容**: 静止画3枚と音声データからのリップシンク動画生成。

### 適用されたペルソナロジック (Shinkai Logic)
- **解像度と空気感**: 単なる黒背景ではなく、CSSグラデーションで「夕暮れの空」を生成。
- **距離への介入**: 画面手前にパーティクル（光の塵）を飛ばし、奥行きを作ることで「距離」を演出。
- **光の演出**: レンズフレア風のオーバーレイ処理を追加。
- **カメラワーク**: 5秒間でわずかにズームインする「感情のフォーカス」。

### 結果
- Remotionにより完全自動で描画完了。
- ユーザー評価: 「おお、すごいすごい！」（合格）

---

## 6. 実証実験レポート: Twilight Station (Cinemagraph)
**実施日**: 2026/01/21
**内容**: 静止画1枚（AI生成）に対し、Remotionで微細なアニメーション効果を加えて「動く絵画」化。

### 使用ツール
1.  **Image Generation**: `gemini-3-pro-image` (Antigravity Native Tool)
    - *Prompt*: Makoto Shinkai style, anime art background, empty suburban train station platform at blue hour twilight...
2.  **Animation Engine**: Remotion (React-based Video)

### 適用されたペルソナロジック (Shinkai Logic)
- **Concept**: 「一枚の絵の中に永遠の時間を閉じ込める」。派手なアクションではなく、環境の微細な変化（鼓動）を描く。
- **Layering Technique**:
    1.  **Particles**: `random()` と `Math.sin()` を用いて、不規則に浮遊・明滅する光の粒子（蛍/塵）を80個生成。
    2.  **Train Shadow**: `linear-gradient` と `mixBlendMode: 'overlay'` を使い、画面外を電車が通過する際の「光と影の帯」を表現。
    3.  **Breathing Light**: レンズフレアの不透明度を正弦波で揺らし、空間自体が呼吸しているような演出。

### 結果
- 10秒間のループ映像として出力。
- 静止画の美しさを損なわず、リッチな時間経過を感じさせる映像表現に成功。

---

## 7. 今後の拡張計画 (Future Roadmap)

### 新規メンバーの追加方法
1. 対象の巨匠の「インタビュー」「制作の裏話」「名言」を収集する。
2. 上記「3. ペルソナ定義要件」に従って構造化する（特に「思考アルゴリズム」の言語化が重要）。
3. `.agent/skills/persona-[新メンバー]` を作成。
4. `antigravity-core` に翻訳ガイドラインを追加。

### チーム連携 (Collaboration)
- **コラボレーション機能**:「Fincherの映像 × Nakataの音楽」のように、スキルを掛け合わせて同時読み込みするワークフローの整備。

以上
