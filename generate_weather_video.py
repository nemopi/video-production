
import ffmpeg
import sys

def generate_video():
    input_image = "/Users/takayukinemoto/.gemini/antigravity/brain/c1e5b6ad-5b5b-4061-9cb4-8428d5352550/tokyo_winter_morning_1769005392599.png"
    output_video = "/Users/takayukinemoto/Desktop/映像制作/tokyo_weather_forecast.mp4"

    # 16:9 (1920x1080)
    WIDTH = 1920
    HEIGHT = 1080
    DURATION = 5

    print(f"Generating video from {input_image}...")

    try:
        stream = ffmpeg.input(input_image, loop=1, t=DURATION)
        
        # Scale and Crop to 16:9 (Input is Square)
        # Scale width to 1920, height will become 1920
        stream = stream.filter('scale', w=WIDTH, h=-1) 
        
        # Crop center 1920x1080
        stream = stream.filter('crop', w=WIDTH, h=HEIGHT, x='(iw-ow)/2', y='(ih-oh)/2')
        
        # Zoom Effect (Slow Dolly In)
        # zoom+0.0015 per frame
        stream = stream.filter('zoompan', z='min(zoom+0.0015,1.5)', d=DURATION*30, x='iw/2-(iw/zoom/2)', y='ih/2-(ih/zoom/2)', s=f'{WIDTH}x{HEIGHT}')
        
        # Text Overlay
        stream = stream.drawtext(
            text="2026.01.22 TOKYO / Sunny",
            fontfile="/System/Library/Fonts/Helvetica.ttc",
            fontcolor="white",
            fontsize=80,
            x="(w-text_w)/2",
            y="h-150",
            shadowcolor="black",
            shadowx=3,
            shadowy=3,
            box=1,
            boxcolor="black@0.5",
            boxborderw=10
        )

        stream = ffmpeg.output(stream, output_video, pix_fmt='yuv420p', t=DURATION)
        ffmpeg.run(stream, overwrite_output=True)
        print(f"Success! Video saved to: {output_video}")
        
    except ffmpeg.Error as e:
        print("FFmpeg Error:", e.stderr.decode() if e.stderr else str(e))
        sys.exit(1)

if __name__ == "__main__":
    generate_video()
