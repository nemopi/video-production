import sys
import os

# パスを通す
sys.path.append(os.path.join(os.getcwd(), 'creative_studio_mcp/src'))

from tools.ffmpeg_tools import zoom_image

input_path = os.path.abspath("test_output/alternative_source.png")
output_path = os.path.abspath("test_output/zoom_test.mp4")

print(f"Testing zoom_image tool...")
print(f"Input: {input_path}")
print(f"Output: {output_path}")

result = zoom_image(input_path, output_path, duration=5.0)

print(f"Result: {result}")
