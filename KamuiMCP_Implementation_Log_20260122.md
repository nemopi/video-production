# KamuiMCP Implementation Log & Lessons Learned
**Date**: 2026-01-22
**Project**: Tokyo Weather / Rainy Tokyo Short Movie
**Author**: Antigravity

## 1. Overview
本日のセッションでは、KamuiMCPを使用した2つの動画生成タスク（天気予報、雨の東京ショート）を実施しました。
特に「Sora2Pro (I2V)」の実装において、**解像度の不一致**と**リモート環境の制約**により失敗し、代替手段（Hailuo 2.3 Pro）への切り替えを行いました。
本ドキュメントは、その失敗原因、試行錯誤のプロセス、および確立された正しい接続手順を将来のリファレンスとして構造化したものです。

---

## 2. 接続・実行環境の確立 (The Golden Path)

### 成功した接続方法
以前のセッション（`stdio_test_workflow_v2.py`）に基づき、以下の構成が**唯一の安定した接続方法**であることが確定しました。

- **Protocol**: Stdio (Standard Input/Output) over `npx mcp-remote`
- **Runner Script**: Python `subprocess.Popen`
- **Command Pattern**:
  ```python
  cmd = ["npx", "-y", "mcp-remote", ENDPOINT_URL, "--transport", "http-only", "--header", f"KAMUI-CODE-PASS: {PASS}"]
  ```
- **重要**: `requests`ライブラリや`curl`によるSSE/HTTP直接接続は、SSL証明書エラーやタイムアウトにより**不安定**であるため使用しないこと。

### 関連スクリプト
- `kamui_stdio_runner.py`: 基本的なNanobanana + Hailuoランナー
- `kamui_sora_runner.py`: Sora用（失敗したが構造は正しい）
- `kamui_hailuo_runner.py`: Hailuo 2.3 Pro用（成功）

---

## 3. Sora2Pro I2V 実装における失敗と反省

### 3.1. 解像度不一致 (Resolution Mismatch)
**事象**:
Nanobanana Proで生成した画像を `openai_sora_submit` (I2V) に渡した際、以下のエラーで拒否された。

```json
"error": {
  "message": "Inpaint image must match the requested width and height",
  "type": "invalid_request_error"
}
```

**原因**:
1.  **Sora2Proの厳密性**: Sora2Pro (I2V) は、入力画像と出力動画の解像度が**完全に一致**していることを要求する。
    - Supported: `720x1280`, `1280x720`, `1024x1792`, `1792x1024`
    - Rejected: `1080x1920` (Standard FHD)
2.  **Nanobanana Proの出力**: `image_size: "portrait_16_9"` を指定しても、モデル内部でアップスケールや調整が行われ、Soraが期待するピクセル数（例: 1024x1792）と数ピクセルでも異なるとエラーになる可能性がある。
3.  **連携の欠如**: 生成パイプラインにおいて、「T2Iの出力サイズを強制する」または「I2V前にリサイズする」工程が欠落していた。

### 3.2. リモート環境でのリサイズ障壁 (Resize & Upload Barrier)
**試行した解決策**:
ローカル（Agent環境）で画像をダウンロードし、FFmpegで `720x1280` にリサイズしてから、KamuiMCPのアップローダー (`kamui_file_upload_fal`) で公開URL化してSoraに渡そうとした。

**失敗原因**:
- **FAL API Keyの不在**: `kamui_file_upload_fal` 自体はローカルの `.env` や環境変数から `FAL_KEY` を参照してアップロードを行う仕様であった。
- Agent環境には `KAMUI-CODE-PASS` はあるが、ユーザー個人の `FAL_KEY` は設定されていないため、アップロードが機能しなかった。

---

## 4. 成功した代替案 (Hailuo 2.3 Pro)

**採用理由**:
- **柔軟性**: `hailuo_23_pro_image_to_video` モデルは、入力画像の解像度に対して寛容であり、自動的にクロップやリサイズを行って動画を生成できる。
- **画質**: 現時点での最高峰モデルの一つであり、Sora2Proの有力な代替となる。

**結果**:
Nanobanana Proの高解像度画像をそのまま入力として受け入れ、エラーなく高品質なI2V生成に成功した。

---

## 5. 次回以降のTodo & Best Practices

1.  **Check Tool Compatibility First**:
    - Sora2Proを使用する場合、必ず**入力画像の解像度をSoraのサポートリスト (`720x1280`等) に完全準拠**させる。
    - T2Iツール（Nanobanana等）に対し、`image_size: {width: 720, height: 1280}` のように明示的な数値指定が可能か検証し、依存する。

2.  **Explicit Resolution Handling**:
    - パイプラインを組む際、「何となく高画質」ではなく、「ピクセル単位での一致」を設計に含める。
    - 「Pro」モデルは標準解像度（FHD 1080p）を出す傾向があるが、Soraはモバイル最適化サイズ（720p/HD+）を好む場合がある競合を理解する。

3.  **Fallback Strategy**:
    - **Plan A**: Sora2Pro (解像度一致前提)
    - **Plan B**: Hailuo 2.3 Pro (柔軟性優先)
    - **Plan C**: T2V (画像を使用せず、プロンプトのみで再生成)
    - 今回は Plan B が最良の解であった。

4.  **Do Not Assume Upload Capability**:
    - Agent環境から外部へのファイルアップロード（リサイズ後の画像など）は、APIキーへの依存があるため、原則として**「URL to URL」のクラウド完結型パイプライン**を目指すこと。

## 6. 保存ファイル一覧（今回の成果物）

| ファイル名 | 説明 | 状態 |
| :--- | :--- | :--- |
| `kamui_stdio_runner.py` | 接続成功の原型スクリプト | ✅ Working |
| `kamui_sora_runner.py` | Sora2Pro I2V試行（解像度エラー） | ❌ Resolution Error |
| `kamui_hailuo_runner.py` | Hailuo 2.3 Pro I2V (成功版) | ✅ Working |
| `test_upload_sora.py` | アップロード試行（Keyエラー） | ❌ Key Error |
| `kamui_tokyo_movie.mp4` | 天気予報動画 (Nanobanana + Hailuo) | ✅ Complete |
| `kamui_tokyo_rain_movie_hailuo.mp4` | 雨の東京ショート (Nanobanana + Hailuo) | ✅ Complete |

---

# 超重要設定事項 (Unified Configuration & Backup Rules)

以下は、本プロジェクトにおける構成管理とバックアップに関する決定事項の記録です。（2026-01-09時点の合意事項の再確認含む）

### 1. マスター設定ファイル: `mcp_config.json`
- **経緯**: `claude_desktop_config_stdio.json` を `mcp_config.json` にリネーム（コピー）し、これを「正解（Stdio版）」の設定ファイルとして統一しました。
- **運用ルール**:
    - デスクトップにある `mcp_config.json` が**マスターデータ**です。
    - ドキュメント内の記述はすべて `mcp_config.json` に統一します。
    - Claude Desktop App で使用する場合は、このファイルを設定フォルダにコピーし、`claude_desktop_config.json` という名前で保存して使用してください。

### 2. バックアップ記録 (`backup_20260109` & `backup_20260122`)
プロジェクトの区切りとして、これまでに以下のバックアップが実施されています。本日（2026-01-22）も同様のバックアップを実施します。

- **`backup_20260122/`** (今回作成):
    - `brain_docs/`: 本日の全ての思考ログ、レポート、タスクリスト。
    - `project_files/`: `mcp_config.json`、成功した `kamui_hailuo_runner.py`、および生成された動画ファイル。

このバックアップ体制により、プロジェクトの状態を日次で保全します。

以上
