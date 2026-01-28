import toml
import json

def convert_toml_to_json_v3(toml_path, output_path):
    try:
        with open(toml_path, 'r') as f:
            data = toml.load(f)
        
        mcp_servers = data.get('mcp_servers', {})
        claude_config = {"mcpServers": {}}

        for name, config in mcp_servers.items():
            args = config.get('args', [])
            description = config.get('description', "")
            
            # mcp-remote を使っているかチェック
            if config.get('command') == 'npx' and any('mcp-remote' in arg for arg in args):
                # HTTP Type に変換
                server_url = None
                headers = {}
                
                # URLを探す (httpで始まる引数)
                for arg in args:
                    if arg.startswith('http'):
                        server_url = arg
                        break
                
                # Headerを探す
                if '--header' in args:
                    try:
                        header_idx = args.index('--header') + 1
                        header_str = args[header_idx]
                        key, value = header_str.split(':', 1)
                        headers[key.strip()] = value.strip()
                    except (ValueError, IndexError):
                        pass

                if server_url:
                    # 末尾に /sse を付与 (既に無ければ)
                    if not server_url.endswith('/sse'):
                        server_url += '/sse'

                    claude_config['mcpServers'][name] = {
                        "type": "http", # http (sse) type
                        "url": server_url, # SSEエンドポイントを指定
                        "description": description,
                        "headers": headers
                    }
                else:
                    # Fallback (URLなし)
                     claude_config['mcpServers'][name] = {
                        "command": "npx",
                        "args": ["-y"] + args,
                        "env": config.get('env', {})
                    }
            else:
                # mcp-remote 以外
                claude_config['mcpServers'][name] = {
                    "command": "npx",
                    "args": ["-y"] + args if config.get('command') == 'npx' else args,
                    "env": config.get('env', {})
                }

        # ローカルMCP (Creative Studio)
        claude_config['mcpServers']['creative-studio'] = {
            "command": "python",
            "args": ["/Users/takayukinemoto/Desktop/映像制作/creative_studio_mcp/src/main.py"]
        }

        with open(output_path, 'w') as f:
            json.dump(claude_config, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully converted to {output_path} (v3: SSE Endpoint Corrected)")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    convert_toml_to_json_v3('codex_config.toml', 'claude_desktop_config.json')
