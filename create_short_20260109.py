import subprocess
import os
import sys

# パス設定
BASE_DIR = "/Users/takayukinemoto/Desktop/映像制作/20260109"
OUTPUT_DIR = "/Users/takayukinemoto/Desktop/映像制作/test_output"
VIDEO_INPUT = os.path.join(BASE_DIR, "e41ded5a-a0ab-4330-8269-f5984878b511.mp4")
AUDIO_INPUT = os.path.join(BASE_DIR, "2026_01_09_お昼.mp3")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "short_movie_20260109.mp4")

def create_short_movie():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print(f"--- Starting Movie Creation ---")
    
    # FFmpegコマンド: 
    # 1. 動画入力を10秒にカット (-t 10)
    # 2. 音声入力を10秒にカット (-t 10)
    # 3. 再エンコードして合成
    # 4. 音声の終わりにフェードアウトを追加 (1秒)
    
    cmd = [
        "ffmpeg", "-y",
        "-i", VIDEO_INPUT,
        "-i", AUDIO_INPUT,
        "-t", "10",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-af", "afade=t=out:st=9:d=1",
        "-shortest",
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
