import subprocess
import json
import os
import sys
import threading
import time
import base64
import re
import urllib.request

KAMUI_PASS = "kamui_Dpcha0qsvsuvbrdieb7Br8Bse3ufxPBNiNrDdJXokZk"
UPLOADER_URL = "https://kamui-code.ai/uploader/fal"
SORA_URL = "https://kamui-code.ai/t2v/openai/sora"
TEST_IMG_URL = "https://v3b.fal.media/files/b/0a8b4ada/vADuMQK8iy5o_lrEdTna4.png"
LOCAL_IMG = "test_input.png"
RESIZED_IMG = "test_resized_720x1280.png"
VIDEO_PATH = "sora_output_test.mp4"

def log(msg):
    print(f"[Bridge] {msg}")
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
        self.lock = threading.Lock()
        self.response_future = {}

    def start(self):
        cmd = ["npx", "-y", "mcp-remote", self.endpoint_url, "--transport", "http-only", "--header", f"KAMUI-CODE-PASS: {KAMUI_PASS}"]
        self.process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=0)
        threading.Thread(target=read_stream, args=(self.process.stderr, lambda x: None), daemon=True).start()
        def stdout_reader(line):
            try:
                msg = json.loads(line)
                if msg.get("id") is not None: self.response_future[msg["id"]] = msg
            except: pass
        threading.Thread(target=read_stream, args=(self.process.stdout, stdout_reader), daemon=True).start()
        self.send_request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}, 1)
        self.wait_for_response(1)
        self.send_notification("notifications/initialized")

    def send_request(self, method, params, req_id):
        with self.lock:
            self.process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": req_id}) + "\n")
            self.process.stdin.flush()

    def send_notification(self, method, params=None):
        with self.lock:
            payload = {"jsonrpc": "2.0", "method": method}
            if params: payload["params"] = params
            self.process.stdin.write(json.dumps(payload) + "\n")
            self.process.stdin.flush()

    def wait_for_response(self, req_id, timeout=30):
        start = time.time()
        while time.time() - start < timeout:
            if req_id in self.response_future: return self.response_future.pop(req_id)
            time.sleep(0.1)
        return None

    def close(self):
        if self.process: self.process.terminate()

def run_upload_test():
    # 1. Download
    log("Downloading image...")
    subprocess.run(["curl", "-s", "-o", LOCAL_IMG, TEST_IMG_URL])
    
    # 2. Resize
    log("Resizing to 720x1280...")
    subprocess.run([
        "ffmpeg", "-y", "-i", LOCAL_IMG, 
        "-vf", "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280", 
        RESIZED_IMG
    ], stderr=subprocess.DEVNULL)
    
    # 3. Upload
    log("Attempting Upload...")
    c = MCPClient(UPLOADER_URL)
    uploaded_url = None
    try:
        c.start()
        abs_path = os.path.abspath(RESIZED_IMG)
        log(f"Uploading file: {abs_path}")
        
        c.send_request("tools/call", {"name": "kamui_file_upload_fal", "arguments": {"file_path": abs_path}}, 10)
        res = c.wait_for_response(10, timeout=60)
        
        if res and "result" in res:
            content = res["result"].get("content", [])
            log(f"Upload Result: {content}")
            for item in content:
                txt = item.get("text", "")
                if "http" in txt:
                    uploaded_url = txt
                    break
    except Exception as e:
        log(f"Upload Error: {e}")
    finally:
        c.close()
        
    if not uploaded_url:
        log("Upload failed. Cannot proceed specific Sora I2V.")
        return

    log(f"Uploaded URL: {uploaded_url}")

    # 4. Sora I2V
    log("Submitting to Sora with Resized Image...")
    sora = MCPClient(SORA_URL)
    try:
        sora.start()
        args = {
            "prompt": "The girl in the rainsteps forward, smiling through tears. 10 seconds duration. High quality, cinematic motion.",
            "input_reference": uploaded_url,
            "model": "sora-2-pro",
            "seconds": "12",
            "size": "720x1280"
        }
        log(f"Args: {args}")
        sora.send_request("tools/call", {"name": "openai_sora_submit", "arguments": args}, 20)
        res = sora.wait_for_response(20, timeout=30)
        
        # Check success (video_id extraction not fully implemented here, just checking if submit works without 400 error)
        if res and "result" in res:
            log(f"Sora Submit Response: {res['result']}")
        else:
            log(f"Sora Submit Failed or Timed out")
            
    finally:
        sora.close()

if __name__ == "__main__":
    run_upload_test()
