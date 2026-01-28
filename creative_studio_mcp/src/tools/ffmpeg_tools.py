import ffmpeg
import os

def zoom_image(input_path: str, output_path: str, duration: float = 5.0, zoom_factor: float = 1.5):
    """
    静止画からズーム動画を生成する
    """
    try:
        # 入力ストリーム
        input_stream = ffmpeg.input(input_path, loop=1, t=duration)
        
        # フィルタチェーン: scale -> pad -> zoompan
        # 縦型(720x1280)に固定
        WIDTH = 720
        HEIGHT = 1280
        
        stream = (
            input_stream
            .filter('scale', w=WIDTH, h=HEIGHT, force_original_aspect_ratio='decrease')
            .filter('pad', w=WIDTH, h=HEIGHT, x='(ow-iw)/2', y='(oh-ih)/2')
            .filter(
                'zoompan',
                z=f'min(zoom+0.0015,{zoom_factor})',
                d=int(duration * 25), # 25fps想定
                x='iw/2-(iw/zoom/2)',
                y='ih/2-(ih/zoom/2)',
                s=f'{WIDTH}x{HEIGHT}'
            )
        )
        
        # 出力
        stream = ffmpeg.output(stream, output_path, pix_fmt='yuv420p', t=duration)
        ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
        return {"status": "success", "output_path": output_path}
        
    except ffmpeg.Error as e:
        error_message = e.stderr.decode('utf8') if e.stderr else str(e)
        return {"status": "error", "message": error_message}

def apply_effect(input_path: str, output_path: str, effect_type: str, intensity: float = 1.0):
    """
    動画にエフェクトを適用する
    """
    try:
        stream = ffmpeg.input(input_path)
        WIDTH = 720
        HEIGHT = 1280
        
        # 基本的なリサイズとパディングを先に適用
        stream = (
             stream
             .filter('scale', w=WIDTH, h=HEIGHT, force_original_aspect_ratio='decrease')
             .filter('pad', w=WIDTH, h=HEIGHT, x='(ow-iw)/2', y='(oh-ih)/2')
        )

        if effect_type == 'slow_motion':
            # スローモーション (PTSを増やす)
            pts_factor = 1.0 + intensity
            stream = stream.filter('setpts', f'{pts_factor}*PTS')
            # 音声はカットするか別途処理が必要だが、今回は映像のみ簡易実装
            
        elif effect_type == 'glitch_noise':
            # ノイズ
            noise_strength = int(20 * intensity)
            stream = stream.filter('noise', alls=noise_strength, allf='t+u')
            
        # 出力
        stream = ffmpeg.output(stream, output_path, pix_fmt='yuv420p')
        ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
        return {"status": "success", "output_path": output_path}

    except ffmpeg.Error as e:
        error_message = e.stderr.decode('utf8') if e.stderr else str(e)
        return {"status": "error", "message": error_message}

def concat_videos(video_paths: list[str], output_path: str):
    """
    動画リストを結合する
    """
    try:
        # 一時ファイルリスト作成
        list_file_path = os.path.join(os.path.dirname(output_path), 'concat_list.txt')
        with open(list_file_path, 'w') as f:
            for path in video_paths:
                f.write(f"file '{path}'\n")
        
        # concat demuxerを使用
        (
            ffmpeg
            .input(list_file_path, format='concat', safe=0)
            .output(output_path, c='copy')
            .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
        )
        
        # クリーンアップ
        os.remove(list_file_path)
        return {"status": "success", "output_path": output_path}

    except ffmpeg.Error as e:
        error_message = e.stderr.decode('utf8') if e.stderr else str(e)
        return {"status": "error", "message": error_message}
