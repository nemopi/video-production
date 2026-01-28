import subprocess
import json
import os
import sys
import threading
import time
import uuid
import urllib.request

# 設定
OUTPUT_DIR = os.path.abspath("test_output/hyakumeiki")
KAMUI_PASS = "kamui_Dpcha0qsvsuvbrdieb7Br8Bse3ufxPBNiNrDdJXokZk"

def log(msg):
    print(f"[Hyakumeiki-Gen] {msg}")
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
        self.send("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "hyakumeiki-tool", "version": "1.0"}}, 1)
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
    
    # 承認された実装計画に基づくプロンプト
    prompts = [
        # Scene 1: Modern Utsunomiya
        'A dark street in modern Utsunomiya at night, rain wet asphalt reflection, street sign saying "Hyakumeiki" (Japanese kanji), silhouette of a young woman passing by, Science SARU anime style, vibrant neon gradient lights from eyes in darkness, cinematic wide angle, ominous atmosphere.',
        
        # Scene 2: Heian period
        'Heian period Japan, misty horse dumping ground, legendary warrior Fujiwara no Hidesato aiming a bow, dynamic fish-eye perspective, facing a giant 3m demon silhouette with hundred glowing eyes on its body, Science SARU eclectic style, ink wash painting texture mixed with neon colors, dramatic composition.',
        
        # Scene 3: Redemption
        'Inside an old wooden temple (Hongwanji), a beautiful woman praying in tears, sunlight filtering through trees, ghostly hundred scars fading from her hands, spiritual atmosphere, Science SARU soft touch, pastel and monochrome mix, emotional close-up.',
        
        # Scene 4: Ending
        'Modern Utsunomiya street daytime, back view of the woman walking away, her shadow cast on the ground shaped like a demon with horns, ominous yet peaceful, Science SARU vibrant anime style, ending scene.'
    ]
    
    client = MCPClient("https://kamui-code.ai/t2i/fal/nano-banana-pro")
    client.start()
    
    for i, p in enumerate(prompts):
        scene_num = i + 1
        log(f"Generating Scene {scene_num}/4...")
        url = client.generate(p)
        if url:
            path = os.path.join(OUTPUT_DIR, f"scene_{scene_num}.png")
            urllib.request.urlretrieve(url, path)
            log(f"Scene {scene_num} Saved: {path}")
        else:
            log(f"Scene {scene_num} Failed.")
            
    client.process.terminate()

if __name__ == "__main__":
    run()
