import toml
import json
import os

def convert_toml_to_gemini_json(toml_path, output_path):
    try:
        with open(toml_path, 'r') as f:
            data = toml.load(f)
        
        mcp_servers = data.get('mcp_servers', {})
        # Gemini CLIはルートが mcpServers オブジェクトそのもの (settings.jsonのmcpServersセクション)
        # しかしユーザー指示では "mcpServersセクションを追加" とあるため、
        # 出力は {"mcpServers": { ... }} の形式にするのが適切。
        gemini_config = {"mcpServers": {}}

        for name, config in mcp_servers.items():
            args = config.get('args', [])
            
            # mcp-remote を使っているか (HTTP接続)
            if config.get('command') == 'npx' and any('mcp-remote' in arg for arg in args):
                server_url = None
                headers = {}
                
                for arg in args:
                    if arg.startswith('http'):
                        server_url = arg
                        break
                
                if '--header' in args:
                    try:
                        header_idx = args.index('--header') + 1
                        header_str = args[header_idx]
                        key, value = header_str.split(':', 1)
                        headers[key.strip()] = value.strip()
                    except (ValueError, IndexError):
                        pass

                if server_url:
                    if not server_url.endswith('/sse'):
                        server_url += '/sse'

                    # Gemini CLI Spec
                    gemini_config['mcpServers'][name] = {
                        "httpUrl": server_url, # url -> httpUrl
                        "headers": headers,
                        "timeout": 10000       # timeout追加
                        # type, description は削除
                    }
                else:
                    # Fallback (Command type)
                     gemini_config['mcpServers'][name] = {
                        "command": "npx",
                        "args": ["-y"] + args,
                        "env": config.get('env', {})
                    }
            else:
                gemini_config['mcpServers'][name] = {
                    "command": "npx",
                    "args": ["-y"] + args if config.get('command') == 'npx' else args,
                    "env": config.get('env', {})
                }

        # ローカルMCP
        gemini_config['mcpServers']['creative-studio'] = {
            "command": "python",
            "args": ["/Users/takayukinemoto/Desktop/映像制作/creative_studio_mcp/src/main.py"]
        }

        # ディレクトリ作成
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(gemini_config, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully converted to {output_path} (Gemini CLI Spec)")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    convert_toml_to_gemini_json('codex_config.toml', '.gemini/settings.json')
