import requests
import json
import time
import sys
import threading

KAMUI_PASS = "kamui_Dpcha0qsvsuvbrdieb7Br8Bse3ufxPBNiNrDdJXokZk"
HEADERS = {
    "KAMUI-CODE-PASS": KAMUI_PASS,
    "Accept": "text/event-stream"
}

SERVERS = {
    "file-upload": "https://kamui-code.ai/uploader/fal/sse",
    "video-analysis": "https://kamui-code.ai/video-analysis/google/gemini/sse"
}

def log(msg):
    print(f"[Tool-Check] {msg}")

def send_json_rpc(url, payload):
    h = HEADERS.copy()
    h["Content-Type"] = "application/json"
    res = requests.post(url, headers=h, json=payload)
    return res.json()

def check_server(name, sse_url):
    log(f"Connecting to {name} ({sse_url})...")
    
    try:
        # Stream=True for SSE
        response = requests.get(sse_url, headers=HEADERS, stream=True)
        post_endpoint = None
        
        for line in response.iter_lines():
            if not line:
                continue
            
            line_str = line.decode('utf-8')
            
            if line_str.startswith("event: endpoint"):
                # Next line should be data
                continue
            
            if line_str.startswith("data:"):
                endpoint_uri = line_str.split(":", 1)[1].strip()
                
                if endpoint_uri.startswith("/"):
                    from urllib.parse import urlparse
                    parsed = urlparse(sse_url)
                    base = f"{parsed.scheme}://{parsed.netloc}"
                    post_endpoint = base + endpoint_uri
                else:
                    post_endpoint = endpoint_uri
                
                log(f"Endpoint found: {post_endpoint}")
                break
        
        response.close()
        
        if not post_endpoint:
            log("Failed to get endpoint")
            return

        # Initialize
        send_json_rpc(post_endpoint, {
            "jsonrpc": "2.0", "method": "initialize", 
            "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "checker", "version": "1.0"}}, 
            "id": 1
        })
        
        send_json_rpc(post_endpoint, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        
        # List Tools
        res = send_json_rpc(post_endpoint, {"jsonrpc": "2.0", "method": "tools/list", "id": 2})
        
        tools = res.get("result", {}).get("tools", [])
        print(f"\n=== Tools for {name} ===")
        print(json.dumps(tools, indent=2, ensure_ascii=False))
        
        with open(f"{name}_tools.json", "w") as f:
            json.dump(tools, f, indent=2)
            
    except Exception as e:
        log(f"Error: {e}")

if __name__ == "__main__":
    for name, url in SERVERS.items():
        check_server(name, url)
