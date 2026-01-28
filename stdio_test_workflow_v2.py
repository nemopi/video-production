import subprocess
import json
import os
import sys
import threading
import time
import base64
import uuid

# 設定
OUTPUT_DIR = os.path.abspath("test_output")
IMAGE_PATH_V2 = os.path.join(OUTPUT_DIR, "v2_gen.png")
VIDEO_PATH_V2 = os.path.join(OUTPUT_DIR, "v2_video.mp4")

# MCP Server Definitions
T2I_SERVER_NAME = "t2i-kamui-fal-nano-banana-pro"
I2V_SERVER_NAME = "i2v-kamui-hailuo-02-fast"

# Kamui Code Config (Hardcoded from claude_desktop_config_stdio.json for standalone test)
KAMUI_PASS = "kamui_Dpcha0qsvsuvbrdieb7Br8Bse3ufxPBNiNrDdJXokZk"

def log(msg):
    print(f"[V2-Exec] {msg}")
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
                if line.strip():
                    callback(line.strip())
        except Exception as e:
            log(f"Stream error: {e}")
            break

class MCPClient:
    def __init__(self, endpoint_url):
        self.endpoint_url = endpoint_url
        self.process = None
        self.lock = threading.Lock()
        self.response_future = {} 
        self.tools = []

    def start(self):
        cmd = [
            "npx", "-y", "mcp-remote",
            self.endpoint_url,
            "--transport", "http-only",
            "--header", f"KAMUI-CODE-PASS: {KAMUI_PASS}"
        ]
        # log(f"Starting MCP: {self.endpoint_url}")
        self.process = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=0
        )
        
        threading.Thread(target=read_stream, args=(self.process.stderr, lambda x: None), daemon=True).start()
        
        def stdout_reader(line):
            # log(f"RECV: {line[:200]}")
            try:
                msg = json.loads(line)
                msg_id = msg.get("id")
                if msg_id is not None:
                    self.response_future[msg_id] = msg
            except: pass

        threading.Thread(target=read_stream, args=(self.process.stdout, stdout_reader), daemon=True).start()

        # Initialize
        self.send_request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test-v2", "version": "1.0"}}, 1)
        res = self.wait_for_response(1)
        if not res or "result" not in res:
            raise Exception("Init failed")
            
        self.send_notification("notifications/initialized")
        
        # Tools List
        self.send_request("tools/list", {}, 2)
        res = self.wait_for_response(2)
        if not res or "result" not in res:
            raise Exception("Tools list failed")
        
        self.tools = res["result"].get("tools", [])
        # log(f"Tools loaded: {[t['name'] for t in self.tools]}")

    def send_request(self, method, params, req_id):
        payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": req_id}
        self.write_stdin(payload)

    def send_notification(self, method, params=None):
        payload = {"jsonrpc": "2.0", "method": method}
        if params: payload["params"] = params
        self.write_stdin(payload)

    def write_stdin(self, payload):
        with self.lock:
            if self.process:
                self.process.stdin.write(json.dumps(payload) + "\n")
                self.process.stdin.flush()

    def wait_for_response(self, req_id, timeout=30):
        start = time.time()
        while time.time() - start < timeout:
            if req_id in self.response_future:
                return self.response_future.pop(req_id)
            time.sleep(0.1)
        return None

    def close(self):
        if self.process: self.process.terminate()

    def get_tool(self, keyword):
        for t in self.tools:
            if keyword in t["name"]: return t
        return None

    def execute_async_task(self, submit_args, timeout=600, fetch_result_url=True):
        # Find tools
        submit_tool = None
        result_tool = None
        
        # Heuristic search
        for t in self.tools:
            name = t["name"]
            if "submit" in name: submit_tool = name
            elif "result" in name: result_tool = name
            elif "status" in name: result_tool = name # sometimes status is used for polling
        
        if not submit_tool or not result_tool:
            # Fallback for simple names potentially (e.g. if single tool works sync)
            # But assume async for Fal usually
            raise Exception("Required submit/result tools not found")

        log(f"Tools: {submit_tool} -> {result_tool}")
        
        # Submit
        log("Submitting...")
        submit_args["request_id"] = str(uuid.uuid4())
        self.send_request("tools/call", {"name": submit_tool, "arguments": submit_args}, 10)
        res = self.wait_for_response(10)
        
        # Extract ID
        request_id = None
        content = res["result"].get("content", [])
        for item in content:
            txt = item.get("text", "")
            if "{" in txt:
                try: 
                    request_id = json.loads(txt).get("request_id")
                except: pass
            if not request_id:
                import re
                match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', txt)
                if match: request_id = match.group(0)
        
        if not request_id:
            msg_str = json.dumps(content)
            # fallback: maybe it's sync and result is in content already?
            if "http" in msg_str: return content # Return content directly if sync
            raise Exception(f"Request ID not found in: {msg_str}")
            
        log(f"Request ID: {request_id}. Polling...")
        
        # Poll
        start = time.time()
        poll_id = 100
        while time.time() - start < timeout:
            self.send_request("tools/call", {"name": result_tool, "arguments": {"request_id": request_id}}, poll_id)
            res = self.wait_for_response(poll_id)
            poll_id += 1
            
            if res and "result" in res:
                content = res["result"].get("content", [])
                
                # Check for completion via status in text JSON
                response_url = None
                for item in content:
                    if item.get("type") == "text":
                         txt = item["text"]
                         if "{" in txt:
                             try:
                                 json_data = json.loads(txt)
                                 status = json_data.get("status")
                                 if status == "COMPLETED":
                                     response_url = json_data.get("response_url")
                             except: pass
                
                if response_url and fetch_result_url:
                    log(f"Job Completed. Fetching result from: {response_url}")
                    # Fetch actual result from Fal queue URL
                    try:
                        import urllib.request
                        with urllib.request.urlopen(response_url) as f:
                            resp_body = f.read().decode('utf-8')
                            # Look for url inside response
                            # Fal image response: {"images": [{"url": "..."}], ...}
                            # Fal video response: {"video": {"url": "..."}, ...}
                            try:
                                final_json = json.loads(resp_body)
                                # Flatten to content-like structure for return
                                new_content = []
                                # Images
                                if "images" in final_json:
                                    for img in final_json["images"]:
                                        if "url" in img:
                                            new_content.append({"type": "text", "text": img["url"]})
                                # Video
                                if "video" in final_json and "url" in final_json["video"]:
                                    new_content.append({"type": "text", "text": final_json["video"]["url"]})
                                
                                return new_content
                            except: pass
                    except Exception as e:
                        log(f"Failed to fetch result URL: {e}")

                # Fallback: Check for completion (Image or Video) directly in content
                is_done = False
                for item in content:
                    if item.get("type") == "image": is_done = True
                    if item.get("type") == "text":
                         txt = item["text"]
                         # Check log information
                         if "http" in txt and ("fal.media" in txt or "storage" in txt):
                             is_done = True
                if is_done:
                    return content
            
            time.sleep(5)
            
        raise Exception("Polling timed out")


