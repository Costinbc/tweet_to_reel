import subprocess
import os
import sys

def assemble_reel(image, video, output):
    cmd = [
        "ffmpeg",
        "-i", video,
        "-i", image,
        "-filter_complex",
        "[0:v]crop='min(iw,ih)':'min(iw,ih)',scale=720:-1[vid];"
        "[1:v]scale=720:-1[img];"
        "[img][vid]vstack=inputs=2[stacked];"
        "color=white:s=720x1280:d=5[bg];"
        "[bg][stacked]overlay=(W-w)/2:(H-h)/2[final]",
        "-map", "[final]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "128k",
        "-preset", "veryfast",
        "-crf", "28",
        "-shortest",
        "-y", output
    ]
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python assemble_reel.py <image> <video> <output>")
        sys.exit(1)

    image_path = os.path.abspath(sys.argv[1])
    video_path = os.path.abspath(sys.argv[2])
    output_path = os.path.abspath(sys.argv[3])

    if not os.path.exists(image_path):
        print(f"Image file '{image_path}' does not exist.")
        sys.exit(1)

    if not os.path.exists(video_path):
        print(f"Video file '{video_path}' does not exist.")
        sys.exit(1)

    assemble_reel(image_path, video_path, output_path)
