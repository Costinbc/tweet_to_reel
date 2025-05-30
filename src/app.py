import json
import os
import subprocess
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, jsonify, render_template, request, send_file
from get_video_duration import get_video_duration

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
template_dir = os.path.join(base_dir, "templates")
static_dir = os.path.join(base_dir, "static")
downloads_dir = os.path.join(base_dir, "downloads")
results_dir = os.path.join(base_dir, "results")
src_dir = os.path.join(base_dir, "src")

os.makedirs(downloads_dir, exist_ok=True)
os.makedirs(results_dir, exist_ok=True)

screenshot_py = os.path.join(src_dir, "screenshot_ors.py")
crop_py = os.path.join(src_dir, "crop_tweet.py")
video_dl_py = os.path.join(src_dir, "video_dl.py")
assemble_py = os.path.join(src_dir, "assemble_reel.py")

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

executor = ThreadPoolExecutor(max_workers=4)

step_weights = {
    "start": 1,
    "screenshot": 5,
    "crop": 1,
    "video": 1,
    "reel": 4,
    "done": 1,
}

def progress_path(job_id: str) -> str:
    return os.path.join(base_dir, f"progress_{job_id}.json")

def write_progress(job_id: str, data: dict):
    with open(progress_path(job_id), "w") as f:
        json.dump(data, f)

def load_progress(job_id: str):
    try:
        with open(progress_path(job_id)) as f:
            return json.load(f)
    except Exception:
        return {}

def process_job(tweet_url: str, mode: str, job_id: str):
    tweet_id = tweet_url.rstrip("/").split("/")[-1]
    img_raw = os.path.join(downloads_dir, f"{tweet_id}.png")
    img_cropped = os.path.join(downloads_dir, f"{tweet_id}_cropped.png")
    img_final = os.path.join(results_dir, f"{job_id}_photo.png")
    video_path = os.path.join(downloads_dir, f"{tweet_id}_video.mp4")
    reel_output = os.path.join(results_dir, f"{job_id}_reel.mp4")

    start_time = time.time()
    write_progress(job_id, {
        "status": "Starting...",
        "step": "start",
        "start_time": start_time,
        "video_duration": 0,
        "type": mode,
    })

    if mode in ("white", "blur"):
        write_progress(job_id, {
            "status": "Downloading video...",
            "step": "video",
            "start_time": start_time,
            "video_duration": 0,
            "type": "video",
        })
        subprocess.run(["python", video_dl_py, tweet_url], check=True)

        video_duration = get_video_duration(video_path)
        write_progress(job_id, {
            "status": "Downloading image...",
            "step": "screenshot",
            "start_time": start_time,
            "video_duration": video_duration,
            "type": "video",
        })
        subprocess.run(["python", screenshot_py, "video", tweet_url, img_raw], check=True)

        video_duration = get_video_duration(video_path)
        write_progress(job_id, {
            "status": "Cropping image...",
            "step": "crop",
            "start_time": start_time,
            "video_duration": video_duration,
            "type": "video",
        })
        subprocess.run(["python", crop_py, "tweet_card", mode, img_raw, img_final], check=True)

        video_duration = get_video_duration(video_path)
        write_progress(job_id, {
            "status": "Creating reel...",
            "step": "reel",
            "start_time": start_time,
            "video_duration": video_duration,
            "type": "video",
        })
        subprocess.run(["python", assemble_py, mode, img_final, video_path, reel_output], check=True)

        write_progress(job_id, {
            "status": "Reel created.",
            "step": "done",
            "start_time": start_time,
            "video_duration": video_duration,
            "type": "video",
            "redirect_url": f"/result/reel/{job_id}",
        })

    else:
        write_progress(job_id, {
            "status": "Downloading image...",
            "step": "screenshot",
            "start_time": start_time,
            "video_duration": 0,
            "type": "photo",
        })
        subprocess.run(["python", screenshot_py, "photo", tweet_url, img_raw], check=True)

        write_progress(job_id, {
            "status": "Cropping image...",
            "step": "crop",
            "start_time": start_time,
            "video_duration": 0,
            "type": "photo",
        })
        subprocess.run(["python", crop_py, "photo_card", img_raw, img_cropped], check=True)

        write_progress(job_id, {
            "status": "Padding image...",
            "step": "pad",
            "start_time": start_time,
            "video_duration": 0,
            "type": "photo",
        })
        subprocess.run(["python", crop_py, "pad_photo", img_cropped, img_final], check=True)

        write_progress(job_id, {
            "status": "Reel created.",
            "step": "done",
            "start_time": start_time,
            "video_duration": 0,
            "type": "photo",
            "redirect_url": f"/result/photo/{job_id}",
        })

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        tweet_url = request.form.get("url")
        mode = request.form.get("mode")
        if not tweet_url:
            return render_template("index.html", error="Please enter a tweet URL")

        job_id = uuid.uuid4().hex[:8]
        executor.submit(process_job, tweet_url, mode, job_id)
        return jsonify(job_id=job_id, type=mode), 202

    return render_template("index.html")

@app.route("/result/reel/<job_id>")
def reel_result(job_id):
    return render_template("download_reel.html", filename=f"{job_id}_reel.mp4")

@app.route("/result/photo/<job_id>")
def photo_result(job_id):
    return render_template("download_photo.html", filename=f"{job_id}_photo.png")

@app.route("/download/<filename>")
def download(filename):
    return send_file(os.path.join(results_dir, filename), as_attachment=True)

@app.route("/health")
def health():
    return "App is running!"

@app.route("/progress")
def progress():
    job_id = request.args.get("job_id")
    if not job_id:
        resp = jsonify(status="Waiting...", time_left="-")
        resp.headers["Cache-Control"] = "no-store"
        return resp

    data = load_progress(job_id)
    if not data:
        resp = jsonify(status="Starting...", time_left="Estimating...")
        resp.headers["Cache-Control"] = "no-store"
        return resp

    status = data.get("status", "Working...")
    start_time = data.get("start_time", time.time())
    video_duration = data.get("video_duration", 0)
    step = data.get("step", "start")
    type_ = data.get("type", "video")

    no_video_duration = False

    if type_ == "photo":
        step_weights["reel"] = 0
        step_weights["video"] = 0
    else:
        if video_duration:
            step_weights["reel"] = int(video_duration * 0.9)
        else:
            step_weights["reel"] = 0
            no_video_duration = True

    elapsed = time.time() - start_time
    est_total = sum(step_weights.values())
    est_remaining = max(int(est_total - elapsed), 0)
    if no_video_duration:
        est_remaining = 0

    resp = jsonify(
        status=status,
        time_left=f"~{est_remaining}s" if est_remaining else "Wait...",
        redirect_url=data.get("redirect_url"),
    )
    resp.headers["Cache-Control"] = "no-store"
    return resp

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
