import subprocess
import json
import os
import sys
import threading
import time
import re
import urllib.request

KAMUI_PASS = "kamui_Dpcha0qsvsuvbrdieb7Br8Bse3ufxPBNiNrDdJXokZk"
OUTPUT_DIR = "/Users/takayukinemoto/Desktop/映像制作"
IMAGE_PATH = os.path.join(OUTPUT_DIR, "kamui_twilight_station_gen.png")
VIDEO_PATH = os.path.join(OUTPUT_DIR, "kamui_twilight_station_movie.mp4")

# Endpoints
T2I_URL = "https://kamui-code.ai/t2i/fal/nano-banana-pro"
I2V_URL = "https://kamui-code.ai/i2v/fal/minimax/hailuo-2.3/pro/image-to-video"

# Prompts
IMAGE_PROMPT = "Makoto Shinkai style, anime art, empty train station platform at twilight, golden hour, deep blue and orange gradient sky, lens flare, highly detailed clouds, nostalgic atmosphere, visual novel background, wide angle, 8k, masterpiece --ar 16:9"
VIDEO_PROMPT = "Shadow of a fast train passing by, creating dynamic lighting changes and wind, dust particles floating, light leaks flickering, subtle camera movement. 5 seconds."

def log(msg):
    print(f"[Kamui-Twilight] {msg}")
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
                if msg.get("id") is not None:
                    self.response_future[msg["id"]] = msg
            except: pass
        
        threading.Thread(target=read_stream, args=(self.process.stdout, stdout_reader), daemon=True).start()
        
        self.send_request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "kamui-client", "version": "1.0"}}, 1)
        self.wait_for_response(1)
        self.send_notification("notifications/initialized")
        
        # Tools discovery ignored for speed, using known tool names or heuristically guessing if needed
        # But good practice to verify tool name if unsure. Nanobanana = nano_banana_pro_t2i_submit. Hailuo = hailuo_23_pro_image_to_video_submit.

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

    def execute_and_poll(self, tool_name, args, status_tool_name, request_id_key="request_id"):
        # Submit
        log(f"Submitting to {tool_name}...")
        self.send_request("tools/call", {"name": tool_name, "arguments": args}, 10)
        res = self.wait_for_response(10, timeout=60)
        if not res or "result" not in res:
             log(f"Submit Failed")
             return None

        # Extract Request ID/URL
        content = res["result"].get("content", [])
        request_id = None
        
        # Check for immediate URL (Nanobanana sometimes)
        for item in content:
            txt = item.get("text", "")
            urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', txt)
            if urls and "fal.media" in urls[0]:
                return urls[0] # Immediate success
        
        # Check for Request ID
        for item in content:
            txt = item.get("text", "")
            if request_id_key in txt:
                try: 
                    jd = json.loads(txt)
                    request_id = jd.get(request_id_key)
                except: pass
            if not request_id:
                  match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', txt)
                  if match: request_id = match.group(0)

        if not request_id:
             log(f"No request_id found in: {str(content)}")
             return None

        log(f"Polling ID: {request_id}")
        start = time.time()
        pid = 100
        
        while time.time() - start < 600:
            self.send_request("tools/call", {"name": status_tool_name, "arguments": {request_id_key: request_id}}, pid)
            pres = self.wait_for_response(pid)
            pid += 1
            
            if pres and "result" in pres:
                p_content = pres["result"].get("content", [])
                for item in p_content:
                    txt = item.get("text", "")
                    if "{" in txt:
                        try:
                            jd = json.loads(txt)
                            status = jd.get("status")
                            # log(status)
                            if status == "COMPLETED":
                                if "response_url" in jd:
                                     # Fetch result from URL
                                     with urllib.request.urlopen(jd["response_url"]) as f:
                                        final_data = json.loads(f.read().decode())
                                        if "video" in final_data: return final_data["video"]["url"]
                                        if "images" in final_data: return final_data["images"][0]["url"]
                                        if "url" in final_data: return final_data["url"]
                        except: pass
                    # Sometimes simple text URL?
                    urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', txt)
                    if urls and "fal.media" in urls[0]: return urls[0]

            time.sleep(5)
        return None

def main():
    image_url = None
    
    # 1. Nanobanana Pro (T2I)
    log("=== Step 1: Nanobanana Pro (Background) ===")
    c1 = MCPClient(T2I_URL)
    try:
        c1.start()
        # Requesting Landscape 16:9
        nano_args = {
            "prompt": IMAGE_PROMPT,
            "image_size": "landscape_16_9"
        }
        # Note: Tool name 'nano_banana_pro_t2i_submit' and status 'nano_banana_pro_t2i_status' (Guesses based on pattern, or use list to check?)
        # To be safe, I'll list tools quickly first.
        c1.send_request("tools/list", {}, 2)
        res = c1.wait_for_response(2)
        tools = res["result"]["tools"]
        submit_tool = next(t["name"] for t in tools if "submit" in t["name"])
        status_tool = next(t["name"] for t in tools if "status" in t["name"])
        
        image_url = c1.execute_and_poll(submit_tool, nano_args, status_tool)
        if image_url:
            log(f"Image URL: {image_url}")
            subprocess.run(["curl", "-s", "-o", IMAGE_PATH, image_url])
        else:
            log("T2I Failed")
            return
            
    except Exception as e:
        log(f"T2I Error: {e}")
        return
    finally:
        c1.close()

    # 2. Hailuo 2.3 Pro (I2V)
    log("=== Step 2: Hailuo 2.3 Pro (Effects) ===")
    c2 = MCPClient(I2V_URL)
    try:
        c2.start()
        
        c2.send_request("tools/list", {}, 2)
        res = c2.wait_for_response(2)
        tools = res["result"]["tools"]
        submit_tool = next(t["name"] for t in tools if "submit" in t["name"])
        status_tool = next(t["name"] for t in tools if "status" in t["name"])
        
        # Hailuo usually handles resolution well.
        hailuo_args = {
            "image_url": image_url,
            "prompt": VIDEO_PROMPT
        }
        
        video_url = c2.execute_and_poll(submit_tool, hailuo_args, status_tool)
        
        if video_url:
            log(f"Video URL: {video_url}")
            subprocess.run(["curl", "-s", "-o", VIDEO_PATH, video_url])
            log(f"Saved to {VIDEO_PATH}")
        else:
            log("I2V Failed")
            
    except Exception as e:
        log(f"I2V Error: {e}")
    finally:
        c2.close()

if __name__ == "__main__":
    main()
