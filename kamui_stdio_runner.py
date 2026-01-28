import subprocess
import json
import os
import sys
import threading
import time
import base64
import uuid
import re

# Configuration
KAMUI_PASS = "kamui_Dpcha0qsvsuvbrdieb7Br8Bse3ufxPBNiNrDdJXokZk"
OUTPUT_DIR = "/Users/takayukinemoto/Desktop/映像制作"
IMAGE_PATH = os.path.join(OUTPUT_DIR, "kamui_tokyo_gen.png")
VIDEO_PATH = os.path.join(OUTPUT_DIR, "kamui_tokyo_movie.mp4")

# MCP Server URLs
T2I_URL = "https://kamui-code.ai/t2i/fal/nano-banana"
I2V_URL = "https://kamui-code.ai/i2v/fal/minimax/hailuo-02/pro"

# Prompts
IMAGE_PROMPT = "Photorealistic cinematic shot, Tokyo city street in winter morning, clear blue sky, crisp sunlight casting long shadows. Low angle shot of a busy intersection (Shibuya or Shinjuku), people waiting for traffic signal. Atmosphere: Cold air, high contrast, sharp details. Weather: Sunny, clear visibility. Aspect Ratio: 16:9"
VIDEO_PROMPT = "(Cinematic Movement) Camera: Slow dolly forward into the intersection. Action: People start walking as the light changes. Atmosphere: Sunlight flaring through buildings. High quality, smooth motion."

def log(msg):
    print(f"[Kamui-Stdio] {msg}")
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
        # log(f"Starting MCP Client for {self.endpoint_url}")
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
        
        # List Tools
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
        # Heuristic: Find 'text_to_image' or 'generate' or 'submit'
        # Nanobanana tools: usually `nano_banana_t2i` (submit) and `nano_banana_t2i_result` (polling)
        tool_name = None
        for t in self.tools:
            name = t["name"]
            if "result" not in name and "status" not in name:
                tool_name = name
                break
        
        if not tool_name: tool_name = self.tools[0]["name"] # Fallback
        log(f"Using Tool: {tool_name}")
        
        # Call
        self.send_request("tools/call", {"name": tool_name, "arguments": args}, 10)
        res = self.wait_for_response(10, timeout=timeout) # Direct wait for synchronous-like tools?
        # Note: Some Fal tools are async via Request ID pattern, but `mcp-remote` or the wrapper might handle it?
        # The previous validated script had complex polling logic. I will include a simplified polling or assume the MCP adapter handles it?
        # Re-reading previous script: It implemented manual polling. I should do the same to be safe.
        
        if not res: raise Exception("Tool call timed out or failed")
        
        content = res["result"].get("content", [])
        
        # Check if it gave us a Request ID to poll, OR if it gave the result directly
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
            # Maybe it finished already?
            return content

        log(f"Polling Request ID: {request_id}")
        # Poll loop
        start = time.time()
        pid = 100
        while time.time() - start < timeout:
            # We need to find the "result" or "status" tool. 
            # Previous script searched for "result" in name.
            res_tool = None
            for t in self.tools:
                if "result" in t["name"] or "status" in t["name"]: res_tool = t["name"]
            
            if not res_tool: 
                 # Fallback: maybe call the same tool with request_id? Unlikely for Fal.
                 # If no result tool, maybe we wait?
                 time.sleep(5)
                 continue

            self.send_request("tools/call", {"name": res_tool, "arguments": {"request_id": request_id}}, pid)
            pres = self.wait_for_response(pid)
            pid += 1
            
            if pres and "result" in pres:
                p_content = pres["result"].get("content", [])
                # Check for "completed" or URL
                for item in p_content:
                    txt = item.get("text", "")
                    if "http" in txt and ("fal.media" in txt or "storage" in txt):
                        return p_content
                    # Also check JSON status
                    if "{" in txt:
                        try:
                            jd = json.loads(txt)
                            if jd.get("status") == "COMPLETED" and jd.get("response_url"):
                                # Fetch result manually
                                import urllib.request
                                with urllib.request.urlopen(jd["response_url"]) as f:
                                    final_res = json.loads(f.read().decode())
                                    # Convert to content
                                    ret = []
                                    if "images" in final_res:
                                        for i in final_res["images"]: ret.append({"type": "text", "text": i["url"]})
                                    if "video" in final_res:
                                        ret.append({"type": "text", "text": final_res["video"]["url"]})
                                    return ret
                        except: pass
            
            time.sleep(5)
        
        raise Exception("Polling timed out")

def main():
    image_url = None
    
    # 1. NanoBanana
    log("=== Step 1: Nanobanana ===")
    c1 = MCPClient(T2I_URL)
    try:
        c1.start()
        res = c1.execute_task({"prompt": IMAGE_PROMPT})
        for item in res:
            txt = item.get("text", "")
            urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', txt)
            if urls:
                image_url = urls[0]
                log(f"Image URL: {image_url}")
                # Save
                subprocess.run(["curl", "-s", "-o", IMAGE_PATH, image_url])
                break
    except Exception as e:
        log(f"Error in T2I: {e}")
    finally:
        c1.close()

    if not image_url:
        log("No image URL generated. Aborting.")
        return

    # 2. Hailuo
    log("=== Step 2: Hailuo ===")
    c2 = MCPClient(I2V_URL)
    try:
        c2.start()
        res = c2.execute_task({"prompt": VIDEO_PROMPT, "image_url": image_url}, timeout=600)
        for item in res:
            txt = item.get("text", "")
            urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', txt)
            if urls:
                video_url = urls[0]
                log(f"Video URL: {video_url}")
                # Save
                subprocess.run(["curl", "-s", "-o", VIDEO_PATH, video_url])
                log(f"Saved to {VIDEO_PATH}")
                break
    except Exception as e:
        log(f"Error in I2V: {e}")
    finally:
        c2.close()

if __name__ == "__main__":
    main()
