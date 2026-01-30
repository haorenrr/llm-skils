import shlex
import subprocess
import os
import argparse
from datetime import datetime
import sys
import re

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--duration", type=int, default=15)
    parser.add_argument("--caption", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    out_dir = "output"
    if not os.path.exists(out_dir): os.makedirs(out_dir)

    ts = datetime.now().strftime("%y%m%d_%H%M%S")
    safe_title = re.sub(r'[\\/*?:"<<>>|]', '', args.caption).replace(' ', '_')
    final_name = args.output if args.output else f"{safe_title}_{ts}.mp4"

    tmp_full = os.path.join(out_dir, f"full_{ts}.mp4")
    final_video = os.path.join(out_dir, final_name)

    try:
        # 1. Download
        print(f"--- Downloading video resource ---")
        dl_cmd = [
            'yt-dlp', '--quiet', '--no-warnings', '--js-runtimes', 'node',
            '-f', 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]',
            '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            '--no-check-certificates', '-o', tmp_full, args.url
        ]
        print(f">>> exec cmd: {shlex.join(dl_cmd)}")
        subprocess.run(dl_cmd, check=True)

        # 2. Clip and Process (9:16)
        print(f"--- Clipping and visual standardization (9:16) ---")
        sc = ';'
        filter_str = (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:10[bg]{sc}"
            f"[0:v]scale=1080:-1[fg]{sc}"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[outv]"
        )

        process_cmd = [
            'ffmpeg', '-i', tmp_full,
            '-ss', args.start, '-t', str(args.duration),
            '-filter_complex', filter_str,
            '-map', '[outv]', '-map', '0:a?',
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
            '-c:a', 'aac', '-y', final_video
        ]
        print(f">>> exec cmd: {shlex.join(process_cmd)}")
        subprocess.run(process_cmd, check=True)
        
        if os.path.exists(final_video) and os.path.getsize(final_video) > 1000:
            print(f"Task completed successfully! Path: {final_video}")
        else:
            print(f"Warning: The generated video might be empty. Please check if the start time exceeds the total video duration.")

    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if os.path.exists(tmp_full): os.remove(tmp_full)

if __name__ == "__main__":
    main()
