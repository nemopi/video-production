import json
import os
import subprocess
import time
import sys
import select

# Config
KAMUI_PASS = "kamui_Dpcha0qsvsuvbrdieb7Br8Bse3ufxPBNiNrDdJXokZk"
HEADERS = {"KAMUI-CODE-PASS": KAMUI_PASS}

SERVERS = {
    "video-analysis": "https://kamui-code.ai/video-analysis/google/gemini/sse",
    "file-upload": "https://kamui-code.ai/uploader/fal/sse"
}

def log(msg):
    print(f"[Tools-Check] {msg}")

def execute_curl_post(url, headers, payload):
    cmd = ["curl", "-s", "-X", "POST", url]
    for k, v in headers.items():
        cmd.extend(["-H", f"{k}: {v}"])
    cmd.extend(["-H", "Content-Type: application/json"])
    cmd.extend(["-d", json.dumps(payload)])
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout

def get_endpoint(sse_url):
    cmd = ["curl", "-N", "-s", sse_url]
    for k, v in HEADERS.items():
        cmd.extend(["-H", f"{k}: {v}"])
    cmd.extend(["-H", "Accept: text/event-stream"])
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    post_endpoint = None
    start_time = time.time()
    
    buffer = ""
    
    try:
        while True:
            if time.time() - start_time > 10:
                log(f"Timeout connecting to {sse_url}")
                break
                
            # Non-blocking read check
            reads = [process.stdout.fileno()]
            ret = select.select(reads, [], [], 0.5)

            if reads[0] in ret[0]:
                chunk = process.stdout.read(1) # Read char by char to avoid buffering block
                if not chunk:
                    break
                buffer += chunk
                
                if "\n\n" in buffer: # End of event
                    events = buffer.split("\n\n")
                    buffer = events[-1] # Keep incomplete part
                    
                    for event_block in events[:-1]:
                        lines = event_block.strip().split("\n")
                        event_type = None
                        data_str = None
                        
                        for line in lines:
                            if line.startswith("event:"):
                                event_type = line.split(":", 1)[1].strip()
                            elif line.startswith("data:"):
                                data_str = line.split(":", 1)[1].strip()
                        
                        if event_type == "endpoint" and data_str:
                            uri = data_str
                            if uri.startswith("/"):
                                from urllib.parse import urlparse
                                parsed = urlparse(sse_url)
                                base = f"{parsed.scheme}://{parsed.netloc}"
                                post_endpoint = base + uri
                            else:
                                post_endpoint = uri
                            
                            process.terminate()
                            return post_endpoint
    finally:
        if process.poll() is None:
            process.terminate()
            
    return None

def check_tools(server_name, sse_url):
    log(f"Checking {server_name}...")
    endpoint = get_endpoint(sse_url)
    if not endpoint:
        log(f"Failed to get endpoint for {server_name}")
        return

    log(f"Endpoint: {endpoint}")
    
    # Initialize
    execute_curl_post(endpoint, HEADERS, {
        "jsonrpc": "2.0", "method": "initialize", 
        "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "checker", "version": "1.0"}}, 
        "id": 1
    })
    
    execute_curl_post(endpoint, HEADERS, {"jsonrpc": "2.0", "method": "notifications/initialized"})
    
    # List Tools
    res = execute_curl_post(endpoint, HEADERS, {"jsonrpc": "2.0", "method": "tools/list", "id": 2})
    try:
        data = json.loads(res)
        if "result" in data:
            tools = data["result"].get("tools", [])
            print(f"\n=== Tools for {server_name} ===")
            print(json.dumps(tools, indent=2, ensure_ascii=False))
            
            # Save relevant info to file for later use
            if server_name == "file-upload":
                 with open("upload_tool.json", "w") as f:
                     json.dump(tools, f)
            elif server_name == "video-analysis":
                 with open("analysis_tool.json", "w") as f:
                     json.dump(tools, f)

    except Exception as e:
        log(f"Error parsing response: {e}, Raw: {res}")

if __name__ == "__main__":
    for name, url in SERVERS.items():
        check_tools(name, url)
