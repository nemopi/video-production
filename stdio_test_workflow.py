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
IMAGE_PATH = os.path.join(OUTPUT_DIR, "stdio_gen.png")
VIDEO_PATH = os.path.join(OUTPUT_DIR, "stdio_video.mp4")
FFMPEG_TOOLS_PATH = "/Users/takayukinemoto/Desktop/映像制作/creative_studio_mcp/src/tools/ffmpeg_tools.py"

# Kamui Code / mcp-remote command (Stdio spec)
# npx -y mcp-remote <URL> --transport http-only --header ...
CMD = [
    "npx", "-y", "mcp-remote",
    "https://kamui-code.ai/t2i/fal/flux/schnell", 
    "--transport", "http-only",
    "--header", "KAMUI-CODE-PASS: kamui_Dpcha0qsvsuvbrdieb7Br8Bse3ufxPBNiNrDdJXokZk"
]

def log(msg):
    print(f"[Stdio-Exec] {msg}")
    sys.stdout.flush()

def read_stream(stream, callback):
    """Reads lines from a stream and calls callback."""
    buffer = ""
    while True:
        try:
            # Read character by character to handle various buffering or lack of newlines
            chunk = stream.read(1)
            if not chunk:
                break
            buffer += chunk
            if '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                if line.strip():
                    callback(line.strip())
        except Exception as e:
            log(f"Stream error: {e}")
            break

class MCPClient:
    def __init__(self):
        self.process = None
        self.lock = threading.Lock()
        self.response_future = {} # id -> result
        self.tools = []

    def start(self):
        log("Starting MCP Server process...")
        self.process = subprocess.Popen(
            CMD,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0 # Unbuffered
        )
        
        # Stderr logger
        def stderr_reader(line):
            # log(f"STDERR: {line}")
            pass
        
        # Stdout reader (JSON-RPC)
        def stdout_reader(line):
            # log(f"RECV: {line}")
            try:
                msg = json.loads(line)
                self.handle_message(msg)
            except json.JSONDecodeError:
                log(f"Invalid JSON received: {line}")

        threading.Thread(target=read_stream, args=(self.process.stderr, stderr_reader), daemon=True).start()
        threading.Thread(target=read_stream, args=(self.process.stdout, stdout_reader), daemon=True).start()

    def send(self, payload):
        if not self.process: return
        json_str = json.dumps(payload)
        # log(f"SEND: {json_str}")
        with self.lock:
            self.process.stdin.write(json_str + "\n")
            self.process.stdin.flush()

    def handle_message(self, msg):
        msg_id = msg.get("id")
        if msg_id is not None:
            self.response_future[msg_id] = msg

    def wait_for_response(self, req_id, timeout=30):
        start = time.time()
        while time.time() - start < timeout:
            if req_id in self.response_future:
                return self.response_future.pop(req_id)
            time.sleep(0.1)
        return None

    def close(self):
        if self.process:
            self.process.terminate()

