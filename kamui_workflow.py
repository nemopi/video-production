import requests
import json
import time
import sys
import os
from urllib.parse import urlparse

# Configuration
KAMUI_PASS = "kamui_Dpcha0qsvsuvbrdieb7Br8Bse3ufxPBNiNrDdJXokZk"
HEADERS = {
    "KAMUI-CODE-PASS": KAMUI_PASS,
    "Accept": "text/event-stream"
}

SERVERS = {
    "nanobanana": "https://kamui-code.ai/t2i/fal/nano-banana",
    "hailuo": "https://kamui-code.ai/i2v/fal/minimax/hailuo-02/pro"
}

OUTPUT_DIR = "/Users/takayukinemoto/Desktop/映像制作"
IMAGE_PROMPT = "Photorealistic cinematic shot, Tokyo city street in winter morning, clear blue sky, crisp sunlight casting long shadows. Low angle shot of a busy intersection (Shibuya or Shinjuku), people wearing warm coats and scarves. Atmosphere: Cold air, high contrast, sharp details. Weather: Sunny, clear visibility. Aspect Ratio: 16:9"
VIDEO_PROMPT = "(Cinematic Movement) Camera: Slow dolly forward and slight tilt up towards the clear blue sky. Action: People walking naturally, wind gently blowing coat tails. Atmosphere: The sunlight glimmers between buildings."

def get_rpc_endpoint(sse_url):
    print(f"Connecting to {sse_url}...")
    try:
        # Long timeout for slow connections
        response = requests.get(sse_url, headers=HEADERS, stream=True, timeout=60)
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
    return None

def json_rpc(url, method, params=None):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "id": int(time.time())
    }
    if params:
        payload["params"] = params
        
    h = HEADERS.copy()
    h["Content-Type"] = "application/json"
    
    try:
        res = requests.post(url, headers=h, json=payload, timeout=120) # Long timeout for generation
        return res.json()
    except Exception as e:
        print(f"Error calling {method}: {e}")
        return None

def main():
    # 1. Image Generation (Nanobanana)
    print("\n=== Step 1: Image Generation (Nanobanana) ===")
    nano_url = get_rpc_endpoint(SERVERS["nanobanana"])
    if not nano_url:
        print("Failed to connect to Nanobanana")
        return

    # Discover tool name
    tools_res = json_rpc(nano_url, "tools/list")
    if not tools_res or "result" not in tools_res:
        print("Failed to list Nanobanana tools")
        return
        
    img_tool = tools_res["result"]["tools"][0] # Assume first tool is the one
    print(f"Found tool: {img_tool['name']}")
    
    # Call Generate Image
    print("Generating image...")
    img_res = json_rpc(nano_url, "tools/call", {
        "name": img_tool["name"],
        "arguments": {
            "prompt": IMAGE_PROMPT,
            "image_size": "landscape_16_9" # Guessing common arg, or fallback to default
        }
    })
    
    image_url = None
    if img_res and "result" in img_res:
        # Parse result (usually TextContent containing URL or ImageContent)
        content = img_res["result"]["content"][0]
        if content["type"] == "text":
            # Looking for URL in text? Or assume parsed?
            # Creating simplified assumption: user-facing tool usually returns a URL
             print(f"Result: {content['text']}")
             # Try to extract URL if simple
        elif content["type"] == "image":
             image_url = content.get("url") # Standard MCP ImageContent
             print(f"Image URL: {image_url}")
             
    # Download Image for inspection
    if image_url:
        img_data = requests.get(image_url).content
        with open(os.path.join(OUTPUT_DIR, "kamui_tokyo.png"), "wb") as f:
            f.write(img_data)
        print("Saved kamui_tokyo.png")
    else:
        print("Could not retrieve Image URL. Aborting.")
        # Fallback for demo: use local image if generation failed?
        # But we want to test the flow.
        return

    # 2. Video Generation (Hailuo)
    print("\n=== Step 2: Video Generation (Hailuo) ===")
    hailuo_url = get_rpc_endpoint(SERVERS["hailuo"])
    if not hailuo_url:
        print("Failed to connect to Hailuo")
        return

    # Discover tool name
    video_tools_res = json_rpc(hailuo_url, "tools/list")
    if not video_tools_res or "result" not in video_tools_res:
         print("Failed to list Hailuo tools")
         return
         
    vid_tool = video_tools_res["result"]["tools"][0]
    print(f"Found tool: {vid_tool['name']}")
    
    # Call Generate Video
    print("Generating video...")
    vid_res = json_rpc(hailuo_url, "tools/call", {
        "name": vid_tool["name"],
        "arguments": {
            "prompt": VIDEO_PROMPT,
            "image_url": image_url # Pass the URL from Step 1
        }
    })
    
    video_url = None
    if vid_res and "result" in vid_res:
        content = vid_res["result"]["content"][0]
        if content["type"] == "text":
             print(f"Result: {content['text']}")
             # Need to parse URL from text if it's not structured?
             # For now assume it might be embedded or structured.
        elif content["type"] == "resource": # Some tools return resources
             video_url = content["resource"]["uri"]
             print(f"Video URL: {video_url}")
        
    # Download Video
    if video_url:
         vid_data = requests.get(video_url).content
         with open(os.path.join(OUTPUT_DIR, "kamui_tokyo_movie.mp4"), "wb") as f:
             f.write(vid_data)
         print("Saved kamui_tokyo_movie.mp4")
    else:
         print("Could not retrieve Video URL.")

if __name__ == "__main__":
    main()
