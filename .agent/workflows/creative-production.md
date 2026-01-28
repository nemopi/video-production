---
description: 巨匠AIチームを使って、クリエイティブな制作とリファインを行う完全サイクル
---

# 巨匠クリエイティブチーム・制作サイクル (Legendary Creative Cycle)

このワークフローは、実装された専門ペルソナ（巨匠AI）たちを指揮し、高品質なクリエイティブを制作するための手順です。

1.  **目的の定義 (Define Objective)**
    - 作りたいコンテンツの種類（映像、音楽、シーン）と、表現したい感情やスタイルを決めます。
    - 担当させる「メイン監督」を選びます（例：サスペンスならHitchcock、Lo-fiならNujabes）。

2.  **ペルソナ召喚・プランニング (Summon & Planning)**
    - 対象のスキルファイルを読み込みます： `view_file .agent/skills/persona-[name]/SKILL.md`
    - ペルソナの「思考アルゴリズム」を使って、プロンプトや構成案を作成させます。
    - *指示例*: 「Hitchcock監督、このシーンのカメラ割り（ブロッキング）を考えてください」

3.  **Antigravityによる翻訳 (Antigravity Translation)**
    - コアスキルを読み込みます： `view_file .agent/skills/antigravity-core/SKILL.md`
    - ペルソナの抽象的な指示を、具体的な技術パラメータ（Python, ffmpeg, MCPツール）に変換します。
    - *指示例*: 「『切ない夕暮れ』という指示を、具体的なライティング設定とカラーコードに変換して」

4.  **実行 (Execution)**
    - `generate_image`, `run_command` (ffmpeg), `Remotion` などのツールを使って、実際に素材を作成します。

5.  **ペルソナによるレビュー (Verification Phase)**
    - 生成されたものを、ペルソナの「行動指針」や「NGリスト」に基づいてチェックさせます。
    - *指示例*: 「Gondry監督、この映像はCGっぽすぎませんか？ もっと手作り感を出すにはどうすればいいですか？」

6.  **仕上げ (Final Polish)**
    - レビューに基づく修正を行い、完成させます。
