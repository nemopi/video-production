import glob
import subprocess
import os

IMAGE_DIR = "/Users/takayukinemoto/Desktop/映像制作/temp_weather_data"
OUTPUT_FILE = "/Users/takayukinemoto/Desktop/映像制作/temp_output/weather_ocr_result.txt"

def run_ocr():
    images = sorted(glob.glob(os.path.join(IMAGE_DIR, "*.jpg")))
    
    with open(OUTPUT_FILE, "w") as f_out:
        for img_path in images:
            print(f"Processing {img_path}...")
            # Fallback to English/snum as jpn is not installed
            try:
                res = subprocess.run(["tesseract", img_path, "stdout", "-l", "eng", "--psm", "6"], capture_output=True, text=True)
                text = res.stdout.strip()
                
                f_out.write(f"--- File: {os.path.basename(img_path)} ---\n")
                f_out.write(text + "\n\n")

            except Exception as e:
                f_out.write(f"Error processing {os.path.basename(img_path)}: {e}\n\n")

    print(f"OCR completed. Result saved to {OUTPUT_FILE}")
    with open(OUTPUT_FILE, "r") as f:
        print(f.read())

if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    run_ocr()
