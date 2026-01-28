import subprocess
import json
import threading
import sys
import os
import time

# 設定
MCP_SERVER_URL = "https://kamui-code.ai/t2i/fal/flux/schnell/sse"
API_KEY = "kamui_Dpcha0qsvsuvbrdieb7Br8Bse3ufxPBNiNrDdJXokZk"
PROMPT = "Cyberpunk city street, neon lights, futuristic atmosphere, highly detailed"
OUTPUT_IMAGE_PATH = os.path.abspath("test_output/antigravity_gemini_gen.png")

def log(msg):
    print(f"[Gemini-MCP] {msg}")

def send_post(url, payload):
    # curlを使用してPOST送信 (SSL問題回避)
    cmd = [
        "curl", "-s", "-X", "POST",
        "-H", f"KAMUI-CODE-PASS: {API_KEY}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload),
        url
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        # log(f"Posted to {url} payload size: {len(json.dumps(payload))}")
    except subprocess.CalledProcessError as e:
        log(f"Error posting: {e}")

def run_curl_mcp_client():
    log(f"Connecting to {MCP_SERVER_URL} via curl...")
    
    # curlを使用してSSEストリームを受信
    cmd = [
        "curl", "-N", "-s", 
        "-H", f"KAMUI-CODE-PASS: {API_KEY}",
        "-H", "Accept: text/event-stream",
        MCP_SERVER_URL
    ]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
    
    post_endpoint = None
    step = 0 # 0:init, 1:initialized, 2:list_tools, 3:call_tool, 4:done

    try:
        while True:
            line = process.stdout.readline()
            if not line:
                break
            
            line = line.strip()
            if not line:
                continue

            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
                # data行を読む
                data_line = process.stdout.readline().strip()
                if data_line.startswith("data:"):
                    data_content = data_line.split(":", 1)[1].strip()
                    
                    # --- Event Handlers ---
                    
                    if event_type == "endpoint":
                        # エンドポイント受信
                        uri = data_content
                        # 相対パス対応
                        if uri.startswith("/"):
                            from urllib.parse import urlparse
                            parsed = urlparse(MCP_SERVER_URL)
                            base = f"{parsed.scheme}://{parsed.netloc}"
                            post_endpoint = base + uri
                        else:
                            post_endpoint = uri
                        
                        log(f"Endpoint received: {post_endpoint}")
                        
                        # Initialize送信
                        send_post(post_endpoint, {
                            "jsonrpc": "2.0",
                            "method": "initialize",
                            "params": {
                                "protocolVersion": "2024-11-05",
                                "capabilities": {},
                                "clientInfo": {"name": "antigravity-curl-client", "version": "1.0"}
                            },
                            "id": 1
                        })
                        step = 1

                    elif event_type == "message":
                        try:
                            msg = json.loads(data_content)
                            
                            # Initialize Response -> Send initialized & List Tools
                            if msg.get("id") == 1 and "result" in msg:
                                log("Initialized. Sending notifications...")
                                send_post(post_endpoint, {
                                    "jsonrpc": "2.0",
                                    "method": "notifications/initialized"
                                })
                                log("Listing tools...")
                                send_post(post_endpoint, {
                                    "jsonrpc": "2.0",
                                    "method": "tools/list",
                                    "id": 2
                                })
                                step = 2
                            
                            # List Tools Response -> Call Tool
                            elif msg.get("id") == 2 and "result" in msg:
                                tools = msg["result"].get("tools", [])
                                if tools:
                                    tool_name = tools[0]["name"]
                                    log(f"Generating image with tool: {tool_name}")
                                    send_post(post_endpoint, {
                                        "jsonrpc": "2.0",
                                        "method": "tools/call",
                                        "params": {
                                            "name": tool_name,
                                            "arguments": {
                                                "prompt": PROMPT,
                                                "image_size": "landscape_16_9"
                                            }
                                        },
                                        "id": 3
                                    })
                                    step = 3
                            
                            # Tool Call Response
                            elif msg.get("id") == 3:
                                if "result" in msg:
                                    log("Generation success!")
                                    content = msg["result"].get("content", [])
                                    for item in content:
                                        if item.get("type") == "image":
                                            import base64
                                            img_data = base64.b64decode(item["data"])
                                            with open(OUTPUT_IMAGE_PATH, "wb") as f:
                                                f.write(img_data)
                                            log(f"Image saved to {OUTPUT_IMAGE_PATH}")
                                            process.terminate()
                                            sys.exit(0)
                                        elif item.get("type") == "text":
                                            text = item["text"]
                                            log(f"Result text: {text}")
                                            # URLが含まれていればダウンロード (curlで)
                                            if "http" in text:
                                                import re
                                                urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', text)
                                                if urls:
                                                    img_url = urls[0]
                                                    log(f"Downloading from {img_url} via curl...")
                                                    subprocess.run(["curl", "-s", "-o", OUTPUT_IMAGE_PATH, img_url], check=True)
                                                    log(f"Image saved to {OUTPUT_IMAGE_PATH}")
                                                    process.terminate()
                                                    sys.exit(0)
                                    process.terminate()
                                    sys.exit(0)
                                elif "error" in msg:
                                    log(f"Tool Error: {msg['error']}")
                                    process.terminate()
                                    sys.exit(1)

                        except json.JSONDecodeError:
                            pass

    except KeyboardInterrupt:
        process.terminate()

if __name__ == "__main__":
    run_curl_mcp_client()
