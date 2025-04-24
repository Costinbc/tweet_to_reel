import subprocess
import os
import sys
from PIL import Image, ImageDraw

def generate_rounded_mask(input_image, output_path):
    image = Image.open(input_image)
    width, height = image.size
    radius = 30
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, width, height), radius=radius, fill=255)
    mask.save(output_path)

def assemble_reel_white(image, video, output):
    cmd = [
        "ffmpeg",
        "-i", video,
        "-i", image,
        "-filter_complex",
        "[0:v]crop='min(iw,ih)':'min(iw,ih)',scale=1080:1080[vid];"
        "[1:v]scale=1080:-1[img];"
        "[img][vid]vstack=inputs=2[stacked];"
        "color=white:s=1080x1920:d=5[bg];"
        "[bg][stacked]overlay=(W-w)/2:((H-h)/2 + 70)[final]",
        "-map", "[final]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "128k",
        "-preset", "veryfast",
        "-crf", "28",
        "-threads", "2",
        "-shortest",
        "-y", output
    ]
    subprocess.run(cmd, check=True)


def assemble_reel_blur(image, video, mask, output):
    cmd = [
        "ffmpeg",
        "-i", video,
        "-i", image,
        "-i", mask,
        "-filter_complex",
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bg];"
        "[0:v]crop='min(iw,ih)':'min(iw,ih)',scale=1080:1080[vid];"
        "[1:v]format=rgba[img];"
        "[2:v]scale=iw:ih[mask];"
        "[img][mask]alphamerge[rounded];"
        "[rounded]pad=1080:ih:(ow-iw)/2:0:color=0x00000000[img_padded];"
        "[img_padded][vid]vstack=inputs=2[stacked];"
        "[bg][stacked]overlay=(W-w)/2:((H-h)/2 + 70)[final]",
        "-map", "[final]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "128k",
        "-preset", "veryfast",
        "-crf", "28",
        "-threads", "2",
        "-shortest",
        "-y", output
    ]
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python assemble_reel.py <type> <image> <video> <output>")
        sys.exit(1)

    reel_type = sys.argv[1]
    image_path = os.path.abspath(sys.argv[2])
    video_path = os.path.abspath(sys.argv[3])
    output_path = os.path.abspath(sys.argv[4])

    if not os.path.exists(image_path):
        print(f"Image file '{image_path}' does not exist.")
        sys.exit(1)

    if not os.path.exists(video_path):
        print(f"Video file '{video_path}' does not exist.")
        sys.exit(1)

    if reel_type == "white":
        print("Creating the reel with white background...")
        assemble_reel_white(image_path, video_path, output_path)
    elif reel_type == "blur":
        print("Generating rounded mask...")
        mask_path = os.path.splitext(image_path)[0] + "_mask.png"
        generate_rounded_mask(image_path, mask_path)
        print("Creating the reel with blurred background...")
        assemble_reel_blur(image_path, video_path, mask_path, output_path)
    else:
        print("Invalid reel type. Use 'white' or 'blur'.")
        sys.exit(1)