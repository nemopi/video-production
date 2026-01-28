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
    print(f"[Manga-Gen] {msg}")
    sys.stdout.flush()

class MCPClient:
    def __init__(self, endpoint_url):
        self.endpoint_url = endpoint_url
        self.process = None
        self.response_future = {}
        self.lock = threading.Lock()

    def start(self):
        cmd = ["npx", "-y", "mcp-remote", self.endpoint_url, "--transport", "http-only", "--header", f"KAMUI-CODE-PASS: {KAMUI_PASS}"]
        self.process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=0)
        
        def stdout_reader():
            while True:
                line = self.process.stdout.readline()
                if not line: break
                try:
                    msg = json.loads(line)
                    if "id" in msg: self.response_future[msg["id"]] = msg
                except: pass
        threading.Thread(target=stdout_reader, daemon=True).start()

        # Init
        self.send("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "manga-tool", "version": "1.0"}}, 1)
        self.wait(1)
        self.send("notifications/initialized", None, None)

    def send(self, method, params, req_id):
        payload = {"jsonrpc": "2.0", "method": method}
        if params is not None: payload["params"] = params
        if req_id is not None: payload["id"] = req_id
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
        request_id = str(uuid.uuid4())
        # Submit
        log(f"Submitting: {prompt[:30]}...")
        self.send("tools/call", {"name": "nano_banana_pro_t2i_submit", "arguments": {"prompt": prompt, "image_size": "landscape_16_9", "request_id": request_id}}, 10)
        res = self.wait(10)
        
        # Poll
        poll_id = 100
        start = time.time()
        while time.time() - start < timeout:
            time.sleep(5)
            self.send("tools/call", {"name": "nano_banana_pro_t2i_status", "arguments": {"request_id": request_id}}, poll_id)
            res = self.wait(poll_id)
            poll_id += 1
            
            if res and "result" in res:
                content = res["result"].get("content", [])
                response_url = None
                for item in content:
                    if item.get("type") == "text":
                        txt = item["text"]
                        if "{" in txt:
                            try:
                                json_data = json.loads(txt)
                                if json_data.get("status") == "COMPLETED":
                                    response_url = json_data.get("response_url")
                            except: pass
                
                if response_url:
                    log(f"Fetch Result: {response_url}")
                    try:
                        with urllib.request.urlopen(response_url) as f:
                            data = json.loads(f.read().decode())
                            return data["images"][0]["url"]
                    except Exception as e:
                        log(f"Fetch failed: {e}")
        return None

def run_manga_gen():
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    
    prompts = [
        "4-panel manga style, panel 1: A futuristic young creator typing on a floating holographic keyboard, saying 'Make a Cyberpunk Movie!', vibrant anime style, high detail",
        "4-panel manga style, panel 2: A glowing nano-banana mascot AI processing data, energy sparks, a beautiful cyberpunk city image appearing in a digital bubble, anime style",
        "4-panel manga style, panel 3: A high-tech 'Creative Studio' console with mechanical arms editing video, adding camera movement and music tracks, complex machinery, anime style",
        "4-panel manga style, panel 4: The creator watching a brilliant cyberpunk movie on a huge screen with stars in eyes, 'Perfect!' written in corner, satisfying ending, vibrant anime style"
    ]
    
    client = MCPClient("https://kamui-code.ai/t2i/fal/nano-banana-pro")
    client.start()
    
    for i, p in enumerate(prompts):
        log(f"Generating Panel {i+1}...")
        url = client.generate(p)
        if url:
            path = os.path.join(OUTPUT_DIR, f"panel_{i+1}.png")
            urllib.request.urlretrieve(url, path)
            log(f"Saved: {path}")
        else:
            log(f"Failed Panel {i+1}")
    
    client.process.terminate()

if __name__ == "__main__":
    run_manga_gen()
