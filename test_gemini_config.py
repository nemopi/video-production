import json
import os
import subprocess
import sys

# 設定ファイルパス
SETTINGS_JSON_PATH = os.path.abspath(".gemini/settings.json")

def log(msg):
    print(f"[Gemini-Config-Test] {msg}")

def test_gemini_config():
    if not os.path.exists(SETTINGS_JSON_PATH):
        log(f"Error: {SETTINGS_JSON_PATH} not found.")
        sys.exit(1)

    try:
        with open(SETTINGS_JSON_PATH, 'r') as f:
            config = json.load(f)
            
        mcp_servers = config.get("mcpServers", {})
        
        # テスト対象: t2i-kamui-flux-schnell
        target_server = "t2i-kamui-flux-schnell"
        
        if target_server not in mcp_servers:
            log(f"Target server {target_server} not found in config.")
            sys.exit(1)
            
        server_conf = mcp_servers[target_server]
        
        # Gemini Spec: httpUrl
        http_url = server_conf.get("httpUrl")
        headers = server_conf.get("headers", {})
        
        if not http_url:
            log("Error: 'httpUrl' property missing (Gemini Spec violation?).")
            print(json.dumps(server_conf, indent=2))
            sys.exit(1)

        log(f"Found httpUrl: {http_url}")
        log(f"Headers: {list(headers.keys())}")
        
        # curlで接続テスト (Status check)
        cmd = ["curl", "-I", "-s", http_url]
        for k, v in headers.items():
            cmd.extend(["-H", f"{k}: {v}"])
            
        log(f"Executing curl to check connectivity...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            log("Curl executed successfully.")
            # Status code check
            lines = result.stdout.splitlines()
            if lines:
                log(f"Response Status: {lines[0]}")
                if "200" in lines[0]:
                    log("SUCCESS: Connection established using Gemini CLI config format!")
                else:
                    log(f"WARNING: Server returned non-200 status: {lines[0]}")
            else:
                 log("No output from curl.")
        else:
            log(f"Curl failed: {result.stderr}")

    except Exception as e:
        log(f"Exception: {e}")

if __name__ == "__main__":
    test_gemini_config()
