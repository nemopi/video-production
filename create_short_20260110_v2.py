import subprocess
import os
import sys

# パス設定
BASE_DIR = "/Users/takayukinemoto/Desktop/映像制作/20260110"
OUTPUT_DIR = "/Users/takayukinemoto/Desktop/映像制作/test_output"

VIDEO_INPUT = os.path.join(BASE_DIR, "tokyo_weather_2026-01-10_weathernews.mp4")
# 新しく見つかったWAVファイルを使用
AUDIO_INPUT = os.path.join(BASE_DIR, "Control_Interlude_Songstarter_Cmin_120bpm.wav") 
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "short_movie_20260110_v2.mp4")

def create_short_movie():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    if not os.path.exists(AUDIO_INPUT):
        print(f"ERROR: Audio file not found at {AUDIO_INPUT}")
        return

    print(f"--- Starting Movie Creation V2 (Correct Audio) ---")
    
    # FFmpegコマンド: 
    # 1. 動画入力
    # 2. 音声入力 (WAV)
    # 3. 5秒でカット (-t 5) ※Safety measure
    # 4. フェードアウト (ラスト0.5秒)
    # 5. 動画の長さに合わせる (-shortest) - 今回は動画が約5秒なのでそれに合う
    
    cmd = [
        "ffmpeg", "-y",
        "-i", VIDEO_INPUT,
        "-i", AUDIO_INPUT,
        "-t", "5",         # 明示的に5秒
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-af", "afade=t=out:st=4.5:d=0.5", # 4.5秒目からフェードアウト
        OUTPUT_FILE
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"SUCCESS: {OUTPUT_FILE}")
    else:
        print(f"FAILED: {result.stderr}")

if __name__ == "__main__":
    create_short_movie()