def run_v2_workflow():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    image_url = None

    # Step 1: NanoBanana T2I
    log("=== Step 1: T2I (NanoBanana Pro) ===")
    t2i_url = "https://kamui-code.ai/t2i/fal/nano-banana-pro"
    client1 = MCPClient(t2i_url)
    try:
        client1.start()
        result = client1.execute_async_task({
            "prompt": "Cyberpunk city street, neon lights, highly detailed, futuristic, 8k",
            "image_size": "landscape_16_9"
        })
        
        # Save Result
        for item in result:
            if item.get("type") == "image":
                data = base64.b64decode(item["data"])
                with open(IMAGE_PATH_V2, "wb") as f:
                    f.write(data)
                log(f"Image Saved: {IMAGE_PATH_V2}")
                # We need URL for next step usually. Fal results usually have URL in text too or we upload?
                # If we only have binary, we might need an uploader MCP.
                # BUT, wait. Usually result text contains URL.
            elif item.get("type") == "text":
                txt = item["text"]
                if "http" in txt:
                    import re
                    urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', txt)
                    if urls:
                        image_url = urls[0]
                        log(f"Image URL: {image_url}")
                        subprocess.run(["curl", "-s", "-o", IMAGE_PATH_V2, image_url])

        if not image_url and os.path.exists(IMAGE_PATH_V2):
             # If we have file but no URL, and I2V needs URL...
             # Hailuo I2V usually takes `image_url`.
             # If we don't have a public URL, we might be stuck unless we use the uploader tool.
             # Let's hope NanoBanana returns a URL.
             pass

    except Exception as e:
        log(f"T2I Failed: {e}")
        return
    finally:
        client1.close()

    if not image_url:
        log("Cannot proceed to I2V without Image URL.")
        # Try to use previous image URL if available or fail
        return

    # Step 2: Hailuo I2V
    log("=== Step 2: I2V (Hailuo Fast) ===")
    i2v_url = "https://kamui-code.ai/i2v/fal/minimax/hailuo-02/fast"
    client2 = MCPClient(i2v_url)
    try:
        client2.start()
        # Hailuo args: prompt, image_url
        result = client2.execute_async_task({
            "prompt": "Cyberpunk city street, zoom out slowly, neon flicker", # Added simple prompt for guidance
            "image_url": image_url
        }, timeout=300) # Hailuo might take longer
        
        for item in result:
             if item.get("type") == "text":
                txt = item["text"]
                if "http" in txt:
                    import re
                    urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', txt)
                    if urls:
                        video_url = urls[0]
                        log(f"Video URL: {video_url}")
                        subprocess.run(["curl", "-s", "-o", VIDEO_PATH_V2, video_url])
                        log(f"Video Saved: {VIDEO_PATH_V2}")
                        print("WORKFLOW_SUCCESS")
                        return

    except Exception as e:
        log(f"I2V Failed: {e}")
    finally:
        client2.close()

if __name__ == "__main__":
    run_v2_workflow()
