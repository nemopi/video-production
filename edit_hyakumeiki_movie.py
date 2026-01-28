import subprocess
import os

# 設定
BASE_DIR = os.path.abspath("test_output/hyakumeiki")
OUTPUT_FILE = os.path.abspath("test_output/hyakumeiki_movie.mp4")

def concat_clips():
    clips = [f"clip_{i+1}.mp4" for i in range(4)]
    
    # Check exisistence
    valid_clips = []
    for c in clips:
        path = os.path.join(BASE_DIR, c)
        if os.path.exists(path):
            valid_clips.append(path)
        else:
            print(f"Warning: {c} not found.")

    if not valid_clips:
        print("No clips found.")
        return

    # Create list file for ffmpeg concat demuxer
    list_path = os.path.join(BASE_DIR, "concat_list.txt")
    with open(list_path, "w") as f:
        for path in valid_clips:
            f.write(f"file '{path}'\n")

    print(f"Concatenating {len(valid_clips)} clips...")
    
    # FFmpeg Concat
    # -safe 0 is needed for absolute paths
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_path,
        "-c", "copy",
        OUTPUT_FILE
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"SUCCESS: {OUTPUT_FILE}")
        # Clean up list file
        if os.path.exists(list_path): os.remove(list_path)
    else:
        print(f"FAILED: {result.stderr}")

if __name__ == "__main__":
    concat_clips()
