import subprocess
import json
import os
import sys
import threading

KAMUI_PASS = "kamui_Dpcha0qsvsuvbrdieb7Br8Bse3ufxPBNiNrDdJXokZk"
SORA_URL = "https://kamui-code.ai/t2v/openai/sora"

def read_stream(stream):
    while True:
        line = stream.readline()
        if not line: break
        # print(f"LOG: {line.strip()}")

def main():
    cmd = ["npx", "-y", "mcp-remote", SORA_URL, "--transport", "http-only", "--header", f"KAMUI-CODE-PASS: {KAMUI_PASS}"]
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=0)
    threading.Thread(target=read_stream, args=(process.stderr,), daemon=True).start()
    
    # Init
    process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}, "id": 1}) + "\n")
    process.stdin.flush()
    # Read init response (blocking read for simplicity in test)
    while True:
        line = process.stdout.readline()
        if "result" in line: break
    
    process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
    process.stdin.flush()
    
    # List tools
    process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "tools/list", "id": 2}) + "\n")
    process.stdin.flush()
    
    while True:
        line = process.stdout.readline()
        if '"id":2' in line or '"id": 2' in line:
            jd = json.loads(line)
            print(json.dumps(jd["result"]["tools"], indent=2))
            break
            
    process.terminate()

if __name__ == "__main__":
    main()
