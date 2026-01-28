import requests
import json
import sseclient
import threading
import sys
import os

# 設定
MCP_SERVER_URL = "https://kamui-code.ai/t2i/fal/flux/schnell/sse"
API_KEY = "kamui_Dpcha0qsvsuvbrdieb7Br8Bse3ufxPBNiNrDdJXokZk"
PROMPT = "Cyberpunk city street, neon lights, futuristic atmosphere, highly detailed"
OUTPUT_IMAGE_PATH = os.path.abspath("test_output/antigravity_gen.png")

headers = {
    "KAMUI-CODE-PASS": API_KEY,
    "Accept": "text/event-stream"
}

def run_mcp_client():
    print(f"Connecting to {MCP_SERVER_URL} ...")
    
    # SSE接続
    response = requests.get(MCP_SERVER_URL, headers=headers, stream=True)
    client = sseclient.SSEClient(response)
    
    post_url = None
    session_id = None
    
    for event in client.events():
        # print(f"Event: {event.event}, Data: {event.data}")
        
        if event.event == "endpoint":
            # POST用のエンドポイント取得
            # endpointイベントは相対パスまたは絶対パスで来る
            # Kamui Codeの場合は、base URL + endpoint path の可能性があるが
            # 仕様上は SSE URLのクエリパラメータに ?sessionId=... をつけたものになることが多い
            # ここではイベントデータをパースしてPOST先を特定
            # data は単なる文字列としてのURI
            endpoint_uri = event.data
            
            # 相対パスなら絶対パスに変換
            if endpoint_uri.startswith("/"):
                # https://kamui-code.ai + /...
                from urllib.parse import urlparse
                parsed = urlparse(MCP_SERVER_URL)
                base = f"{parsed.scheme}://{parsed.netloc}"
                post_url = base + endpoint_uri
            else:
                post_url = endpoint_uri
                
            print(f"POST Endpoint: {post_url}")
            
            # 初期化リクエスト送信
            send_json_rpc(post_url, {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05", # 最新のMCP仕様バージョン
                    "capabilities": {},
                    "clientInfo": {"name": "antigravity-client", "version": "1.0"}
                },
                "id": 1
            })
            
        elif event.event == "endpoint" and not post_url:
             # 一応フォールバック（最初のイベントで取れるはず）
             pass

        elif event.event == "message":
             # サーバーからのJSON-RPC応答
             try:
                 data = json.loads(event.data)
                 # print(f"Received: {data}")
                 
                 # 初期化完了通知受信 -> ツール実行へ
                 if data.get("id") == 1 and "result" in data:
                     print("Initialized. Sending notifications/initialized...")
                     # initialized 通知
                     send_json_rpc(post_url, {
                         "jsonrpc": "2.0",
                         "method": "notifications/initialized"
                     })
                     
                     print("Listing tools...")
                     send_json_rpc(post_url, {
                         "jsonrpc": "2.0",
                         "method": "tools/list",
                         "id": 2
                     })

                 elif data.get("id") == 2 and "result" in data:
                     print("Too list received. Calling generate_image...")
                     # ツール実行: t2i-kamui-flux-schnell (ツール名はサーバー定義に依存するが、推測またはlist結果から使う)
                     # Kamuiのこのエンドポイントは単一の機能を提供している可能性が高いが、tools/listを見ると確実。
                     # ここでは決め打ちで 'generate_image' または 'flux_schnell' などを試すが、
                     # まずはlistの結果を見て動的にツール名を取得するのが確実
                     tools = data["result"].get("tools", [])
                     if tools:
                         tool_name = tools[0]["name"]
                         print(f"Using tool: {tool_name}")
                         
                         send_json_rpc(post_url, {
                             "jsonrpc": "2.0",
                             "method": "tools/call",
                             "params": {
                                 "name": tool_name,
                                 "arguments": {
                                     "prompt": PROMPT,
                                     "image_size": "landscape_16_9" # 仮の引数
                                 }
                             },
                             "id": 3
                         })
                     else:
                         print("No tools found.")
                         sys.exit(1)

                 elif data.get("id") == 3:
                     if "result" in data:
                         print("Generation success!")
                         # 結果のパース（画像URLなどはcontent内にあるはず）
                         content = data["result"].get("content", [])
                         for item in content:
                             if item.get("type") == "image":
                                 # Base64の場合
                                 import base64
                                 img_data = base64.b64decode(item["data"])
                                 with open(OUTPUT_IMAGE_PATH, "wb") as f:
                                     f.write(img_data)
                                 print(f"Image saved to {OUTPUT_IMAGE_PATH}")
                                 sys.exit(0)
                             elif item.get("type") == "text":
                                 # URLの場合の処理など
                                 text = item["text"]
                                 print(f"Result text: {text}")
                                 # URLが含まれていればダウンロードする処理などをここに追加
                                 # Kamuiは通常URLを返す
                                 if "http" in text:
                                     import re
                                     urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', text)
                                     if urls:
                                         img_url = urls[0]
                                         print(f"Downloading image from {img_url}...")
                                         img_res = requests.get(img_url)
                                         with open(OUTPUT_IMAGE_PATH, "wb") as f:
                                             f.write(img_res.content)
                                         print(f"Image saved to {OUTPUT_IMAGE_PATH}")
                                         sys.exit(0)
                         
                         sys.exit(0)
                     elif "error" in data:
                         print(f"Error calling tool: {data['error']}")
                         sys.exit(1)

             except json.JSONDecodeError:
                 pass
        
def send_json_rpc(url, payload):
    # print(f"Sending: {payload}")
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    if not os.path.exists("test_output"):
        os.makedirs("test_output")
    try:
        run_mcp_client()
    except KeyboardInterrupt:
        print("Interrupted")
    except Exception as e:
        print(f"Error: {e}")
