import subprocess
import sys
import os

def run(type: str, tweet_url: str):
    tweet_id = tweet_url.split("/")[-1]

    script_path = os.path.abspath(__file__)
    project_root = os.path.abspath(os.path.join(script_path, "..", ".."))

    src_dir = os.path.join(project_root, "src")
    downloads_dir = os.path.join(project_root, "downloads")
    results_dir = os.path.join(project_root, "results")
    # print(f"Project root: {project_root}")
    # print(f"Source directory: {src_dir}")
    # print(f"Downloads directory: {downloads_dir}")
    # print(f"Results directory: {results_dir}")

    os.makedirs(downloads_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    screenshot_py = os.path.join(src_dir, "screenshot_ors.py")
    extract_py = os.path.join(src_dir, "crop_tweet.py")
    video_dl_py = os.path.join(src_dir, "video_dl.py")
    assemble_py = os.path.join(src_dir, "assemble_reel.py")
    # screenshot_sh = os.path.join(src_dir, "screenshot.sh")

    img_raw = os.path.join(downloads_dir, f"{tweet_id}.png")
    img_cropped = os.path.join(downloads_dir, f"{tweet_id}_cropped.png")
    img_final = os.path.join(results_dir, f"{tweet_id}_final.png")
    video_path = os.path.join(downloads_dir, f"{tweet_id}_video.mp4")
    reel_output = os.path.join(results_dir, f"{tweet_id}_reel.mp4")

    # Old API
    # print("▶️ Downloading tweet screenshot...")
    # subprocess.run(["python", screenshot_py, tweet_url], check=True)

    # print("💡 Verifying image exists:", os.path.exists(img_raw), "|", img_raw)

    if type == "video":
        print("▶️ Running screenshot.sh to download tweet screenshot...")
        subprocess.run(["python", screenshot_py, type, tweet_url, img_raw], check=True)
        print("💡 Verifying image exists:", os.path.exists(img_raw), "|", img_raw)

        print("✂️ Extracting only tweet text...")
        subprocess.run(["python", extract_py, "tweet_card", img_raw, img_final], check=True)

        # print("✂️ Cropping tweet...")
        # subprocess.run(["python", extract_py, "crop_tweet", img_raw, img_final], check=True)
        # print(f"✅ Done! Tweet text saved as {img_final}")

        print("📽 Downloading tweet video...")
        subprocess.run(["python", video_dl_py, tweet_url], check=True)
        print("✅ Done! Tweet video downloaded.")

        print("🎬 Creating the reel...")
        subprocess.run(["python", assemble_py, img_final, video_path, reel_output], check=True)
        print(f"✅ Done! Reel created as {reel_output}")

    elif type == "photo":
        print("▶️ Downloading tweet screenshot...")
        subprocess.run(["python", screenshot_py, type, tweet_url, img_raw], check=True)
        print("💡 Verifying image exists:", os.path.exists(img_raw), "|", img_raw)

        print("✂️ Cropping tweet...")
        subprocess.run(["python", extract_py, "photo_card", img_raw, img_final], check=True)

        print("Padding the image...")
        subprocess.run(["python", extract_py, "pad_photo", img_final, img_final], check=True)
        print(f"✅ Done! Tweet text saved as {img_final}")

    else:
        print("❌ Invalid type. Use 'photo' or 'video'.")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python run_all.py <type> <tweet_url>")
        sys.exit(1)

    type = sys.argv[1]
    tweet_url = sys.argv[2]
    run(type, tweet_url)