def run_workflow():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    client = MCPClient()
    try:
        client.start()
        
        # 1. Initialize
        log("Sending Initialize...")
        client.send({
            "jsonrpc": "2.0", "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test-client", "version": "1.0"}},
            "id": 1
        })
        
        res = client.wait_for_response(1)
        if not res or "result" not in res:
            log("Initialize failed or timed out")
            return False
        
        # 2. Notification
        client.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        
        # 3. List Tools
        log("Listing Tools...")
        client.send({"jsonrpc": "2.0", "method": "tools/list", "id": 2})
        res = client.wait_for_response(2)
        if not res or "result" not in res:
            log("List Tools failed")
            return False
        
        tools = res["result"].get("tools", [])
        if not tools:
            log("No tools found")
            return False
            
        if not tools:
            log("No tools found")
            return False

        # Find tools
        tool_map = {t['name']: t for t in tools}
        submit_tool = None
        result_tool = None
        for name in tool_map:
            if "submit" in name:
                submit_tool = name
            elif "result" in name:
                result_tool = name
        
        if not submit_tool or not result_tool:
            log(f"Required tools (submit/result) not found. Tools: {list(tool_map.keys())}")
            return False

        log(f"Flow: Submit({submit_tool}) -> Poll({result_tool})")

        # 1. Submit Request
        log("Submitting Request...")
        client.send({
            "jsonrpc": "2.0", "method": "tools/call",
            "params": {
                "name": submit_tool,
                "arguments": {
                    "prompt": "Cyberpunk city street, neon lights, highly detailed, futuristic",
                    "image_size": "landscape_16_9"
                }
            },
            "id": 3
        })
        
        res = client.wait_for_response(3)
        if not res or "result" not in res:
            log(f"Submit Failed: {res}")
            return False
            
        # Extract Request ID
        # Response content usually contains text with request_id or JSON
        content = res["result"].get("content", [])
        request_id = None
        
        # Try to parse request_id from text
        # Assuming format like "Request submitted: <id>" or JSON
        for item in content:
            if item.get("type") == "text":
                text = item["text"]
                # log(f"Submit Response: {text}")
                try:
                    # check if response is just the ID or JSON
                    if "{" in text:
                        import json
                        data = json.loads(text)
                        request_id = data.get("request_id")
                except:
                    pass
                if not request_id:
                    # simple regex for uuid
                    import re
                    match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', text)
                    if match:
                        request_id = match.group(0)

        if not request_id:
            log(f"Could not extract Request ID from: {content}")
            return False
            
        log(f"Request ID: {request_id}")
        
        # 2. Poll Result
        log("Polling for Result...")
        start_time = time.time()
        final_image_url = None
        
        poll_id = 4
        while time.time() - start_time < 120:
            client.send({
                "jsonrpc": "2.0", "method": "tools/call",
                "params": {
                    "name": result_tool,
                    "arguments": {
                        "request_id": request_id
                    }
                },
                "id": poll_id
            })
            
            res = client.wait_for_response(poll_id)
            poll_id += 1
            
            if res and "result" in res:
                content = res["result"].get("content", [])
                # check for image
                for item in content:
                    if item.get("type") == "image":
                         # Success!
                         data = base64.b64decode(item["data"])
                         with open(IMAGE_PATH, "wb") as f:
                             f.write(data)
                         log(f"Image Saved: {IMAGE_PATH}")
                         final_image_url = "saved"
                         break
                    elif item.get("type") == "text":
                         text = item["text"]
                         # Check if it contains image URL (Fal often returns URL in result)
                         if "http" in text and (".png" in text or ".jpg" in text or "storage.googleapis.com" in text or "fal.media" in text):
                             # Extract URL
                             import re
                             urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', text)
                             if urls:
                                 final_image_url = urls[0]
                                 log(f"Found Image URL: {final_image_url}")
                                 subprocess.run(["curl", "-s", "-o", IMAGE_PATH, final_image_url], check=True)
                                 break
                
                if final_image_url:
                    break
            
            log("Waiting...")
            time.sleep(5)
            
        if not final_image_url:
            log("Polling timed out or failed")
            return False

    except Exception as e:
        log(f"Error: {e}")
        return False
    finally:
        client.close()

    # 6. Video Conversion (Local)
    log("Starting Video Conversion...")
    try:
        # sys.path hack to use local tools
        sys.path.append(os.path.dirname(os.path.dirname(FFMPEG_TOOLS_PATH))) # Add src to path
        from tools import ffmpeg_tools
        # Need to re-import or use call directly if name clash?
        # Directly calling function from file if possible, or subprocess wrapper
        
        # Let's use the subprocess wrapper logic for clean env
        script_content = f"""
import sys
import os
sys.path.append("{os.path.dirname(os.path.dirname(FFMPEG_TOOLS_PATH))}") 
from tools.ffmpeg_tools import zoom_image

input_path = "{IMAGE_PATH}"
output_path = "{VIDEO_PATH}"

if not os.path.exists(input_path):
    print("Input image missing")
    sys.exit(1)

print(f"Zooming...")
result = zoom_image(input_path, output_path, duration=5.0, zoom_factor=1.2)
print("Video Gen Result:", result)
"""
        tmp_run = os.path.join(OUTPUT_DIR, "run_zoom_stdio.py")
        with open(tmp_run, "w") as f:
            f.write(script_content)
        
        subprocess.run([sys.executable, tmp_run], check=True)
        log(f"Video Created Successfully: {VIDEO_PATH}")
        return True

    except Exception as e:
        log(f"Video Conversion Error: {e}")
        return False

if __name__ == "__main__":
    if run_workflow():
        print("WORKFLOW_SUCCESS")
    else:
        print("WORKFLOW_FAILED")
