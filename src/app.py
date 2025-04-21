import json

from flask import Flask, request, render_template, send_file, redirect, url_for, jsonify
from concurrent.futures import ThreadPoolExecutor
import subprocess
import os
import uuid
import time
from get_video_duration import get_video_duration

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
template_dir = os.path.join(base_dir, "templates")
downloads_dir = os.path.join(base_dir, "downloads")
results_dir = os.path.join(base_dir, "results")
src_dir = os.path.join(base_dir, "src")

os.makedirs(downloads_dir, exist_ok=True)
os.makedirs(results_dir, exist_ok=True)

screenshot_py = os.path.join(src_dir, "screenshot_ors.py")
crop_py = os.path.join(src_dir, "crop_tweet.py")
video_dl_py = os.path.join(src_dir, "video_dl.py")
assemble_py = os.path.join(src_dir, "assemble_reel.py")

app = Flask(__name__, template_folder=template_dir, static_folder=os.path.join(base_dir, "static"))


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        tweet_url = request.form.get("url")
        mode = request.form.get("mode")
        if not tweet_url:
            return render_template("index.html", error="Please enter a tweet URL")

        tweet_id = tweet_url.split("/")[-1]
        job_id = str(uuid.uuid4())[:8]

        img_raw = os.path.join(downloads_dir, f"{tweet_id}.png")
        img_cropped = os.path.join(downloads_dir, f"{tweet_id}_cropped.png")
        img_final = os.path.join(results_dir, f"{job_id}_photo.png")
        video_path = os.path.join(downloads_dir, f"{tweet_id}_video.mp4")
        reel_output = os.path.join(results_dir, f"{job_id}_reel.mp4")

        try:
            start_time = time.time()
            video_duration = get_video_duration(video_path)
            with open("progress.json", "w") as f:
                json.dump({
                    "status": "Starting...",
                    "step": "start",
                    "start_time": start_time,
                    "video_duration": video_duration,
                    "type": "video",
                }, f)

            if mode == "white":
                executor = ThreadPoolExecutor(max_workers=1)

                with open("progress.json") as f:
                    existing = json.load(f)

                start_time = existing.get("start_time", time.time())

                with open("progress.json", "w") as f:
                    json.dump({
                    "status": "Downloading video...",
                    "step": "video",
                    "start_time": start_time,
                    "video_duration": video_duration,
                    "type": "video",
                }, f)
                video_download = executor.submit(
                    subprocess.run,
                    ["python", video_dl_py, tweet_url],
                    check=True
                )

                with open("progress.json") as f:
                    existing = json.load(f)

                start_time = existing.get("start_time", time.time())

                with open("progress.json", "w") as f:
                    json.dump({
                        "status": "Downloading image...",
                        "step": "image",
                        "start_time": start_time,
                        "video_duration": video_duration,
                        "type": "video",
                    }, f)
                subprocess.run(["python", screenshot_py, "video", tweet_url, img_raw], check=True)

                with open("progress.json") as f:
                    existing = json.load(f)

                start_time = existing.get("start_time", time.time())

                with open("progress.json", "w") as f:
                    json.dump({
                        "status": "Cropping image...",
                        "step": "crop",
                        "start_time": start_time,
                        "video_duration": video_duration,
                        "type": "video",
                    }, f)
                subprocess.run([
                    "python", crop_py,
                    "tweet_card",
                    "white",
                    img_raw,
                    img_final
                ], check=True)

                video_download.result()

                with open("progress.json") as f:
                    existing = json.load(f)

                start_time = existing.get("start_time", time.time())

                with open("progress.json", "w") as f:
                    json.dump({
                        "status": "Creating reel...",
                        "step": "reel",
                        "start_time": start_time,
                        "video_duration": video_duration,
                        "type": "video",
                    }, f)
                subprocess.run([
                    "python", assemble_py,
                    "white",
                    img_final,
                    video_path,
                    reel_output
                ], check=True)


                return redirect(url_for("reel_result", job_id=job_id))

            elif mode == "blur":
                executor = ThreadPoolExecutor(max_workers=1)

                with open("progress.json") as f:
                    existing = json.load(f)

                start_time = existing.get("start_time", time.time())

                with open("progress.json", "w") as f:
                    json.dump({
                        "status": "Downloading video...",
                        "step": "video",
                        "start_time": start_time,
                        "video_duration": video_duration,
                        "type": "video",
                    }, f)
                video_download = executor.submit(
                    subprocess.run,
                    ["python", video_dl_py, tweet_url],
                    check=True
                )

                with open("progress.json") as f:
                    existing = json.load(f)

                start_time = existing.get("start_time", time.time())

                with open("progress.json", "w") as f:
                    json.dump({
                        "status": "Downloading image...",
                        "step": "image",
                        "start_time": start_time,
                        "video_duration": video_duration,
                        "type": "video",
                    }, f)
                subprocess.run(["python", screenshot_py, "video", tweet_url, img_raw], check=True)

                with open("progress.json") as f:
                    existing = json.load(f)

                start_time = existing.get("start_time", time.time())

                with open("progress.json", "w") as f:
                    json.dump({
                        "status": "Cropping image...",
                        "step": "crop",
                        "start_time": start_time,
                        "video_duration": video_duration,
                        "type": "video",
                    }, f)
                subprocess.run([
                    "python", crop_py,
                    "tweet_card",
                    "blur",
                    img_raw,
                    img_final
                ], check=True)

                video_download.result()

                with open("progress.json") as f:
                    existing = json.load(f)

                start_time = existing.get("start_time", time.time())

                with open("progress.json", "w") as f:
                    json.dump({
                        "status": "Creating reel...",
                        "step": "reel",
                        "start_time": start_time,
                        "video_duration": video_duration,
                        "type": "video",
                    }, f)
                subprocess.run([
                    "python", assemble_py,
                    "blur",
                    img_final,
                    video_path,
                    reel_output
                ], check=True)

                with open("progress.json", "w") as f:
                    json.dump({"status": "Reel created."}, f)

                return redirect(url_for("reel_result", job_id=job_id))

            elif mode == "photo":
                with open("progress.json", "w") as f:
                    json.dump({
                        "status": "Downloading image...",
                        "step": "image",
                        "start_time": start_time,
                        "video_duration": 0,
                        "type": "photo",
                    }, f)
                subprocess.run(["python", screenshot_py, "photo", tweet_url, img_raw], check=True)

                with open("progress.json", "w") as f:
                    json.dump({
                        "status": "Cropping image...",
                        "step": "crop",
                        "start_time": start_time,
                        "video_duration": 0,
                        "type": "photo",
                    }, f)
                subprocess.run([
                    "python", crop_py,
                    "photo_card",
                    img_raw,
                    img_cropped
                ], check=True)

                with open("progress.json", "w") as f:
                    json.dump({
                        "status": "Padding image...",
                        "step": "pad",
                        "start_time": start_time,
                        "video_duration": 0,
                        "type": "photo",
                    }, f)
                subprocess.run([
                    "python", crop_py,
                    "pad_photo",
                    img_cropped,
                    img_final
                ], check=True)

                return redirect(url_for("photo_result", job_id=job_id))

        except subprocess.CalledProcessError as e:
            return render_template("index.html", error="Something went wrong during processing.")


    return render_template("index.html")

