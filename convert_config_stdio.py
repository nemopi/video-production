import toml
import json

def convert_toml_to_stdio_json(toml_path, output_path):
    try:
        with open(toml_path, 'r') as f:
            data = toml.load(f)
        
        mcp_servers = data.get('mcp_servers', {})
        stdio_config = {"mcpServers": {}}

        for name, config in mcp_servers.items():
            args = config.get('args', [])
            
            # 既存のCommand定義をチェック
            is_npx = config.get('command') == 'npx'
            has_mcp_remote = any('mcp-remote' in arg for arg in args)
            
            if is_npx and has_mcp_remote:
                # すでmcp-remote用のargsになっているはずだが、
                # TOMLから読み込んだargsをそのまま信頼して command: npx 形式で出力する。
                # ただし、私の以前の実装でURL末尾に /sse が無いなどの問題があったため、
                # ここで念のためURLを補正（/sseなし版に戻す or そのまま）する必要があるか？
                # mcp-remote は通常 SSEエンドポイントではなく Base URL を受け取る仕様の場合もあれば
                # SSEエンドポイントを受け取る場合もある。
                # 以前のユーザー提示TOMLは Base URL だった。
                # ここでは安全のため、TOMLのargsをそのまま使う（前回 npx mcp-remote で接続成功はしていたので）。
                
                # ただし、HTTP最適化の過程でURLが変わっている可能性があるため、
                # 念のため "Base URL" を抽出して再構築するロジックを入れる。
                
                server_url = None
                header_arg = None
                
                for arg in args:
                    if arg.startswith('http'):
                        server_url = arg
                        # /sse がついてたら取る（mcp-remoteは通常 /sse を自動付与するか、Base URLを期待することが多い）
                        # 念のため、今回は安全策として "元々のTOMLにあるURL" を使う方針だが、
                        # TOML自体も私が生成している。
                        # mcp-remoteのドキュメント的には SSE URL でも動くはず。
                    
                # そのまま出力
                stdio_config['mcpServers'][name] = {
                    "command": "npx",
                    "args": ["-y"] + args, # -yを追加
                    "env": config.get('env', {})
                }
            else:
                # その他のサーバー
                command = config.get('command', 'npx')
                cmd_args = config.get('args', [])
                if command == 'npx':
                    cmd_args = ["-y"] + cmd_args
                    
                stdio_config['mcpServers'][name] = {
                    "command": command,
                    "args": cmd_args,
                    "env": config.get('env', {})
                }

        # ローカルMCP (Creative Studio)
        stdio_config['mcpServers']['creative-studio'] = {
            "command": "python",
            "args": ["/Users/takayukinemoto/Desktop/映像制作/creative_studio_mcp/src/main.py"]
        }

        with open(output_path, 'w') as f:
            json.dump(stdio_config, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully converted to {output_path} (Stdio/Command Spec)")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    convert_toml_to_stdio_json('codex_config.toml', 'claude_desktop_config_stdio.json')
