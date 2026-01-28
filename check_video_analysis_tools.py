import json
import os
import subprocess
import time
import sys

SERVER_URL = "https://kamui-code.ai/video-analysis/google/gemini/sse"
HEADERS = {
    "KAMUI-CODE-PASS": "kamui_Dpcha0qsvsuvbrdieb7Br8Bse3ufxPBNiNrDdJXokZk"
}

def log(msg):
    print(f"[Analyze-Tools] {msg}")

def execute_curl_post(url, headers, payload):
    cmd = ["curl", "-s", "-X", "POST", url]
    for k, v in headers.items():
        cmd.extend(["-H", f"{k}: {v}"])
    cmd.extend(["-H", "Content-Type: application/json"])
    cmd.extend(["-d", json.dumps(payload)])
    subprocess.run(cmd, check=True)

def list_tools():
    cmd = ["curl", "-N", "-s", SERVER_URL]
    for k, v in HEADERS.items():
        cmd.extend(["-H", f"{k}: {v}"])
    cmd.extend(["-H", "Accept: text/event-stream"])
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    post_endpoint = None
    start_time = time.time()
    
    try:
        while True:
            if time.time() - start_time > 30:
                log("Timeout")
                break

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
                        uri = data_str
                        if uri.startswith("/"):
                            from urllib.parse import urlparse
                            parsed = urlparse(SERVER_URL)
                            base = f"{parsed.scheme}://{parsed.netloc}"
                            post_endpoint = base + uri
                        else:
                            post_endpoint = uri
                        log(f"Endpoint: {post_endpoint}")
                        
                        # Initialize
                        execute_curl_post(post_endpoint, HEADERS, {
                            "jsonrpc": "2.0", "method": "initialize", 
                            "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "tool-checker", "version": "1.0"}}, 
                            "id": 1
                        })
                        
                    elif event_type == "message":
                        msg = json.loads(data_str)
                        if msg.get("id") == 1:
                            execute_curl_post(post_endpoint, HEADERS, {"jsonrpc": "2.0", "method": "notifications/initialized"})
                            execute_curl_post(post_endpoint, HEADERS, {"jsonrpc": "2.0", "method": "tools/list", "id": 2})
                            
                        elif msg.get("id") == 2:
                            tools = msg["result"].get("tools", [])
                            print("\n=== Available Tools ===")
                            print(json.dumps(tools, indent=2, ensure_ascii=False))
                            process.terminate()
                            return

    finally:
        if process.poll() is None:
            process.terminate()

if __name__ == "__main__":
    list_tools()
