import json
import os
import subprocess
import sys
import time
import select
import base64
import threading

# 設定ファイルパス
SETTINGS_JSON_PATH = os.path.abspath(".gemini/settings.json")
OUTPUT_DIR = os.path.abspath("test_output")
IMAGE_PATH = os.path.join(OUTPUT_DIR, "gemini_gen.png")
VIDEO_PATH = os.path.join(OUTPUT_DIR, "gemini_video.mp4")

# ローカルツールのパス
FFMPEG_TOOLS_PATH = "/Users/takayukinemoto/Desktop/映像制作/creative_studio_mcp/src/tools/ffmpeg_tools.py"

def log(msg):
    print(f"[Gemini-Exec] {msg}")

def load_gemini_config():
    if not os.path.exists(SETTINGS_JSON_PATH):
        raise FileNotFoundError(f"{SETTINGS_JSON_PATH} not found")
    with open(SETTINGS_JSON_PATH, 'r') as f:
        config = json.load(f)
    return config

def execute_curl_post(url, headers, payload):
    cmd = ["curl", "-s", "-X", "POST", url]
    for k, v in headers.items():
        cmd.extend(["-H", f"{k}: {v}"])
    cmd.extend(["-H", "Content-Type: application/json"])
    cmd.extend(["-d", json.dumps(payload)])
    
    # log(f"Posting to {url}...")
    subprocess.run(cmd, check=True)

def run_image_generation(config):
    server_conf = config.get("mcpServers", {}).get("t2i-kamui-flux-schnell")
    if not server_conf:
        raise ValueError("Server 't2i-kamui-flux-schnell' not found in config")

    base_url = server_conf.get("httpUrl")
    if not base_url:
        raise ValueError("'httpUrl' is missing")
        
    headers = server_conf.get("headers", {})
    
    log(f"Connecting to {base_url} (Gemini Spec)...")
    
    # Curl process for SSE
    cmd = ["curl", "-N", "-s", base_url]
    for k, v in headers.items():
        cmd.extend(["-H", f"{k}: {v}"])
    cmd.extend(["-H", "Accept: text/event-stream"])
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    post_endpoint = None
    step = 0
    start_time = time.time()
    
    try:
        while True:
            # Check timeout
            if time.time() - start_time > 60:
                log("Timeout waiting for generation")
                break

            # Read line (non-blockingish via select, but readline blocks if data not available)
            # Simplification: readline() in a concise loop
            line = process.stdout.readline()
            if not line:
                if process.poll() is not None:
                    break
                continue
                
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
                data_line = process.stdout.readline().strip()
                if data_line.startswith("data:"):
                    data_str = data_line.split(":", 1)[1].strip()
                    
                    if event_type == "endpoint":
                        # Endpoint discovery
                        uri = data_str
                        if uri.startswith("/"):
                            from urllib.parse import urlparse
                            parsed = urlparse(base_url)
                            base = f"{parsed.scheme}://{parsed.netloc}"
                            post_endpoint = base + uri
                        else:
                            post_endpoint = uri
                        log(f"Endpoint: {post_endpoint}")
                        
                        # Send Initialize
                        execute_curl_post(post_endpoint, headers, {
                            "jsonrpc": "2.0", "method": "initialize", 
                            "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "gemini-tester", "version": "1.0"}}, 
                            "id": 1
                        })
                        
                    elif event_type == "message":
                        msg = json.loads(data_str)
                        
                        if msg.get("id") == 1: # Init response
                            execute_curl_post(post_endpoint, headers, {"jsonrpc": "2.0", "method": "notifications/initialized"})
                            execute_curl_post(post_endpoint, headers, {"jsonrpc": "2.0", "method": "tools/list", "id": 2})
                            
                        elif msg.get("id") == 2: # List response
                            tools = msg["result"].get("tools", [])
                            if tools:
                                tool_name = tools[0]["name"]
                                log(f"Calling tool: {tool_name}")
                                execute_curl_post(post_endpoint, headers, {
                                    "jsonrpc": "2.0", "method": "tools/call",
                                    "params": {
                                        "name": tool_name,
                                        "arguments": {
                                            "prompt": "Cyberpunk city street, neon lights, 5 sec video style",
                                            "image_size": "landscape_16_9"
                                        }
                                    }, 
                                    "id": 3
                                })
                            else:
                                log("No tools found")
                                return False

                        elif msg.get("id") == 3: # Tool response
                            if "result" in msg:
                                log("Generation Result Received")
                                content = msg["result"].get("content", [])
                                for item in content:
                                    if item.get("type") == "image":
                                        img_data = base64.b64decode(item["data"])
                                        with open(IMAGE_PATH, "wb") as f:
                                            f.write(img_data)
                                        log(f"Saved image to {IMAGE_PATH}")
                                        process.terminate()
                                        return True
                                    elif item.get("type") == "text":
                                        text = item["text"]
                                        log(f"Got text result: {text}")
                                        # URL handling
                                        if "http" in text:
                                            import re
                                            urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', text)
                                            if urls:
                                                subprocess.run(["curl", "-s", "-o", IMAGE_PATH, urls[0]], check=True)
                                                log(f"Downloaded image to {IMAGE_PATH}")
                                                process.terminate()
                                                return True
                                process.terminate()
                                return True
                            elif "error" in msg:
                                log(f"Tool Error: {msg['error']}")
                                process.terminate()
                                return False
    finally:
        if process.poll() is None:
            process.terminate()
            
    return False

def run_local_video_conversion():
    log("Starting local video conversion...")
    
    # クイックにZoom機能を呼び出すために、ffmpeg_tools.pyをインポートして使うか、
    # 既存の test_zoom.py を流用/修正して実行する。
    # ここでは ffmpeg_tools.py の zoom_image を直接呼び出すラッパーを書く。
    
    # pythonpath hack
    sys.path.append(os.path.dirname(FFMPEG_TOOLS_PATH))
    
    # 簡易的なスクリプトを生成して実行する（依存関係解決のため）
    script_content = f"""
import sys
import os
sys.path.append("{os.path.dirname(os.path.dirname(FFMPEG_TOOLS_PATH))}") # src dir
from tools.ffmpeg_tools import zoom_image

input_path = "{IMAGE_PATH}"
output_path = "{VIDEO_PATH}"

if not os.path.exists(input_path):
    print("Input image not found")
    sys.exit(1)

print(f"Zooming {{input_path}} -> {{output_path}}")
result = zoom_image(input_path, output_path, duration=5.0, zoom_factor=1.5)
print(result)
"""
    tmp_script = os.path.join(OUTPUT_DIR, "exec_zoom.py")
    with open(tmp_script, "w") as f:
        f.write(script_content)
        
    subprocess.run([sys.executable, tmp_script], check=True)
    log(f"Video created at {VIDEO_PATH}")


def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    try:
        config = load_gemini_config()
        if run_image_generation(config):
            run_local_video_conversion()
            log("User Request Completed Successfully!")
        else:
            log("Image generation failed.")
            sys.exit(1)
            
    except Exception as e:
        log(f"Execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
