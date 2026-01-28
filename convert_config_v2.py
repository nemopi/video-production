import toml
import json
import re

def convert_toml_to_json_v2(toml_path, output_path):
    try:
        with open(toml_path, 'r') as f:
            data = toml.load(f)
        
        mcp_servers = data.get('mcp_servers', {})
        claude_config = {"mcpServers": {}}

        # URLとヘッダーを抽出するための正規表現
        # args: ["mcp-remote", "URL", ..., "--header", "KEY: VALUE"]
        
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
                        header_str = args[header_idx] # "KEY: VALUE"
                        key, value = header_str.split(':', 1)
                        headers[key.strip()] = value.strip()
                    except (ValueError, IndexError):
                        pass

                if server_url:
                    claude_config['mcpServers'][name] = {
                        "type": "http", # ユーザー指定の書式
                        "url": server_url,
                        "description": description,
                        "headers": headers
                    }
                else:
                    # URLが見つからない場合はフォールバック
                     claude_config['mcpServers'][name] = {
                        "command": "npx",
                        "args": ["-y"] + args,
                        "env": config.get('env', {})
                    }
            else:
                # mcp-remote 以外（例: remotion）はそのまま command 形式
                claude_config['mcpServers'][name] = {
                    "command": "npx",
                    "args": ["-y"] + args if config.get('command') == 'npx' else args,
                    "env": config.get('env', {})
                }

        # ローカルMCP (Creative Studio) を追加
        claude_config['mcpServers']['creative-studio'] = {
            "command": "python",
            "args": ["/Users/takayukinemoto/Desktop/映像制作/creative_studio_mcp/src/main.py"]
        }

        with open(output_path, 'w') as f:
            json.dump(claude_config, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully converted to {output_path} (HTTP Type Optimized)")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    convert_toml_to_json_v2('codex_config.toml', 'claude_desktop_config.json')
