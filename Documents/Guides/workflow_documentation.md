# ショートムービー制作ワークフロー：プロジェクト「来訪者 (The Visitor)」

本ドキュメントは、素材（画像・動画・音声）から1分間のサスペンスショートムービーを制作するための全工程、ストーリー構成、および実際に使用した詳細なFFmpegコマンドをまとめたものです。

## 1. プロジェクト概要
- **タイトル**: 来訪者 (The Visitor)
- **コンセプト**: 深夜のドアスコープ越しに見える「笑顔の来訪者」と、不穏な重低音の対比によるサイコサスペンス。
- **最終出力**: 1分 (60秒), 720x1280 (9:16), MP4形式

## 2. 使用素材
| 素材タイプ | ファイル名 | 用途 |
| :--- | :--- | :--- |
| **静止画** | `001.png` | イントロ、展開、クライマックス（ズーム演出用） |
| **動画** | `695f526139abdbd3d0f0f32d.mp4` | アクション、葛藤パート（メイン映像） |
| **音声** | `Heavy Tone [Stereo mix (WAV)].wav` | 全編を通したBGM |

---

## 3. ストーリー構成・演出計画 (Storyboard)

| パート | 時間 | 映像演出 (Visual) | 音声演出 (Audio) |
| :--- | :--- | :--- | :--- |
| **Intro** | 00-10s | **黒画面 + タイトル**<br>中央に白文字「AM 2:00」を表示。 | 無音（静寂の強調） |
| **Develop** | 10-25s | **静止画ズーム**<br>ドアスコープ映像。ゆっくりとズームインし、緊張感を高める。 | フェードインで開始 |
| **Action** | 25-30s | **動画素材**<br>訪問者が動く様子。少し近づく。 | BGM継続 |
| **Conflict** | 30-50s | **スロー & ノイズ**<br>「帰らない」恐怖を表現。動画をスロー再生、彩度を落とし、ノイズを追加。<br>テキスト「She never leaves.」を表示。 | BGM継続 |
| **Climax** | 50-55s | **高速ズーム & グリッチ**<br>静止画を一気にズーム。<br>強いノイズを乗せて恐怖のピークを作る。 | 音量ピーク |
| **Ending** | 55-60s | **黒画面 + 警告**<br>赤文字で「Don't Open.」。 | フェードアウト |

---

## 4. 実装プロセスと詳細コマンド (Technical Workflow)

すべての処理は `FFmpeg` コマンドラインツールを使用して実行されました。
共通設定として、出力解像度は **720x1280** に統一されています。

### Step 0: 準備
作業用の一時ディレクトリを作成します。
```bash
mkdir -p temp_output
```

### Step 1: イントロ (Intro) 生成
黒背景（`color=c=black`）にテキストを描画します。
- `drawtext`: テキスト描画フィルタ。中央揃えで配置。
```bash
ffmpeg -y -f lavfi -i color=c=black:s=720x1280:d=10 -vf "drawtext=fontfile=/System/Library/Fonts/Helvetica.ttc:text='AM 2\:00':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=(h-text_h)/2" -c:v libx264 -pix_fmt yuv420p temp_output/part1_intro.mp4
```

### Step 2: 展開 (Develop) 生成
静止画（`001.png`）を読み込み、ゆっくりとしたズームパン（`zoompan`）を適用して動画化します。
- `scale,pad`: 縦横比を維持して720x1280の画角に収め、余白を黒で埋める。
- `zoompan`: 1倍から1.5倍までゆっくりズーム。
```bash
ffmpeg -y -loop 1 -i 001.png -vf "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,zoompan=z='min(zoom+0.0015,1.5)':d=375:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=720x1280" -c:v libx264 -t 15 -pix_fmt yuv420p temp_output/part2_develop.mp4
```

### Step 3: アクション (Action) 生成
動画素材を使用。サイズ調整のみ行います。
```bash
ffmpeg -y -i 695f526139abdbd3d0f0f32d.mp4 -vf "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2" -c:v libx264 -c:a copy -t 5 -pix_fmt yuv420p temp_output/part3_action.mp4
```

### Step 4: 葛藤 (Conflict) 生成
動画素材をスローモーションにし、ノイズとテキストを加えます。
- `setpts=4.0*PTS`: 4倍のスローモーション（0.25倍速）。
- `eq`: 彩度（saturation）とコントラストを調整し、不気味なトーンに。
- `noise`: 映像にノイズを付加。
- `drawtext`: "She never leaves." のテキストを表示。`enable='gt(t,2)'` で2秒後に出現させる。
```bash
ffmpeg -y -i 695f526139abdbd3d0f0f32d.mp4 -vf "setpts=4.0*PTS,scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,eq=saturation=0.5:contrast=1.2,noise=alls=20:allf=t+u,drawtext=fontfile=/System/Library/Fonts/Helvetica.ttc:text='She never leaves.':fontcolor=white:fontsize=50:x=(w-text_w)/2:y=h-150:enable='gt(t,2)'" -c:v libx264 -an -t 20 -pix_fmt yuv420p temp_output/part4_conflict.mp4
```

### Step 5: クライマックス (Climax) 生成
静止画を高速でズームし、激しいノイズを加えます。
- `zoompan`: ズーム速度を速め、最大5倍まで拡大。
- `noise`: Step 4より強いノイズ（`alls=50`）。
```bash
ffmpeg -y -loop 1 -i 001.png -vf "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,zoompan=z='min(zoom+0.1,5)':d=125:x='iw/2':y='ih/2':s=720x1280,noise=alls=50:allf=t+u" -c:v libx264 -t 5 -pix_fmt yuv420p temp_output/part5_climax.mp4
```

### Step 6: 結末 (Ending) 生成
黒画面に赤字で警告メッセージを表示します。
```bash
ffmpeg -y -f lavfi -i color=c=black:s=720x1280:d=5 -vf "drawtext=fontfile=/System/Library/Fonts/Helvetica.ttc:text='Don\'t Open.':fontcolor=red:fontsize=60:x=(w-text_w)/2:y=(h-text_h)/2" -c:v libx264 -pix_fmt yuv420p temp_output/part6_ending.mp4
```

### Step 7: 動画の結合
生成したパートを結合するためのリストファイルを作成し、結合します。

**parts.txt の内容:**
```text
file 'part1_intro.mp4'
file 'part2_develop.mp4'
file 'part3_action.mp4'
file 'part4_conflict.mp4'
file 'part5_climax.mp4'
file 'part6_ending.mp4'
```

**結合コマンド:**
```bash
ffmpeg -y -f concat -safe 0 -i temp_output/parts.txt -c copy temp_output/video_concat.mp4
```

### Step 8: 音声合成と最終出力
結合した動画に音声を合成します。音声はループさせ、最初と最後にフェード処理を入れます。
- `-stream_loop -1`: 音声を無限ループさせる。
- `afade`: 音声のフェードイン（冒頭10秒）とフェードアウト（55秒目から5秒間）。
- `-shortest`: 動画の長さに合わせてカット。
```bash
ffmpeg -y -i temp_output/video_concat.mp4 -stream_loop -1 -i "Heavy Tone [Stereo mix (WAV)].wav" -filter_complex "[1:a]afade=t=in:st=0:d=10,afade=t=out:st=55:d=5[a]" -map 0:v -map "[a]" -c:v copy -shortest -t 60 final_movie.mp4
```

---
このワークフローにより、素材の魅力を活かした構成的なショートムービー作成が可能です。各パラメータ（ズーム速度、ノイズ量、テキスト内容）を調整することで、異なる雰囲気の動画も作成できます。
