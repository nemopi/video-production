import subprocess
import json
import os
import sys
import threading
import time
import uuid
import base64
import urllib.request

# 設定
BASE_DIR = os.path.abspath("test_output/hyakumeiki")
KAMUI_PASS = "kamui_Dpcha0qsvsuvbrdieb7Br8Bse3ufxPBNiNrDdJXokZk"

def log(msg):
    print(f"[Hyakumeiki-Vid] {msg}")
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

        self.send("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "hyakumeiki-vid", "version": "1.0"}}, 1)
        self.wait(1)
        self.send_notification("notifications/initialized")
        time.sleep(2)

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

    def generate(self, prompt, image_path, timeout=600):
        # Base64 Encode
        with open(image_path, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode('utf-8')
        image_url = f"data:image/png;base64,{b64_data}"

        req_id = str(uuid.uuid4())
        log(f"Submitting: {prompt[:30]}...")
        # Try passing image_url as data URI
        self.send("tools/call", {"name": "hailuo_02_fast_submit", "arguments": {"prompt": prompt, "image_url": image_url, "request_id": req_id}}, 10)
        res = self.wait(10)
        
        # Get request_id
        actual_id = None
        try:
            for item in res["result"]["content"]:
                if item.get("type") == "text":
                    txt = item["text"]
                    if "request_id" in txt: actual_id = json.loads(txt)["request_id"]
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
            time.sleep(10) # Video takes longer
            self.send("tools/call", {"name": "hailuo_02_fast_status", "arguments": {"request_id": actual_id}}, poll_idx)
            res = self.wait(poll_idx)
            poll_idx += 1
            
            if res and "result" in res:
                content = res["result"].get("content", [])
                for item in content:
                    if item.get("type") == "text" and '"status": "COMPLETED"' in item["text"]:
                        try:
                            resp_url = json.loads(item["text"])["response_url"]
                            log(f"Fetching result from: {resp_url}")
                            with urllib.request.urlopen(resp_url) as f:
                                data = json.loads(f.read().decode())
                                return data["video"]["url"]
                        except: pass
        return None

def run():
    if not os.path.exists(BASE_DIR):
        log("Image directory not found.")
        return
    
    # Scene Prompts for I2V (Animation instructions)
    prompts = [
        # Scene 1: Modern
        "Slow camera pan right, rain falling with neon reflections flickering on wet asphalt, silhouette of woman walking away slowly, mysterious vibe.",
        # Scene 2: Heian
        "Dynamic camera zoom out, mist swirling around the warrior, bow string trembling, hundred eyes on the demon glowing and blinking asynchronously.",
        # Scene 3: Redemption
        "Gentle wind blowing through temple, sunlight rays shifting, woman praying with subtle tears falling, fading scars on hands, peaceful motion.",
        # Scene 4: Ending
        "Woman walking away into distance, shadow on ground morphs into demon shape and back, slight camera shake, cinematic ending."
    ]
    
    client = MCPClient("https://kamui-code.ai/i2v/fal/minimax/hailuo-02/fast")
    client.start()
    
    for i, p in enumerate(prompts):
        scene_num = i + 1
        img_path = os.path.join(BASE_DIR, f"scene_{scene_num}.png")
        if not os.path.exists(img_path):
            log(f"Scene {scene_num} Image not found: {img_path}")
            continue

        log(f"Generating Video {scene_num}/4...")
        url = client.generate(p, img_path)
        if url:
            path = os.path.join(BASE_DIR, f"clip_{scene_num}.mp4")
            urllib.request.urlretrieve(url, path)
            log(f"Clip {scene_num} Saved: {path}")
        else:
            log(f"Clip {scene_num} Failed.")
            
    client.process.terminate()

if __name__ == "__main__":
    run()
