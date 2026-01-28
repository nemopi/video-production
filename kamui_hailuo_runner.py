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
OUTPUT_DIR = "/Users/takayukinemoto/Desktop/映像制作"
VIDEO_PATH = os.path.join(OUTPUT_DIR, "kamui_tokyo_rain_movie_hailuo.mp4")
HAILUO_URL = "https://kamui-code.ai/i2v/fal/minimax/hailuo-2.3/pro/image-to-video"
IMAGE_URL = "https://v3b.fal.media/files/b/0a8b4ada/vADuMQK8iy5o_lrEdTna4.png" # Existing Nanobanana image

def log(msg):
    print(f"[Kamui-Hailuo] {msg}")
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
        self.tools = []

    def start(self):
        cmd = ["npx", "-y", "mcp-remote", self.endpoint_url, "--transport", "http-only", "--header", f"KAMUI-CODE-PASS: {KAMUI_PASS}"]
        self.process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=0)
        
        threading.Thread(target=read_stream, args=(self.process.stderr, lambda x: None), daemon=True).start()
        
        def stdout_reader(line):
            try:
                msg = json.loads(line)
                if msg.get("id") is not None:
                    self.response_future[msg["id"]] = msg
            except: pass
        
        threading.Thread(target=read_stream, args=(self.process.stdout, stdout_reader), daemon=True).start()
        
        self.send_request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "kamui-client", "version": "1.0"}}, 1)
        self.wait_for_response(1)
        self.send_notification("notifications/initialized")
        
        self.send_request("tools/list", {}, 2)
        res = self.wait_for_response(2)
        if res and "result" in res:
             self.tools = res["result"].get("tools", [])

    def send_request(self, method, params, req_id):
        with self.lock:
            if self.process:
                self.process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": req_id}) + "\n")
                self.process.stdin.flush()

    def send_notification(self, method, params=None):
        with self.lock:
            if self.process:
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

def main():
    log("=== Step 2: Hailuo 2.3 Pro (I2V) ===")
    c2 = MCPClient(HAILUO_URL)
    try:
        c2.start()
        
        args = {
            "image_url": IMAGE_URL,
            "prompt": "The girl in the rainsteps forward, smiling through tears. High quality, cinematic motion."
        }
        
        log(f"Submitting to Hailuo: {args}")
        # Find submit tool
        tool_name = "hailuo_23_pro_image_to_video_submit"
        
        c2.send_request("tools/call", {"name": tool_name, "arguments": args}, 20)
        res = c2.wait_for_response(20, timeout=30)
        
        if not res: 
             log("Submit timeout")
             return

        content = res["result"].get("content", [])
        request_id = None
        for item in content:
            txt = item.get("text", "")
            if "request_id" in txt:
                try: 
                    jd = json.loads(txt)
                    request_id = jd.get("request_id")
                except: pass
            if not request_id:
                  match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', txt)
                  if match: request_id = match.group(0)

        if not request_id:
             log(f"No request_id found in: {str(content)}")
             return

        log(f"Polling Request ID: {request_id}")
        start = time.time()
        pid = 100
        
        while time.time() - start < 1200:
            c2.send_request("tools/call", {"name": "hailuo_23_pro_image_to_video_status", "arguments": {"request_id": request_id}}, pid)
            pres = c2.wait_for_response(pid)
            pid += 1
            
            if pres and "result" in pres:
                p_content = pres["result"].get("content", [])
                for item in p_content:
                    txt = item.get("text", "")
                    if "http" in txt:
                        # Sometimes status returns URL directly if done? No, likely in result tool
                        pass 
                    
                    if "{" in txt:
                        try:
                            jd = json.loads(txt)
                            status = jd.get("status")
                            # log(f"Status: {status}")
                            if status == "COMPLETED":
                                log("Job Completed. Fetching result...")
                                # Call result tool or use response_url
                                if "response_url" in jd:
                                     with urllib.request.urlopen(jd["response_url"]) as f:
                                        final_data = json.loads(f.read().decode())
                                        if "video" in final_data:
                                            v_url = final_data["video"]["url"]
                                            log(f"Video URL: {v_url}")
                                            subprocess.run(["curl", "-s", "-o", VIDEO_PATH, v_url])
                                            log(f"Saved to {VIDEO_PATH}")
                                            return
                                        if "url" in final_data:
                                             v_url = final_data["url"]
                                             log(f"Video URL: {v_url}")
                                             subprocess.run(["curl", "-s", "-o", VIDEO_PATH, v_url])
                                             log(f"Saved to {VIDEO_PATH}")
                                             return
                        except: pass
            
            time.sleep(10)
            
    except Exception as e:
        log(f"Hailuo Error: {e}")
    finally:
        c2.close()

if __name__ == "__main__":
    main()
