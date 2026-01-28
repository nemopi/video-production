from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from tools.ffmpeg_tools import zoom_image, apply_effect, concat_videos
import asyncio

# サーバーの初期化
app = Server("creative-studio-mcp")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """利用可能なツール一覧を返す"""
    return [
        Tool(
            name="zoom_image",
            description="静止画から少しずつズームする動画クリップを生成します。オープニングや回想シーンに使えます。",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_path": {"type": "string", "description": "入力画像の絶対パス"},
                    "output_path": {"type": "string", "description": "出力動画の絶対パス"},
                    "duration": {"type": "number", "description": "動画の長さ(秒)", "default": 5.0},
                    "zoom_factor": {"type": "number", "description": "ズーム倍率(1.0以上)", "default": 1.5}
                },
                "required": ["input_path", "output_path"]
            }
        ),
        Tool(
            name="apply_effect",
            description="動画にエフェクト（スローモーション、ノイズなど）を適用します。",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_path": {"type": "string", "description": "入力動画の絶対パス"},
                    "output_path": {"type": "string", "description": "出力動画の絶対パス"},
                    "effect_type": {
                        "type": "string", 
                        "enum": ["slow_motion", "glitch_noise"],
                        "description": "適用するエフェクトの種類"
                    },
                    "intensity": {"type": "number", "description": "エフェクトの強度(標準: 1.0)", "default": 1.0}
                },
                "required": ["input_path", "output_path", "effect_type"]
            }
        ),
        Tool(
            name="concat_videos",
            description="複数の動画ファイルを結合します。",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_paths": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "description": "結合する動画パスのリスト"
                    },
                    "output_path": {"type": "string", "description": "出力動画の絶対パス"}
                },
                "required": ["video_paths", "output_path"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """ツールの実行ハンドラ"""
    if name == "zoom_image":
        result = zoom_image(
            arguments["input_path"],
            arguments["output_path"],
            arguments.get("duration", 5.0),
            arguments.get("zoom_factor", 1.5)
        )
        if result["status"] == "success":
            return [TextContent(type="text", text=f"Success: Video created at {result['output_path']}")]
        else:
            return [TextContent(type="text", text=f"Error: {result.get('message', 'Unknown error')}")]

    elif name == "apply_effect":
        result = apply_effect(
            arguments["input_path"],
            arguments["output_path"],
            arguments["effect_type"],
            arguments.get("intensity", 1.0)
        )
        if result["status"] == "success":
            return [TextContent(type="text", text=f"Success: Effect applied, saved to {result['output_path']}")]
        else:
            return [TextContent(type="text", text=f"Error: {result.get('message', 'Unknown error')}")]

    elif name == "concat_videos":
        result = concat_videos(
            arguments["video_paths"],
            arguments["output_path"]
        )
        if result["status"] == "success":
            return [TextContent(type="text", text=f"Success: Videos concatenated at {result['output_path']}")]
        else:
            return [TextContent(type="text", text=f"Error: {result.get('message', 'Unknown error')}")]

    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    # 標準入力/出力を使ってMCPサーバーを実行
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
