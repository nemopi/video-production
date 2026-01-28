import subprocess
import json
import os
import sys
import threading
import time
import base64
import re
import urllib.request

# Configuration
KAMUI_PASS = "kamui_Dpcha0qsvsuvbrdieb7Br8Bse3ufxPBNiNrDdJXokZk"
OUTPUT_DIR = "/Users/takayukinemoto/Desktop/映像制作"
IMAGE_PATH = os.path.join(OUTPUT_DIR, "kamui_tokyo_rain_gen.png")
VIDEO_PATH = os.path.join(OUTPUT_DIR, "kamui_tokyo_rain_movie.mp4")

# Endpoints
T2I_URL = "https://kamui-code.ai/t2i/fal/nano-banana-pro"
# Using Sora endpoint. If it supports I2V, it likely takes `image_url`.
# If not, we might be forced to use T2V or another model, but let's try Sora first as requested.
SORA_URL = "https://kamui-code.ai/t2v/openai/sora" 

# Prompts
IMAGE_PROMPT = "(masterpiece, best quality, highres:1.2), anime illustration, high-key, pure white background, (1girl:1.2), seated pose, knees together, hands resting in front of knees, shy gentle posture, slight forward lean, soft smile, head slightly tilted, (big sparkling blue eyes:1.25), long wavy hair, glossy hair, chestnut brown hair with warm blonde highlights on the right side, cool bluish shadow on the left side, navy school blazer with glossy fabric highlights and wrinkles, cream cardigan with buttons, white shirt collar, light cyan necktie/ribbon, gray plaid pleated skirt, bare legs, soft rim light from upper right, minimal soft shadow, subtle floating dust particles, smooth gradients, delicate shading, clean look --no logo --ar 9:16 --seed 771231 --sref 1747399850 --style raw"

VIDEO_PROMPT = "The girl in the rainsteps forward, smiling through tears. 10 seconds duration. High quality, cinematic motion."

def log(msg):
    print(f"[Kamui-Sora] {msg}")
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
        
        # Init
        self.send_request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "kamui-client", "version": "1.0"}}, 1)
        if not self.wait_for_response(1): raise Exception("Init failed")
        self.send_notification("notifications/initialized")
        
        # Tools
        self.send_request("tools/list", {}, 2)
        res = self.wait_for_response(2)
        if not res or "result" not in res: raise Exception("Tools list failed")
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

    def execute_task(self, args, timeout=300):
        # Heuristic for submit tool
        tool_name = None
        for t in self.tools:
            name = t["name"]
            if "result" not in name and "status" not in name:
                tool_name = name
                break
        if not tool_name: tool_name = self.tools[0]["name"]
        
        log(f"Using Tool: {tool_name}")
        self.send_request("tools/call", {"name": tool_name, "arguments": args}, 10)
        
        # Polling Logic
        res = self.wait_for_response(10, timeout=10) # Initial submit might be fast
        if not res: raise Exception("Tool call submission timed out")
        
        content = res["result"].get("content", [])
        request_id = None
        
        # 1. Check for request_id
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

        # 2. If no request_id, maybe immediate result?
        if not request_id:
             # Look for URL directly
             for item in content:
                 txt = item.get("text", "")
                 if "http" in txt and ("fal.media" in txt or "storage" in txt or "kamui" in txt):
                     return content
             # If neither, fail?
             log(f"No request_id found in: {str(content)}")
             return content # Return anyway to debug

        log(f"Polling Request ID: {request_id}")
        start = time.time()
        pid = 100
        
        while time.time() - start < timeout:
            # Find status tool
            status_tool = None
            for t in self.tools:
                nm = t["name"]
                if "result" in nm or "status" in nm: status_tool = nm
            
            if not status_tool: 
                time.sleep(5)
                continue
                
            self.send_request("tools/call", {"name": status_tool, "arguments": {"request_id": request_id}}, pid)
            pres = self.wait_for_response(pid)
            pid += 1
            
            if pres and "result" in pres:
                p_content = pres["result"].get("content", [])
                for item in p_content:
                    txt = item.get("text", "")
                    if "http" in txt and ("fal.media" in txt or "storage" in txt):
                        return p_content
                    if "{" in txt:
                        try:
                            jd = json.loads(txt)
                            if jd.get("status") == "COMPLETED" and jd.get("response_url"):
                                log("Job Completed via JSON status")
                                # fetch response_url
                                with urllib.request.urlopen(jd["response_url"]) as f:
                                    final_data = json.loads(f.read().decode())
                                    log(f"Final Data Keys: {final_data.keys()}")
                                    ret = []
                                    if "images" in final_data:
                                        for i in final_data["images"]: ret.append({"type": "text", "text": i["url"]})
                                    if "video" in final_data:
                                        ret.append({"type": "text", "text": final_data["video"]["url"]})
                                    if "url" in final_data: # Sometimes direct url
                                        ret.append({"type":"text", "text": final_data["url"]})
                                    return ret
                        except: pass
            
            time.sleep(5)
        raise Exception("Polling timed out")

