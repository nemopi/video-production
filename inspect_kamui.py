import requests
import json
import sys

KAMUI_PASS = "kamui_Dpcha0qsvsuvbrdieb7Br8Bse3ufxPBNiNrDdJXokZk"
HEADERS = {
    "KAMUI-CODE-PASS": KAMUI_PASS,
    "Accept": "text/event-stream"
}

TARGETS = {
    "nanobanana": "https://kamui-code.ai/t2i/fal/nano-banana",
    "hailuo": "https://kamui-code.ai/i2v/fal/minimax/hailuo-02/pro"
}

def get_rpc_endpoint(sse_url):
    print(f"Connecting to {sse_url}...")
    try:
        response = requests.get(sse_url, headers=HEADERS, stream=True, timeout=30)
        for line in response.iter_lines():
            if not line: continue
            line_str = line.decode('utf-8')
            if line_str.startswith("data:"):
                endpoint_uri = line_str.split(":", 1)[1].strip()
                response.close()
                if endpoint_uri.startswith("/"):
                    from urllib.parse import urlparse
                    parsed = urlparse(sse_url)
                    return f"{parsed.scheme}://{parsed.netloc}{endpoint_uri}"
                return endpoint_uri
    except Exception as e:
        print(f"Error connecting to SSE: {e}")
        return None

def list_tools(post_url):
    payload = {
        "jsonrpc": "2.0", 
        "method": "tools/list", 
        "id": 1
    }
    h = HEADERS.copy()
    h["Content-Type"] = "application/json"
    
    try:
        res = requests.post(post_url, headers=h, json=payload)
        return res.json()
    except Exception as e:
        print(f"Error calling tools/list: {e}")
        return None

def main():
    for name, url in TARGETS.items():
        print(f"\n--- Checking {name} ---")
        rpc_url = get_rpc_endpoint(url)
        if rpc_url:
            print(f"RPC Endpoint: {rpc_url}")
            res = list_tools(rpc_url)
            if res and "result" in res:
                print(json.dumps(res["result"]["tools"], indent=2, ensure_ascii=False))
            else:
                print("Failed to list tools or no tools found.")
        else:
            print("Could not retrieve RPC endpoint.")

if __name__ == "__main__":
    main()
