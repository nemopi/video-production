import subprocess
import json
import os
import sys
import threading
import time
import uuid
import urllib.request

# 設定
OUTPUT_DIR = os.path.abspath("test_output/manga")
KAMUI_PASS = "kamui_Dpcha0qsvsuvbrdieb7Br8Bse3ufxPBNiNrDdJXokZk"

def log(msg):
    print(f"[Manga-Final] {msg}")
    sys.stdout.flush()

def read_stream(stream, callback):
    buffer = ""
    while True:
        try:
            chunk = stream.read(1)
            if not chunk: break
            buffer += chunk
            if '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                if line.strip(): callback(line.strip())
        except: break

class MCPClient:
    def __init__(self, endpoint_url):
        self.endpoint_url = endpoint_url
        self.process = None
        self.response_future = {}
        self.lock = threading.Lock()

    def start(self):
        cmd = ["npx", "-y", "mcp-remote", self.endpoint_url, "--transport", "http-only", "--header", f"KAMUI-CODE-PASS: {KAMUI_PASS}"]
        self.process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=0)
        
        def stdout_reader(line):
            try:
                msg = json.loads(line)
                if "id" in msg: self.response_future[msg["id"]] = msg
            except: pass
        threading.Thread(target=read_stream, args=(self.process.stdout, stdout_reader), daemon=True).start()
        threading.Thread(target=read_stream, args=(self.process.stderr, lambda x: None), daemon=True).start()

        # Init
        self.send("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "manga-tool-final", "version": "1.0"}}, 1)
        self.wait(1)
        self.send_notification("notifications/initialized")
        time.sleep(2) # Stabilize session

    def send(self, method, params, req_id):
        payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": req_id}
        with self.lock:
            self.process.stdin.write(json.dumps(payload) + "\n")
            self.process.stdin.flush()

    def send_notification(self, method, params=None):
        payload = {"jsonrpc": "2.0", "method": method}
        if params: payload["params"] = params
        with self.lock:
            self.process.stdin.write(json.dumps(payload) + "\n")
            self.process.stdin.flush()

    def wait(self, req_id, timeout=30):
        start = time.time()
        while time.time() - start < timeout:
            if req_id in self.response_future: return self.response_future.pop(req_id)
            time.sleep(0.1)
        return None

    def generate(self, prompt, timeout=600):
        req_id = str(uuid.uuid4())
        log(f"Submitting: {prompt[:30]}...")
        self.send("tools/call", {"name": "nano_banana_pro_t2i_submit", "arguments": {"prompt": prompt, "image_size": "landscape_16_9", "request_id": req_id}}, 10)
        res = self.wait(10)
        
        # Get request_id from response
        actual_id = None
        try:
            for item in res["result"]["content"]:
                if item.get("type") == "text":
                    txt = item["text"]
                    if "request_id" in txt:
                        actual_id = json.loads(txt)["request_id"]
                    import re
                    match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', txt)
                    if match: actual_id = match.group(0)
        except: pass
        
        if not actual_id: 
            log("Failed to get Request ID")
            return None

        # Poll
        log(f"Polling ID: {actual_id}")
        start = time.time()
        poll_idx = 100
        while time.time() - start < timeout:
            time.sleep(5)
            self.send("tools/call", {"name": "nano_banana_pro_t2i_status", "arguments": {"request_id": actual_id}}, poll_idx)
            res = self.wait(poll_idx)
            poll_idx += 1
            
            if res and "result" in res:
                content = res["result"].get("content", [])
                for item in content:
                    if item.get("type") == "text" and '"status": "COMPLETED"' in item["text"]:
                        try:
                            resp_url = json.loads(item["text"])["response_url"]
                            log(f"Fetching from: {resp_url}")
                            with urllib.request.urlopen(resp_url) as f:
                                data = json.loads(f.read().decode())
                                return data["images"][0]["url"]
                        except: pass
        return None

def run():
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    prompts = [
        "4-panel manga, panel 1: Anime style girl typing on a keyboard, bubble: 'Make a cyberpunk movie!'. Vibrant colors, futuristic room.",
        "4-panel manga, panel 2: A floating cute Banana mascot AI glowing, processing data, anime style sparks, digital city blueprint in background.",
        "4-panel manga, panel 3: Mechanical robotic arms combining a film reel and a music note icon, 'Creative Studio' logo on screen, high-tech editing room.",
        "4-panel manga, panel 4: Anime girl looking at a spectacular cyberpunk movie screen with stars in eyes, bubble: 'It's a Masterpiece!', happy atmosphere."
    ]
    client = MCPClient("https://kamui-code.ai/t2i/fal/nano-banana-pro")
    client.start()
    for i, p in enumerate(prompts):
        log(f"Generating {i+1}/4...")
        url = client.generate(p)
        if url:
            path = os.path.join(OUTPUT_DIR, f"panel_{i+1}.png")
            urllib.request.urlretrieve(url, path)
            log(f"Panel {i+1} Saved.")
        else:
            log(f"Panel {i+1} Failed.")
    client.process.terminate()

if __name__ == "__main__":
    run()