def main():
    image_url = None

    # 1. Nanobanana Pro
    log("=== Step 1: Nanobanana Pro ===")
    c1 = MCPClient(T2I_URL)
    try:
        c1.start()
        # Attempt to force specific resolution to match Sora's requirement (720x1280)
        nano_args = {
            "prompt": IMAGE_PROMPT.replace("--ar 9:16", ""), # Remove AR from prompt to rely on explicit size
            "image_size": {
                "width": 720,
                "height": 1280
            }
        }
        res = c1.execute_task(nano_args)
        for item in res:
            txt = item.get("text", "")
            urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', txt)
            if urls:
                image_url = urls[0]
                log(f"Image URL: {image_url}")
                subprocess.run(["curl", "-s", "-o", IMAGE_PATH, image_url])
                break
    except Exception as e:
        log(f"T2I Error: {e}")
    finally:
        c1.close()

    if not image_url:
        log("Image generation failed.")
        return

    # 2. Sora Video
    log("=== Step 2: Sora Video (I2V) ===")
    c2 = MCPClient(SORA_URL)
    try:
        c2.start()
        
        # Sora Submit
        sora_args = {
            "prompt": VIDEO_PROMPT,
            "input_reference": image_url, 
            "model": "sora-2-pro", 
            "seconds": "12",
            "size": "720x1280" # Matching Nanobanana
        }
        
        log(f"Submitting to Sora: {sora_args}")
        c2.send_request("tools/call", {"name": "openai_sora_submit", "arguments": sora_args}, 20)
        res = c2.wait_for_response(20, timeout=30)
        if not res: raise Exception("Sora submit timed out")
        
        # Parse video_id
        # Result content usually: "Job submitted. Video ID: video_..."
        content = res["result"].get("content", [])
        video_id = None
        for item in content:
            txt = item.get("text", "")
            if "video_id" in txt:
                try:
                    jd = json.loads(txt)
                    video_id = jd.get("video_id")
                except: pass
            if not video_id:
                # Regex for video_...
                match = re.search(r'video_[a-zA-Z0-9]+', txt)
                if match: video_id = match.group(0)
        
        if not video_id:
             log(f"No video_id found in: {str(content)}")
             return

        log(f"Sora Job ID: {video_id}. Polling...")
        
        # Poll Loop
        start = time.time()
        pid = 200
        while time.time() - start < 1200: # Sora takes time, 20 mins max
            c2.send_request("tools/call", {"name": "openai_sora_status", "arguments": {"video_id": video_id}}, pid)
            pres = c2.wait_for_response(pid)
            pid += 1
            
            if pres and "result" in pres:
                p_content = pres["result"].get("content", [])
                for item in p_content:
                    txt = item.get("text", "")
                    if "completed" in txt:
                        log("Status: COMPLETED. Fetching result...")
                        # Get Result
                        c2.send_request("tools/call", {"name": "openai_sora_result", "arguments": {"video_id": video_id}}, pid+1000)
                        rres = c2.wait_for_response(pid+1000)
                        if rres and "result" in rres:
                             r_content = rres["result"]["content"]
                             for r_item in r_content:
                                 r_txt = r_item.get("text", "")
                                 if "http" in r_txt:
                                     video_url = r_txt
                                     log(f"Video URL: {video_url}")
                                     subprocess.run(["curl", "-s", "-o", VIDEO_PATH, video_url])
                                     log(f"Saved to {VIDEO_PATH}")
                                     return
                    elif "failed" in txt:
                        log(f"Job Failed: {txt}")
                        return
                    else:
                        # log(f"Status: {txt}") # verbose
                        pass
            
            time.sleep(10) # 10s poll interval
            
    except Exception as e:
        log(f"Sora Error: {e}")
    finally:
        c2.close()

if __name__ == "__main__":
    main()
