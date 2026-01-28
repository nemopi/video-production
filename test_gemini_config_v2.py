import json
import os
import subprocess
import sys
import time

SETTINGS_JSON_PATH = os.path.abspath(".gemini/settings.json")

def log(msg):
    print(f"[Gemini-Config-Test] {msg}")

def test_gemini_config_v2():
    if not os.path.exists(SETTINGS_JSON_PATH):
        log(f"Error: {SETTINGS_JSON_PATH} not found.")
        sys.exit(1)

    try:
        with open(SETTINGS_JSON_PATH, 'r') as f:
            config = json.load(f)
            
        mcp_servers = config.get("mcpServers", {})
        target_server = "t2i-kamui-flux-schnell"
        
        if target_server not in mcp_servers:
            log(f"Target server {target_server} not found.")
            sys.exit(1)
            
        server_conf = mcp_servers[target_server]
        http_url = server_conf.get("httpUrl")
        headers = server_conf.get("headers", {})
        
        log(f"Testing URL: {http_url}")
        
        # curl -v で GETリクエストを送り、ヘッダーの一部を読み取って終了
        cmd = ["curl", "-v", "-N", http_url]
        for k, v in headers.items():
            cmd.extend(["-H", f"{k}: {v}"])
            
        # タイムアウト付きで実行
        try:
            # 5秒だけ実行して、接続確立を確認する
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            time.sleep(3)
            proc.terminate()
            
            stdout, stderr = proc.communicate()
            
            # stderrに "Connected to" や "200 OK" があるか確認
            if "Connected to" in stderr or "HTTP/2 200" in stderr:
                log("SUCCESS: Connection established successfully!")
                log("Gemini-style config (httpUrl) represents a valid endpoint.")
            elif "404" in stderr:
                log("FAILURE: Server returned 404 Not Found.")
            else:
                log("WARNING: Connection status unclear. Check logs.")
                # print(stderr)
                
        except Exception as e:
            log(f"Execution error: {e}")

    except Exception as e:
        log(f"Exception: {e}")

if __name__ == "__main__":
    test_gemini_config_v2()
