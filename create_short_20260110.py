import subprocess
import os
import sys

# パス設定
BASE_DIR_VIDEO = "/Users/takayukinemoto/Desktop/映像制作/20260110"
BASE_DIR_AUDIO = "/Users/takayukinemoto/Desktop/映像制作/20260109"
OUTPUT_DIR = "/Users/takayukinemoto/Desktop/映像制作/test_output"

VIDEO_INPUT = os.path.join(BASE_DIR_VIDEO, "tokyo_weather_2026-01-10_weathernews.mp4")
AUDIO_INPUT = os.path.join(BASE_DIR_AUDIO, "2026_01_09_お昼.mp3") # 代用音声
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "short_movie_20260110.mp4")

def create_short_movie():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    if not os.path.exists(AUDIO_INPUT):
        print(f"ERROR: Audio file not found at {AUDIO_INPUT}")
        return

    print(f"--- Starting Movie Creation (20260110) ---")
    
    # FFmpegコマンド: 
    # 1. 動画入力
    # 2. 音声入力 (前回の素材)
    # 3. 動画の尺(約5秒)に合わせてカット (-shortest)
    # 4. 音声の終わりにフェードアウトを追加 (0.5秒)
    
    cmd = [
        "ffmpeg", "-y",
        "-i", VIDEO_INPUT,
        "-i", AUDIO_INPUT,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-af", "afade=t=out:st=4.5:d=0.5", # 5秒動画のラスト0.5秒でフェード
        "-shortest", # 短い方(動画)に合わせる
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
