# Creative Studio MCP Server

映像制作（FFmpeg操作）を自動化するMCPサーバーです。
エージェント（Claude Desktopなど）から、自然言語で動画の編集処理を呼び出すことができます。

## 機能
- `zoom_image`: 静止画からズーム動画を生成
- `apply_effect`: 動画にエフェクト（スロー、ノイズ）を適用
- `concat_videos`: 複数の動画を結合

## セットアップ手順

### 1. 前提条件
- Python 3.10以上
- FFmpeg がシステムにインストールされていること (`ffmpeg -version` で確認)

### 2. インストール
ターミナルで本ディレクトリに移動し、ライブラリをインストールします。

```bash
cd /Users/takayukinemoto/Desktop/映像制作/creative_studio_mcp
pip install -e .
```
※ 必要に応じて仮想環境(venv)を使用してください。

### 3. Claude Desktopでの設定
Claude Desktopの設定ファイル（`~/Library/Application Support/Claude/claude_desktop_config.json`）に以下を追加します。

```json
{
  "mcpServers": {
    "creative-studio": {
      "command": "python",
      "args": [
        "/Users/takayukinemoto/Desktop/映像制作/creative_studio_mcp/src/main.py"
      ]
    }
  }
}
```
※ `python` コマンドのパスは環境に合わせて絶対パス（例: `/usr/bin/python3` や venv内のpython）に書き換えることを推奨します。

## 使い方
Claudeに対して以下のように話しかけてください。
> 「このフォルダの画像を使って、10秒のズーム動画を作って」
> 「video.mp4をノイズがかかったような不気味な映像にして」
