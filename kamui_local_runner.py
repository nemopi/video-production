import requests
import json
import time
import sys
import os
from urllib.parse import urlparse

# === CONFIGURATION ===
KAMUI_PASS = "kamui_Dpcha0qsvsuvbrdieb7Br8Bse3ufxPBNiNrDdJXokZk"
HEADERS = {
    "KAMUI-CODE-PASS": KAMUI_PASS,
    "Accept": "text/event-stream"
}

# Endpoints
NANOBANANA_URL = "https://kamui-code.ai/t2i/fal/nano-banana"
HAILUO_URL = "https://kamui-code.ai/i2v/fal/minimax/hailuo-02/pro"

# Prompts
IMAGE_PROMPT = "Photorealistic cinematic shot, Tokyo city street in winter morning, clear blue sky, crisp sunlight casting long shadows. Low angle shot of a busy intersection (Shibuya or Shinjuku), people waiting for traffic signal. Atmosphere: Cold air, high contrast, sharp details. Weather: Sunny, clear visibility. Aspect Ratio: 16:9"
VIDEO_PROMPT = "(Cinematic Movement) Camera: Slow dolly forward into the intersection. Action: People start walking as the light changes. Atmosphere: Sunlight flaring through buildings. High quality, smooth motion."

def get_rpc_endpoint(sse_url):
    print(f"Connecting to {sse_url}...")
    try:
        response = requests.get(sse_url, headers=HEADERS, stream=True, timeout=30)
        for line in response.iter_lines():
            if not line: continue
            line_str = line.decode('utf-8')
            if line_str.startswith("data:"):
                endpoint_uri = line_str.split(":", 1)[1].strip()
                response.close()
                if endpoint_uri.startswith("/"):
                    parsed = urlparse(sse_url)
                    return f"{parsed.scheme}://{parsed.netloc}{endpoint_uri}"
                return endpoint_uri
    except Exception as e:
        print(f"Error connecting to SSE: {e}")
    return None

def json_rpc(url, method, params=None):
    payload = {"jsonrpc": "2.0", "method": method, "id": int(time.time())}
    if params: payload["params"] = params
    h = HEADERS.copy()
    h["Content-Type"] = "application/json"
    try:
        res = requests.post(url, headers=h, json=payload, timeout=120)
        return res.json()
    except Exception as e:
        print(f"Error calling {method}: {e}")
        return None

def main():
    print("=== Kamui Local Runner: Tokyo Weather Video ===")
    
    # 1. Nanobanana
    nano_rpc = get_rpc_endpoint(NANOBANANA_URL)
    if not nano_rpc: return
    
    tools = json_rpc(nano_rpc, "tools/list")
    tool_name = tools["result"]["tools"][0]["name"]
    print(f"Using Image Tool: {tool_name}")
    
    print("Generating Image...")
    img_res = json_rpc(nano_rpc, "tools/call", {
        "name": tool_name,
        "arguments": {"prompt": IMAGE_PROMPT}
    })
    
    # Extract Image URL (Adjust logic based on actual response structure)
    # Assuming first content item is the image URL or text containing it
    content = img_res["result"]["content"][0]
    image_url = content.get("url") if content["type"] == "image" else content.get("text")
    print(f"Image URL: {image_url}")

    # 2. Hailuo
    hailuo_rpc = get_rpc_endpoint(HAILUO_URL)
    if not hailuo_rpc: return
    
    v_tools = json_rpc(hailuo_rpc, "tools/list")
    v_tool_name = v_tools["result"]["tools"][0]["name"]
    print(f"Using Video Tool: {v_tool_name}")
    
    print("Generating Video...")
    vid_res = json_rpc(hailuo_rpc, "tools/call", {
        "name": v_tool_name,
        "arguments": {"prompt": VIDEO_PROMPT, "image_url": image_url}
    })
    
    v_content = vid_res["result"]["content"][0]
    video_url = v_content.get("resource", {}).get("uri")
    print(f"\nSUCCESS! Video generated at:\n{video_url}")

if __name__ == "__main__":
    main()