@app.route("/result/reel/<job_id>", endpoint="reel_result")
def result(job_id):
    filename = f"{job_id}_reel.mp4"
    return render_template("download_reel.html", filename=filename)

@app.route("/result/photo/<job_id>", endpoint="photo_result")
def result_photo(job_id):
    filename = f"{job_id}_photo.png"
    return render_template("download_photo.html", filename=filename)

@app.route("/download/<filename>")
def download(filename):
    path = os.path.join(results_dir, filename)
    return send_file(path, as_attachment=True)

@app.route("/health")
def health():
    return "App is running!"

step_weights = {
    "start": 0,
    "screenshot": 5,
    "crop": 1,
    "video": 1,
    "reel": 4,
    "done": 0
}

@app.route("/progress")
def progress():
    try:
        with open("progress.json", "r") as f:
            data = json.load(f)
    except Exception:
        return jsonify(status="Working...", time_left="Estimating...")

    status = data.get("status", "Working...")
    start_time = data.get("start_time", time.time())
    video_duration = data.get("video_duration", 0)
    type = data.get("type", "video")

    elapsed = time.time() - start_time

    if type == "photo":
        step_weights["reel"] = 0
        step_weights["video"] = 0
    elif type == "video":
        step_weights["reel"] = video_duration * 0.7
    steps = list(step_weights.keys())
    est_total = sum([step_weights[s] for s in steps])
    est_remaining = max(0, int(est_total - elapsed))

    return jsonify(
        status=status,
        time_left=f"~{est_remaining}s" if est_remaining else "Almost done"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))